"""Expose Prometheus metrics and logs via FastAPI."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Callable, Coroutine

import httpx

import psutil
from fastapi import FastAPI, Request, Response

from backend.shared.profiling import add_fastapi_profiler
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from backend.shared.tracing import configure_tracing
from backend.shared.db import session_scope
from backend.shared.db.models import Idea, Listing, Mockup
from sqlalchemy import select

from .pagerduty import trigger_sla_violation

from .logging_config import configure_logging
from .settings import settings

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
configure_tracing(app, settings.app_name)
add_fastapi_profiler(app)

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


@app.get("/status")
async def status() -> dict[str, str]:
    """Return health status for core services."""
    services = {
        "mockup_generation": "http://mockup-generation:8000/health",
        "marketplace_publisher": "http://marketplace-publisher:8000/health",
        "orchestrator": "http://orchestrator:8000/health",
    }
    results: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=2) as client:
        for name, url in services.items():
            try:
                resp = await client.get(url)
                results[name] = (
                    resp.json().get("status") if resp.status_code == 200 else "down"
                )
            except Exception:  # pragma: no cover - network failures
                results[name] = "down"
    return results


def _check_sla() -> None:
    """Trigger PagerDuty alert if latest listing exceeds SLA."""
    stmt = (
        select(Listing.created_at, Idea.created_at)
        .join(Mockup, Listing.mockup_id == Mockup.id)
        .join(Idea, Mockup.idea_id == Idea.id)
        .order_by(Listing.created_at.desc())
        .limit(1)
    )
    with session_scope() as session:
        row = session.execute(stmt).first()
    if row is None:
        return
    listing_time, idea_time = row
    hours = (listing_time - idea_time).total_seconds() / 3600
    if hours > 2:
        trigger_sla_violation(hours)


@app.get("/sla")
async def sla() -> dict[str, str]:
    """Check SLA status and emit PagerDuty alert if violated."""
    _check_sla()
    return {"status": "checked"}


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
