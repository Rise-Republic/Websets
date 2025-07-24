from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Job, JobStatus, User
from app.auth.dependencies import get_current_active_user
from app.tasks.mining_tasks import start_mining_job
from app.middleware import rbac_required

router = APIRouter(prefix="/jobs", tags=["v1-jobs"])


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
async def create_job(
    job_data: JobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new mining job."""
    
    # Create job record
    job = Job(
        user_id=current_user.id,
        prompt=job_data.prompt,
        status=JobStatus.PENDING
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
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
        error_message=job.error_message
    )


@router.get("/", response_model=JobListResponse)
@rbac_required(permissions=["jobs:read"])
async def list_jobs(
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's jobs with pagination."""
    
    # Build query
    query = db.query(Job).filter(Job.user_id == current_user.id)
    
    if status:
        try:
            status_enum = JobStatus(status)
            query = query.filter(Job.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * size
    jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(size).all()
    
    # Convert to response format
    job_responses = []
    for job in jobs:
        job_responses.append(JobResponse(
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
            error_message=job.error_message
        ))
    
    return JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        size=size
    )


@router.get("/{job_id}", response_model=JobResponse)
@rbac_required(permissions=["jobs:read"])
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get job details."""
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
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
        error_message=job.error_message
    )


@router.delete("/{job_id}")
@rbac_required(permissions=["jobs:delete"])
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel a running job."""
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled"
        )
    
    # Update job status
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Job cancelled successfully"}


@router.post("/{job_id}/restart")
@rbac_required(permissions=["jobs:restart"])
async def restart_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Restart a failed or cancelled job."""
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status not in [JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed or cancelled jobs can be restarted"
        )
    
    # Reset job status
    job.status = JobStatus.PENDING
    job.started_at = None
    job.completed_at = None
    job.error_message = None
    job.crawled_urls = 0
    job.extracted_records = 0
    db.commit()
    
    # Start background task
    background_tasks.add_task(start_mining_job.delay, str(job.id))
    
    return {"message": "Job restarted successfully"}