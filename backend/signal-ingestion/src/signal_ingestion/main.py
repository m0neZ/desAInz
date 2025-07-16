"""Entrypoint for the signal ingestion service application."""

from __future__ import annotations

import logging
import uuid
from typing import Callable, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, FastAPI, Request, Response

from backend.shared.tracing import configure_tracing

from .database import get_session, init_db
from .ingestion import ingest
from .logging_config import configure_logging
from .settings import settings

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
configure_tracing("signal-ingestion", app)


@app.on_event("startup")
async def startup() -> None:
    """Initialize resources."""
    await init_db()


@app.middleware("http")
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Ensure every request contains a correlation ID."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    logger.info("request received", extra={"correlation_id": correlation_id})
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


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
