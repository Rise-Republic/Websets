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
        client.post("/auth/register", json=sample_user_data)

        response = client.post("/auth/register", json=sample_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    def test_register_user_weak_password(self, client):
        """Test registration with weak password fails."""
        user_data = {
            "email": "test@example.com",
            "password": "weak",
            "full_name": "Test User",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_invalid_email(self, client):
        """Test registration with invalid email fails."""
        user_data = {
            "email": "invalid-email",
            "password": "TestPassword123!",
            "full_name": "Test User",
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_success(self, client, db_session, sample_user_data):
        """Test successful login after verification."""
        client.post("/auth/register", json=sample_user_data)
        from app.models.user import User

        user = (
            db_session.query(User)
            .filter(User.email == sample_user_data["email"])
            .first()
        )
        token = user.verification_token
        client.get(f"/auth/verify?token={token}")

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
        client.post("/auth/register", json=sample_user_data)

        login_data = {
            "username": sample_user_data["email"],
            "password": "wrong_password",
        }
        response = client.post("/auth/login", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_unverified_user(self, client, sample_user_data):
        """Login should fail until email is verified."""
        client.post("/auth/register", json=sample_user_data)

        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        response = client.post("/auth/login", data=login_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email not verified" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user fails."""
        login_data = {"username": "nonexistent@example.com", "password": "password"}
        response = client.post("/auth/login", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_email_verification_flow(self, client, db_session, sample_user_data):
        """User can verify email and then login."""
        client.post("/auth/register", json=sample_user_data)
        from app.models.user import User

        user = (
            db_session.query(User)
            .filter(User.email == sample_user_data["email"])
            .first()
        )
        token = user.verification_token

        response = client.get(f"/auth/verify?token={token}")
        assert response.status_code == status.HTTP_200_OK

        user = (
            db_session.query(User)
            .filter(User.email == sample_user_data["email"])
            .first()
        )
        assert user.is_verified is True

        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == status.HTTP_200_OK

    def test_verification_invalid_token(self, client):
        """Invalid verification token returns error."""
        response = client.get("/auth/verify?token=badtoken")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verification_expired_token(self, client, db_session, sample_user_data):
        """Expired token should fail."""
        client.post("/auth/register", json=sample_user_data)
        from app.models.user import User

        user = (
            db_session.query(User)
            .filter(User.email == sample_user_data["email"])
            .first()
        )
        token = user.verification_token
        from datetime import datetime, timedelta

        user.verification_token_expiry = datetime.utcnow() - timedelta(seconds=1)
        db_session.commit()

        response = client.get(f"/auth/verify?token={token}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_current_user_success(self, client, db_session, sample_user_data):
        """Test getting current user info with valid token."""
        client.post("/auth/register", json=sample_user_data)
        from app.models.user import User

        user = (
            db_session.query(User)
            .filter(User.email == sample_user_data["email"])
            .first()
        )
        token = user.verification_token
        client.get(f"/auth/verify?token={token}")

        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        login_response = client.post("/auth/login", data=login_data)
        access_token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}
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
