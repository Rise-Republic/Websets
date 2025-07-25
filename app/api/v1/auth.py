from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from pydantic import BaseModel, EmailStr, validator, ConfigDict
import hashlib
import os
import secrets
from loguru import logger

import pyotp
from prometheus_client import Counter, generate_latest
from app.utils.mailer import send_password_reset
from app.utils.password_validation import validate_password

from app.database import get_db
from app.models.user import User
from app.auth.jwt_handler import create_access_token, get_password_hash, verify_password
from app.repositories import UserRepository

from app.config import settings
from app.middleware import limiter, RateLimits
from app.middleware.audit_middleware import SecurityEventLogger
from app.utils import send_email
from app.api.dependencies import get_user_repository

router = APIRouter(prefix="/auth", tags=["v1-authentication"])

# Prometheus metrics
login_success = Counter("auth_login_success_total", "Successful logins")
login_fail = Counter("auth_login_fail_total", "Failed logins")
mfa_challenge_failures = Counter("auth_mfa_challenge_failures", "Failed MFA challenges")
password_reset_requests = Counter(
    "auth_password_reset_requests", "Password reset requests"
)
password_reset_success = Counter(
    "auth_password_reset_success", "Successful password resets"
)


# Helper for secrets management
def get_env_secret(key, default=None):
    return os.environ.get(key, getattr(settings, key, default))


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = None
    mfa_enabled: bool = False
    mfa_method: str = "totp"  # or "email"/"sms"
    consent: bool = False

    @validator("password")
    def validate_password_field(cls, v):
        return validate_password(v)


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str = None
    is_active: bool
    created_at: str
    mfa_enabled: bool = False
    mfa_method: str = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str = None


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
    try:
        existing_user = user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        import secrets
        import hashlib
        from datetime import datetime, timedelta

        hashed_password = get_password_hash(user_data.password)
        mfa_secret = None
        if user_data.mfa_enabled and user_data.mfa_method == "totp":
            # Generate a base32 secret for TOTP and store it
            secret = pyotp.random_base32()
            mfa_secret = secret
        token = secrets.token_urlsafe(32)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
            mfa_enabled=user_data.mfa_enabled,
            mfa_method=user_data.mfa_method,
            mfa_secret=mfa_secret,
            consent_given=user_data.consent,
            consent_given_at=datetime.utcnow() if user_data.consent else None,
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
            mfa_enabled=user.mfa_enabled,
            mfa_method=user.mfa_method,
            verification_token=token,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback

        logger.exception(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=Token)
@limiter.limit(RateLimits.AUTH_LOGIN)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Login and get access token."""
    user = user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        login_fail.inc()
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
    # MFA enforcement
    if user.mfa_enabled:
        # Require MFA challenge
        return Response(
            content="MFA required",
            status_code=status.HTTP_202_ACCEPTED,
            headers={"X-MFA-Required": "true"},
        )
    # Create access and refresh tokens
    access_token_expires = timedelta(
        minutes=int(get_env_secret("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
    )
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = secrets.token_urlsafe(32)
    user.refresh_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    user.refresh_token_expiry = datetime.utcnow() + timedelta(days=7)
    user.last_login = datetime.utcnow()
    user_repo.commit()
    login_success.inc()
    response = {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }
    return response


@router.get("/me", response_model=UserResponse)
@limiter.limit(RateLimits.API_READ)
async def get_current_user_info(
    request: Request, current_user: User = Depends(lambda: __import__('app.auth.dependencies', fromlist=['get_current_active_user']).get_current_active_user())
):
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        mfa_enabled=current_user.mfa_enabled,
        mfa_method=current_user.mfa_method,
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
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expiry = None
    user_repo.commit()
    return {"message": "Email verified"}


@router.get("/verify-email")
@limiter.limit(RateLimits.AUTH_REGISTER)
async def verify_email(
    request: Request,
    token: str,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Confirm a user's email address using a verification token."""
    import hashlib
    from datetime import datetime

    user = user_repo.get_by_verification_token(
        hashlib.sha256(token.encode()).hexdigest()
    )
    if not user or user.verification_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expiry = None
    user_repo.commit()
    return {"message": "Email verified"}


# MFA setup
class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


