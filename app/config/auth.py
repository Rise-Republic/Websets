from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    """Authentication related settings."""

    jwt_secret_key: str = Field(validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v:
            raise ValueError("JWT secret key is required")
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        if v.lower() in ("your-secret-key", "secret", "changeme"):
            raise ValueError("JWT secret key cannot be a default or weak value")
        return v
