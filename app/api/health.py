from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
from datetime import datetime
import psutil
import asyncio
from typing import Dict, Any

from app.database import get_db
from app.config import settings
from app.storage import get_vector_store
from app.storage.object_storage import get_object_storage
from app.monitoring.metrics import MetricsCollector
from app.tasks.celery_app import celery_app
from app.middleware import limiter, RateLimits

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
@limiter.limit(RateLimits.PUBLIC)
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "webset-miner",
        "version": "1.0.0"
    }


@router.get("/detailed")
@limiter.limit(RateLimits.PUBLIC)
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check including dependencies."""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "webset-miner",
        "version": "1.0.0",
        "uptime": get_uptime(),
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
    
    # Check vector store
    try:
        vector_store = get_vector_store()
        stats = asyncio.run(vector_store.get_statistics())
        health_status["components"]["vector_store"] = {
            "status": "healthy",
            "provider": stats.get("provider", "unknown"),
            "total_vectors": stats.get("total_vectors", 0)
        }
    except Exception as e:
        health_status["components"]["vector_store"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check object storage
    try:
        storage = get_object_storage()
        # Try to list files to verify connectivity
        files = asyncio.run(storage.list_files(prefix="health_check"))
        health_status["components"]["object_storage"] = {
            "status": "healthy",
            "provider": settings.object_storage_provider,
            "accessible": True
        }
    except Exception as e:
        health_status["components"]["object_storage"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check Celery workers
    try:
        inspector = celery_app.control.inspect()
        active_workers = inspector.active()
        scheduled_tasks = inspector.scheduled()
        
        if active_workers:
            health_status["components"]["celery"] = {
                "status": "healthy",
                "active_workers": len(active_workers),
                "scheduled_tasks": len(scheduled_tasks) if scheduled_tasks else 0
            }
        else:
            health_status["components"]["celery"] = {
                "status": "unhealthy",
                "error": "No active workers found"
            }
            health_status["status"] = "unhealthy"
            
    except Exception as e:
        health_status["components"]["celery"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/metrics")
@limiter.limit(RateLimits.PUBLIC)
async def get_metrics():
    """Prometheus metrics endpoint."""
    from app.monitoring.metrics import get_metrics_collector
    metrics_collector = get_metrics_collector()
    return metrics_collector.get_metrics()


@router.get("/system")
@limiter.limit(RateLimits.PUBLIC)
async def system_health():
    """System resource monitoring."""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Network stats
        network = psutil.net_io_counters()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "cores": psutil.cpu_count()
                },
                "memory": {
                    "total_bytes": memory.total,
                    "used_bytes": memory.used,
                    "available_bytes": memory.available,
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total_bytes": disk.total,
                    "used_bytes": disk.used,
                    "free_bytes": disk.free,
                    "usage_percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_received": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_received": network.packets_recv
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/ready")
@limiter.limit(RateLimits.PUBLIC)
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe."""
    try:
        # Check critical dependencies
        checks = []
        
        # Database
        db.execute(text("SELECT 1"))
        checks.append("database")
        
        # Redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        checks.append("redis")
        
        # Vector store
        vector_store = get_vector_store()
        asyncio.run(vector_store.get_statistics())
        checks.append("vector_store")
        
        return {
            "status": "ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, 503


@router.get("/live")
@limiter.limit(RateLimits.PUBLIC)
async def liveness_check():
    """Kubernetes liveness probe."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


def get_uptime() -> str:
    """Get system uptime."""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return f"{days}d {hours}h {minutes}m"
        
    except:
        return "unknown"
