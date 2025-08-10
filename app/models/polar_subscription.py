from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, String

from app.database import Base
from app.models.types import GUID as UUID


class PolarSubscription(Base):
    """Model representing a Polar subscription."""

    __tablename__ = "polar_subscriptions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    subscription_id = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<PolarSubscription(subscription_id={self.subscription_id}, "
            f"status={self.status})>"
        )
