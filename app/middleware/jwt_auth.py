from typing import Optional

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.tenancy import set_current_tenant


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Authenticate requests using Bearer JWT tokens."""

    async def dispatch(self, request: Request, call_next):
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return await call_next(request)

        token = authorization.split(" ", 1)[1]

        from jose import JWTError, jwt
        from app.config import settings

        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[getattr(settings, "jwt_algorithm", "HS256")],
            )
        except JWTError:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        email = payload.get("email") or payload.get("sub")
        tenant_claim = payload.get("tenant_id")

        from app.database import SessionLocal
        from app.models import User
        from app.models.role import Role
        from sqlalchemy.orm import joinedload

        db = SessionLocal()
        try:
            user = (
                db.query(User)
                .options(joinedload(User.roles).joinedload(Role.permissions))
                .filter(User.email == email)
                .first()
            )
        finally:
            db.close()

        if not user or not getattr(user, "is_active", False):
            return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})

        if tenant_claim and str(tenant_claim) != str(user.tenant_id):
            return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})

        request.state.user = user
        request.state.user_id = str(user.id)
        request.state.tenant_id = str(user.tenant_id) if user.tenant_id else None

        set_current_tenant(user.tenant_id)
        try:
            return await call_next(request)
        finally:
            set_current_tenant(None)
