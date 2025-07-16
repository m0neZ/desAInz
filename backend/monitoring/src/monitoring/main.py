"""FastAPI application exposing monitoring endpoints."""

from __future__ import annotations

import logging
from pathlib import Path

import psutil
from fastapi import FastAPI, Query
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Gauge,
    generate_latest,
)

from backend.shared.tracing import configure_tracing
from .logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title="Monitoring Service")
configure_tracing("monitoring", app)

registry = CollectorRegistry()
CPU_USAGE = Gauge(
    "cpu_usage_percent", "Current CPU usage percentage", registry=registry
)
MEM_USAGE = Gauge(
    "memory_usage_mb", "Current memory usage in megabytes", registry=registry
)


@app.on_event("startup")  # type: ignore[misc]
async def startup() -> None:
    """Initialize metrics on startup."""
    _update_metrics()


def _update_metrics() -> None:
    """Refresh metrics from the system state."""
    CPU_USAGE.set(psutil.cpu_percent())
    MEM_USAGE.set(psutil.virtual_memory().used / 1024 / 1024)


@app.get("/metrics")  # type: ignore[misc]
def metrics() -> Response:
    """Expose Prometheus metrics for scraping."""
    _update_metrics()
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/overview")  # type: ignore[misc]
def overview() -> dict[str, float]:
    """Return current CPU and memory usage."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_mb": psutil.virtual_memory().used / 1024 / 1024,
    }


@app.get("/dashboard")  # type: ignore[misc]
def dashboard() -> dict[str, float]:
    """Return simple aggregated analytics."""
    cpu = psutil.cpu_percent(interval=1)
    mem_percent = psutil.virtual_memory().percent
    return {"avg_cpu_percent": cpu, "memory_percent": mem_percent}


LOG_FILE = Path(__file__).resolve().parent / "service.log"


@app.get("/logs")  # type: ignore[misc]
def logs(lines: int = Query(100, gt=1, le=1000)) -> dict[str, str]:
    """Return the last ``lines`` of the log file."""
    if not LOG_FILE.exists():
        return {"logs": ""}
    content = "\n".join(LOG_FILE.read_text().splitlines()[-lines:])
    return {"logs": content}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "monitoring.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