@router.post("/mfa/setup", response_model=MFASetupResponse)
@limiter.limit(RateLimits.AUTH_REGISTER)
async def mfa_setup(
    request: Request,
    current_user: User = Depends(lambda: __import__('app.auth.dependencies', fromlist=['get_current_active_user']).get_current_active_user()),
    user_repo: UserRepository = Depends(get_user_repository),
):
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA already enabled")
    secret = pyotp.random_base32()
    current_user.mfa_secret = secret
    current_user.mfa_enabled = True
    current_user.mfa_method = "totp"
    user_repo.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=current_user.email, issuer_name="WebSet Miner"
    )
    return MFASetupResponse(secret=secret, provisioning_uri=uri)


# MFA endpoints
class MFAVerifyRequest(BaseModel):
    email: EmailStr
    code: str


@router.post("/mfa/verify", response_model=Token)
@limiter.limit(RateLimits.AUTH_LOGIN)
async def mfa_verify(
    request: Request,
    data: MFAVerifyRequest,
    user_repo: UserRepository = Depends(get_user_repository),
):
    user = user_repo.get_by_email(data.email)
    if not user or not user.mfa_enabled:
        mfa_challenge_failures.inc()
        raise HTTPException(status_code=401, detail="MFA not enabled or user not found")
    # TOTP verification
    if user.mfa_method == "totp":
        totp = pyotp.TOTP(user.mfa_secret)
        # allow codes from previous or next 30s window
        if not totp.verify(data.code, valid_window=1):
            mfa_challenge_failures.inc()
            raise HTTPException(status_code=401, detail="Invalid MFA code")
    # Issue tokens
    access_token_expires = timedelta(
        minutes=int(get_env_secret("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
    )
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = secrets.token_urlsafe(32)
    user.refresh_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    user.refresh_token_expiry = datetime.utcnow() + timedelta(days=7)
    user_repo.commit()
    login_success.inc()
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


# Password reset endpoints
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @validator("new_password")
    def validate_new_password(cls, v: str) -> str:
        return validate_password(v)


@router.post("/password-reset/request")
@limiter.limit(RateLimits.AUTH_REGISTER)
async def password_reset_request(
    request: Request,
    data: PasswordResetRequest,
    user_repo: UserRepository = Depends(get_user_repository),
):
    user = user_repo.get_by_email(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    token = secrets.token_urlsafe(32)
    user.password_reset_token = hashlib.sha256(token.encode()).hexdigest()
    user.password_reset_expiry = datetime.utcnow() + timedelta(minutes=15)
    user_repo.commit()
    password_reset_requests.inc()
    reset_url = f"{request.base_url}v1/auth/password-reset/confirm?token={token}"
    send_email(user.email, "Password Reset", f"Reset your password: {reset_url}")
    return {"message": "Password reset link sent"}

@router.post("/password-reset/confirm", name="password_reset_confirm")
@limiter.limit(RateLimits.AUTH_REGISTER)
async def password_reset_confirm(
    request: Request,
    data: PasswordResetConfirm,
    user_repo: UserRepository = Depends(get_user_repository),
):
    user = user_repo.get_by_password_reset_token(
        hashlib.sha256(data.token.encode()).hexdigest()
    )
    if not user or user.password_reset_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user.hashed_password = get_password_hash(data.new_password)
    user.password_reset_token = None
    user.password_reset_expiry = None
    user.refresh_token = None  # Revoke refresh tokens
    user_repo.commit()
    password_reset_success.inc()
    return {"message": "Password reset successful"}


# Refresh token endpoint
class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=Token)
@limiter.limit(RateLimits.AUTH_LOGIN)
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    user_repo: UserRepository = Depends(get_user_repository),
):
    hashed = hashlib.sha256(data.refresh_token.encode()).hexdigest()
    user = user_repo.get_by_refresh_token(hashed)
    if not user or user.refresh_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    access_token_expires = timedelta(
        minutes=int(get_env_secret("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
    )
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    # Optionally rotate refresh token
    refresh_token = secrets.token_urlsafe(32)
    user.refresh_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    user.refresh_token_expiry = datetime.utcnow() + timedelta(days=7)
    user_repo.commit()
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@router.get("/debug")
async def auth_debug(
    current_user: User = Depends(lambda: __import__('app.auth.dependencies', fromlist=['get_current_active_user']).get_current_active_user()), request: Request = None
):
    perms = getattr(request.state, "token_permissions", []) if request else []
    return {"user": current_user.email, "permissions": perms}


# Prometheus metrics endpoint
@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
