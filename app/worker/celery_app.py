"""Celery application configuration."""

from __future__ import annotations

import logging

from celery import Celery

from app.core import configure_logging, settings


configure_logging()
logger = logging.getLogger(__name__)


celery_app = Celery(
    "price_tracker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_default_queue=settings.CELERY_TASK_QUEUE,
    worker_hijack_root_logger=False,
    beat_schedule={
        "run-price-monitoring-cycle": {
            "task": "app.worker.tasks.run_price_monitoring_task",
            "schedule": settings.CELERY_PRICE_CHECK_INTERVAL_SECONDS,
        },
    },
)

logger.info(
    "event=celery_configured broker=%s default_queue=%s schedule_seconds=%s",
    settings.CELERY_BROKER_URL,
    settings.CELERY_TASK_QUEUE,
    settings.CELERY_PRICE_CHECK_INTERVAL_SECONDS,
)
