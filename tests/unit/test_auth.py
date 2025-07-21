import pytest
from datetime import timedelta
from app.auth.jwt_handler import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password
)


@pytest.mark.unit
class TestJWTHandler:
    def test_create_access_token(self, mock_settings):
        """Test creating access token."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self, mock_settings):
        """Test creating access token with custom expiry."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta)
        
        assert token is not None
        assert isinstance(token, str)

    def test_verify_token_valid(self, mock_settings):
        """Test verifying valid token."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        email = verify_token(token)
        assert email == "test@example.com"

    def test_verify_token_invalid(self, mock_settings):
        """Test verifying invalid token."""
        invalid_token = "invalid.jwt.token"
        email = verify_token(invalid_token)
        assert email is None

    def test_password_hashing(self):
        """Test password hashing and verification."""
        plain_password = "TestPassword123!"
        hashed = get_password_hash(plain_password)
        
        assert hashed != plain_password
        assert len(hashed) > 0
        assert verify_password(plain_password, hashed) is True
        assert verify_password("wrong_password", hashed) is False