from celery import Celery
from app.config import settings
from opentelemetry.instrumentation.celery import CeleryInstrumentor

# Create Celery app
celery_app = Celery(
    "webset_miner",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.mining_tasks",
        "app.tasks.secret_rotation",
    ],
)

if settings.enable_tracing:
    CeleryInstrumentor().instrument()

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Optional: Configure periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-jobs": {
        "task": "app.tasks.mining_tasks.cleanup_old_jobs",
        "schedule": 3600.0,  # Run every hour
    },
    "rotate-minio-creds": {
        "task": "app.tasks.secret_rotation.rotate_minio_credentials",
        "schedule": 24 * 3600,  # Daily
    },
    "rotate-minio-root-creds": {
        "task": "app.tasks.secret_rotation.rotate_minio_root_credentials",
        "schedule": 7 * 24 * 3600,  # Weekly
    },
}
