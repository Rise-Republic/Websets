from typing import List, Optional
from fastapi import Request
from starlette.routing import Match
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.dependencies import get_current_user_optional
from app.middleware.audit_middleware import SecurityEventLogger


class RBACMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing role and permission checks."""

    async def dispatch(self, request: Request, call_next):
        endpoint = request.scope.get("endpoint")
        if endpoint is None:
            for route in request.app.routes:
                if hasattr(route, 'matches'):
                    match, _ = route.matches(request.scope)
                    if match == Match.FULL:
                        endpoint = getattr(route, 'endpoint', None)
                        break
        if endpoint is not None:
            required_roles = getattr(endpoint, "required_roles", [])
            required_perms = getattr(endpoint, "required_permissions", [])
            if required_roles or required_perms:
                user = await get_current_user_optional(request)
                if not user:
                    SecurityEventLogger.log_security_event(
                        "RBAC_DENIED",
                        ip_address=request.client.host if request.client else "unknown",
                        details={"path": str(request.url.path), "reason": "not_authenticated"},
                        severity="warning",
                    )
                    return JSONResponse(
                        status_code=401, content={"detail": "Not authenticated"}
                    )

                request.state.user_id = str(user.id)
                request.state.user_email = user.email

                if required_roles:
                    user_roles = {r.name for r in getattr(user, "roles", [])}
                    if not any(role in user_roles for role in required_roles):
                        SecurityEventLogger.log_security_event(
                            "RBAC_DENIED",
                            user_id=user.id,
                            email=user.email,
                            ip_address=request.client.host if request.client else "unknown",
                            details={"required_roles": required_roles, "path": str(request.url.path)},
                            severity="warning",
                        )
                        return JSONResponse(
                            status_code=403,
                            content={"detail": f"Insufficient role. Required: {required_roles}"},
                        )

                if required_perms:
                    user_perms = set(getattr(request.state, 'token_permissions', []) or [])
                    for role in getattr(user, "roles", []):
                        user_perms.update(
                            {p.name for p in getattr(role, "permissions", [])}
                        )
                    if not any(p in user_perms for p in required_perms):
                        SecurityEventLogger.log_security_event(
                            "RBAC_DENIED",
                            user_id=user.id,
                            email=user.email,
                            ip_address=request.client.host if request.client else "unknown",
                            details={"required_permissions": required_perms, "path": str(request.url.path)},
                            severity="warning",
                        )
                        return JSONResponse(
                            status_code=403,
                            content={"detail": f"Insufficient permission. Required: {required_perms}"},
                        )
        return await call_next(request)


def rbac_required(
    *, roles: Optional[List[str]] = None, permissions: Optional[List[str]] = None
):
    """Decorator to attach RBAC requirements to endpoints."""

    def decorator(func):
        setattr(func, "required_roles", roles or [])
        setattr(func, "required_permissions", permissions or [])
        return func

    return decorator
