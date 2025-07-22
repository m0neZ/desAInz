"""FastAPI application exposing optimization endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
import asyncio
import psutil
import logging
import os
import uuid
from typing import Callable, Coroutine, List, cast

from fastapi import FastAPI, Request, Response
from backend.shared.security import require_status_api_key
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared.metrics import register_metrics
from backend.shared.security import add_security_headers
from backend.shared.responses import json_cached
from backend.shared.logging import configure_logging
from backend.shared import add_error_handlers, configure_sentry
from backend.shared.config import settings as shared_settings
from .metrics import MetricsAnalyzer, ResourceMetric
from .storage import MetricsStore


configure_logging()
logger = logging.getLogger(__name__)

SERVICE_NAME = os.getenv("SERVICE_NAME", "optimization")
app = FastAPI(title="Optimization Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=shared_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
configure_tracing(app, SERVICE_NAME)
configure_sentry(app, SERVICE_NAME)
add_profiling(app)
add_error_handlers(app)
register_metrics(app)
add_security_headers(app)


def _identify_user(request: Request) -> str:
    """Return identifier for logging, header ``X-User`` or client IP."""
    client_host = request.client.host if request.client else "unknown"
    return cast(str, request.headers.get("X-User", client_host))


@app.middleware("http")
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Ensure each request includes a correlation ID."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    try:
        import sentry_sdk

        sentry_sdk.set_tag("correlation_id", correlation_id)
    except Exception:  # pragma: no cover - sentry optional
        pass
    logger.info(
        "request received",
        extra={
            "correlation_id": correlation_id,
            "user": _identify_user(request),
            "path": request.url.path,
            "method": request.method,
        },
    )
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


store = MetricsStore()
scheduler = AsyncIOScheduler()


def record_resource_usage(target_store: MetricsStore = store) -> None:
    """Capture current CPU, memory and disk usage and store the metric."""
    metric = ResourceMetric(
        timestamp=datetime.now(timezone.utc),
        cpu_percent=psutil.cpu_percent(),
        memory_mb=psutil.virtual_memory().used / (1024 * 1024),
        disk_usage_mb=psutil.disk_usage("/").used / (1024 * 1024),
    )
    target_store.add_metric(metric)


@app.on_event("startup")
def start_metrics_collection() -> None:
    """Schedule periodic resource usage collection."""
    if not scheduler.running:
        scheduler.start()
    scheduler.add_job(
        record_resource_usage,
        trigger=IntervalTrigger(seconds=30),
        id="collect_metrics",
        replace_existing=True,
    )


@app.on_event("startup")
async def create_continuous_aggregate() -> None:
    """Create hourly aggregate view if PostgreSQL is used."""
    if not store._use_sqlite:
        store.create_hourly_continuous_aggregate()


@app.on_event("startup")
def start_scheduler() -> None:
    """Start job scheduler for refreshing aggregates."""
    if scheduler.running:
        return
    scheduler.add_job(
        store.create_hourly_continuous_aggregate,
        trigger=IntervalTrigger(hours=1),
        next_run_time=None,
    )
    scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler() -> None:
    """Shutdown the aggregate scheduler."""
    if scheduler.running:
        scheduler.shutdown()


class MetricIn(BaseModel):
    """Request body for submitting a resource metric."""

    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    disk_usage_mb: float | None = None


@app.post("/metrics")
def add_metric(metric: MetricIn) -> dict[str, str]:
    """Store a new resource metric."""
    store.add_metric(
        ResourceMetric(
            timestamp=metric.timestamp,
            cpu_percent=metric.cpu_percent,
            memory_mb=metric.memory_mb,
            disk_usage_mb=metric.disk_usage_mb,
        )
    )
    return {"status": "ok"}


@app.get("/optimizations")
def get_optimizations(limit: int = 10, offset: int = 0) -> List[str]:
    """Return recommended cost optimizations."""
    analyzer = MetricsAnalyzer(store.get_metrics())
    recs = analyzer.recommend_optimizations()
    return recs[offset : offset + limit]


@app.get("/recommendations")
def get_recommendations(limit: int = 3, offset: int = 0) -> List[str]:
    """Return top optimization actions."""
    analyzer = MetricsAnalyzer(store.get_metrics())
    recs = analyzer.top_recommendations(limit + offset)
    return recs[offset : offset + limit]


@app.get("/health")
async def health() -> Response:
    """Return service liveness."""
    return json_cached({"status": "ok"})


@app.get("/ready")
async def ready(request: Request) -> Response:
    """Return service readiness."""
    require_status_api_key(request)
    return json_cached({"status": "ready"})
