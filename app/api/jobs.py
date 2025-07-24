from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import JobStatus, User
from app.auth.dependencies import get_current_active_user
from app.tasks.mining_tasks import start_mining_job
from app.utils import sanitize_prompt
from app.middleware import rbac_required, user_limiter, tenant_limiter, RateLimits
from app.repositories.job_repository import JobRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_repository(db: Session = Depends(get_db)) -> JobRepository:
    """Dependency injector for ``JobRepository``."""
    return JobRepository(db)


class JobCreate(BaseModel):
    prompt: str


class JobResponse(BaseModel):
    id: str
    prompt: str
    status: str
    plan: dict = None
    total_urls: int = 0
    crawled_urls: int = 0
    extracted_records: int = 0
    created_at: str
    started_at: str = None
    completed_at: str = None
    error_message: str = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    size: int


@router.post("/", response_model=JobResponse)
@rbac_required(permissions=["jobs:create"])
@user_limiter.limit(RateLimits.USER_JOBS)
@tenant_limiter.limit(RateLimits.TENANT_JOBS)
async def create_job(
    job_data: JobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    job_repo: JobRepository = Depends(get_job_repository),
):
    """Create a new mining job."""
    try:
        sanitize_prompt(job_data.prompt)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Create job record
    job = job_repo.create_job(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        prompt=job_data.prompt,
    )

    # Start background task
    background_tasks.add_task(start_mining_job.delay, str(job.id))

    return JobResponse(
        id=str(job.id),
        prompt=job.prompt,
        status=job.status.value,
        plan=job.plan,
        total_urls=job.total_urls,
        crawled_urls=job.crawled_urls,
        extracted_records=job.extracted_records,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        error_message=job.error_message,
    )


@router.get("/", response_model=JobListResponse)
@rbac_required(permissions=["jobs:read"])
@user_limiter.limit(RateLimits.USER_JOBS)
@tenant_limiter.limit(RateLimits.TENANT_JOBS)
async def list_jobs(
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    job_repo: JobRepository = Depends(get_job_repository),
):
    """List user's jobs with pagination."""

    status_enum: Optional[JobStatus] = None
    if status:
        try:
            status_enum = JobStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}",
            )

    jobs, total = job_repo.list_jobs(
        tenant_id=current_user.tenant_id,
        status=status_enum,
        page=page,
        size=size,
    )

    # Convert to response format
    job_responses = []
    for job in jobs:
        job_responses.append(
            JobResponse(
                id=str(job.id),
                prompt=job.prompt,
                status=job.status.value,
                plan=job.plan,
                total_urls=job.total_urls,
                crawled_urls=job.crawled_urls,
                extracted_records=job.extracted_records,
                created_at=job.created_at.isoformat(),
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                error_message=job.error_message,
            )
        )

    return JobListResponse(jobs=job_responses, total=total, page=page, size=size)


@router.get("/{job_id}", response_model=JobResponse)
@rbac_required(permissions=["jobs:read"])
@user_limiter.limit(RateLimits.USER_JOBS)
@tenant_limiter.limit(RateLimits.TENANT_JOBS)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    job_repo: JobRepository = Depends(get_job_repository),
):
    """Get job details."""

    job = job_repo.get_job(job_id, current_user.tenant_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    return JobResponse(
        id=str(job.id),
        prompt=job.prompt,
        status=job.status.value,
        plan=job.plan,
        total_urls=job.total_urls,
        crawled_urls=job.crawled_urls,
        extracted_records=job.extracted_records,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        error_message=job.error_message,
    )


@router.delete("/{job_id}")
@rbac_required(permissions=["jobs:delete"])
@user_limiter.limit(RateLimits.USER_JOBS)
@tenant_limiter.limit(RateLimits.TENANT_JOBS)
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    job_repo: JobRepository = Depends(get_job_repository),
):
    """Cancel a running job."""

    job = job_repo.get_job(job_id, current_user.tenant_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Job cannot be cancelled"
        )

    # Update job status
    job_repo.cancel_job(job)

    return {"message": "Job cancelled successfully"}


@router.post("/{job_id}/restart")
@rbac_required(permissions=["jobs:restart"])
@user_limiter.limit(RateLimits.USER_JOBS)
@tenant_limiter.limit(RateLimits.TENANT_JOBS)
async def restart_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    job_repo: JobRepository = Depends(get_job_repository),
):
    """Restart a failed or cancelled job."""

    job = job_repo.get_job(job_id, current_user.tenant_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    if job.status not in [JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed or cancelled jobs can be restarted",
        )

    # Reset job status
    job_repo.restart_job(job)

    # Start background task
    background_tasks.add_task(start_mining_job.delay, str(job.id))

    return {"message": "Job restarted successfully"}
