from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
from datetime import datetime

from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "webset-miner"
    }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check including dependencies."""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "webset-miner",
        "components": {}
    }
    
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check Redis connection
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        health_status["components"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check Celery workers (basic check)
    try:
        from app.tasks.celery_app import celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            health_status["components"]["celery"] = {
                "status": "healthy",
                "active_workers": len(stats)
            }
        else:
            health_status["components"]["celery"] = {
                "status": "unhealthy",
                "error": "No active workers"
            }
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["celery"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check for Kubernetes."""
    
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        # Test Redis connection
        r = redis.from_url(settings.redis_url)
        r.ping()
        
        return {"status": "ready"}
        
    except Exception as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/liveness")
async def liveness_check():
    """Liveness check for Kubernetes."""
    return {"status": "alive"}