from __future__ import annotations

from typing import List, Optional, Tuple
import uuid

from sqlalchemy.orm import Session

from app.models import Dataset, DataRecord, Job


class DatasetRepository:
    """Data access layer for ``Dataset`` objects."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_datasets(
        self, tenant_id: uuid.UUID, page: int, size: int
    ) -> Tuple[List[Dataset], int]:
        query = self.db.query(Dataset).join(Job).filter(Job.tenant_id == tenant_id)
        total = query.count()
        offset = (page - 1) * size
        datasets = (
            query.order_by(Dataset.created_at.desc()).offset(offset).limit(size).all()
        )
        return datasets, total

    def get_dataset(self, dataset_id: str, tenant_id: uuid.UUID) -> Optional[Dataset]:
        return (
            self.db.query(Dataset)
            .join(Job)
            .filter(Dataset.id == dataset_id, Job.tenant_id == tenant_id)
            .first()
        )

    def get_dataset_records(
        self, dataset_id: str, page: int, size: int, tenant_id: uuid.UUID
    ) -> Tuple[List[DataRecord], int]:
        query = (
            self.db.query(DataRecord)
            .filter(
                DataRecord.dataset_id == dataset_id,
                DataRecord.tenant_id == tenant_id,
            )
        )
        total = query.count()
        offset = (page - 1) * size
        records = (
            query.order_by(DataRecord.created_at.desc()).offset(offset).limit(size).all()
        )
        return records, total

    def get_all_records(self, dataset_id: str, tenant_id: uuid.UUID) -> List[DataRecord]:
        return (
            self.db.query(DataRecord)
            .filter(
                DataRecord.dataset_id == dataset_id,
                DataRecord.tenant_id == tenant_id,
            )
            .all()
        )

    def get_records_by_ids(self, record_ids: List[uuid.UUID]) -> List[DataRecord]:
        if not record_ids:
            return []
        return self.db.query(DataRecord).filter(DataRecord.id.in_(record_ids)).all()

    def delete_dataset(self, dataset: Dataset) -> None:
        self.db.delete(dataset)
        self.db.commit()
