"""FastAPI application exposing optimization endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import configure_profiling

from .metrics import MetricsAnalyzer, ResourceMetric
from .storage import MetricsStore

app = FastAPI(title="Optimization Service")
configure_tracing(app, "optimization")
configure_profiling(app)
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
