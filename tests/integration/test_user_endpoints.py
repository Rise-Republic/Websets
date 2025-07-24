import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.usefixtures("mock_redis")
class TestUserEndpoints:
    def _auth_headers(self, client, user_data):
        client.post("/auth/register", json=user_data)
        login_data = {"username": user_data["email"], "password": user_data["password"]}
        resp = client.post("/auth/login", data=login_data)
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_get_profile(self, client, sample_user_data):
        headers = self._auth_headers(client, sample_user_data)
        resp = client.get("/users/me", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["email"] == sample_user_data["email"]

    def test_update_profile(self, client, sample_user_data):
        headers = self._auth_headers(client, sample_user_data)
        resp = client.patch("/users/me", headers=headers, json={"full_name": "New Name"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["full_name"] == "New Name"

    def test_change_password(self, client, sample_user_data):
        headers = self._auth_headers(client, sample_user_data)
        change = {"current_password": sample_user_data["password"], "new_password": "NewPass123!"}
        resp = client.patch("/users/me/password", headers=headers, json=change)
        assert resp.status_code == status.HTTP_200_OK
        # old password fails
        old_login = {"username": sample_user_data["email"], "password": sample_user_data["password"]}
        assert client.post("/auth/login", data=old_login).status_code == status.HTTP_401_UNAUTHORIZED
        new_login = {"username": sample_user_data["email"], "password": "NewPass123!"}
        assert client.post("/auth/login", data=new_login).status_code == status.HTTP_200_OK

    def test_change_email(self, client, sample_user_data):
        headers = self._auth_headers(client, sample_user_data)
        new_email = "new@example.com"
        change = {"password": sample_user_data["password"], "new_email": new_email}
        resp = client.patch("/users/me/email", headers=headers, json=change)
        assert resp.status_code == status.HTTP_200_OK
        old_login = {"username": sample_user_data["email"], "password": sample_user_data["password"]}
        assert client.post("/auth/login", data=old_login).status_code == status.HTTP_401_UNAUTHORIZED
        new_login = {"username": new_email, "password": sample_user_data["password"]}
        assert client.post("/auth/login", data=new_login).status_code == status.HTTP_200_OK

    def test_deactivate_account(self, client, sample_user_data):
        headers = self._auth_headers(client, sample_user_data)
        resp = client.delete("/users/me", headers=headers)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        login = {"username": sample_user_data["email"], "password": sample_user_data["password"]}
        assert client.post("/auth/login", data=login).status_code == status.HTTP_400_BAD_REQUEST

