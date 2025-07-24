from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple
import uuid

from sqlalchemy.orm import Session

from app.models import Job, JobStatus


class JobRepository:
    """Data access layer for ``Job`` objects."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(self, user_id: uuid.UUID, tenant_id: uuid.UUID, prompt: str) -> Job:
        job = Job(user_id=user_id, tenant_id=tenant_id, prompt=prompt, status=JobStatus.PENDING)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def list_jobs(
        self,
        tenant_id: uuid.UUID,
        status: Optional[JobStatus],
        page: int,
        size: int,
    ) -> Tuple[List[Job], int]:
        query = self.db.query(Job).filter(Job.tenant_id == tenant_id)
        if status:
            query = query.filter(Job.status == status)
        total = query.count()
        offset = (page - 1) * size
        jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(size).all()
        return jobs, total

    def get_job(self, job_id: str, tenant_id: uuid.UUID) -> Optional[Job]:
        return (
            self.db.query(Job)
            .filter(Job.id == job_id, Job.tenant_id == tenant_id)
            .first()
        )

    def cancel_job(self, job: Job) -> None:
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        self.db.commit()

    def restart_job(self, job: Job) -> None:
        job.status = JobStatus.PENDING
        job.started_at = None
        job.completed_at = None
        job.error_message = None
        job.crawled_urls = 0
        job.extracted_records = 0
        self.db.commit()
