"""HTTP service for the feedback loop scheduler."""

from __future__ import annotations

import logging
import uuid
from typing import Callable, Coroutine

from fastapi import FastAPI, Request, Response

from .scheduler import setup_scheduler

app = FastAPI(title="Feedback Loop")
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup() -> None:
    """Start background scheduler."""
    # Setup scheduler with no-op defaults for health endpoints
    scheduler = setup_scheduler([], "")
    scheduler.start()


@app.middleware("http")
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Ensure each request has a correlation ID."""
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


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "feedback_loop.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
