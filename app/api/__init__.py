from .v1.auth import router as auth_router
from .v1.jobs import router as jobs_router
from .v1.datasets import router as datasets_router
from .v1.health import router as health_router
from .gdpr import router as gdpr_router
from .v1.users import router as users_router

__all__ = [
    "auth_router",
    "jobs_router", 
    "datasets_router",
    "health_router",
    "gdpr_router",
    "users_router",
]
