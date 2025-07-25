from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import HTTPException, status

from app.tenancy import set_current_tenant

class TenantGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """Ensure tenant ID from session matches any provided header."""
        user = getattr(request.state, "user", None)
        tenant_id = None
        if user:
            tenant_id = getattr(user, "tenant_id", None) or getattr(
                user, "organization_id", None
            )

        header_tenant = request.headers.get("X-Org-ID")

        if header_tenant and tenant_id and header_tenant != str(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant isolation enforced",
            )

        if request.url.path.startswith("/v1") and tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant context missing",
            )

        set_current_tenant(tenant_id)
        try:
            return await call_next(request)
        finally:
            set_current_tenant(None)
