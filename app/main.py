"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI

from app.api.router import api_router
from app.core import configure_logging, settings


configure_logging()
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.PROJECT_NAME,
)


@app.on_event("startup")
async def on_startup() -> None:
    """Log application startup for operational visibility."""
    logger.info("event=application_startup status=started")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Log application shutdown for operational visibility."""
    logger.info("event=application_shutdown status=started")


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    """Expose a lightweight healthcheck endpoint for runtime probes."""
    logger.info("event=healthcheck_requested")
    return {"status": "ok"}


app.include_router(api_router, prefix="/api")
