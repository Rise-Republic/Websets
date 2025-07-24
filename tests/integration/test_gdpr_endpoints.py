import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.usefixtures("mock_redis")
class TestGDPREndpoints:
    def _auth_headers(self, client, user_data):
        import uuid
        from app.middleware.audit_middleware import AuditMiddleware
        from unittest.mock import AsyncMock
        AuditMiddleware._log_audit_entry = AsyncMock()
        tenant_headers = {"X-Tenant-ID": str(uuid.uuid4())}
        client.post("/auth/register", json=user_data, headers=tenant_headers)
        login = {"username": user_data["email"], "password": user_data["password"]}
        resp = client.post("/auth/login", data=login, headers=tenant_headers)
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}", **tenant_headers}

    def test_export_data(self, client, sample_user_data, mocker):
        task_mock = mocker.patch("app.tasks.gdpr_tasks.export_user_data_task.delay")
        headers = self._auth_headers(client, sample_user_data)
        resp = client.get("/gdpr/export", headers=headers)
        assert resp.status_code == status.HTTP_202_ACCEPTED
        assert resp.json()["message"] == "Export initiated"
        task_mock.assert_called_once()

    def test_delete_data(self, client, sample_user_data, mocker):
        task_mock = mocker.patch("app.tasks.gdpr_tasks.delete_user_data_task.delay")
        headers = self._auth_headers(client, sample_user_data)
        resp = client.delete("/gdpr/delete", headers=headers)
        assert resp.status_code == status.HTTP_202_ACCEPTED
        task_mock.assert_called_once()

    def test_update_consent(self, client, sample_user_data, db_session):
        headers = self._auth_headers(client, sample_user_data)
        resp = client.post("/gdpr/consent", headers=headers, json={"consent": True})
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        from app.models.user import User
        user = db_session.query(User).first()
        assert user.consent_given is True

