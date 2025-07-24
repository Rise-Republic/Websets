from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, ConfigDict, validator

from app.models import User
from app.auth.dependencies import get_current_active_user
from app.api.dependencies import get_user_repository
from app.repositories.user_repository import UserRepository


router = APIRouter(prefix="/users", tags=["v1-users"])


class UserProfileResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    created_at: str
    is_verified: bool = False

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    created_at: str
    is_verified: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @validator("new_password")
    def validate_password(cls, v: str):
        return validate_password(v)


class EmailChangeRequest(BaseModel):
    password: str
    new_email: EmailStr

    @validator("password")
    def validate_password_field(cls, v: str):
        return validate_password(v)


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat(),
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    current_user.updated_at = datetime.utcnow()
    user_repo.commit()
    user_repo.refresh(current_user)
    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat(),
    )


@router.patch("/me/password")
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
    current_user.hashed_password = get_password_hash(data.new_password)
    current_user.last_password_change = datetime.utcnow()
    user_repo.commit()
    return {"message": "Password updated"}


@router.patch("/me/email")
async def change_email(
    data: EmailChangeRequest,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    if not verify_password(data.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
    existing = user_repo.get_by_email(data.new_email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    current_user.email = data.new_email
    current_user.is_verified = False
    current_user.updated_at = datetime.utcnow()
    user_repo.commit()
    user_repo.refresh(current_user)
    return {"message": "Email updated"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_account(
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    current_user.is_active = False
    current_user.updated_at = datetime.utcnow()
    user_repo.commit()
    return None

