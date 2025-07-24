"""Endpoints for GDPR compliance."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Job, Dataset
from app.auth.dependencies import get_current_active_user
from app.middleware.audit_middleware import DataAccessAudit


router = APIRouter(prefix="/gdpr", tags=["gdpr"])


@router.get("/export")
async def export_user_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Export user data for portability."""

    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    jobs: List[Job] = db.query(Job).filter(Job.tenant_id == user.tenant_id).all()
    datasets: List[Dataset] = (
        db.query(Dataset).filter(Dataset.tenant_id == user.tenant_id).all()
    )

    DataAccessAudit.log_data_access(
        user_id=user.id, tenant_id=user.tenant_id, access_type="export"
    )

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat(),
        },
        "jobs": [
            {
                "id": str(job.id),
                "prompt": job.prompt,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
            }
            for job in jobs
        ],
        "datasets": [
            {
                "id": str(ds.id),
                "job_id": str(ds.job_id),
                "name": ds.name,
                "created_at": ds.created_at.isoformat(),
            }
            for ds in datasets
        ],
    }


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete user account and all related data."""

    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    DataAccessAudit.log_data_access(
        user_id=user.id, tenant_id=user.tenant_id, access_type="delete"
    )

    db.delete(user)
    db.commit()

    return None
