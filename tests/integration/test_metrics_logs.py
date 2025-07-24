import pytest
from fastapi import status
from loguru import logger
from app.logging_utils import configure_logging


@pytest.mark.integration
def test_metrics_endpoint(client):
    response = client.get("/health/metrics")
    assert response.status_code == status.HTTP_200_OK
    assert "websets_http_requests_total" in response.text


@pytest.mark.integration
def test_logging_redaction(caplog):
    configure_logging("INFO")
    logger.add(caplog.handler, level="INFO")
    with caplog.at_level("INFO"):
        logger.info("token=abcd password=mysecret email=user@example.com")
    assert "abcd" not in caplog.text
    assert "mysecret" not in caplog.text
    assert "user@example.com" not in caplog.text
    assert "token=<redacted>" in caplog.text
    assert "password=<redacted>" in caplog.text
