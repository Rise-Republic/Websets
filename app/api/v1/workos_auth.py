"""
WorkOS AuthKit integration for Websets authentication
Implements enterprise-grade auth with secure session management
"""
import os
import secrets
import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Response, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import APIKeyCookie
from starlette.middleware.base import BaseHTTPMiddleware
from workos import WorkOSClient
from workos.exceptions import AuthenticationException, BadRequestException
from typing import Optional, Dict, Any, Callable

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["workos-auth"])

# Security constants
COOKIE_NAME = "session"
COOKIE_MAX_AGE = 14 * 24 * 3600  # 14 days in seconds
STATE_MAX_AGE = 300  # 5 minutes in seconds

# Authentication options
ENFORCE_MFA = os.getenv("WORKOS_ENFORCE_MFA", "false").lower() == "true"  # Make MFA optional by default
ALLOW_PASSKEYS = True  # Enable passkey support

# Environment-aware WorkOS configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Use test credentials in development, live in production
api_key = os.getenv("WORKOS_API_KEY_LIVE" if IS_PRODUCTION else "WORKOS_API_KEY_TEST")
client_id = os.getenv("WORKOS_CLIENT_ID_LIVE" if IS_PRODUCTION else "WORKOS_CLIENT_ID_TEST")
redirect_uri = os.getenv("WORKOS_REDIRECT_URI", "http://localhost:8001/api/auth/callback")

if not api_key or not client_id:
    raise RuntimeError(f"WorkOS credentials missing for {ENVIRONMENT} environment: API_KEY and/or CLIENT_ID not set")

# Debug logging for WorkOS credentials
print(f"DEBUG: Environment: {ENVIRONMENT}")
print(f"DEBUG: Using WorkOS client_id: {client_id}")
print(f"DEBUG: Using WorkOS API key: {api_key[:10]}...")
print(f"DEBUG: Using WorkOS redirect URI: {redirect_uri}")

# Initialize WorkOS client with environment-specific credentials
workos_client = WorkOSClient(
    api_key=api_key,
    client_id=client_id
)

# Get session password from environment (in production, from Vault)
cookie_password = os.getenv("WORKOS_COOKIE_PASSWORD")
if not cookie_password:
    if ENVIRONMENT == "production":
        raise RuntimeError("WORKOS_COOKIE_PASSWORD not set in production environment")
    else:
        # Only use default in development, never in production
        cookie_password = "yvHkj2U4tkv+oYGZon1EDfQVtbb4ro9cabdEAV9YH9A="
        logger.warning(
            "Using default WORKOS_COOKIE_PASSWORD in development. "
            "This is insecure and should NEVER be used in production."
        )

WORKOS_COOKIE_PASSWORD = cookie_password

# Session cookie security
session_cookie = APIKeyCookie(name=COOKIE_NAME, auto_error=False)

# Session validation dependency using WorkOS sealed sessions
async def require_session(request: Request):
    """
    Validate user session using WorkOS sealed session pattern from official docs
    Raises 401 if session is invalid or missing
    """
    sealed_session = request.cookies.get(COOKIE_NAME)
    
    if not sealed_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        # Load sealed session using WorkOS SDK (per official docs)
        session = workos_client.user_management.load_sealed_session(
            sealed_session=sealed_session,
            cookie_password=cookie_password
        )
        
        # Authenticate the session (per official docs)
        auth_response = session.authenticate()
        
        if auth_response.authenticated:
            # Store user in request state for route handlers
            request.state.user = auth_response.user
            request.state.session = session
            return session
        
        # If session is not authenticated, try to refresh
        if auth_response.reason == "no_session_cookie_provided":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Attempt session refresh (per official docs)
        try:
            refresh_result = session.refresh()
            if refresh_result.authenticated:
                request.state.user = refresh_result.user
                request.state.session = session
                return session
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired"
                )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Session verification failed: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

@router.get("/login")
async def initiate_login(request: Request):
    """
    Redirect users to WorkOS AuthKit for authentication
    Follows official WorkOS documentation pattern
    """
    try:
        # Generate WorkOS authorization URL (per official docs)
        authorization_url = workos_client.user_management.get_authorization_url(
            provider="authkit",
            redirect_uri=redirect_uri
        )
        
        return RedirectResponse(url=authorization_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Failed to initiate login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate login: {str(e)}")

@router.get("/callback")
async def auth_callback(
    request: Request,
    code: Optional[str] = None
):
    """
    Handle WorkOS callback after user authentication
    Uses official WorkOS sealed session pattern from documentation
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")
    
    try:
        # Exchange code for user profile using WorkOS sealed session (per official docs)
        auth_response = workos_client.user_management.authenticate_with_code(
            code=code,
            session={
                "seal_session": True,
                "cookie_password": cookie_password
            }
        )
        
        # Create redirect response
        response = RedirectResponse(url="/dashboard", status_code=302)
        
        # Set secure session cookie with sealed session (per official docs)
        response.set_cookie(
            COOKIE_NAME,
            auth_response.sealed_session,
            httponly=True,
            secure=IS_PRODUCTION,  # Only use secure=True in production
            samesite="lax",
            max_age=COOKIE_MAX_AGE,
            path="/"
        )
        
        # Log successful authentication (without PII)
        logger.info(f"User authenticated: {auth_response.user.id}")
        
        return response
        
    except AuthenticationException as e:
        logger.warning(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.post("/logout")
async def logout(request: Request, session = Depends(require_session)):
    """
    Handle user logout by clearing session cookie
    """
    try:
        # Clear session cookie
        response = JSONResponse(content={"message": "Logged out successfully"})
        response.delete_cookie(COOKIE_NAME, path="/")
        
        return response
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

# Example protected route
@router.get("/me")
async def get_current_user(request: Request, session = Depends(require_session)):
    """
    Protected route that returns the current authenticated user
    Returns complete WorkOS user object structure
    """
    user = request.state.user
    return {
        "object": "user",
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email_verified": getattr(user, 'email_verified', True),
        "profile_picture_url": getattr(user, 'profile_picture_url', None),
        "last_sign_in_at": getattr(user, 'last_sign_in_at', None),
        "external_id": getattr(user, 'external_id', None),
        "metadata": getattr(user, 'metadata', {}),
        "created_at": getattr(user, 'created_at', None),
        "updated_at": getattr(user, 'updated_at', None)
    }

# Middleware class for global session validation
class SessionMiddleware(BaseHTTPMiddleware):
    """
    Global middleware to validate sessions for protected routes
    """
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip auth for public routes
        if request.url.path.startswith("/api/auth/login") or \
           request.url.path.startswith("/api/auth/callback") or \
           request.url.path.startswith("/api/health"):
            return await call_next(request)
            
        # Check for session cookie
        session_cookie = request.cookies.get(COOKIE_NAME)
        if not session_cookie and request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"}
            )
            
        # For protected routes, validate session
        if session_cookie and request.url.path.startswith("/api/"):
            try:
                session = workos_client.user_management.deserialize_session(
                    session_cookie,
                    WORKOS_COOKIE_PASSWORD,
                    max_token_age_seconds=COOKIE_MAX_AGE
                )
                request.state.user = session.user
                request.state.session = session
            except Exception as e:
                logger.warning(f"Session verification failed in middleware: {type(e).__name__}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired session"}
                )
                
        return await call_next(request)
