from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from app.models.types import GUID as UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base
from app.models.role import user_roles


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Profile
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    verification_token = Column(String, nullable=True)
    verification_token_expiry = Column(DateTime, nullable=True)

    # Security fields
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    last_password_change = Column(DateTime, default=datetime.utcnow)

    # MFA fields
    mfa_secret = Column(String, nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_method = Column(String, nullable=True)  # "totp", "email", "sms"
    backup_codes = Column(Text, nullable=True)  # JSON encrypted backup codes

    # Password reset fields
    password_reset_token = Column(String, nullable=True)
    password_reset_expiry = Column(DateTime, nullable=True)

    # Refresh token fields
    refresh_token = Column(String, nullable=True)
    refresh_token_expiry = Column(DateTime, nullable=True)

    # Tenant information (for multi-tenancy)
    tenant_id = Column(UUID, nullable=True)

    # GDPR compliance
    consent_given = Column(Boolean, default=False)
    consent_given_at = Column(DateTime, nullable=True)
    data_retention_days = Column(Integer, default=365)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)

    # Relationships
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        foreign_keys=[user_roles.c.user_id, user_roles.c.role_id],
    )
    audit_logs = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )
    data_access_logs = relationship(
        "DataAccessLog", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
