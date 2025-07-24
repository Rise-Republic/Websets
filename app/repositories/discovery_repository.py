from __future__ import annotations

from typing import List
import uuid

from sqlalchemy.orm import Session

from app.models import DiscoveredURL


class DiscoveryRepository:
    """Data access layer for ``DiscoveredURL`` objects."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_discovered_url(
        self,
        job_id: uuid.UUID,
        tenant_id: uuid.UUID,
        url: str,
        discovery_method: str = "discovery",
    ) -> DiscoveredURL:
        discovered_url = DiscoveredURL(
            job_id=job_id,
            tenant_id=tenant_id,
            url=url,
            discovery_method=discovery_method,
        )
        self.db.add(discovered_url)
        return discovered_url

    def list_for_job(self, job_id: uuid.UUID) -> List[DiscoveredURL]:
        return self.db.query(DiscoveredURL).filter(DiscoveredURL.job_id == job_id).all()

    def commit(self) -> None:
        self.db.commit()
