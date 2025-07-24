import hashlib
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.usefixtures("mock_redis")
class TestAuthVerification:
    def test_verification_flow(self, client, sample_user_data, db_session):
        resp = client.post("/auth/register", json=sample_user_data)
        assert resp.status_code == status.HTTP_200_OK
        token = resp.json()["verification_token"]

        from app.models.user import User

        user = (
            db_session.query(User)
            .filter(User.email == sample_user_data["email"])
            .first()
        )
        assert user.verification_token == hashlib.sha256(token.encode()).hexdigest()
        assert user.is_verified is False

        # login before verification should fail
        login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        login = client.post("/auth/login", data=login_data)
        assert login.status_code == status.HTTP_403_FORBIDDEN

        # verify
        verify_resp = client.post("/auth/verify", json={"token": token})
        assert verify_resp.status_code == status.HTTP_200_OK

        db_session.refresh(user)
        assert user.is_verified is True
        assert user.verification_token is None

        login_after = client.post("/auth/login", data=login_data)
        assert login_after.status_code == status.HTTP_200_OK
