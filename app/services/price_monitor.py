"""Background price monitoring service."""

from __future__ import annotations

import logging
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models import PriceHistory, Product, Subscription
from app.services.parser import parse_product_url
from app.services.parser.exceptions import ParserError


logger = logging.getLogger(__name__)


class NotificationPayload(TypedDict):
    """Describe the data required to send one notification."""

    user_id: int
    product_id: int
    product_url: str
    product_title: str | None
    current_price: float
    target_price: float
    channel: str
    email: str | None
    telegram_user_id: int | None


class PriceMonitoringResult(TypedDict):
    """Describe the result of one monitoring cycle."""

    checked_products: int
    queued_notifications: int
    notifications: list[NotificationPayload]


def _resolve_notification_channel(subscription: Subscription) -> str | None:
    """Return the preferred notification channel for the subscription user."""
    if subscription.user and subscription.user.telegram_user_id is not None:
        return "telegram"

    if subscription.user and subscription.user.email:
        return "email"

    return None


async def run_price_monitoring_cycle() -> PriceMonitoringResult:
    """Run one background monitoring cycle and prepare notification payloads."""
    logger.info("event=price_monitoring_started")

    async with SessionLocal() as session:
        products = (
            await session.execute(select(Product).join(Subscription).distinct())
        ).scalars().all()

        notifications: list[NotificationPayload] = []

        for product in products:
            logger.info(
                "event=price_monitoring_product_started product_id=%s url=%s",
                product.id,
                product.url,
            )

            try:
                parsed_product = await parse_product_url(product.url)
            except ParserError:
                logger.exception(
                    "event=price_monitoring_product_failed product_id=%s url=%s",
                    product.id,
                    product.url,
                )
                continue

            old_price = product.current_price
            new_price = parsed_product.price

            product.title = parsed_product.title or product.title
            product.last_parsed_at = parsed_product.parsed_at

            if new_price is None:
                logger.warning(
                    "event=price_monitoring_product_skipped reason=missing_price product_id=%s",
                    product.id,
                )
                continue

            price_changed = old_price != new_price
            product.current_price = new_price

            if price_changed:
                session.add(
                    PriceHistory(
                        product_id=product.id,
                        price=new_price,
                        timestamp=parsed_product.parsed_at,
                    )
                )
                logger.info(
                    "event=price_monitoring_price_changed product_id=%s old_price=%s new_price=%s",
                    product.id,
                    old_price,
                    new_price,
                )
            else:
                logger.info(
                    "event=price_monitoring_price_unchanged product_id=%s current_price=%s",
                    product.id,
                    new_price,
                )

            matching_subscriptions = (
                await session.execute(
                    select(Subscription)
                    .options(selectinload(Subscription.user))
                    .where(
                        Subscription.product_id == product.id,
                        Subscription.target_price >= new_price,
                        Subscription.is_notified.is_(False),
                    )
                )
            ).scalars().all()

            for subscription in matching_subscriptions:
                channel = _resolve_notification_channel(subscription)

                if channel is None:
                    logger.warning(
                        "event=price_monitoring_notification_skipped subscription_id=%s user_id=%s reason=no_available_channel",
                        subscription.id,
                        subscription.user_id,
                    )
                    continue

                subscription.is_notified = True
                notifications.append(
                    {
                        "user_id": subscription.user_id,
                        "product_id": product.id,
                        "product_url": product.url,
                        "product_title": product.title,
                        "current_price": new_price,
                        "target_price": subscription.target_price,
                        "channel": channel,
                        "email": subscription.user.email if subscription.user else None,
                        "telegram_user_id": (
                            subscription.user.telegram_user_id
                            if subscription.user
                            else None
                        ),
                    }
                )
                logger.info(
                    "event=price_monitoring_notification_queued subscription_id=%s user_id=%s product_id=%s",
                    subscription.id,
                    subscription.user_id,
                    product.id,
                )

            subscriptions_to_reset = (
                await session.execute(
                    select(Subscription).where(
                        Subscription.product_id == product.id,
                        Subscription.target_price < new_price,
                        Subscription.is_notified.is_(True),
                    )
                )
            ).scalars().all()

            for subscription in subscriptions_to_reset:
                subscription.is_notified = False
                logger.info(
                    "event=price_monitoring_notification_reset subscription_id=%s user_id=%s product_id=%s",
                    subscription.id,
                    subscription.user_id,
                    product.id,
                )

        await session.commit()

    result: PriceMonitoringResult = {
        "checked_products": len(products),
        "queued_notifications": len(notifications),
        "notifications": notifications,
    }

    logger.info(
        "event=price_monitoring_finished checked_products=%s queued_notifications=%s",
        result["checked_products"],
        result["queued_notifications"],
    )
    return result
