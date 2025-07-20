"""Expose Prometheus metrics and logs via FastAPI."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Callable, Coroutine, Iterable

import httpx

import psutil
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Histogram
from backend.shared.metrics import register_metrics

from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared import add_error_handlers, configure_sentry
from backend.shared.config import settings as shared_settings
from backend.shared.db import session_scope
from backend.shared.db.models import Idea, Listing, Mockup, Signal
from sqlalchemy import func, select

from .pagerduty import trigger_sla_violation
from .metrics_store import (
    PublishLatencyMetric,
    TimescaleMetricsStore,
    LATENCY_CACHE_KEY,
)
from backend.shared.cache import sync_get, sync_set

from .logging_config import configure_logging
from .settings import settings

metrics_store = TimescaleMetricsStore()

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=shared_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
configure_tracing(app, settings.app_name)
configure_sentry(app, settings.app_name)
add_profiling(app)
add_error_handlers(app)
register_metrics(app)
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
    try:
        import sentry_sdk

        sentry_sdk.set_tag("correlation_id", correlation_id)
    except Exception:  # pragma: no cover - sentry optional
        pass

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


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
            Idea.id,
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
    for idea_id, signal_time, listing_time in rows:
        seconds = (listing_time - signal_time).total_seconds()
        latencies.append(seconds)
        SIGNAL_TO_PUBLISH_SECONDS.observe(seconds)
        metrics_store.add_latency(
            PublishLatencyMetric(
                idea_id=idea_id,
                timestamp=listing_time,
                latency_seconds=seconds,
            )
        )
    return latencies


def get_average_latency() -> float:
    """Return cached average latency or compute and store it."""
    cached = sync_get(LATENCY_CACHE_KEY)
    if cached is not None:
        try:
            return float(cached)
        except (TypeError, ValueError):
            pass
    latencies = _record_latencies()
    avg = sum(latencies) / max(len(latencies), 1)
    try:
        sync_set(LATENCY_CACHE_KEY, str(avg), ttl=300)
    except Exception:  # pragma: no cover - redis optional
        pass
    return avg


def _check_sla() -> float:
    """Check average latency and trigger PagerDuty if above threshold."""
    avg = get_average_latency()
    if avg == 0.0:
        return avg
    threshold = getattr(settings, "SLA_THRESHOLD_HOURS", settings.sla_threshold_hours)
    if avg > threshold * 3600:
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
    avg = get_average_latency()
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
