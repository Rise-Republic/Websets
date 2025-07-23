from typing import List, Dict, Any

from sqlalchemy.orm import Session
from loguru import logger
import asyncio
from datetime import datetime, timedelta

from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models import Job, JobStatus, DiscoveredURL, CrawlResult, Dataset, DataRecord
from app.agents import PlannerAgent, DiscoveryAgent, SchemaInferenceAgent
from app.crawler import BrowserCrawler
from app.tasks.progress_tracker import ProgressContext, JobProgressTracker


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
        
        # Initialize progress tracker
        tracker = JobProgressTracker(job_id)
        
        # Update job status
        asyncio.run(tracker.update_status(JobStatus.PLANNING, "Starting job execution"))
        
        # Phase 1: Planning
        with ProgressContext(job_id, "planning", 100) as progress:
            plan = execute_planning_phase(job, db, progress)
        
        # Phase 2: Discovery
        with ProgressContext(job_id, "discovering", 100) as progress:
            discovered_urls = execute_discovery_phase(job, plan, db, progress)
        
        # Phase 3: Crawling
        with ProgressContext(job_id, "crawling", len(discovered_urls)) as progress:
            crawl_results = execute_crawling_phase(job, discovered_urls, db, progress)
        
        # Phase 4: Data Extraction
        with ProgressContext(job_id, "extracting", len(crawl_results)) as progress:
            extracted_data = execute_extraction_phase(job, crawl_results, db, progress)
        
        # Complete job
        summary = {
            "total_urls_discovered": len(discovered_urls),
            "total_pages_crawled": len(crawl_results),
            "total_records_extracted": len(extracted_data),
            "job_duration": str(datetime.utcnow() - job.started_at)
        }
        
        asyncio.run(tracker.complete_job(summary))
        
        return {
            "job_id": job_id,
            "status": "completed",
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        tracker = JobProgressTracker(job_id)
        asyncio.run(tracker.report_error(str(e)))
        raise
    finally:
        db.close()


def execute_planning_phase(job: Job, db: Session, progress: ProgressContext = None) -> Dict[str, Any]:
    """Execute the planning phase."""
    try:
        if progress:
            asyncio.run(progress.log("Starting planning phase", "info"))
        
        planner = PlannerAgent()
        plan = asyncio.run(planner.execute(job.prompt))

        job.plan = plan
        db.commit()

        if progress:
            asyncio.run(progress.update_step(100, {"plan": plan}))
            asyncio.run(progress.log("Planning phase completed", "success"))
        
        return plan.dict()
        
    except Exception as e:
        if progress:
            asyncio.run(progress.log(f"Planning failed: {str(e)}", "error"))
        raise


def execute_discovery_phase(job: Job, plan: Dict[str, Any], db: Session, progress: ProgressContext = None) -> List[str]:
    """Execute the discovery phase."""
    try:
        if progress:
            asyncio.run(progress.log("Starting discovery phase", "info"))
        
        discovery_agent = DiscoveryAgent()
        discovered_urls = asyncio.run(discovery_agent.execute(plan))
        
        # Store discovered URLs
        for url in discovered_urls:
            discovered_url = DiscoveredURL(
                job_id=job.id,
                url=url,
                source="discovery"
            )
            db.add(discovered_url)
        
        job.total_urls = len(discovered_urls)
        db.commit()
        
        if progress:
            asyncio.run(progress.update_step(100, {"discovered_urls": len(discovered_urls)}))
            asyncio.run(progress.log(f"Discovered {len(discovered_urls)} URLs", "success"))
        
        return discovered_urls
        
    except Exception as e:
        if progress:
            asyncio.run(progress.log(f"Discovery failed: {str(e)}", "error"))
        raise


def execute_crawling_phase(job: Job, urls: List[str], db: Session, progress: ProgressContext = None) -> List[Dict[str, Any]]:
    """Execute the crawling phase."""
    try:
        if progress:
            asyncio.run(progress.log("Starting crawling phase", "info"))
        
        crawl_results = []
        
        for i, url in enumerate(urls):
            if progress:
                asyncio.run(progress.log(f"Crawling URL {i+1}/{len(urls)}: {url}", "info"))
            
            try:
                crawler = BrowserCrawler()
                result = asyncio.run(crawler.crawl_url(url, str(job.id)))
                
                crawl_result = CrawlResult(
                    job_id=job.id,
                    url=url,
                    html_content=result.get("html", ""),
                    screenshot_path=result.get("screenshot_path"),
                    title=result.get("title", ""),
                    meta_description=result.get("meta_description", ""),
                    status_code=result.get("status_code", 200)
                )
                db.add(crawl_result)
                db.commit()
                
                crawl_results.append({
                    "url": url,
                    "crawl_result_id": str(crawl_result.id),
                    "title": result.get("title", ""),
                    "content_length": len(result.get("html", ""))
                })
                
                if progress:
                    asyncio.run(progress.increment({
                        "url": url,
                        "status": "success"
                    }))
                
            except Exception as e:
                if progress:
                    asyncio.run(progress.log(f"Failed to crawl {url}: {str(e)}", "warning"))
                    asyncio.run(progress.increment({
                        "url": url,
                        "status": "failed",
                        "error": str(e)
                    }))
        
        if progress:
            asyncio.run(progress.log(f"Crawled {len(crawl_results)} pages successfully", "success"))
        
        return crawl_results
        
    except Exception as e:
        if progress:
            asyncio.run(progress.log(f"Crawling failed: {str(e)}", "error"))
        raise


def execute_extraction_phase(job: Job, crawl_results: List[Dict[str, Any]], db: Session, progress: ProgressContext = None) -> List[Dict[str, Any]]:
    """Execute the data extraction phase."""
    try:
        if progress:
            asyncio.run(progress.log("Starting extraction phase", "info"))
        
        extracted_data = []
        
        # Create dataset
        dataset = Dataset(
            job_id=job.id,
            name=f"Dataset for {job.prompt[:50]}...",
            description=f"Automatically extracted data for prompt: {job.prompt}",
            schema={"type": "object", "properties": {}}
        )
        db.add(dataset)
        db.commit()
        
        # Extract data from each crawl result
        for i, result in enumerate(crawl_results):
            if progress:
                asyncio.run(progress.log(f"Extracting data from page {i+1}/{len(crawl_results)}", "info"))
            
            try:
                # Get crawl result from database
                crawl_result = db.query(CrawlResult).filter(
                    CrawlResult.id == result["crawl_result_id"]
                ).first()
                
                if not crawl_result:
                    continue
                
                # Use schema inference agent to extract data
                schema_agent = SchemaInferenceAgent()
                result_data = asyncio.run(
                    schema_agent.execute(
                        crawl_result.html_content,
                        crawl_result.url,
                        job.plan,
                    )
                )
                extracted = result_data.get("data", [])
                
                # Store extracted records
                for record in extracted:
                    data_record = DataRecord(
                        dataset_id=dataset.id,
                        crawl_result_id=crawl_result.id,
                        data=record,
                        url=crawl_result.url
                    )
                    db.add(data_record)
                    extracted_data.append(record)
                
                db.commit()
                
                if progress:
                    asyncio.run(progress.increment({
                        "extracted_records": len(extracted),
                        "url": crawl_result.url
                    }))
                
            except Exception as e:
                if progress:
                    asyncio.run(progress.log(f"Failed to extract from {result['url']}: {str(e)}", "warning"))
        
        # Update job with final counts
        job.extracted_records = len(extracted_data)
        db.commit()
        
        if progress:
            asyncio.run(progress.log(f"Extracted {len(extracted_data)} records successfully", "success"))
        
        return extracted_data
        
    except Exception as e:
        if progress:
            asyncio.run(progress.log(f"Extraction failed: {str(e)}", "error"))
        raise



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