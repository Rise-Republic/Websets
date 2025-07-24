import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.e2e
def test_root_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "WebSet Miner API"
