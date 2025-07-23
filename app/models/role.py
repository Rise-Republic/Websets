"""
Role-Based Access Control (RBAC) Models
Implements comprehensive role and permission system
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
)

# Association table for role permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime, default=datetime.utcnow),
    Column('granted_by', UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
)


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # Cannot be deleted
    
    # Hierarchy support
    parent_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        foreign_keys=[user_roles.c.role_id, user_roles.c.user_id]
    )
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    children = relationship("Role")
    parent = relationship("Role", remote_side=[id])


class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    resource = Column(String(50), nullable=False, index=True)  # e.g., 'jobs', 'datasets', 'users'
    action = Column(String(50), nullable=False, index=True)   # e.g., 'create', 'read', 'update', 'delete'
    conditions = Column(ARRAY(String), nullable=True)  # JSON conditions for fine-grained control
    
    # Scope restrictions
    tenant_scoped = Column(Boolean, default=False)  # Permission is tenant-specific
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User information
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    user_email = Column(String, nullable=True)  # For deleted users
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Action details
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(100), nullable=True)
    resource_name = Column(String(255), nullable=True)
    
    # Request details
    method = Column(String(10), nullable=True)
    path = Column(String(500), nullable=True)
    query_params = Column(Text, nullable=True)
    request_body = Column(Text, nullable=True)  # Sensitive data filtered
    
    # Response details
    status_code = Column(Integer, nullable=True)
    response_size = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Additional context
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    session_id = Column(String(255), nullable=True)
    trace_id = Column(String(255), nullable=True)  # For distributed tracing
    
    # Performance metrics
    duration_ms = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class DataAccessLog(Base):
    __tablename__ = "data_access_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User information
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Data accessed
    dataset_id = Column(UUID(as_uuid=True), ForeignKey('datasets.id'), nullable=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id'), nullable=True)
    
    # Access details
    access_type = Column(String(20), nullable=False)  # 'read', 'download', 'export', 'delete'
    records_accessed = Column(Integer, nullable=True)
    filters_applied = Column(Text, nullable=True)  # JSON of search filters
    
    # Data sensitivity
    contains_pii = Column(Boolean, default=False)
    data_categories = Column(ARRAY(String), nullable=True)  # Types of data accessed
    
    # Timestamps
    accessed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="data_access_logs")
    dataset = relationship("Dataset", back_populates="access_logs")
    job = relationship("Job", back_populates="data_access_logs")
