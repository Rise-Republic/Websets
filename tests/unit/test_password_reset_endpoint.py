import importlib
import pytest
import uuid
from starlette.requests import Request


@pytest.mark.unit
@pytest.mark.asyncio
async def test_password_reset_request_no_token_leaked(
    db_session, mocker, mock_settings
):
    auth = importlib.import_module("app.api.v1.auth")
    mock_send = mocker.patch.object(auth, "send_email")
    user = auth.User(
        email="user@example.com",
        hashed_password=auth.get_password_hash("secret"),
        tenant_id=uuid.uuid4(),
    )
    db_session.add(user)
    db_session.commit()

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [],
        "scheme": "http",
        "server": ("testserver", 80),
    }
    req = Request(scope)
    data = auth.PasswordResetRequest(email="user@example.com")

    result = await auth.password_reset_request(req, data, db_session)
    assert "token" not in result
    mock_send.assert_called_once()
