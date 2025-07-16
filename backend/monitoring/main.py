"""FastAPI application exposing monitoring endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Coroutine

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST

from backend.common.tracing import init_fastapi_tracing
from .metrics import REQUEST_COUNT, REQUEST_LATENCY, prometheus_metrics

app = FastAPI(title="Monitoring Service")
init_fastapi_tracing(app, "monitoring")


@app.middleware("http")
async def track_metrics(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Record metrics for every request."""
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        response = await call_next(request)
    return response


@app.get("/metrics")
async def metrics() -> Response:
    """Return Prometheus metrics."""
    return Response(prometheus_metrics(), media_type=CONTENT_TYPE_LATEST)


@app.get("/overview")
async def overview() -> dict[str, str]:
    """Return high-level system status information."""
    return {"status": "operational"}


@app.get("/analytics")
async def analytics() -> dict[str, float]:
    """Return aggregated analytics data."""
    if REQUEST_COUNT._value.get() == 0:
        latency = 0.0
    else:
        latency = REQUEST_LATENCY._sum.get() / REQUEST_COUNT._value.get()
    return {"average_latency": latency}


@app.get("/logs")
async def logs() -> dict[str, str]:
    """Return the latest log entries if available."""
    log_path = Path("service.log")
    if log_path.exists():
        lines = log_path.read_text().splitlines()[-10:]
        return {"logs": "\n".join(lines)}
    return {"logs": ""}
