"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.router import api_router
from app.core import configure_logging, settings


configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    logger.info("event=application_startup status=started")
    yield
    logger.info("event=application_shutdown status=started")


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    """Expose a lightweight healthcheck endpoint for runtime probes."""
    logger.info("event=healthcheck_requested")
    return {"status": "ok"}


app.include_router(api_router, prefix="/api")
