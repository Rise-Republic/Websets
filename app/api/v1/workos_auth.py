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

# Initialize WorkOS client
workos_client = WorkOSClient(
    api_key=os.getenv("WORKOS_API_KEY"),
    client_id=os.getenv("WORKOS_CLIENT_ID")
)

# Get session password from environment (in production, from Vault)
WORKOS_COOKIE_PASSWORD = os.getenv("WORKOS_COOKIE_PASSWORD", "yvHkj2U4tkv+oYGZon1EDfQVtbb4ro9cabdEAV9YH9A=")

# Session cookie security
session_cookie = APIKeyCookie(name=COOKIE_NAME, auto_error=False)

# Session validation dependency
async def require_session(request: Request, session_cookie: str = Depends(session_cookie)):
    """
    Validate user session from encrypted cookie
    Raises 401 if session is invalid or missing
    """
    if not session_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        # Deserialize and verify session
        session = workos_client.user_management.deserialize_session(
            session_cookie,
            WORKOS_COOKIE_PASSWORD,
            max_token_age_seconds=COOKIE_MAX_AGE
        )
        
        # Store user in request state for route handlers
        request.state.user = session.user
        request.state.session = session
        return session
        
    except Exception as e:
        logger.warning(f"Session verification failed: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

@router.get("/login")
async def initiate_login(request: Request):
    """
    Redirect users to WorkOS AuthKit for authentication
    Implements PKCE flow with state parameter for security
    """
    try:
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Generate WorkOS authorization URL with state
        authorization_url = workos_client.user_management.get_authorization_url(
            provider="authkit",
            redirect_uri=os.getenv("WORKOS_REDIRECT_URI", "http://localhost:8001/api/auth/callback"),
            state=state
        )
        
        # Create response with state cookie for verification
        response = RedirectResponse(url=authorization_url)
        response.set_cookie(
            "workos_state",
            state,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=STATE_MAX_AGE,
            path="/api/auth"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to initiate login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate login: {str(e)}")

@router.get("/callback")
async def auth_callback(
    request: Request, 
    response: Response,
    code: Optional[str] = None,
    state: Optional[str] = None
):
    """
    Handle WorkOS callback after user authentication
    Implements secure session with encrypted cookies
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")
    
    # Verify state parameter to prevent CSRF
    expected_state = request.cookies.get("workos_state")
    if not state or not expected_state or state != expected_state:
        logger.warning("State parameter mismatch or missing")
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        # Exchange code for user profile with state verification and expiration
        profile = workos_client.user_management.authenticate_with_code(
            code=code,
            expected_state=state,
            max_age=STATE_MAX_AGE
        )
        
        # Create encrypted session cookie
        encrypted_session = workos_client.user_management.serialize_session(
            profile, 
            WORKOS_COOKIE_PASSWORD
        )
        
        # Clear state cookie
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.delete_cookie("workos_state", path="/api/auth")
        
        # Set secure session cookie
        response.set_cookie(
            COOKIE_NAME,
            encrypted_session,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=COOKIE_MAX_AGE,
            path="/"
        )
        
        # Log successful authentication (without PII)
        logger.info(f"User authenticated: {profile.user.id}")
        
        return response
        
    except AuthenticationException as e:
        logger.warning(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.post("/logout")
async def logout(request: Request, session: Dict = Depends(require_session)):
    """
    Handle user logout by clearing session cookie
    """
    try:
        # Log logout event
        logger.info(f"User logged out: {session.user.id}")
        
        # Clear session cookie
        response = JSONResponse(content={"message": "Logged out successfully"})
        response.delete_cookie(COOKIE_NAME, path="/")
        
        return response
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

# Example protected route
@router.get("/me")
async def get_current_user(session: Dict = Depends(require_session)):
    """
    Example protected route that requires authentication
    Returns the current authenticated user
    """
    return {
        "user": {
            "id": session.user.id,
            "email": session.user.email,
            "first_name": session.user.first_name,
            "last_name": session.user.last_name,
            "is_mfa_verified": session.is_mfa_verified
        }
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
