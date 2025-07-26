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
        data = {"sub": "test@example.com", "tenant_id": "t1"}
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
        
        payload = self.verify_token(token)
        assert payload["sub"] == "test@example.com"

    def test_verify_token_invalid(self, mock_settings):
        """Test verifying invalid token."""
        invalid_token = "invalid.jwt.token"
        payload = self.verify_token(invalid_token)
        assert payload is None

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
    def auth_client(self, db_session, monkeypatch, mocker, mock_redis, mock_settings):
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

        import sys, types
        api_pkg = types.ModuleType("app.api")
        api_pkg.__path__ = ["app/api"]
        sys.modules["app.api"] = api_pkg
        sys.modules["app.api.dependencies"] = importlib.import_module("app.api.dependencies")

        spec.loader.exec_module(auth_module)
        sys.modules["app.api.v1.auth"] = auth_module
        mock_send = mocker.patch.object(auth_module, "send_email")
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
    def registered_user(self, auth_client, db_session, sample_user_data):
        from app.models.user import User
        from app.auth.jwt_handler import get_password_hash
        import uuid

        user = User(
            email=sample_user_data["email"],
            hashed_password=get_password_hash(sample_user_data["password"]),
            full_name=sample_user_data["full_name"],
            tenant_id=uuid.uuid4(),
            consent_given=True,
        )
        db_session.add(user)
        db_session.commit()
        return sample_user_data

    def test_password_reset_sends_email(self, auth_client, registered_user):
        client, mock_send = auth_client
        resp = client.post('/auth/password-reset/request', json={'email': registered_user['email']})
        assert resp.status_code == 200
        mock_send.assert_called_once()
        args = mock_send.call_args.args
        assert args[0] == registered_user['email']
        assert args[1] == "Password Reset"
        assert "token=" in args[2]
