import pytest
from starlette.requests import Request
from starlette.datastructures import Headers

from app.middleware.rate_limiting import get_user_id_from_request
from app.auth.jwt_handler import create_access_token, get_password_hash
from app.models.user import User
from slowapi.util import get_remote_address


@pytest.mark.unit
def test_get_user_id_from_request_with_valid_token(db_session):
    user = User(email="token@example.com", hashed_password=get_password_hash("pw"))
    db_session.add(user)
    db_session.commit()

    token = create_access_token({"sub": user.email})
    headers = Headers({"Authorization": f"Bearer {token}"})
    scope = {"type": "http", "method": "GET", "path": "/", "headers": headers.raw, "client": ("1.1.1.1", 1234)}
    request = Request(scope)

    assert get_user_id_from_request(request) == str(user.id)


@pytest.mark.unit
def test_get_user_id_from_request_invalid_token_returns_ip():
    headers = Headers({"Authorization": "Bearer invalid"})
    scope = {"type": "http", "method": "GET", "path": "/", "headers": headers.raw, "client": ("2.2.2.2", 5678)}
    request = Request(scope)
    assert get_user_id_from_request(request) == get_remote_address(request)
