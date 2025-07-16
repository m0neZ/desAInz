"""Entrypoint for the signal ingestion service application."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, FastAPI

from .database import get_session, init_db
from .ingestion import ingest
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


@app.on_event("startup")
async def startup() -> None:
    """Initialize resources."""
    await init_db()


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}


@app.post("/ingest")
async def ingest_signals(
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Trigger signal ingestion."""
    await ingest(session)
    return {"status": "ingested"}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "signal_ingestion.main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level,
    )
