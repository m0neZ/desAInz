"""FastAPI application exposing optimization endpoints."""

from __future__ import annotations

from datetime import datetime
import logging
import os
import uuid
from typing import Callable, Coroutine, List, cast

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared.logging import configure_logging
from backend.shared import add_error_handlers, configure_sentry
from .metrics import MetricsAnalyzer, ResourceMetric
from .storage import MetricsStore


configure_logging()
logger = logging.getLogger(__name__)

SERVICE_NAME = os.getenv("SERVICE_NAME", "optimization")
app = FastAPI(title="Optimization Service")
configure_tracing(app, SERVICE_NAME)
configure_sentry(app, SERVICE_NAME)
add_profiling(app)
add_error_handlers(app)


def _identify_user(request: Request) -> str:
    """Return identifier for logging, header ``X-User`` or client IP."""
    return cast(str, request.headers.get("X-User", request.client.host))


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


class MetricIn(BaseModel):
    """Request body for submitting a resource metric."""

    timestamp: datetime
    cpu_percent: float
    memory_mb: float


@app.post("/metrics")
def add_metric(metric: MetricIn) -> dict[str, str]:
    """Store a new resource metric."""
    store.add_metric(
        ResourceMetric(
            timestamp=metric.timestamp,
            cpu_percent=metric.cpu_percent,
            memory_mb=metric.memory_mb,
        )
    )
    return {"status": "ok"}


@app.get("/optimizations")
def get_optimizations() -> List[str]:
    """Return recommended cost optimizations."""
    analyzer = MetricsAnalyzer(store.get_metrics())
    return analyzer.recommend_optimizations()


@app.get("/recommendations")
def get_recommendations() -> List[str]:
    """Return top optimization actions."""
    analyzer = MetricsAnalyzer(store.get_metrics())
    return analyzer.top_recommendations()


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}
