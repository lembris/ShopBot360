from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "shopbot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Dar_es_Salaam",
    enable_utc=True,
    beat_schedule={
        "daily-report": {
            "task": "app.workers.report_worker.send_daily_reports",
            "schedule": crontab(hour=20, minute=0),
        },
        "low-stock-check": {
            "task": "app.workers.low_stock_worker.check_low_stock",
            "schedule": crontab(hour="*/6"),
        },
        "cleanup-sessions": {
            "task": "app.workers.cleanup_worker.cleanup_stale_sessions",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)
celery_app.autodiscover_tasks(["app.workers"])
