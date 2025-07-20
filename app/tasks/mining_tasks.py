from typing import List, Dict, Any, Optional
from celery import current_task
from sqlalchemy.orm import Session
from loguru import logger
import asyncio
from datetime import datetime, timedelta

from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models import Job, JobStatus, DiscoveredURL, CrawlResult, Dataset, DataRecord
from app.agents import PlannerAgent, DiscoveryAgent, SchemaInferenceAgent
from app.crawler import BrowserCrawler
from app.storage import VectorStore, EmbeddingGenerator


@celery_app.task(bind=True)
def start_mining_job(self, job_id: str):
    """
    Main task to orchestrate the complete web mining pipeline.
    
    Args:
        job_id: UUID of the job to execute
    """
    db = SessionLocal()
    try:
        # Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        logger.info(f"Starting mining job {job_id}: {job.prompt}")
        
        # Update job status
        job.status = JobStatus.PLANNING
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Phase 1: Planning
        self.update_state(state='PROGRESS', meta={'phase': 'planning', 'progress': 10})
        plan = execute_planning_phase(job, db)
        
        # Phase 2: Discovery
        self.update_state(state='PROGRESS', meta={'phase': 'discovery', 'progress': 30})
        discovered_urls = execute_discovery_phase(job, plan, db)
        
        # Phase 3: Crawling
        self.update_state(state='PROGRESS', meta={'phase': 'crawling', 'progress': 50})
        crawl_results = execute_crawling_phase(job, discovered_urls, db)
        
        # Phase 4: Data Extraction
        self.update_state(state='PROGRESS', meta={'phase': 'extraction', 'progress': 80})
        dataset = execute_extraction_phase(job, crawl_results, plan, db)
        
        # Phase 5: Vector Storage
        self.update_state(state='PROGRESS', meta={'phase': 'vectorization', 'progress': 95})
        execute_vectorization_phase(job, dataset, db)
        
        # Complete job
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Completed mining job {job_id}")
        return {
            'status': 'completed',
            'job_id': job_id,
            'extracted_records': job.extracted_records,
            'total_urls': job.total_urls
        }
        
    except Exception as e:
        logger.error(f"Mining job {job_id} failed: {e}")
        
        # Update job with error
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        raise
        
    finally:
        db.close()


def execute_planning_phase(job: Job, db: Session) -> Dict[str, Any]:
    """Execute the planning phase using PlannerAgent."""
    
    # Initialize planner agent
    planner = PlannerAgent()
    
    # Generate plan
    plan = asyncio.run(planner.execute(job.prompt))
    
    # Save plan to job
    job.plan = plan
    job.status = JobStatus.DISCOVERING
    db.commit()
    
    logger.info(f"Generated plan for job {job.id}: {plan.get('summary', '')}")
    return plan


def execute_discovery_phase(job: Job, plan: Dict[str, Any], db: Session) -> List[DiscoveredURL]:
    """Execute URL discovery phase using DiscoveryAgent."""
    
    # Initialize discovery agent
    discovery_agent = DiscoveryAgent()
    
    # Discover URLs
    discovered_data = asyncio.run(discovery_agent.execute(plan))
    
    # Save discovered URLs to database
    discovered_urls = []
    for url_data in discovered_data:
        discovered_url = DiscoveredURL(
            job_id=job.id,
            url=url_data.get('url'),
            title=url_data.get('title'),
            description=url_data.get('description'),
            discovery_method='llm_discovery',
            priority=url_data.get('priority', 3)
        )
        db.add(discovered_url)
        discovered_urls.append(discovered_url)
    
    # Update job statistics
    job.total_urls = len(discovered_urls)
    job.status = JobStatus.CRAWLING
    db.commit()
    
    logger.info(f"Discovered {len(discovered_urls)} URLs for job {job.id}")
    return discovered_urls


def execute_crawling_phase(job: Job, discovered_urls: List[DiscoveredURL], db: Session) -> List[CrawlResult]:
    """Execute crawling phase using BrowserCrawler."""
    
    # Extract URLs for crawling
    urls_to_crawl = [du.url for du in discovered_urls]
    
    # Execute crawling
    crawl_results = asyncio.run(crawl_urls_batch(urls_to_crawl, str(job.id)))
    
    # Save crawl results to database
    saved_results = []
    for i, result in enumerate(crawl_results):
        discovered_url = discovered_urls[i]
        
        crawl_result = CrawlResult(
            discovered_url_id=discovered_url.id,
            status_code=result.get('status_code'),
            success=result.get('success', False),
            error_message=result.get('error_message'),
            raw_html=result.get('html_content'),
            page_title=result.get('title'),
            meta_description=result.get('meta_description'),
            html_file_path=result.get('html_file_path'),
            screenshot_path=result.get('screenshot_path')
        )
        
        db.add(crawl_result)
        saved_results.append(crawl_result)
        
        # Update discovered URL status
        discovered_url.is_crawled = True
        discovered_url.last_crawl_attempt = datetime.utcnow()
        
        # Update job progress
        job.crawled_urls += 1
    
    job.status = JobStatus.EXTRACTING
    db.commit()
    
    logger.info(f"Crawled {len(saved_results)} URLs for job {job.id}")
    return saved_results


