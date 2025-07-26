from typing import List, Dict, Any
import uuid

from sqlalchemy.orm import Session
from loguru import logger
import asyncio
from datetime import datetime, timedelta

from app.tasks.celery_app import celery_app
from app.monitoring import get_metrics_collector
from app.database import SessionLocal
from app.tenancy import set_current_tenant
from app.models import Job, JobStatus, CrawlResult, Dataset, DataRecord
from app.repositories import DiscoveryRepository
from app.agents import PlannerAgent, DiscoveryAgent, SchemaInferenceAgent
from app.crawler import BrowserCrawler
from app.tasks.progress_tracker import ProgressContext, JobProgressTracker


async def _run_mining_job(job_id: str) -> Dict[str, Any]:
    """Async helper to orchestrate the mining pipeline."""
    db = SessionLocal()
    metrics = get_metrics_collector()
    job_start = datetime.utcnow()
    metrics.record_job_started()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        set_current_tenant(job.tenant_id)

        logger.info(f"Starting mining job {job_id}: {job.prompt}")

        tracker = JobProgressTracker(job_id)
        await tracker.update_status(JobStatus.PLANNING, "Starting job execution")

        async with ProgressContext(job_id, "planning", 100) as progress:
            plan = await execute_planning_phase(job, db, progress)

        async with ProgressContext(job_id, "discovering", 100) as progress:
            discovered_urls = await execute_discovery_phase(job, plan, db, progress)

        async with ProgressContext(
            job_id, "crawling", len(discovered_urls)
        ) as progress:
            crawl_results = await execute_crawling_phase(
                job, discovered_urls, db, progress
            )

        async with ProgressContext(
            job_id, "extracting", len(crawl_results)
        ) as progress:
            extracted_data = await execute_extraction_phase(
                job, crawl_results, db, progress
            )

        summary = {
            "total_urls_discovered": len(discovered_urls),
            "total_pages_crawled": len(crawl_results),
            "total_records_extracted": len(extracted_data),
            "job_duration": str(datetime.utcnow() - job.started_at),
        }

        await tracker.complete_job(summary)
        metrics.record_job_completed(
            duration=(datetime.utcnow() - job_start).total_seconds()
        )
        return {"job_id": job_id, "status": "completed", "summary": summary}

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        metrics.record_job_failed(
            duration=(datetime.utcnow() - job_start).total_seconds()
        )
        tracker = JobProgressTracker(job_id)
        await tracker.report_error(str(e))
        raise

    finally:
        set_current_tenant(None)
        db.close()


