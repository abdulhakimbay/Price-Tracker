"""Integration tests for the price monitoring service.

These tests patch `SessionLocal` in the price_monitor module so the
monitoring cycle runs against the in-memory SQLite database instead of
the production PostgreSQL instance.
"""

from __future__ import annotations

import datetime
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import app.services.price_monitor as pm_module
from app.models import PriceHistory, Product, Subscription, User
from app.services.price_monitor import run_price_monitoring_cycle
from app.services.parser.demo import DemoParser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _demo_price(url: str) -> float:
    """Return the deterministic price that DemoParser will produce for url."""
    result = await DemoParser().parse(url)
    return result.price


async def _setup_product_with_subscription(
    session: AsyncSession,
    *,
    url: str,
    current_price: float | None,
    target_price: float,
    is_notified: bool = False,
    has_telegram: bool = False,
) -> tuple[Product, Subscription]:
    """Persist a product + user + subscription and commit."""
    user = User(
        email=f"monitor_{url[-6:]}@example.com" if not has_telegram else None,
        hashed_password="x" if not has_telegram else None,
        telegram_user_id=999001 if has_telegram else None,
    )
    session.add(user)
    await session.flush()

    product = Product(url=url, current_price=current_price, title="Test")
    session.add(product)
    await session.flush()

    sub = Subscription(
        user_id=user.id,
        product_id=product.id,
        target_price=target_price,
        is_notified=is_notified,
    )
    session.add(sub)
    await session.commit()
    return product, sub


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def patched_session(session_factory, monkeypatch):
    """Patch SessionLocal used by price_monitor to use the test engine."""
    monkeypatch.setattr(pm_module, "SessionLocal", session_factory)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_no_products_no_notifications(patched_session):
    """Empty database must produce zero checked products and notifications."""
    result = await run_price_monitoring_cycle()
    assert result["checked_products"] == 0
    assert result["queued_notifications"] == 0


async def test_price_unchanged_no_history_record(
    patched_session, session_factory
):
    """If the parsed price equals current_price, no PriceHistory row is added."""
    url = "https://shop.example.com/unchanged-item"
    demo_price = await _demo_price(url)

    async with session_factory() as session:
        await _setup_product_with_subscription(
            session,
            url=url,
            current_price=demo_price,  # same as DemoParser will return
            target_price=999.0,
        )

    await run_price_monitoring_cycle()

    async with session_factory() as session:
        history = (await session.execute(select(PriceHistory))).scalars().all()
    assert len(history) == 0


async def test_price_changed_creates_history(
    patched_session, session_factory
):
    """If the parsed price differs from current_price, a PriceHistory row is created."""
    url = "https://shop.example.com/changed-item"
    demo_price = await _demo_price(url)

    async with session_factory() as session:
        await _setup_product_with_subscription(
            session,
            url=url,
            current_price=demo_price + 10.0,  # intentionally different
            target_price=999.0,
        )

    await run_price_monitoring_cycle()

    async with session_factory() as session:
        history = (await session.execute(select(PriceHistory))).scalars().all()
    assert len(history) == 1
    assert history[0].price == demo_price


async def test_target_price_reached_queues_notification(
    patched_session, session_factory
):
    """When target_price >= new_price and is_notified=False, a notification is queued."""
    url = "https://shop.example.com/target-item"
    demo_price = await _demo_price(url)

    async with session_factory() as session:
        await _setup_product_with_subscription(
            session,
            url=url,
            current_price=demo_price + 5.0,
            target_price=demo_price + 1.0,  # target >= demo_price → fires
        )

    result = await run_price_monitoring_cycle()

    assert result["queued_notifications"] == 1
    notification = result["notifications"][0]
    assert notification["current_price"] == demo_price


async def test_notification_not_queued_if_already_notified(
    patched_session, session_factory
):
    """Subscription with is_notified=True must not produce a duplicate notification."""
    url = "https://shop.example.com/notified-item"
    demo_price = await _demo_price(url)

    async with session_factory() as session:
        await _setup_product_with_subscription(
            session,
            url=url,
            current_price=demo_price + 5.0,
            target_price=demo_price + 1.0,
            is_notified=True,  # already notified → must be skipped
        )

    result = await run_price_monitoring_cycle()

    assert result["queued_notifications"] == 0


async def test_is_notified_reset_when_price_rises(
    patched_session, session_factory
):
    """When price rises above target_price, is_notified must be reset to False."""
    url = "https://shop.example.com/rising-item"
    demo_price = await _demo_price(url)

    async with session_factory() as session:
        _, sub = await _setup_product_with_subscription(
            session,
            url=url,
            current_price=demo_price - 5.0,  # old price was LOW
            target_price=demo_price - 1.0,   # target < demo_price → reset fires
            is_notified=True,
        )
        sub_id = sub.id

    await run_price_monitoring_cycle()

    async with session_factory() as session:
        updated_sub = await session.get(Subscription, sub_id)
    assert updated_sub.is_notified is False


async def test_no_channel_skips_notification(
    patched_session, session_factory
):
    """User with neither email nor telegram must not produce a queued notification."""
    url = "https://shop.example.com/no-channel-item"
    demo_price = await _demo_price(url)

    async with session_factory() as session:
        # DB requires at least one channel to save the user
        await _setup_product_with_subscription(
            session,
            url=url,
            current_price=demo_price + 5.0,
            target_price=demo_price + 1.0,
            has_telegram=True,
        )

    # Mock the channel resolution to simulate a user with no channels
    with patch("app.services.price_monitor._resolve_notification_channel", return_value=None):
        result = await run_price_monitoring_cycle()

    assert result["queued_notifications"] == 0
