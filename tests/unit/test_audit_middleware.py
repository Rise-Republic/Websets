import pytest
from app.models import AuditLog

@pytest.mark.unit
def test_audit_log_created(client, db_session):
    response = client.get("/")
    assert response.status_code == 200
    logs = db_session.query(AuditLog).all()
    assert len(logs) >= 1
    assert logs[0].action.startswith("GET_")
