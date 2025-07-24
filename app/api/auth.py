from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr, field_validator
import re

from app.database import get_db
from app.models.user import User
from app.auth.jwt_handler import create_access_token, get_password_hash, verify_password
from app.repositories import UserRepository
from app.auth.dependencies import get_current_active_user
from app.config import settings
from app.middleware import limiter, RateLimits
from app.middleware.audit_middleware import SecurityEventLogger

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency injector for ``UserRepository``."""
    return UserRepository(db)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str = None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class RegistrationResponse(UserResponse):
    verification_token: str


@router.post("/register", response_model=RegistrationResponse)
@limiter.limit(RateLimits.AUTH_REGISTER)
async def register(
    request: Request,
    user_data: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Register a new user."""

    # Check if user already exists
    existing_user = user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    import secrets
    import hashlib
    from datetime import datetime, timedelta

    hashed_password = get_password_hash(user_data.password)
    token = secrets.token_urlsafe(32)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        verification_token=hashlib.sha256(token.encode()).hexdigest(),
        verification_token_expiry=datetime.utcnow() + timedelta(hours=24),
    )

    user_repo.add(user)

    return RegistrationResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        verification_token=token,
    )


@router.post("/login", response_model=Token)
@limiter.limit(RateLimits.AUTH_LOGIN)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Login and get access token."""

    # Authenticate user
    user = user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        SecurityEventLogger.log_failed_login(
            email=form_data.username,
            ip_address=request.client.host if request.client else "unknown",
            reason="invalid_credentials",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        SecurityEventLogger.log_failed_login(
            email=user.email,
            ip_address=request.client.host if request.client else "unknown",
            reason="inactive_user",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    if not user.is_verified:
        SecurityEventLogger.log_failed_login(
            email=user.email,
            ip_address=request.client.host if request.client else "unknown",
            reason="unverified_user",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Update last login
    from datetime import datetime

    user.last_login = datetime.utcnow()
    user_repo.commit()

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
@limiter.limit(RateLimits.API_READ)
async def get_current_user_info(
    request: Request, current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )


class VerificationRequest(BaseModel):
    token: str


@router.post("/verify")
@limiter.limit(RateLimits.AUTH_REGISTER)
async def verify_user(
    request: Request,
    data: VerificationRequest,
    user_repo: UserRepository = Depends(get_user_repository),
):
    import hashlib
    from datetime import datetime

    user = user_repo.get_by_verification_token(
        hashlib.sha256(data.token.encode()).hexdigest()
    )
    if not user or user.verification_token_expiry < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expiry = None
    user_repo.commit()
    return {"message": "Email verified"}