@celery_app.task(bind=True)
def start_mining_job(self, job_id: str):
    """Entry point for the mining job Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        try:
            return loop.run_until_complete(_run_mining_job(job_id))
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Unhandled exception for job {job_id}: {exc}")
            raise
    finally:
        loop.close()


async def execute_planning_phase(
    job: Job, db: Session, progress: ProgressContext | None = None
) -> Dict[str, Any]:
    """Execute the planning phase."""
    try:
        if progress:
            await progress.log("Starting planning phase", "info")

        planner = PlannerAgent()
        plan = await planner.execute(job.prompt)

        job.plan = plan
        db.commit()

        if progress:
            await progress.update_step(100, {"plan": plan})
            await progress.log("Planning phase completed", "success")

        # Return plan as dict if possible
        if hasattr(plan, "dict"):
            return plan.dict()
        return plan

    except Exception as e:
        if progress:
            await progress.log(f"Planning failed: {str(e)}", "error")
        raise


async def execute_discovery_phase(
    job: Job, plan: Dict[str, Any], db: Session, progress: ProgressContext | None = None
) -> List[str]:
    """Execute the discovery phase."""
    try:
        if progress:
            await progress.log("Starting discovery phase", "info")

        discovery_agent = DiscoveryAgent()
        discovered_urls = await discovery_agent.execute(plan)

        repo = DiscoveryRepository(db)
        # Store discovered URLs
        for url in discovered_urls:
            repo.create_discovered_url(
                job_id=job.id,
                tenant_id=job.tenant_id,
                url=url,
                discovery_method="discovery",
            )
        repo.commit()

        job.total_urls = len(discovered_urls)

        if progress:
            await progress.update_step(100, {"discovered_urls": len(discovered_urls)})
            await progress.log(f"Discovered {len(discovered_urls)} URLs", "success")

        return discovered_urls

    except Exception as e:
        if progress:
            await progress.log(f"Discovery failed: {str(e)}", "error")
        raise


async def execute_crawling_phase(
    job: Job, urls: List[str], db: Session, progress: ProgressContext | None = None
) -> List[Dict[str, Any]]:
    """Execute the crawling phase."""
    try:
        if progress:
            await progress.log("Starting crawling phase", "info")

        async with BrowserCrawler() as crawler:
            raw_results = await crawler.crawl_multiple_urls(urls, str(job.id))

        crawl_results: List[Dict[str, Any]] = []
        objects_to_save: List[CrawlResult] = []

        for result in raw_results:
            url = result.get("url")
            if progress:
                await progress.log(f"Processed {url}", "info")

            try:
                crawl_result = CrawlResult(
                    id=uuid.uuid4(),
                    job_id=job.id,
                    tenant_id=job.tenant_id,
                    url=url,
                    html_content=result.get("html_content", ""),
                    screenshot_path=result.get("screenshot_path"),
                    title=result.get("title", ""),
                    meta_description=result.get("meta_description", ""),
                    status_code=result.get("status_code", 200),
                )
                objects_to_save.append(crawl_result)

                crawl_results.append(
                    {
                        "url": url,
                        "crawl_result_id": str(crawl_result.id),
                        "title": result.get("title", ""),
                        "content_length": len(result.get("html_content", "")),
                    }
                )

                if progress:
                    await progress.increment(
                        {
                            "url": url,
                            "crawl_result_id": str(crawl_result.id),
                            "title": result.get("title", ""),
                            "content_length": len(result.get("html_content", "")),
                        }
                    )
                    await progress.increment({"url": url, "status": "success"})

            except Exception as e:
                if progress:
                    await progress.log(
                        f"Failed to save result for {url}: {str(e)}", "warning"
                    )
                    await progress.increment(
                        {"url": url, "status": "failed", "error": str(e)}
                    )

        # Bulk save all crawl results
        if objects_to_save:
            db.bulk_save_objects(objects_to_save)
            db.commit()

        if progress:
            await progress.log(
                f"Crawled {len(crawl_results)} pages successfully", "success"
            )

        return crawl_results

    except Exception as e:
        if progress:
            await progress.log(f"Crawling failed: {str(e)}", "error")
        raise


async def execute_extraction_phase(
    job: Job,
    crawl_results: List[Dict[str, Any]],
    db: Session,
    progress: ProgressContext | None = None,
) -> List[Dict[str, Any]]:
    """Execute the data extraction phase."""
    try:
        if progress:
            await progress.log("Starting extraction phase", "info")

        extracted_data: List[Dict[str, Any]] = []
        records_to_save: List[DataRecord] = []

        # Create dataset
        dataset = Dataset(
            id=uuid.uuid4(),
            job_id=job.id,
            tenant_id=job.tenant_id,
            name=f"Dataset for {job.prompt[:50]}...",
            description=f"Automatically extracted data for prompt: {job.prompt}",
            schema={"type": "object", "properties": {}},
        )
        db.add(dataset)

        # Extract data from each crawl result
        for i, result in enumerate(crawl_results):
            if progress:
                await progress.log(
                    f"Extracting data from page {i + 1}/{len(crawl_results)}",
                    "info",
                )

            try:
                # Get crawl result from database
                crawl_result = (
                    db.query(CrawlResult)
                    .filter(CrawlResult.id == result["crawl_result_id"])
                    .first()
                )
                if not crawl_result:
                    continue

                # Use schema inference agent to extract data
                schema_agent = SchemaInferenceAgent()
                result_data = await schema_agent.execute(
                    crawl_result.html_content,
                    crawl_result.url,
                    job.plan,
                )
                records = result_data.get("data", [])

                # Store extracted records
                for record in records:
                    data_record = DataRecord(
                        id=uuid.uuid4(),
                        dataset_id=dataset.id,
                        tenant_id=job.tenant_id,
                        source_url=crawl_result.url,
                        data=record,
                    )
                    records_to_save.append(data_record)
                    extracted_data.append(record)

                if progress:
                    await progress.increment(
                        {
                            "extracted_records": len(records),
                            "source_url": crawl_result.url,
                        }
                    )

            except Exception as e:
                if progress:
                    await progress.log(
                        f"Failed to extract from {result['url']}: {str(e)}",
                        "warning",
                    )

        # Bulk save all data records
        if records_to_save:
            db.bulk_save_objects(records_to_save)

        # Update job with final counts
        job.extracted_records = len(extracted_data)
        db.commit()

        if progress:
            await progress.log(
                f"Extracted {len(extracted_data)} records successfully", "success"
            )

        return extracted_data

    except Exception as e:
        if progress:
            await progress.log(f"Extraction failed: {str(e)}", "error")
        raise


@celery_app.task
def cleanup_old_jobs():
    """Periodic task to clean up old completed jobs."""
    db = SessionLocal()
    try:
        # Delete jobs older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        old_jobs = (
            db.query(Job)
            .execution_options(include_all_tenants=True)
            .filter(
                Job.completed_at < cutoff_date,
                Job.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]),
            )
            .all()
        )

        for job in old_jobs:
            db.delete(job)

        db.commit()
        logger.info(f"Cleaned up {len(old_jobs)} old jobs")

    except Exception as e:
        logger.error(f"Failed to cleanup old jobs: {e}")
        db.rollback()
    finally:
        db.close()
