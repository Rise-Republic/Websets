from fastapi import APIRouter
from .auth import router as auth_router
from .jobs import router as jobs_router
from .datasets import router as datasets_router
from .health import router as health_router
from .websockets import router as websockets_router
from .gdpr import router as gdpr_router

v1_router = APIRouter(prefix="/v1")

# Include all v1 routers
v1_router.include_router(auth_router)
v1_router.include_router(jobs_router)
v1_router.include_router(datasets_router)
v1_router.include_router(health_router)
v1_router.include_router(websockets_router)
v1_router.include_router(gdpr_router)

__all__ = ["v1_router"]