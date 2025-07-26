import uuid

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient



@pytest.fixture
def auth_app(db_session):
    from app.middleware.jwt_auth import JWTAuthMiddleware
    from app.database import get_db
    app = FastAPI()
    app.add_middleware(JWTAuthMiddleware)

    @app.get("/protected")
    async def protected(request: Request):
        user = getattr(request.state, "user", None)
        if not user:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        return {"user": user.email, "tenant": str(request.state.tenant_id)}

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.mark.unit
def test_jwt_auth_middleware_valid(auth_app, db_session):
    from app.models import User
    from jose import jwt
    secret = "test-secret-key-that-is-long-enough-for-testing-purposes"

    user = User(
        email="u@example.com",
        hashed_password="x",
        tenant_id=uuid.uuid4(),
    )
    db_session.add(user)
    db_session.commit()
    token = jwt.encode({"sub": user.email, "tenant_id": str(user.tenant_id)}, secret, algorithm="HS256")
    with TestClient(auth_app) as client:
        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"] == "u@example.com"
        assert data["tenant"] == str(user.tenant_id)


@pytest.mark.unit
def test_jwt_auth_middleware_invalid(auth_app):
    with TestClient(auth_app) as client:
        resp = client.get("/protected", headers={"Authorization": "Bearer bad"})
        assert resp.status_code == 401
