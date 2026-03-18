"""
Celery configuration for background tasks.
"""
from celery import Celery

from app.config import settings

# Create Celery app
celery_app = Celery(
    "whatsapp_bot",
    broker=str(settings.CELERY_BROKER_URL),
    backend=str(settings.CELERY_RESULT_BACKEND),
    include=["reminders.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30,
    worker_prefetch_multiplier=1,
    worker_concurrency=settings.CELERY_WORKERS,
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "reminders.tasks.cleanup_expired_sessions",
            "schedule": 3600,  # Every hour
        },
        "reset-daily-limits": {
            "task": "reminders.tasks.reset_daily_limits",
            "schedule": 86400,  # Every day
        },
    },
)
