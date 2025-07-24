from typing import Dict, Any, List, Optional
import asyncio
import psutil
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis
from sqlalchemy import text
from loguru import logger

from app.config import settings
from app.database import SessionLocal


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    response_time_ms: float
    last_check: datetime
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealth:
    overall_status: HealthStatus
    components: Dict[str, ComponentHealth]
    system_metrics: Dict[str, Any]
    timestamp: datetime


class SystemHealthMonitor:
    """Comprehensive system health monitoring."""
    
    def __init__(self):
        self.component_checks = {}
        self.health_history: List[SystemHealth] = []
        self.max_history_size = 100
        self.check_interval = 30  # seconds
        self.monitoring_task = None
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start background health monitoring."""
        async def monitor_loop():
            while True:
                try:
                    await self.perform_health_check()
                    await asyncio.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    await asyncio.sleep(5)  # Short retry delay
        
        self.monitoring_task = asyncio.create_task(monitor_loop())
    
    async def check_database_health(self) -> ComponentHealth:
        """Check database connectivity and performance."""
        start_time = time.time()
        
        try:
            db = SessionLocal()
            try:
                # Simple connectivity test
                db.execute(text("SELECT 1"))
                
                # Performance test
                result = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
                
                response_time = (time.time() - start_time) * 1000
                
                # Get database stats
                metadata = {
                    "user_count": result,
                    "connection_pool_size": db.bind.pool.size() if hasattr(db.bind, 'pool') else None
                }
                
                status = HealthStatus.HEALTHY if response_time < 1000 else HealthStatus.DEGRADED
                
                return ComponentHealth(
                    name="database",
                    status=status,
                    response_time_ms=response_time,
                    last_check=datetime.utcnow(),
                    metadata=metadata
                )
                
            finally:
                db.close()
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error=str(e)
            )
    
    async def check_redis_health(self) -> ComponentHealth:
        """Check Redis connectivity and performance."""
        start_time = time.time()
        
        try:
            r = redis.from_url(settings.redis_url)
            
            # Connectivity test
            r.ping()
            
            # Performance test
            test_key = "health_check_test"
            r.set(test_key, "test_value", ex=10)  # Expires in 10 seconds
            value = r.get(test_key)
            r.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            # Get Redis info
            info = r.info()
            metadata = {
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "ops_per_sec": info.get("instantaneous_ops_per_sec")
            }
            
            status = HealthStatus.HEALTHY if response_time < 500 else HealthStatus.DEGRADED
            
            return ComponentHealth(
                name="redis",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                metadata=metadata
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error=str(e)
            )
    
    async def check_celery_health(self) -> ComponentHealth:
        """Check Celery worker health."""
        start_time = time.time()
        
        try:
            from app.tasks.celery_app import celery_app
            
            # Get worker stats
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            active_tasks = inspect.active()
            
            response_time = (time.time() - start_time) * 1000
            
            if stats:
                active_workers = len(stats)
                total_active_tasks = sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0
                
                metadata = {
                    "active_workers": active_workers,
                    "active_tasks": total_active_tasks,
                    "worker_stats": stats
                }
                
                status = HealthStatus.HEALTHY if active_workers > 0 else HealthStatus.DEGRADED
            else:
                metadata = {"active_workers": 0}
                status = HealthStatus.UNHEALTHY
            
            return ComponentHealth(
                name="celery",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                metadata=metadata
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="celery",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error=str(e)
            )
    
    async def check_vector_store_health(self) -> ComponentHealth:
        """Check vector store health."""
        start_time = time.time()
        
        try:
            from app.storage.distributed_vector_store import get_vector_store
            
            vector_store = get_vector_store()
            stats = await vector_store.get_statistics()
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine health based on response time and provider
            status = HealthStatus.HEALTHY if response_time < 2000 else HealthStatus.DEGRADED
            
            return ComponentHealth(
                name="vector_store",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                metadata=stats
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="vector_store",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error=str(e)
            )
    
    async def check_object_storage_health(self) -> ComponentHealth:
        """Check object storage health."""
        start_time = time.time()
        
        try:
            from app.storage.object_storage import get_object_storage
            
            storage = get_object_storage()
            
            # Test upload and delete a small file
            test_key = f"health_check_{datetime.utcnow().timestamp()}"
            test_data = b"health check test"
            
            # Upload test
            url = await storage.upload_bytes(test_data, test_key, "text/plain")
            
            # List test (to verify the file exists)
            files = await storage.list_files(test_key)
            
            # Cleanup test
            await storage.delete_file(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY if response_time < 3000 else HealthStatus.DEGRADED
            
            return ComponentHealth(
                name="object_storage",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                metadata={
                    "provider": settings.object_storage_provider,
                    "test_upload_success": bool(url),
                    "test_list_success": len(files) >= 0
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="object_storage",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error=str(e)
            )
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics (basic)
            network = psutil.net_io_counters()
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                "memory": {
                    "total_bytes": memory.total,
                    "available_bytes": memory.available,
                    "used_bytes": memory.used,
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
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}
    
    async def perform_health_check(self) -> SystemHealth:
        """Perform comprehensive health check."""
        logger.debug("Performing health check...")
        
        # Run all component checks concurrently
        checks = await asyncio.gather(
            self.check_database_health(),
            self.check_redis_health(),
            self.check_celery_health(),
            self.check_vector_store_health(),
            self.check_object_storage_health(),
            return_exceptions=True
        )
        
        # Process results
        components = {}
        for check in checks:
            if isinstance(check, ComponentHealth):
                components[check.name] = check
            elif isinstance(check, Exception):
                logger.error(f"Health check failed: {check}")
        
        # Determine overall health status
        if not components:
            overall_status = HealthStatus.UNHEALTHY
        elif any(comp.status == HealthStatus.UNHEALTHY for comp in components.values()):
            overall_status = HealthStatus.UNHEALTHY
        elif any(comp.status == HealthStatus.DEGRADED for comp in components.values()):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Get system metrics
        system_metrics = self.get_system_metrics()
        
        # Create health report
        health = SystemHealth(
            overall_status=overall_status,
            components=components,
            system_metrics=system_metrics,
            timestamp=datetime.utcnow()
        )
        
        # Store in history
        self.health_history.append(health)
        if len(self.health_history) > self.max_history_size:
            self.health_history.pop(0)
        
        return health
    
    def get_latest_health(self) -> Optional[SystemHealth]:
        """Get the latest health check result."""
        return self.health_history[-1] if self.health_history else None
    
    def get_health_history(self, limit: int = 10) -> List[SystemHealth]:
        """Get recent health check history."""
        return self.health_history[-limit:]
    
    def get_component_health(self, component_name: str) -> Optional[ComponentHealth]:
        """Get health for a specific component."""
        latest = self.get_latest_health()
        return latest.components.get(component_name) if latest else None
    
    async def stop_monitoring(self):
        """Stop background health monitoring."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass


# Global health monitor instance
_health_monitor = None

def get_health_monitor() -> SystemHealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = SystemHealthMonitor()
    return _health_monitor
