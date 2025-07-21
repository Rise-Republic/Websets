"""
RBAC enforcement utilities for FastAPI endpoints
"""
from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.models.role import Role, Permission
from app.auth.dependencies import get_current_active_user
from sqlalchemy.orm import Session
from app.database import get_db
from typing import List


def require_roles(*roles: List[str]):
    """Dependency to require user to have at least one of the specified roles."""
    def dependency(current_user: User = Depends(get_current_active_user)):
        user_roles = {role.name for role in getattr(current_user, 'roles', [])}
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {roles}"
            )
        return current_user
    return dependency


def require_permissions(*permissions: List[str]):
    """Dependency to require user to have at least one of the specified permissions."""
    def dependency(current_user: User = Depends(get_current_active_user)):
        user_permissions = set()
        for role in getattr(current_user, 'roles', []):
            user_permissions.update({perm.name for perm in getattr(role, 'permissions', [])})
        if not any(perm in user_permissions for perm in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permission. Required: {permissions}"
            )
        return current_user
    return dependency
