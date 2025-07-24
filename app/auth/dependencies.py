from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from jose import jwt
from app.auth.jwt_handler import verify_token
from app.auth.auth0_utils import verify_auth0_token
from app.auth.rbac import require_roles, require_permissions
from app.auth.user_utils import get_current_active_user

security = HTTPBearer()


async def decode_token(token: str):
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") == "HS256":
            email = verify_token(token)
            return {"sub": email}
        return await verify_auth0_token(token)
    except Exception:
        return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = await decode_token(credentials.credentials)
    if not payload:
        raise credentials_exception

    email = payload.get("email") or payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    request.state.token_permissions = payload.get("permissions", [])

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_user_optional(request: Request) -> Optional[User]:
    """Get current user from request without raising exceptions."""
    try:
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        payload = await decode_token(token)
        if not payload:
            return None
        email = payload.get("email") or payload.get("sub")
        
        # We need a database session here, but can't inject it
        # This is a simplified version for rate limiting purposes
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            return user if user and user.is_active else None
        finally:
            db.close()
    except Exception:
        return None


# Example usage for FastAPI endpoints:
# @router.get("/admin")
# async def admin_dashboard(current_user: User = Depends(require_roles("admin"))):
#     ...
