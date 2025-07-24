import pytest
from datetime import timedelta
from unittest.mock import patch
from app.auth.jwt_handler import create_access_token

@pytest.mark.unit
class TestJWTHandler:
    @pytest.fixture(autouse=True)
    def jwt_imports(self):
        from app.auth.jwt_handler import (
            verify_token,
            get_password_hash,
            verify_password
        )
        self.create_access_token = create_access_token
        self.verify_token = verify_token
        self.get_password_hash = get_password_hash
        self.verify_password = verify_password

    def test_create_access_token(self, mock_settings):
        """Test creating access token."""
        data = {"sub": "test@example.com"}
        token = self.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self, mock_settings):
        """Test creating access token with custom expiry."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=60)
        token = self.create_access_token(data, expires_delta)
        
        assert token is not None
        assert isinstance(token, str)

    def test_verify_token_valid(self, mock_settings):
        """Test verifying valid token."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        email = self.verify_token(token)
        assert email == "test@example.com"

    def test_verify_token_invalid(self, mock_settings):
        """Test verifying invalid token."""
        invalid_token = "invalid.jwt.token"
        email = self.verify_token(invalid_token)
        assert email is None

    def test_password_hashing(self):
        """Test password hashing and verification."""
        plain_password = "TestPassword123!"
        hashed = self.get_password_hash(plain_password)
        
        assert hashed != plain_password
        assert len(hashed) > 0
        assert self.verify_password(plain_password, hashed) is True
        assert self.verify_password("wrong_password", hashed) is False

class TestPasswordResetEmail:
    @pytest.fixture
    def auth_client(self, db_session, monkeypatch, mocker, mock_redis):
        import importlib.util
        from pathlib import Path
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.database import get_db
        from app.middleware import rate_limiting
        monkeypatch.setattr(rate_limiting.limiter, "limit", lambda *a, **k: (lambda f: f))
        import prometheus_client
        class DummyCounter:
            def inc(self):
                pass
        monkeypatch.setattr(prometheus_client, "Counter", lambda *a, **k: DummyCounter())
        auth_path = Path("app/api/v1/auth.py")
        spec = importlib.util.spec_from_file_location("app.api.v1.auth", auth_path)
        auth_module = importlib.util.module_from_spec(spec)
        import sys
        sys.modules["app.api.v1.auth"] = auth_module
        spec.loader.exec_module(auth_module)
        mock_send = mocker.patch.object(auth_module, "send_password_reset")
        from app.database import Base, engine
        Base.metadata.create_all(bind=engine)
        app = FastAPI()
        app.include_router(auth_module.router)
        def override_get_db():
            try:
                yield db_session
            finally:
                db_session.close()
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            yield client, mock_send

    @pytest.fixture
    def registered_user(self, auth_client, sample_user_data):
        client, _ = auth_client
        resp = client.post("/auth/register", json=sample_user_data)
        assert resp.status_code == 200
        return sample_user_data

    def test_password_reset_sends_email(self, auth_client, registered_user):
        client, mock_send = auth_client
        resp = client.post('/auth/password-reset/request', json={'email': registered_user['email']})
        assert resp.status_code == 200
        token = resp.json()['token']
        mock_send.assert_called_once_with(registered_user['email'], token)
