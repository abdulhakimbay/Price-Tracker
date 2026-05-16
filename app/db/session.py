"""Database session utilities shared by API handlers and background jobs."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Yield a request-scoped async database session."""
    logger.debug("event=db_session_opened scope=request")
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            logger.debug("event=db_session_closed scope=request")
