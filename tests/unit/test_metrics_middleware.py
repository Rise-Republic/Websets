import pytest
from fastapi.testclient import TestClient

from app.monitoring.metrics import MetricsCollector, get_metrics_collector


@pytest.fixture
def metrics_client(monkeypatch, db_session):
    # Prevent background tasks from running
    monkeypatch.setattr(
        MetricsCollector, "_start_system_metrics_collection", lambda self: None
    )

    # Reset any existing global collector before importing the app
    import app.monitoring.metrics as metrics_module

    metrics_module._metrics_collector = None

    from app.main import app
    from app.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db

    metrics = get_metrics_collector()
    with TestClient(app) as client:
        yield client, metrics
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_metrics_middleware_records_http_request(metrics_client):
    client, metrics = metrics_client

    response = client.get("/health")
    assert response.status_code == 200

    metrics_output = metrics.get_metrics()
    assert (
        'websets_http_requests_total{endpoint="/health",method="GET",status_code="200"} 1.0'
        in metrics_output
    )
