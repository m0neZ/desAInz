"""Expose Prometheus metrics and logs via FastAPI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Coroutine

import psutil
from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from backend.shared.tracing import configure_tracing

from backend.shared.logging_config import (
    add_correlation_middleware,
    configure_logging,
)
from .settings import settings

configure_logging(settings.app_name)
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
configure_tracing(app, settings.app_name)
add_correlation_middleware(app)

REQUEST_COUNTER = Counter("http_requests_total", "Total HTTP requests")


@app.middleware("http")
async def count_requests(
    request: Request, call_next: Callable[[Request], Coroutine[None, None, Response]]
) -> Response:
    """Increment the request counter."""
    REQUEST_COUNTER.inc()
    return await call_next(request)


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
