from typing import Dict, Any, Optional
import time
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import psutil
from loguru import logger

from app.config import settings


class MetricsCollector:
    """Prometheus metrics collector for WebSet Miner."""
    
    def __init__(self):
        # Create custom registry to avoid conflicts
        self.registry = CollectorRegistry()
        
        # Application metrics
        self.http_requests_total = Counter(
            'websets_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'websets_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Job metrics
        self.jobs_total = Counter(
            'websets_jobs_total',
            'Total jobs processed',
            ['status'],
            registry=self.registry
        )
        
        self.job_duration = Histogram(
            'websets_job_duration_seconds',
            'Job processing duration in seconds',
            ['job_type'],
            registry=self.registry
        )
        
        self.active_jobs = Gauge(
            'websets_active_jobs',
            'Number of currently active jobs',
            registry=self.registry
        )
        
        # Crawler metrics
        self.urls_crawled_total = Counter(
            'websets_urls_crawled_total',
            'Total URLs crawled',
            ['status'],
            registry=self.registry
        )
        
        self.crawl_duration = Histogram(
            'websets_crawl_duration_seconds',
            'URL crawl duration in seconds',
            registry=self.registry
        )
        
        self.crawler_errors_total = Counter(
            'websets_crawler_errors_total',
            'Total crawler errors',
            ['error_type'],
            registry=self.registry
        )
        
        # Vector store metrics
        self.vector_operations_total = Counter(
            'websets_vector_operations_total',
            'Total vector store operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.vector_search_duration = Histogram(
            'websets_vector_search_duration_seconds',
            'Vector search duration in seconds',
            registry=self.registry
        )
        
        self.vectors_stored = Gauge(
            'websets_vectors_stored_total',
            'Total number of vectors stored',
            registry=self.registry
        )
        
        # Database metrics
        self.db_connections_active = Gauge(
            'websets_db_connections_active',
            'Number of active database connections',
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'websets_db_query_duration_seconds',
            'Database query duration in seconds',
            ['query_type'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'websets_cache_operations_total',
            'Total cache operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'websets_cache_hit_ratio',
            'Cache hit ratio',
            registry=self.registry
        )
        
        # WebSocket metrics
        self.websocket_connections_active = Gauge(
            'websets_websocket_connections_active',
            'Number of active WebSocket connections',
            registry=self.registry
        )
        
        self.websocket_messages_total = Counter(
            'websets_websocket_messages_total',
            'Total WebSocket messages sent',
            ['message_type'],
            registry=self.registry
        )
        
        # System metrics
        self.system_cpu_usage = Gauge(
            'websets_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'websets_system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self.system_memory_total = Gauge(
            'websets_system_memory_total_bytes',
            'Total system memory in bytes',
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'websets_system_disk_usage_bytes',
            'System disk usage in bytes',
            registry=self.registry
        )
        
        self.system_disk_total = Gauge(
            'websets_system_disk_total_bytes',
            'Total system disk space in bytes',
            registry=self.registry
        )
        
        # Application info
        self.app_info = Gauge(
            'websets_app_info',
            'Application information',
            ['version', 'environment'],
            registry=self.registry
        )
        
        # Set app info
        self.app_info.labels(
            version="1.0.0",
            environment=settings.environment
        ).set(1)
        
        # Start collecting system metrics
        self._start_system_metrics_collection()
    
    def _start_system_metrics_collection(self):
        """Start collecting system metrics in the background."""
        import asyncio
        
        async def collect_system_metrics():
            while True:
                try:
                    self.update_system_metrics()
                    await asyncio.sleep(30)  # Update every 30 seconds
                except Exception as e:
                    logger.error(f"Failed to collect system metrics: {e}")
                    await asyncio.sleep(5)
        
        asyncio.create_task(collect_system_metrics())
    
    def update_system_metrics(self):
        """Update system-level metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.used)
            self.system_memory_total.set(memory.total)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_disk_usage.set(disk.used)
            self.system_disk_total.set(disk.total)
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_job_started(self, job_type: str = "mining"):
        """Record job started."""
        self.jobs_total.labels(status="started").inc()
        self.active_jobs.inc()
    
    def record_job_completed(self, job_type: str = "mining", duration: float = None):
        """Record job completed."""
        self.jobs_total.labels(status="completed").inc()
        self.active_jobs.dec()
        
        if duration is not None:
            self.job_duration.labels(job_type=job_type).observe(duration)
    
    def record_job_failed(self, job_type: str = "mining", duration: float = None):
        """Record job failed."""
        self.jobs_total.labels(status="failed").inc()
        self.active_jobs.dec()
        
        if duration is not None:
            self.job_duration.labels(job_type=job_type).observe(duration)
    
    def record_url_crawled(self, status: str, duration: float = None):
        """Record URL crawl metrics."""
        self.urls_crawled_total.labels(status=status).inc()
        
        if duration is not None:
            self.crawl_duration.observe(duration)
    
    def record_crawler_error(self, error_type: str):
        """Record crawler error."""
        self.crawler_errors_total.labels(error_type=error_type).inc()
    
    def record_vector_operation(self, operation: str, status: str, duration: float = None):
        """Record vector store operation."""
        self.vector_operations_total.labels(
            operation=operation,
            status=status
        ).inc()
        
        if operation == "search" and duration is not None:
            self.vector_search_duration.observe(duration)
    
    def update_vectors_stored(self, count: int):
        """Update total vectors stored."""
        self.vectors_stored.set(count)
    
    def update_db_connections(self, active_connections: int):
        """Update active database connections."""
        self.db_connections_active.set(active_connections)
    
    def record_db_query(self, query_type: str, duration: float):
        """Record database query metrics."""
        self.db_query_duration.labels(query_type=query_type).observe(duration)
    
    def record_cache_operation(self, operation: str, status: str):
        """Record cache operation."""
        self.cache_operations_total.labels(
            operation=operation,
            status=status
        ).inc()
    
    def update_cache_hit_ratio(self, ratio: float):
        """Update cache hit ratio."""
        self.cache_hit_ratio.set(ratio)
    
    def update_websocket_connections(self, active_connections: int):
        """Update active WebSocket connections."""
        self.websocket_connections_active.set(active_connections)
    
    def record_websocket_message(self, message_type: str):
        """Record WebSocket message sent."""
        self.websocket_messages_total.labels(message_type=message_type).inc()
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return generate_latest(self.registry).decode('utf-8')
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary as JSON."""
        try:
            # This would require parsing the metrics, simplified version:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics_available": True,
                "registry_size": len(list(self.registry._collector_to_names.keys())),
                "system_info": {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent
                }
            }
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }


class MetricsMiddleware:
    """FastAPI middleware to collect HTTP metrics."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
    async def __call__(self, request, call_next):
        start_time = time.time()
        
        # Extract endpoint info
        method = request.method
        path = request.url.path
        
        # Simplify path for metrics (remove dynamic parts)
        endpoint = self._normalize_endpoint(path)
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Record metrics
            duration = time.time() - start_time
            self.metrics.record_http_request(method, endpoint, status_code, duration)
            
            return response
            
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            self.metrics.record_http_request(method, endpoint, 500, duration)
            raise
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics."""
        # Remove trailing slash
        if path.endswith('/') and path != '/':
            path = path[:-1]
        
        # Replace UUIDs and IDs with placeholders
        import re
        
        # UUID pattern
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path,
            flags=re.IGNORECASE
        )
        
        # Numeric ID pattern
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Hash pattern
        path = re.sub(r'/[0-9a-f]{32}', '/{hash}', path)
        
        return path


# Global metrics collector instance
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector