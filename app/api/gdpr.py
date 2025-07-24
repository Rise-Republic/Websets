"""Endpoints for GDPR compliance."""

from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Job, Dataset
from app.repositories import UserRepository
from app.auth.dependencies import get_current_active_user
from app.middleware.audit_middleware import DataAccessAudit
from app.tasks.gdpr_tasks import (
    export_user_data_task,
    delete_user_data_task,
)


router = APIRouter(prefix="/gdpr", tags=["gdpr"])


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency injector for ``UserRepository``."""
    return UserRepository(db)


@router.get("/export", status_code=status.HTTP_202_ACCEPTED)
async def export_user_data(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Export user data asynchronously."""

    user = user_repo.get_by_id(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    background_tasks.add_task(export_user_data_task.delay, str(user.id))

    return {"message": "Export initiated"}


@router.delete("/delete", status_code=status.HTTP_202_ACCEPTED)
async def delete_user_data(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Queue deletion of user account and related data."""

    user = user_repo.get_by_id(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    background_tasks.add_task(delete_user_data_task.delay, str(user.id))

    return None


class ConsentUpdate(BaseModel):
    consent: bool


@router.post("/consent", status_code=status.HTTP_204_NO_CONTENT)
async def update_consent(
    data: ConsentUpdate,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Record user consent status."""
    current_user.consent_given = data.consent
    current_user.consent_given_at = datetime.utcnow() if data.consent else None
    user_repo.commit()
    return None
