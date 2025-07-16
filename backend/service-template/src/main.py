"""Entrypoint for the service template application."""

from __future__ import annotations

import logging
from fastapi import FastAPI

from backend.shared.logging_config import (
    add_correlation_middleware,
    configure_logging,
)
from .settings import settings
from backend.shared.tracing import configure_tracing

configure_logging(settings.app_name)
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
configure_tracing(app, settings.app_name)
add_correlation_middleware(app)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level,
    )
