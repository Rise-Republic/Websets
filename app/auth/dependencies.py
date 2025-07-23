from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.auth.jwt_handler import verify_token
from app.auth.rbac import require_roles, require_permissions
from app.auth.user_utils import get_current_active_user

security = HTTPBearer()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security, use_cache=False),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    email = verify_token(token)
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_user_optional(request: Request) -> Optional[User]:
    """Get current user from request without raising exceptions."""
    try:
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        email = verify_token(token)
        if email is None:
            return None
        
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