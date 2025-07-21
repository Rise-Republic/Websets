"""
Comprehensive audit logging middleware
Tracks all user actions for security and compliance
"""

import json
import time
import uuid
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger
import hashlib

from app.models.role import AuditLog, DataAccessLog
from app.database import SessionLocal
from app.auth.dependencies import get_current_user_optional


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses for audit purposes."""
    
    def __init__(self, app: ASGIApp, skip_paths: Optional[list] = None):
        super().__init__(app)
        self.skip_paths = skip_paths or [
            "/health",
            "/metrics",
            "/favicon.ico",
            "/docs",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Skip audit for health checks and static files
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        
        # Generate trace ID for request correlation
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        
        # Get user info
        user = await get_current_user_optional(request)
        user_id = user.id if user else None
        user_email = user.email if user else None
        
        # Extract request details
        request_body = await self._extract_request_body(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log audit entry
        await self._log_audit_entry(
            request=request,
            response=response,
            user_id=user_id,
            user_email=user_email,
            request_body=request_body,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return response
    
    async def _extract_request_body(self, request: Request) -> Optional[str]:
        """Extract and sanitize request body for audit logging."""
        try:
            # Clone request body to avoid consuming it
            body = await request.body()
            if not body:
                return None
            
            # Parse JSON and filter sensitive data
            try:
                data = json.loads(body.decode())
                sanitized = self._sanitize_sensitive_data(data)
                return json.dumps(sanitized)
            except json.JSONDecodeError:
                # For non-JSON bodies, return truncated content
                return body[:1000].decode('utf-8', errors='ignore')
                
        except Exception as e:
            logger.error(f"Error extracting request body: {e}")
            return None
    
    def _sanitize_sensitive_data(self, data: Any) -> Any:
        """Remove or mask sensitive information from request data."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in [
                    'password', 'token', 'secret', 'key', 'auth', 'credential'
                ]):
                    sanitized[key] = '[REDACTED]'
                elif key_lower == 'email':
                    sanitized[key] = self._mask_email(value)
                else:
                    sanitized[key] = self._sanitize_sensitive_data(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_sensitive_data(item) for item in data]
        else:
            return data
    
    def _mask_email(self, email: str) -> str:
        """Mask email address for privacy."""
        if '@' not in str(email):
            return '[REDACTED]'
        username, domain = str(email).split('@', 1)
        masked_username = username[:2] + '*' * (len(username) - 2)
        return f"{masked_username}@{domain}"
    
    async def _log_audit_entry(
        self,
        request: Request,
        response: Response,
        user_id: Optional[uuid.UUID],
        user_email: Optional[str],
        request_body: Optional[str],
        duration_ms: int,
        trace_id: str
    ):
        """Create audit log entry in database."""
        try:
            db = SessionLocal()
            
            # Extract query parameters
            query_params = dict(request.query_params)
            
            # Create audit log
            audit_log = AuditLog(
                user_id=user_id,
                user_email=user_email,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get('user-agent'),
                action=f"{request.method}_{request.url.path}",
                resource_type=self._extract_resource_type(request.url.path),
                resource_id=self._extract_resource_id(request.url.path),
                method=request.method,
                path=str(request.url.path),
                query_params=json.dumps(query_params) if query_params else None,
                request_body=request_body,
                status_code=response.status_code,
                duration_ms=duration_ms,
                trace_id=trace_id,
                tenant_id=getattr(request.state, 'tenant_id', None)
            )
            
            db.add(audit_log)
            db.commit()
            
            # Log to file as well for redundancy
            logger.info(
                "AUDIT",
                trace_id=trace_id,
                user_id=str(user_id) if user_id else None,
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                ip=self._get_client_ip(request)
            )
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        finally:
            db.close()
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address, considering proxies."""
        # Check for forwarded headers
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else 'unknown'
    
    def _extract_resource_type(self, path: str) -> str:
        """Extract resource type from URL path."""
        parts = path.strip('/').split('/')
        if parts:
            return parts[0]
        return 'unknown'
    
    def _extract_resource_id(self, path: str) -> Optional[str]:
        """Extract resource ID from URL path."""
        parts = path.strip('/').split('/')
        if len(parts) >= 2 and parts[1]:
            # Check if it looks like a UUID
            try:
                uuid.UUID(parts[1])
                return parts[1]
            except ValueError:
                return parts[1]
        return None


class DataAccessAudit:
    """Helper class for logging data access events."""
    
    @staticmethod
    def log_data_access(
        user_id: uuid.UUID,
        access_type: str,
        dataset_id: Optional[uuid.UUID] = None,
        job_id: Optional[uuid.UUID] = None,
        records_accessed: Optional[int] = None,
        filters_applied: Optional[Dict[str, Any]] = None,
        contains_pii: bool = False,
        data_categories: Optional[list] = None
    ):
        """Log data access for GDPR compliance."""
        try:
            db = SessionLocal()
            
            access_log = DataAccessLog(
                user_id=user_id,
                dataset_id=dataset_id,
                job_id=job_id,
                access_type=access_type,
                records_accessed=records_accessed,
                filters_applied=json.dumps(filters_applied) if filters_applied else None,
                contains_pii=contains_pii,
                data_categories=data_categories
            )
            
            db.add(access_log)
            db.commit()
            
            logger.info(
                "DATA_ACCESS",
                user_id=str(user_id),
                access_type=access_type,
                dataset_id=str(dataset_id) if dataset_id else None,
                job_id=str(job_id) if job_id else None,
                records_accessed=records_accessed
            )
            
        except Exception as e:
            logger.error(f"Failed to log data access: {e}")
        finally:
            db.close()


class SecurityEventLogger:
    """Centralized security event logging."""
    
    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: Optional[uuid.UUID] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ):
        """Log security-related events."""
        event_data = {
            "event_type": event_type,
            "user_id": str(user_id) if user_id else None,
            "email": email,
            "ip_address": ip_address,
            "details": details,
            "timestamp": str(time.time()),
            "severity": severity
        }
        
        logger.bind(**event_data).log(severity.upper(), f"SECURITY_{event_type}")
    
    @staticmethod
    def log_failed_login(email: str, ip_address: str, reason: str):
        """Log failed login attempts."""
        SecurityEventLogger.log_security_event(
            "FAILED_LOGIN",
            email=email,
            ip_address=ip_address,
            details={"reason": reason},
            severity="warning"
        )
    
    @staticmethod
    def log_password_change(user_id: uuid.UUID, ip_address: str):
        """Log password changes."""
        SecurityEventLogger.log_security_event(
            "PASSWORD_CHANGE",
            user_id=user_id,
            ip_address=ip_address,
            severity="info"
        )
    
    @staticmethod
    def log_suspicious_activity(user_id: uuid.UUID, activity: str, details: Dict[str, Any]):
        """Log suspicious user activities."""
        SecurityEventLogger.log_security_event(
            "SUSPICIOUS_ACTIVITY",
            user_id=user_id,
            details={"activity": activity, **details},
            severity="warning"
        )
