from enum import Enum
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel


class APIVersion(str, Enum):
    V1 = "v1"
    # Future versions can be added here
    # V2 = "v2"


class VersionInfo(BaseModel):
    version: str
    status: str
    deprecated: bool = False
    sunset_date: str = None
    description: str


class APIVersionManager:
    """Manages API versions and compatibility."""
    
    def __init__(self):
        self.versions: Dict[APIVersion, VersionInfo] = {
            APIVersion.V1: VersionInfo(
                version="1.0.0",
                status="stable",
                deprecated=False,
                description="Initial API version with full WebSet mining functionality"
            )
        }
        self.current_version = APIVersion.V1
        self.default_version = APIVersion.V1
    
    def get_version_from_request(self, request: Request) -> APIVersion:
        """Extract API version from request path or headers."""
        # Check URL path first (/v1/, /v2/, etc.)
        path = request.url.path
        if "/v1/" in path:
            return APIVersion.V1
        
        # Check Accept header for version preference
        accept_header = request.headers.get("Accept", "")
        if "application/vnd.websetminer.v1+json" in accept_header:
            return APIVersion.V1
        
        # Check custom version header
        version_header = request.headers.get("API-Version", "")
        if version_header:
            try:
                return APIVersion(version_header.lower())
            except ValueError:
                pass
        
        # Default to current version
        return self.default_version
    
    def get_version_info(self, version: APIVersion) -> VersionInfo:
        """Get information about a specific API version."""
        return self.versions.get(version)
    
    def is_version_supported(self, version: APIVersion) -> bool:
        """Check if an API version is supported."""
        return version in self.versions
    
    def add_version_headers(self, response, version: APIVersion):
        """Add version-related headers to response."""
        version_info = self.get_version_info(version)
        if version_info:
            response.headers["API-Version"] = version.value
            response.headers["API-Version-Status"] = version_info.status
            if version_info.deprecated:
                response.headers["API-Deprecated"] = "true"
                if version_info.sunset_date:
                    response.headers["Sunset"] = version_info.sunset_date


# Global version manager instance
version_manager = APIVersionManager()


# Version info endpoint
versioning_router = APIRouter(prefix="/api", tags=["versioning"])


@versioning_router.get("/version")
async def get_api_version(request: Request):
    """Get current API version information."""
    version = version_manager.get_version_from_request(request)
    version_info = version_manager.get_version_info(version)
    
    return {
        "current_version": version.value,
        "version_info": version_info.dict(),
        "supported_versions": [v.value for v in version_manager.versions.keys()],
        "default_version": version_manager.default_version.value
    }


@versioning_router.get("/versions")
async def list_api_versions():
    """List all available API versions."""
    return {
        "versions": {
            version.value: info.dict() 
            for version, info in version_manager.versions.items()
        },
        "current_version": version_manager.current_version.value,
        "default_version": version_manager.default_version.value
    }


def require_version(required_version: APIVersion):
    """Decorator to require a specific API version."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            version = version_manager.get_version_from_request(request)
            if version != required_version:
                raise HTTPException(
                    status_code=400,
                    detail=f"This endpoint requires API version {required_version.value}"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
