from __future__ import annotations

import hashlib
import hmac
from importlib import import_module
from typing import Any, Optional, cast

import httpx


class PolarClient:
    """Simple wrapper around Polar's REST API."""

    def __init__(
        self,
        api_key: str,
        org_id: str,
        webhook_secret: Optional[str] = None,
        base_url: str = "https://api.polar.sh/v1",
    ) -> None:
        self.api_key = api_key
        self.org_id = org_id
        self.webhook_secret = webhook_secret
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Polar-Organization": org_id,
            },
        )

    def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Retrieve a subscription by its ID."""
        response = self._client.get(f"/subscriptions/{subscription_id}")
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify webhook payload using HMAC SHA256 signature."""
        if not self.webhook_secret:
            raise ValueError("Webhook secret not configured")

        computed = hmac.new(
            self.webhook_secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(computed, signature)


_polar_client: Optional[PolarClient] = None


def get_polar_client() -> PolarClient:
    """Return a shared PolarClient instance configured from settings."""
    global _polar_client
    if _polar_client is None:
        settings = import_module("app.config").settings

        if not settings.polar_api_key or not settings.polar_org_id:
            raise RuntimeError("Polar API credentials are not configured")

        _polar_client = PolarClient(
            api_key=settings.polar_api_key,
            org_id=settings.polar_org_id,
            webhook_secret=settings.polar_webhook_secret,
        )
    return _polar_client


__all__ = ["PolarClient", "get_polar_client"]
