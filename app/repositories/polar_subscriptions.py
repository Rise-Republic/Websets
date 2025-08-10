from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.models import PolarSubscription


class PolarSubscriptionRepository:
    """Data access layer for ``PolarSubscription`` objects."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[PolarSubscription]:
        return (
            self.db.query(PolarSubscription)
            .filter(PolarSubscription.user_id == user_id)
            .first()
        )

    def get_by_polar_subscription_id(
        self, polar_subscription_id: str
    ) -> Optional[PolarSubscription]:
        return (
            self.db.query(PolarSubscription)
            .filter(PolarSubscription.polar_subscription_id == polar_subscription_id)
            .first()
        )

    def add(self, subscription: PolarSubscription) -> PolarSubscription:
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def update(self, subscription: PolarSubscription, **kwargs) -> PolarSubscription:
        for key, value in kwargs.items():
            setattr(subscription, key, value)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, subscription: PolarSubscription) -> None:
        self.db.refresh(subscription)
