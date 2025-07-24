import pytest
from fastapi import status
import hashlib
from datetime import timedelta, datetime


@pytest.fixture
def auth_client(db_session, monkeypatch, mock_redis):
    import importlib.util
    from pathlib import Path
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.database import get_db

    # patch limiter decorator to no-op
    from app.middleware import rate_limiting

    monkeypatch.setattr(rate_limiting.limiter, "limit", lambda *a, **k: (lambda f: f))
    import prometheus_client

    class DummyCounter:
        def inc(self):
            pass

    monkeypatch.setattr(prometheus_client, "Counter", lambda *a, **k: DummyCounter())
    # load auth module without importing package
    auth_path = Path("app/api/v1/auth.py")
    spec = importlib.util.spec_from_file_location("app.api.v1.auth", auth_path)
    auth_module = importlib.util.module_from_spec(spec)
    import sys

    sys.modules["app.api.v1.auth"] = auth_module
    spec.loader.exec_module(auth_module)
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
        yield client


@pytest.fixture
def registered_user(auth_client, sample_user_data):
    resp = auth_client.post("/auth/register", json=sample_user_data)
    assert resp.status_code == status.HTTP_200_OK
    return sample_user_data


class TestPasswordReset:
    def test_request_password_reset(
        self, auth_client, registered_user, db_session, mocker
    ):
        import sys

        send = mocker.patch.object(sys.modules["app.api.v1.auth"], "send_email")
        response = auth_client.post(
            "/auth/password-reset/request", json={"email": registered_user["email"]}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "token" not in data
        send.assert_called_once()
        body = send.call_args.args[2]
        token = body.split("token=")[1]
        from app.models.user import User

        user = (
            db_session.query(User)
            .filter(User.email == registered_user["email"])
            .first()
        )
        assert user.password_reset_token == hashlib.sha256(token.encode()).hexdigest()
        assert user.password_reset_expiry > datetime.utcnow()

    def test_request_password_reset_unknown_email(self, auth_client, mocker):
        import sys

        send = mocker.patch.object(sys.modules["app.api.v1.auth"], "send_email")
        response = auth_client.post(
            "/auth/password-reset/request", json={"email": "unknown@example.com"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        send.assert_not_called()

    def test_confirm_password_reset(
        self, auth_client, registered_user, db_session, mocker
    ):
        import sys

        send = mocker.patch.object(sys.modules["app.api.v1.auth"], "send_email")
        auth_client.post(
            "/auth/password-reset/request", json={"email": registered_user["email"]}
        )
        body = send.call_args.args[2]
        token = body.split("token=")[1]
        new_pwd = "NewPassw0rd!"
        resp2 = auth_client.post(
            "/auth/password-reset/confirm",
            json={"token": token, "new_password": new_pwd},
        )
        assert resp2.status_code == status.HTTP_200_OK
        from app.models.user import User

        user = (
            db_session.query(User)
            .filter(User.email == registered_user["email"])
            .first()
        )
        assert user.password_reset_token is None
        assert user.refresh_token is None
        # verify login with new password works
        login_data = {"username": registered_user["email"], "password": new_pwd}
        login_resp = auth_client.post("/auth/login", data=login_data)
        assert login_resp.status_code == status.HTTP_200_OK

    def test_confirm_password_reset_invalid_token(self, auth_client, registered_user):
        response = auth_client.post(
            "/auth/password-reset/confirm",
            json={"token": "bad", "new_password": "x" * 8},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_confirm_password_reset_expired_token(
        self, auth_client, registered_user, db_session, mocker
    ):
        import sys

        send = mocker.patch.object(sys.modules["app.api.v1.auth"], "send_email")
        auth_client.post(
            "/auth/password-reset/request", json={"email": registered_user["email"]}
        )
        body = send.call_args.args[2]
        token = body.split("token=")[1]
        from app.models.user import User

        user = (
            db_session.query(User)
            .filter(User.email == registered_user["email"])
            .first()
        )
        user.password_reset_expiry = datetime.utcnow() - timedelta(minutes=1)
        db_session.commit()
        resp2 = auth_client.post(
            "/auth/password-reset/confirm",
            json={"token": token, "new_password": "x" * 8},
        )
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST


class TestRefreshToken:
    def test_refresh_token_success(self, auth_client, registered_user, db_session):
        login_data = {
            "username": registered_user["email"],
            "password": registered_user["password"],
        }
        login_resp = auth_client.post("/auth/login", data=login_data)
        tokens = login_resp.json()
        refresh_resp = auth_client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_resp.status_code == status.HTTP_200_OK
        new_tokens = refresh_resp.json()
        assert new_tokens["refresh_token"] != tokens["refresh_token"]
        from app.models.user import User

        user = (
            db_session.query(User)
            .filter(User.email == registered_user["email"])
            .first()
        )
        assert (
            user.refresh_token
            == hashlib.sha256(new_tokens["refresh_token"].encode()).hexdigest()
        )

    def test_refresh_token_invalid(self, auth_client):
        resp = auth_client.post("/auth/refresh", json={"refresh_token": "badtoken"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_expired(self, auth_client, registered_user, db_session):
        login_data = {
            "username": registered_user["email"],
            "password": registered_user["password"],
        }
        login_resp = auth_client.post("/auth/login", data=login_data)
        tokens = login_resp.json()
        from app.models.user import User

        user = (
            db_session.query(User)
            .filter(User.email == registered_user["email"])
            .first()
        )
        user.refresh_token_expiry = datetime.utcnow() - timedelta(days=1)
        db_session.commit()
        resp = auth_client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
