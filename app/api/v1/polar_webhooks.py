from __future__ import annotations

import hmac
import hashlib
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PolarSubscription

router = APIRouter(prefix="/polar", tags=["polar"])


def verify_signature(body: bytes, signature: str | None) -> None:
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
    body = await request.body()
    signature = request.headers.get("Polar-Signature")
    verify_signature(body, signature)

    event = await request.json()
    event_type = event.get("type")
    data = event.get("data", {})
    subscription_id = data.get("id")
    customer_id = data.get("customer_id")

    if event_type == "subscription_created":
        subscription = (
            db.query(PolarSubscription)
            .filter(PolarSubscription.subscription_id == subscription_id)
            .first()
        )
        if subscription:
            subscription.status = data.get("status", "active")
            subscription.customer_id = customer_id or subscription.customer_id
        else:
            subscription = PolarSubscription(
                subscription_id=subscription_id,
                customer_id=customer_id or "",
                status=data.get("status", "active"),
            )
            db.add(subscription)
        db.commit()
    elif event_type == "subscription_canceled":
        subscription = (
            db.query(PolarSubscription)
            .filter(PolarSubscription.subscription_id == subscription_id)
            .first()
        )
        if subscription:
            subscription.status = "canceled"
            db.commit()
    else:
        # Ignore other events for now
        pass

    return {"status": "ok"}
