import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.usefixtures("mock_redis")
class TestAuthEndpoints:
    def test_register_user_success(self, client, sample_user_data):
        """Test successful user registration."""
        response = client.post("/auth/register", json=sample_user_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_register_user_duplicate_email(self, client, sample_user_data):
        """Test registration with duplicate email fails."""
        # First registration
        client.post("/auth/register", json=sample_user_data)

        # Second registration with same email
        response = client.post("/auth/register", json=sample_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    def test_register_user_weak_password(self, client):
        """Test registration with weak password fails."""
        user_data = {
            "email": "test@example.com",
            "password": "weak",  # Weak password
            "full_name": "Test User",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_invalid_email(self, client):
        """Test registration with invalid email fails."""
        user_data = {
            "email": "invalid-email",  # Invalid email
            "password": "TestPassword123!",
            "full_name": "Test User",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_success(self, client, sample_user_data):
        """Test successful login."""
        # Register user first
        client.post("/auth/register", json=sample_user_data)

        # Login
        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        response = client.post("/auth/login", data=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, sample_user_data):
        """Test login with wrong password fails."""
        # Register user first
        client.post("/auth/register", json=sample_user_data)

        # Login with wrong password
        login_data = {
            "username": sample_user_data["email"],
            "password": "wrong_password",
        }
        response = client.post("/auth/login", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user fails."""
        login_data = {"username": "nonexistent@example.com", "password": "password"}
        response = client.post("/auth/login", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_success(self, client, sample_user_data):
        """Test getting current user info with valid token."""
        # Register and login
        client.post("/auth/register", json=sample_user_data)

        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        login_response = client.post("/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        # Get user info
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]

    def test_get_current_user_no_token(self, client):
        """Test getting current user info without token fails."""
        response = client.get("/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user info with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_reset_request_does_not_leak_token(
        self, client, sample_user_data, mocker
    ):
        """Password reset request should send email and not return token."""
        client.post("/auth/register", json=sample_user_data)
        send_mock = mocker.patch("app.api.v1.auth.send_password_reset_email")

        response = client.post(
            "/auth/password-reset/request",
            json={"email": sample_user_data["email"]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {"message": "Password reset link sent"}
        send_mock.assert_called_once()
