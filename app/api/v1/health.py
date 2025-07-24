from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
from datetime import datetime

from app.database import get_db
from app.config import settings

from app.monitoring import get_health_monitor, get_metrics_collector

router = APIRouter(prefix="/health", tags=["v1-health"])


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "webset-miner"
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check using the health monitor."""
    health_monitor = get_health_monitor()
    latest_health = health_monitor.get_latest_health()
    
    if not latest_health:
        # Trigger an immediate health check if none available
        latest_health = await health_monitor.perform_health_check()
    
    # Convert to API format
    components = {}
    for name, component in latest_health.components.items():
        components[name] = {
            "status": component.status.value,
            "response_time_ms": component.response_time_ms,
            "last_check": component.last_check.isoformat(),
            "error": component.error,
            "metadata": component.metadata
        }
    
    return {
        "status": latest_health.overall_status.value,
        "timestamp": latest_health.timestamp.isoformat(),
        "service": "webset-miner",
        "components": components,
        "system_metrics": latest_health.system_metrics
    }


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


@router.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus metrics endpoint."""
    from fastapi import Response
    
    metrics_collector = get_metrics_collector()
    metrics_data = metrics_collector.get_metrics()
    
    return Response(
        content=metrics_data,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get metrics summary as JSON."""
    metrics_collector = get_metrics_collector()
    return metrics_collector.get_metrics_summary()


@router.get("/history")
async def get_health_history(limit: int = 10):
    """Get health check history."""
    health_monitor = get_health_monitor()
    history = health_monitor.get_health_history(limit)
    
    # Convert to API format
    history_data = []
    for health in history:
        components = {}
        for name, component in health.components.items():
            components[name] = {
                "status": component.status.value,
                "response_time_ms": component.response_time_ms,
                "error": component.error
            }
        
        history_data.append({
            "timestamp": health.timestamp.isoformat(),
            "status": health.overall_status.value,
            "components": components
        })
    
    return {"history": history_data}


@router.get("/component/{component_name}")
async def get_component_health(component_name: str):
    """Get health for a specific component."""
    health_monitor = get_health_monitor()
    component = health_monitor.get_component_health(component_name)
    
    if not component:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component '{component_name}' not found"
        )
    
    return {
        "name": component.name,
        "status": component.status.value,
        "response_time_ms": component.response_time_ms,
        "last_check": component.last_check.isoformat(),
        "error": component.error,
        "metadata": component.metadata
    }
