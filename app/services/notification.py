"""Notification delivery services."""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path
from string import Template
from typing import Any

import httpx

from app.core import settings


logger = logging.getLogger(__name__)

EMAIL_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "emails" / "price_drop.html"


class NotificationDeliveryError(RuntimeError):
    """Raised when a notification cannot be delivered."""


async def deliver_notification(payload: dict[str, Any]) -> str:
    """Dispatch a notification payload to the channel-specific sender."""
    logger.info(
        "event=notification_delivery_started user_id=%s product_id=%s channel=%s",
        payload.get("user_id"),
        payload.get("product_id"),
        payload.get("channel"),
    )

    channel = payload.get("channel")

    if channel == "telegram":
        result = await _send_telegram_notification(payload)
    elif channel == "email":
        result = await _send_email_notification(payload)
    else:
        raise NotificationDeliveryError(f"Unsupported notification channel: {channel}")

    logger.info(
        "event=notification_delivery_finished user_id=%s product_id=%s channel=%s result=%s",
        payload.get("user_id"),
        payload.get("product_id"),
        channel,
        result,
    )
    return result


async def _send_telegram_notification(payload: dict[str, Any]) -> str:
    """Send a Telegram message directly through the Telegram Bot API."""
    chat_id = payload.get("telegram_user_id")
    bot_token = settings.TELEGRAM_BOT_TOKEN

    if not bot_token:
        raise NotificationDeliveryError("TELEGRAM_BOT_TOKEN is not configured")

    if chat_id is None:
        raise NotificationDeliveryError("telegram_user_id is required for Telegram delivery")

    message_text = _build_telegram_message(payload)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message_text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
        )

    if response.is_error:
        raise NotificationDeliveryError(
            f"Telegram delivery failed with status {response.status_code}: {response.text}"
        )

    return "telegram_sent"


async def _send_email_notification(payload: dict[str, Any]) -> str:
    """Send an HTML email notification through SMTP."""
    recipient_email = payload.get("email")

    if not recipient_email:
        raise NotificationDeliveryError("email is required for email delivery")

    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD or not settings.SMTP_FROM_EMAIL:
        raise NotificationDeliveryError(
            "SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL must be configured for email delivery"
        )

    subject = _build_email_subject(payload)
    html_body = _render_price_drop_email(payload)
    text_body = _build_plain_text_email(payload)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = recipient_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    await asyncio.to_thread(_send_email_via_smtp, message)
    return "email_sent"


def _send_email_via_smtp(message: EmailMessage) -> None:
    """Send one message through the configured SMTP server."""
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as smtp:
        if settings.SMTP_USE_STARTTLS:
            smtp.starttls()

        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def _build_telegram_message(payload: dict[str, Any]) -> str:
    """Build the Telegram notification body."""
    product_title = payload.get("product_title") or "Tracked product"
    product_url = payload.get("product_url")
    current_price = payload.get("current_price")
    target_price = payload.get("target_price")

    return (
        "<b>Price target reached</b>\n\n"
        f"<b>Product:</b> {product_title}\n"
        f"<b>Current price:</b> {current_price}\n"
        f"<b>Your target:</b> {target_price}\n"
        f"<b>Link:</b> {product_url}"
    )


def _build_email_subject(payload: dict[str, Any]) -> str:
    """Build the subject line for the price drop email."""
    product_title = payload.get("product_title") or "Tracked product"
    return f"Price alert: {product_title}"


def _build_plain_text_email(payload: dict[str, Any]) -> str:
    """Build the plain-text fallback body for the price drop email."""
    product_title = payload.get("product_title") or "Tracked product"
    product_url = payload.get("product_url")
    current_price = payload.get("current_price")
    target_price = payload.get("target_price")

    return (
        "Price target reached\n\n"
        f"Product: {product_title}\n"
        f"Current price: {current_price}\n"
        f"Your target: {target_price}\n"
        f"Open product: {product_url}\n"
    )


def _render_price_drop_email(payload: dict[str, Any]) -> str:
    """Render the HTML email template for the price drop notification."""
    template = Template(EMAIL_TEMPLATE_PATH.read_text(encoding="utf-8"))
    product_title = payload.get("product_title") or "Tracked product"

    return template.safe_substitute(
        product_title=product_title,
        product_url=payload.get("product_url"),
        current_price=payload.get("current_price"),
        target_price=payload.get("target_price"),
        app_name=settings.PROJECT_NAME,
    )
