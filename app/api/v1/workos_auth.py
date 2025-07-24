"""
WorkOS AuthKit integration for Websets authentication
Replaces the broken Redis/JWT system with enterprise-grade auth
"""
import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from workos import WorkOSClient
from typing import Optional

router = APIRouter(prefix="/auth", tags=["workos-auth"])

# Initialize WorkOS client
workos_client = WorkOSClient(
    api_key=os.getenv("WORKOS_API_KEY"),
    client_id=os.getenv("WORKOS_CLIENT_ID")
)

@router.get("/login")
async def initiate_login(request: Request):
    """
    Redirect users to WorkOS AuthKit for authentication
    Replaces the broken FastAPI login endpoint
    """
    try:
        # Generate WorkOS authorization URL
        authorization_url = workos_client.user_management.get_authorization_url(
            provider="authkit",
            redirect_uri=os.getenv("WORKOS_REDIRECT_URI", "http://127.0.0.1:5173/callback"),
            client_id=os.getenv("WORKOS_CLIENT_ID")
        )
        
        # Redirect user to WorkOS AuthKit
        return RedirectResponse(url=authorization_url)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate login: {str(e)}")

@router.get("/callback")
async def auth_callback(request: Request, code: Optional[str] = None):
    """
    Handle WorkOS callback after user authentication
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")
    
    try:
        # Exchange code for user profile
        profile = workos_client.user_management.authenticate_with_code(
            code=code,
            client_id=os.getenv("WORKOS_CLIENT_ID")
        )
        
        # TODO: Create session, store user data, redirect to dashboard
        # For now, just return user info
        return {
            "user": {
                "id": profile.user.id,
                "email": profile.user.email,
                "first_name": profile.user.first_name,
                "last_name": profile.user.last_name
            },
            "access_token": profile.access_token,
            "refresh_token": profile.refresh_token
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.post("/logout")
async def logout(request: Request):
    """
    Handle user logout
    """
    # TODO: Implement session cleanup
    return {"message": "Logged out successfully"}
