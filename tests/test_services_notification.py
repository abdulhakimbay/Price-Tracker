"""Unit tests for the notification delivery service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.notification import NotificationDeliveryError, deliver_notification

# ---------------------------------------------------------------------------
# Shared payload builders
# ---------------------------------------------------------------------------

def _telegram_payload(**kwargs) -> dict:
    return {
        "channel": "telegram",
        "user_id": 1,
        "product_id": 1,
        "product_title": "Cool Sneakers",
        "product_url": "https://shop.example.com/sneakers",
        "current_price": 49.99,
        "target_price": 60.0,
        "telegram_user_id": 123456789,
        "email": None,
        **kwargs,
    }


def _email_payload(**kwargs) -> dict:
    return {
        "channel": "email",
        "user_id": 1,
        "product_id": 1,
        "product_title": "Cool Sneakers",
        "product_url": "https://shop.example.com/sneakers",
        "current_price": 49.99,
        "target_price": 60.0,
        "telegram_user_id": None,
        "email": "user@example.com",
        **kwargs,
    }


# ---------------------------------------------------------------------------
# Telegram channel
# ---------------------------------------------------------------------------

async def test_deliver_telegram_success(httpx_mock):
    """Successful Telegram delivery must return 'telegram_sent'."""
    httpx_mock.add_response(method="POST", status_code=200, json={"ok": True})
    result = await deliver_notification(_telegram_payload())
    assert result == "telegram_sent"


async def test_deliver_telegram_api_error(httpx_mock):
    """4xx response from Telegram API must raise NotificationDeliveryError."""
    httpx_mock.add_response(method="POST", status_code=400, json={"ok": False})
    with pytest.raises(NotificationDeliveryError, match="Telegram delivery failed"):
        await deliver_notification(_telegram_payload())


async def test_deliver_telegram_missing_chat_id():
    """Missing telegram_user_id must raise NotificationDeliveryError immediately."""
    with pytest.raises(NotificationDeliveryError, match="telegram_user_id is required"):
        await deliver_notification(_telegram_payload(telegram_user_id=None))


async def test_deliver_telegram_missing_token():
    """Empty TELEGRAM_BOT_TOKEN must raise NotificationDeliveryError."""
    with patch("app.services.notification.settings") as mock_settings:
        mock_settings.TELEGRAM_BOT_TOKEN = ""
        with pytest.raises(NotificationDeliveryError, match="TELEGRAM_BOT_TOKEN"):
            await deliver_notification(_telegram_payload())


# ---------------------------------------------------------------------------
# Email channel
# ---------------------------------------------------------------------------

async def test_deliver_email_success():
    """Successful email delivery must return 'email_sent'."""
    with patch("app.services.notification.smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_instance = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = await deliver_notification(_email_payload())

    assert result == "email_sent"
    mock_smtp_instance.send_message.assert_called_once()


async def test_deliver_email_missing_credentials():
    """Missing SMTP credentials must raise NotificationDeliveryError."""
    with patch("app.services.notification.settings") as mock_settings:
        mock_settings.SMTP_USERNAME = ""
        mock_settings.SMTP_PASSWORD = ""
        mock_settings.SMTP_FROM_EMAIL = ""
        with pytest.raises(NotificationDeliveryError, match="SMTP"):
            await deliver_notification(_email_payload())


async def test_deliver_email_missing_recipient():
    """Missing email address must raise NotificationDeliveryError."""
    with pytest.raises(NotificationDeliveryError, match="email is required"):
        await deliver_notification(_email_payload(email=None))


# ---------------------------------------------------------------------------
# Unknown channel
# ---------------------------------------------------------------------------

async def test_deliver_unknown_channel():
    """Unsupported channel must raise NotificationDeliveryError."""
    payload = _telegram_payload()
    payload["channel"] = "sms"
    with pytest.raises(NotificationDeliveryError, match="Unsupported"):
        await deliver_notification(payload)
