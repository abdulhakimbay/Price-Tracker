"""Celery task definitions."""

from __future__ import annotations

import logging
from typing import Any

from app.services.notification import deliver_notification
from app.services.price_monitor import NotificationPayload, run_price_monitoring_cycle
from app.worker.async_runner import async_task_runner
from app.worker.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.worker.tasks.run_price_monitoring_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_price_monitoring_task(self: Any) -> dict[str, int]:
    """Run one monitoring cycle and enqueue notification delivery tasks."""
    logger.info("event=celery_price_monitoring_started task_id=%s", self.request.id)

    result = async_task_runner.run(run_price_monitoring_cycle())
    notifications: list[NotificationPayload] = result.get("notifications", [])

    for payload in notifications:
        send_notification_task.delay(dict(payload))

    logger.info(
        "event=celery_price_monitoring_finished task_id=%s checked_products=%s queued_notifications=%s",
        self.request.id,
        result.get("checked_products", 0),
        len(notifications),
    )
    return {
        "checked_products": int(result.get("checked_products", 0)),
        "queued_notifications": len(notifications),
    }


@celery_app.task(
    bind=True,
    name="app.worker.tasks.send_notification_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_notification_task(self: Any, payload: dict[str, Any]) -> str:
    """Deliver one notification payload through the configured channel."""
    logger.info(
        "event=celery_notification_started task_id=%s user_id=%s product_id=%s",
        self.request.id,
        payload.get("user_id"),
        payload.get("product_id"),
    )

    result = async_task_runner.run(deliver_notification(payload))

    logger.info(
        "event=celery_notification_finished task_id=%s user_id=%s product_id=%s result=%s",
        self.request.id,
        payload.get("user_id"),
        payload.get("product_id"),
        result,
    )
    return result
