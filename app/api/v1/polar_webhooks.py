from __future__ import annotations

import hmac
import hashlib
import os
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PolarSubscription
from app.repositories.polar_subscriptions import PolarSubscriptionRepository

router = APIRouter(prefix="/polar", tags=["polar"])


def verify_signature(body: bytes, signature: str | None) -> None:
    """Verify Polar webhook signature."""
    secret = os.getenv("POLAR_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature header")

    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")


@router.post("/webhook")
async def handle_polar_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Handle incoming Polar webhook events."""
    body = await request.body()
    signature = request.headers.get("Polar-Signature")
    verify_signature(body, signature)

    event = await request.json()
    event_type = event.get("type")
    data = event.get("data", {})
    polar_subscription_id = data.get("id")
    
    if not polar_subscription_id:
        raise HTTPException(status_code=400, detail="Missing subscription ID in webhook data")

    repo = PolarSubscriptionRepository(db)

    if event_type == "subscription_created":
        # Check if subscription already exists
        existing = repo.get_by_polar_subscription_id(polar_subscription_id)
        if existing:
            # Update existing subscription
            existing.status = data.get("status", "active")
            if "tier" in data:
                existing.tier = data["tier"]
            repo.commit()
        else:
            # NOTE: For new subscriptions, we need to map customer_id to user_id
            # This is a simplified implementation. In practice, you would need to:
            # 1. Look up the user by customer_id or email from Polar data
            # 2. Handle the case where user doesn't exist yet
            # 3. Create the subscription with proper user_id
            
            # For now, we'll skip creating new subscriptions without user_id
            # This prevents database constraint violations
            pass
            
    elif event_type == "subscription_canceled":
        subscription = repo.get_by_polar_subscription_id(polar_subscription_id)
        if subscription:
            subscription.status = "canceled"
            repo.commit()
            
    elif event_type == "subscription_updated":
        subscription = repo.get_by_polar_subscription_id(polar_subscription_id)
        if subscription:
            subscription.status = data.get("status", subscription.status)
            if "tier" in data:
                subscription.tier = data["tier"]
            repo.commit()
    else:
        # Log unknown event types but don't fail
        # In production, you might want to log this for monitoring
        pass

    return {"status": "ok"}