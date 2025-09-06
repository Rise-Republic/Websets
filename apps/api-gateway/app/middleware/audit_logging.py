"""
Audit logging middleware for FastAPI
Logs user actions, data access, and failed authentication attempts
"""
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.models.role import AuditLog
from app.database import SessionLocal
from loguru import logger
import time
import uuid

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        user_id = getattr(request.state, 'user_id', None)
        user_email = getattr(request.state, 'user_email', None)
        trace_id = str(uuid.uuid4())
        db = SessionLocal()
        try:
            audit_log = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action=f"{request.method}_{request.url.path}",
                resource_type=request.url.path.split('/')[1] if len(request.url.path.split('/')) > 1 else '',
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                trace_id=trace_id
            )
            db.add(audit_log)
            db.commit()
            logger.info(f"AUDIT: {request.method} {request.url.path} user={user_email} status={response.status_code} duration={duration_ms}ms")
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
        finally:
            db.close()
        return response
