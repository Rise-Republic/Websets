from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from pydantic import BaseModel, EmailStr, field_validator
import re
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.database import get_db
from app.models.user import User
from app.auth.jwt_handler import create_access_token, get_password_hash, verify_password
from app.auth.dependencies import get_current_active_user
from app.config import settings
from app.middleware import limiter, RateLimits
from app.middleware.audit_middleware import SecurityEventLogger

router = APIRouter(prefix="/auth", tags=["authentication"])

serializer = URLSafeTimedSerializer(settings.jwt_secret_key)


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


@router.post("/register", response_model=UserResponse)
@limiter.limit(RateLimits.AUTH_REGISTER)
async def register(
    request: Request, user_data: UserCreate, db: Session = Depends(get_db)
):
    """Register a new user."""

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = serializer.dumps(user.email)
    user.verification_token = token
    user.verification_token_expiry = datetime.utcnow() + timedelta(hours=24)
    db.commit()

    # In a real app, send an email. For tests we just log the link.
    print(f"Verification link: /auth/verify?token={token}")

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


@router.get("/verify")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify a user's email address."""
    try:
        email = serializer.loads(token, max_age=24 * 3600)
    except SignatureExpired:
        raise HTTPException(status_code=400, detail="Token expired")
    except BadSignature:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user or user.verification_token != token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if (
        user.verification_token_expiry
        and user.verification_token_expiry < datetime.utcnow()
    ):
        raise HTTPException(status_code=400, detail="Token expired")

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expiry = None
    db.commit()
    return {"message": "Email verified"}


@router.post("/login", response_model=Token)
@limiter.limit(RateLimits.AUTH_LOGIN)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login and get access token."""

    # Authenticate user
    user = db.query(User).filter(User.email == form_data.username).first()
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

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
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

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Update last login
    from datetime import datetime

    user.last_login = datetime.utcnow()
    db.commit()

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
