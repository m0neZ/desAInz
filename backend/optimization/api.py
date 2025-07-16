"""FastAPI application exposing optimization endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import List

import logging
from fastapi import FastAPI
from pydantic import BaseModel
from backend.shared.tracing import configure_tracing
from backend.shared.logging_config import (
    add_correlation_middleware,
    configure_logging,
)

from .metrics import MetricsAnalyzer, ResourceMetric
from .storage import MetricsStore

configure_logging("optimization")
logger = logging.getLogger(__name__)
app = FastAPI(title="Optimization Service")
configure_tracing(app, "optimization")
add_correlation_middleware(app)
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


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}
