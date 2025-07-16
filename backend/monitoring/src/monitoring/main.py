"""Expose Prometheus metrics and logs via FastAPI."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Callable, Coroutine

import psutil
from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from backend.shared.tracing import configure_tracing

from .logging_config import configure_logging
from .settings import settings

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
configure_tracing(app, settings.app_name)

REQUEST_COUNTER = Counter("http_requests_total", "Total HTTP requests")


@app.middleware("http")
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Attach a correlation ID and record metrics."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    REQUEST_COUNTER.inc()

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/overview")
async def overview() -> dict[str, float]:
    """Return basic system information."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_mb": psutil.virtual_memory().used / 1024**2,
    }


@app.get("/analytics")
async def analytics() -> dict[str, int]:
    """Return placeholder analytics dashboard data."""
    return {"active_users": 0, "error_rate": 0}


@app.get("/logs")
async def logs() -> dict[str, str]:
    """Return the latest application logs."""
    path = Path(settings.log_file)
    if not path.exists():
        return {"logs": ""}
    lines = path.read_text(encoding="utf-8").splitlines()[-100:]
    return {"logs": "\n".join(lines)}


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
        "monitoring.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
