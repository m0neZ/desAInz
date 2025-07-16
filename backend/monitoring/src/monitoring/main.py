"""Expose Prometheus metrics and logs via FastAPI."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Callable, Coroutine, Iterable

import httpx

import psutil
from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared.db import session_scope
from backend.shared.db.models import Idea, Listing, Mockup, Signal
from sqlalchemy import func, select

from .pagerduty import trigger_sla_violation

from .logging_config import configure_logging
from .settings import settings

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
configure_tracing(app, settings.app_name)
add_profiling(app)

REQUEST_COUNTER = Counter("http_requests_total", "Total HTTP requests")
SIGNAL_TO_PUBLISH_SECONDS = Histogram(
    "signal_to_publish_seconds",
    "Latency from first signal ingestion to listing publish per idea",
    buckets=(60, 300, 900, 1800, 3600, 7200, 10800),
)


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


def _record_latencies() -> Iterable[float]:
    """Record per-idea publish latency and return all values."""
    stmt = (
        select(
            func.min(Signal.timestamp),
            func.min(Listing.created_at),
        )
        .join(Signal, Signal.idea_id == Idea.id)
        .join(Mockup, Mockup.idea_id == Idea.id)
        .join(Listing, Listing.mockup_id == Mockup.id)
        .group_by(Idea.id)
    )
    with session_scope() as session:
        rows = session.execute(stmt).all()
    latencies: list[float] = []
    for signal_time, listing_time in rows:
        seconds = (listing_time - signal_time).total_seconds()
        latencies.append(seconds)
        SIGNAL_TO_PUBLISH_SECONDS.observe(seconds)
    return latencies


def _check_sla() -> float:
    """Check average latency and trigger PagerDuty if above threshold."""
    latencies = _record_latencies()
    if not latencies:
        return 0.0
    avg = sum(latencies) / len(latencies)
    if avg > settings.sla_threshold_hours * 3600:
        trigger_sla_violation(avg / 3600)
    return avg


@app.get("/sla")
async def sla() -> dict[str, float]:
    """Check SLA status and emit PagerDuty alert if violated."""
    avg = _check_sla()
    return {"average_seconds": avg}


@app.get("/latency")
async def latency() -> dict[str, float]:
    """Return average signal-to-publish latency without triggering alerts."""
    latencies = _record_latencies()
    avg = sum(latencies) / max(len(latencies), 1)
    return {"average_seconds": avg}


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
