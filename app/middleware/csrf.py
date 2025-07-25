from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status
import secrets

CSRF_HEADER = "x-csrf-token"
CSRF_COOKIE = "csrf_token"

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only enforce on state-changing methods
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            csrf_cookie = request.cookies.get(CSRF_COOKIE)
            csrf_header = request.headers.get(CSRF_HEADER)
            if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
        # On GET, set a CSRF cookie if missing
        response: Response = await call_next(request)
        if request.method == "GET" and not request.cookies.get(CSRF_COOKIE):
            import os
            import base64
            token = base64.urlsafe_b64encode(os.urandom(32)).decode()
            response.set_cookie(CSRF_COOKIE, token, httponly=False, secure=True, samesite="Lax")
        return response
