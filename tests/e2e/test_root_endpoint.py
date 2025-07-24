import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.mark.e2e
def test_root_endpoint_e2e(monkeypatch):
    from app import middleware
    monkeypatch.setattr(middleware.rate_limiting.limiter, "limit", lambda *a, **k: (lambda f: f))
    monkeypatch.setattr(middleware.rate_limiting.user_limiter, "limit", lambda *a, **k: (lambda f: f))
    import app.main
    importlib.reload(app.main)
    with TestClient(app.main.app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "WebSet Miner API"
