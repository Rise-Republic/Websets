from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import HTTPException, status

class TenantGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only enforce on authenticated routes
        user = getattr(request.state, "user", None)
        if user:
            header_org = request.headers.get("X-Org-ID")
            user_org = getattr(user, "org_id", None)
            if header_org and header_org != str(user_org):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant isolation enforced")
        return await call_next(request)
