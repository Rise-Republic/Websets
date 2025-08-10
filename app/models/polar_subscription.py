from sqlalchemy import Column, String, DateTime, ForeignKey
from app.models.types import GUID as UUID
from datetime import datetime
import uuid

from app.database import Base


class PolarSubscription(Base):
    __tablename__ = "polar_subscriptions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    polar_subscription_id = Column(String, nullable=False, unique=True, index=True)
    status = Column(String, nullable=False)
    tier = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<PolarSubscription(id={self.id}, user_id={self.user_id}, "
            f"polar_subscription_id='{self.polar_subscription_id}', status='{self.status}', tier='{self.tier}')>"
        )
