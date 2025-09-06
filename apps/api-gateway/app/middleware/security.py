"""Middleware to add common security headers."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request


class SecurityMiddleware(BaseHTTPMiddleware):
    """Add HSTS, CSP, and X-Frame-Options headers to responses."""

    def __init__(self, app: ASGIApp, *, hsts_seconds: int = 63072000, include_subdomains: bool = True) -> None:
        super().__init__(app)
        value = f"max-age={hsts_seconds}"
        if include_subdomains:
            value += "; includeSubDomains"
        self.hsts_header = value
        self.csp_header = (
            "default-src 'self'; "
            "script-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'"
        )

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("Strict-Transport-Security", self.hsts_header)
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Content-Security-Policy", self.csp_header)
        return response