async def crawl_urls_batch(urls: List[str], job_id: str) -> List[Dict[str, Any]]:
    """Crawl multiple URLs using BrowserCrawler."""
    
    async with BrowserCrawler() as crawler:
        results = await crawler.crawl_multiple_urls(urls, job_id)
    
    return results


def execute_extraction_phase(job: Job, crawl_results: List[CrawlResult], plan: Dict[str, Any], db: Session) -> Dataset:
    """Execute data extraction phase using SchemaInferenceAgent."""
    
    # Create dataset
    dataset = Dataset(
        job_id=job.id,
        name=f"Dataset for: {job.prompt[:100]}",
        description=plan.get('summary', ''),
        schema=None  # Will be updated with inferred schema
    )
    db.add(dataset)
    db.flush()  # Get dataset ID
    
    # Initialize schema inference agent
    schema_agent = SchemaInferenceAgent()
    
    # Process successful crawl results
    all_extracted_data = []
    common_schema = None
    
    for crawl_result in crawl_results:
        if not crawl_result.success or not crawl_result.raw_html:
            continue
        
        try:
            # Extract data using schema inference
            extraction_result = asyncio.run(
                schema_agent.execute(
                    crawl_result.raw_html,
                    crawl_result.discovered_url.url,
                    plan
                )
            )
            
            if extraction_result.get('data'):
                # Store extraction results
                crawl_result.extracted_data = extraction_result['data']
                crawl_result.schema_inference = extraction_result['schema']
                
                # Create data records
                for record_data in extraction_result['data']:
                    data_record = DataRecord(
                        dataset_id=dataset.id,
                        source_url=crawl_result.discovered_url.url,
                        source_title=crawl_result.page_title,
                        data=record_data,
                        confidence_score=extraction_result.get('confidence', 0.0),
                        extraction_method='llm_inference'
                    )
                    db.add(data_record)
                    all_extracted_data.append(data_record)
                
                # Update common schema (use the first good schema)
                if not common_schema and extraction_result.get('schema'):
                    common_schema = extraction_result['schema']
        
        except Exception as e:
            logger.error(f"Extraction failed for {crawl_result.discovered_url.url}: {e}")
            continue
    
    # Update dataset with final statistics and schema
    dataset.total_records = len(all_extracted_data)
    dataset.total_sources = len([cr for cr in crawl_results if cr.success])
    dataset.schema = common_schema
    
    # Update job statistics
    job.extracted_records = len(all_extracted_data)
    
    db.commit()
    
    logger.info(f"Extracted {len(all_extracted_data)} records for job {job.id}")
    return dataset


def execute_vectorization_phase(job: Job, dataset: Dataset, db: Session):
    """Execute vectorization phase for semantic search."""
    
    # Initialize embedding generator and vector store
    embedding_gen = EmbeddingGenerator()
    vector_store = VectorStore(dimension=embedding_gen.get_embedding_dimension())
    
    # Load existing vector store if available
    vector_store.load()
    
    # Get data records
    data_records = db.query(DataRecord).filter(DataRecord.dataset_id == dataset.id).all()
    
    if not data_records:
        logger.warning(f"No data records found for vectorization in dataset {dataset.id}")
        return
    
    # Generate embeddings for records
    embeddings = []
    metadata = []
    
    for record in data_records:
        try:
            # Generate embedding for the record
            embedding = embedding_gen.embed_data_record(record.data)
            embeddings.append(embedding)
            
            # Prepare metadata
            record_metadata = {
                'record_id': str(record.id),
                'dataset_id': str(dataset.id),
                'job_id': str(job.id),
                'source_url': record.source_url,
                'source_title': record.source_title or '',
                'data_preview': str(record.data)[:200],  # First 200 chars
                'confidence_score': record.confidence_score or 0.0
            }
            metadata.append(record_metadata)
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for record {record.id}: {e}")
            continue
    
    if embeddings:
        # Add vectors to store
        embeddings_array = np.array(embeddings)
        vector_ids = vector_store.add_vectors(embeddings_array, metadata)
        
        # Update records with vector IDs
        for i, record in enumerate(data_records[:len(vector_ids)]):
            record.embedding_id = vector_ids[i]
        
        # Save vector store
        vector_store.save()
        
        db.commit()
        
        logger.info(f"Generated {len(embeddings)} embeddings for dataset {dataset.id}")


@celery_app.task
def crawl_urls_task(urls: List[str], job_id: str):
    """Standalone task for crawling URLs."""
    return asyncio.run(crawl_urls_batch(urls, job_id))


@celery_app.task
def extract_data_task(html_content: str, url: str, plan: Dict[str, Any]):
    """Standalone task for data extraction."""
    schema_agent = SchemaInferenceAgent()
    return asyncio.run(schema_agent.execute(html_content, url, plan))


@celery_app.task
def cleanup_old_jobs():
    """Periodic task to clean up old completed jobs."""
    db = SessionLocal()
    try:
        # Delete jobs older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_jobs = db.query(Job).filter(
            Job.completed_at < cutoff_date,
            Job.status.in_([JobStatus.COMPLETED, JobStatus.FAILED])
        ).all()
        
        for job in old_jobs:
            db.delete(job)
        
        db.commit()
        logger.info(f"Cleaned up {len(old_jobs)} old jobs")
        
    except Exception as e:
        logger.error(f"Failed to cleanup old jobs: {e}")
        db.rollback()
    finally:
        db.close()