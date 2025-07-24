import pytest
from app.models import AuditLog


@pytest.mark.unit
def test_audit_log_created(client, db_session):
    response = client.get("/")
    assert response.status_code == 200
    logs = db_session.query(AuditLog).all()
    assert len(logs) >= 1
    assert logs[0].action.startswith("GET_")


@pytest.mark.unit
def test_audit_log_includes_user(client, db_session):
    from app.models import AuditLog

    with client as c:
        c.headers.update({"X-User-Id": "123", "X-User-Email": "foo@example.com"})
        response = c.get("/")
    assert response.status_code == 200
    log = db_session.query(AuditLog).order_by(AuditLog.id.desc()).first()
    assert log.user_id == "123"
    assert log.user_email == "foo@example.com"
