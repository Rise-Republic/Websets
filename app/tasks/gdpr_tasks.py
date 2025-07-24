from datetime import datetime, timedelta
import uuid
from loguru import logger

from .celery_app import celery_app
from app.database import SessionLocal
from app.models import User, Job, Dataset, DataRecord, DiscoveredURL, CrawlResult
from app.middleware.audit_middleware import DataAccessAudit


@celery_app.task
def export_user_data_task(user_id: str):
    """Gather all data for the given user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            return None
        jobs = db.query(Job).filter(Job.tenant_id == user.tenant_id).all()
        datasets = db.query(Dataset).filter(Dataset.tenant_id == user.tenant_id).all()

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
    except Exception as exc:
        logger.error(f"export_user_data_task failed: {exc}")
        raise
    finally:
        db.close()


@celery_app.task
def delete_user_data_task(user_id: str) -> bool:
    """Delete user account and associated data."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            return False
        DataAccessAudit.log_data_access(
            user_id=user.id, tenant_id=user.tenant_id, access_type="delete"
        )
        db.delete(user)
        db.commit()
        return True
    except Exception as exc:
        db.rollback()
        logger.error(f"delete_user_data_task failed: {exc}")
        return False
    finally:
        db.close()


def _purge_records(db, model, timestamp_field: str) -> int:
    now = datetime.utcnow()
    deleted = 0
    for obj in db.query(model).all():
        ts = getattr(obj, timestamp_field)
        days = getattr(obj, "data_retention_days", 365)
        if ts and ts < now - timedelta(days=days):
            db.delete(obj)
            deleted += 1
    return deleted


@celery_app.task
def purge_expired_data() -> int:
    """Purge records past their retention period."""
    db = SessionLocal()
    try:
        total = 0
        total += _purge_records(db, CrawlResult, "crawled_at")
        total += _purge_records(db, DiscoveredURL, "discovered_at")
        total += _purge_records(db, DataRecord, "created_at")
        total += _purge_records(db, Dataset, "created_at")
        total += _purge_records(db, Job, "created_at")
        total += _purge_records(db, User, "created_at")
        db.commit()
        if total:
            logger.info(f"Purged {total} expired records")
        return total
    except Exception as exc:
        db.rollback()
        logger.error(f"purge_expired_data failed: {exc}")
        return 0
    finally:
        db.close()
