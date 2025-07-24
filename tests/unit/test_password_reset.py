import pytest
from starlette.requests import Request
from app.models.user import User
from app.api.v1.auth import password_reset_request, PasswordResetRequest


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_redis")
async def test_password_reset_request_sends_email(db_session, mocker):
    user = User(email="unit@example.com", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    send_mock = mocker.patch("app.api.v1.auth.send_password_reset_email")
    req = Request({"type": "http", "path": "/auth/password-reset/request", "method": "POST"})
    data = PasswordResetRequest(email=user.email)
    response = await password_reset_request.__wrapped__(req, data, db_session)

    assert response == {"message": "Password reset link sent"}
    send_mock.assert_called_once()
