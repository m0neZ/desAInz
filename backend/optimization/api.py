"""
FastAPI application exposing optimization endpoints.

Environment variables
---------------------
SERVICE_NAME:
    Name reported to tracing and logging backends. Defaults to
    :data:`~backend.shared.ServiceName.OPTIMIZATION`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import asyncio
import psutil
import logging
import os
import uuid
import warnings
from functools import lru_cache
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
from backend.shared.http import close_async_clients
from backend.shared.responses import json_cached
from backend.shared.logging import configure_logging
from backend.shared import ServiceName, add_error_handlers, configure_sentry
from backend.shared.config import settings as shared_settings
from .metrics import MetricsAnalyzer, ResourceMetric
from .storage import MetricsStore


configure_logging()
warnings.filterwarnings("ignore", category=DeprecationWarning)
logger = logging.getLogger(__name__)

SERVICE_NAME = os.getenv("SERVICE_NAME", ServiceName.OPTIMIZATION.value)
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


@lru_cache(maxsize=256)
def _cached_user(x_user: str | None, client_host: str) -> str:
    """Return user identifier from ``x_user`` or ``client_host``."""
    return x_user or client_host


def _identify_user(request: Request) -> str:
    """Return identifier for logging, header ``X-User`` or client IP."""
    client_host = request.client.host if request.client else "unknown"
    return _cached_user(request.headers.get("X-User"), cast(str, client_host))


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


def record_resource_usage(target_store: MetricsStore | None = None) -> None:
    """Capture current CPU, memory and disk usage and store the metric."""
    store_obj = target_store or store
    metric = ResourceMetric(
        timestamp=datetime.now(UTC),
        cpu_percent=psutil.cpu_percent(),
        memory_mb=psutil.virtual_memory().used / (1024 * 1024),
        disk_usage_mb=psutil.disk_usage("/").used / (1024 * 1024),
    )
    store_obj.add_metric(metric)


@app.on_event("startup")
def start_metrics_collection() -> None:
    """Schedule periodic resource usage collection."""
    if not scheduler.running:
        scheduler.start()
    scheduler.add_job(
        record_resource_usage,
        trigger=IntervalTrigger(minutes=1),
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
async def shutdown_scheduler() -> None:
    """Shutdown the aggregate scheduler."""
    if scheduler.running:
        scheduler.shutdown()
    await close_async_clients()


@app.on_event("shutdown")
def shutdown_store() -> None:
    """Close database connections on application shutdown."""
    store.close()


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


@app.get("/metrics/recent", response_model=List[ResourceMetric])
def get_recent_metrics(limit: int = 10) -> List[ResourceMetric]:
    """
    Return the most recently captured metrics.

    Parameters
    ----------
    limit : int, optional
        Number of metrics to fetch ordered from newest to oldest.

    Returns
    -------
    list[ResourceMetric]
        Metrics ordered from oldest to newest.
    """

    return store.get_recent_metrics(limit)


@app.get("/optimizations")
def get_optimizations(window_minutes: int | None = None) -> List[str]:
    """
    Return recommended cost optimizations.

    Parameters
    ----------
    window_minutes : int | None, optional
        Limit analysis to metrics collected within the last ``window_minutes``
        minutes. If ``None``, all available metrics are used.

    Returns
    -------
    list[str]
        Ordered list of optimization suggestions.
    """

    since = (
        datetime.now(UTC) - timedelta(minutes=window_minutes)
        if window_minutes is not None
        else None
    )
    analyzer = MetricsAnalyzer.from_store(store, since=since)
    return analyzer.recommend_optimizations()


@app.get("/recommendations")
def get_recommendations(window_minutes: int | None = None) -> List[str]:
    """
    Return prioritized optimization actions.

    Parameters
    ----------
    window_minutes : int | None, optional
        Analyze metrics captured in the last ``window_minutes`` minutes. Use all
        data if ``None``.

    Returns
    -------
    list[str]
        Recommendations ordered by impact.
    """

    since = (
        datetime.now(UTC) - timedelta(minutes=window_minutes)
        if window_minutes is not None
        else None
    )
    analyzer = MetricsAnalyzer.from_store(store, since=since)
    return analyzer.top_recommendations()


@app.get("/hints")
def get_hints(window_minutes: int | None = None) -> List[str]:
    """
    Return optimization hints based on recent metrics.

    Parameters
    ----------
    window_minutes : int | None, optional
        Consider only metrics from the last ``window_minutes`` minutes. When
        ``None`` all stored metrics are analyzed.

    Returns
    -------
    list[str]
        Ranked hints derived from recent data.
    """

    since = (
        datetime.now(UTC) - timedelta(minutes=window_minutes)
        if window_minutes is not None
        else None
    )
    analyzer = MetricsAnalyzer.from_store(store, since=since)
    return analyzer.top_recommendations()


@app.get("/cost_alerts")
def get_cost_alerts(window_minutes: int | None = None) -> List[str]:
    """
    Return alerts when usage or cost thresholds are exceeded.

    Parameters
    ----------
    window_minutes : int | None, optional
        Evaluate metrics recorded within the last ``window_minutes`` minutes. If
        ``None`` all metrics are used.

    Returns
    -------
    list[str]
        Messages describing current cost concerns.
    """

    since = (
        datetime.now(UTC) - timedelta(minutes=window_minutes)
        if window_minutes is not None
        else None
    )
    analyzer = MetricsAnalyzer.from_store(store, since=since)
    return analyzer.cost_alerts()


@app.get("/health")
async def health() -> Response:
    """
    Return service liveness.

    Returns
    -------
    Response
        Cached JSON payload containing ``{"status": "ok"}``.
    """

    return json_cached({"status": "ok"})


@app.get("/ready")
async def ready(request: Request) -> Response:
    """
    Return service readiness if the API key is valid.

    Parameters
    ----------
    request : Request
        Incoming request object.

    Returns
    -------
    Response
        Cached JSON payload ``{"status": "ready"}``.
    """

    require_status_api_key(request)
    return json_cached({"status": "ready"})
