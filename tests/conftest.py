"""Shared fixtures for the price_tracker test suite.

All tests run against an in-memory SQLite database (StaticPool) so no
external services (PostgreSQL, Redis, SMTP, Telegram) are required.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User


# ---------------------------------------------------------------------------
# Engine / session fixtures
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def engine():
    """Yield a fresh in-memory SQLite engine with all tables created."""
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
def session_factory(engine):
    """Return an async_sessionmaker bound to the test engine."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session(session_factory):
    """Yield a single AsyncSession for the duration of one test."""
    async with session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# HTTP client fixture
# ---------------------------------------------------------------------------

@pytest.fixture
async def client(session_factory):
    """Yield an AsyncClient that overrides get_db with the test session."""

    async def override_get_db() -> AsyncSession:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers (plain functions, not fixtures)
# ---------------------------------------------------------------------------

def auth_headers(user_id: int) -> dict[str, str]:
    """Return Bearer-token Authorization headers for the given user ID."""
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


async def make_user(
    db: AsyncSession,
    *,
    email: str | None = "user@example.com",
    password: str | None = "password123",
    telegram_user_id: int | None = None,
    telegram_username: str | None = None,
) -> User:
    """Create, persist, and return a test User."""
    user = User(
        email=email,
        hashed_password=get_password_hash(password) if password else None,
        telegram_user_id=telegram_user_id,
        telegram_username=telegram_username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
