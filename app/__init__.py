# To enable audit logging, add the following to your FastAPI app:
# from app.middleware.audit_logging import AuditLoggingMiddleware
# app.add_middleware(AuditLoggingMiddleware)

from .polar import PolarClient, get_polar_client

__all__ = ["PolarClient", "get_polar_client"]
