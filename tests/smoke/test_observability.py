import os
import httpx
import pytest
from fastapi import status

from app.config import settings


@pytest.mark.smoke
def test_metrics_endpoint_prometheus_format(client):
    response = client.get("/health/metrics")
    assert response.status_code == status.HTTP_200_OK
    assert "websets_http_requests_total" in response.text


@pytest.mark.smoke
def test_otlp_collector_health():
    url = os.getenv("OTLP_HEALTH_ENDPOINT", settings.otlp_endpoint.rstrip('/') + "/-/ready")
    try:
        with httpx.Client(timeout=5.0) as http_client:
            resp = http_client.get(url)
    except Exception as exc:
        pytest.skip(f"OTLP collector not reachable: {exc}")
    assert resp.status_code == status.HTTP_200_OK
