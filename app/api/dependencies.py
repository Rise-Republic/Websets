from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import UserRepository
from app.repositories.job_repository import JobRepository
from app.repositories.dataset_repository import DatasetRepository


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency injector for ``UserRepository``."""
    return UserRepository(db)


def get_job_repository(db: Session = Depends(get_db)) -> JobRepository:
    """Dependency injector for ``JobRepository``."""
    return JobRepository(db)


def get_dataset_repository(db: Session = Depends(get_db)) -> DatasetRepository:
    """Dependency injector for ``DatasetRepository``."""
    return DatasetRepository(db)
