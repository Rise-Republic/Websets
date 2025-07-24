from .auth import router as auth_router
from .jobs import router as jobs_router
from .datasets import router as datasets_router
from .health import router as health_router
from .gdpr import router as gdpr_router
from .users import router as users_router

__all__ = [
    "auth_router",
    "jobs_router", 
    "datasets_router",
    "health_router",
    "gdpr_router",
    "users_router",
]
