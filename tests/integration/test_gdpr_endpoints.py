import pytest
from fastapi import status


@pytest.mark.integration
class TestGDPREndpoints:
    def _auth_headers(self, client, user_data):
        client.post("/auth/register", json=user_data)
        login = {"username": user_data["email"], "password": user_data["password"]}
        resp = client.post("/auth/login", data=login)
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_export_data(self, client, sample_user_data):
        headers = self._auth_headers(client, sample_user_data)
        resp = client.get("/gdpr/export", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["user"]["email"] == sample_user_data["email"]

    def test_delete_data(self, client, sample_user_data, db_session):
        headers = self._auth_headers(client, sample_user_data)
        resp = client.delete("/gdpr/delete", headers=headers)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        from app.models.user import User
        assert db_session.query(User).count() == 0

