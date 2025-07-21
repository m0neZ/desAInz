"""Prometheus metrics utilities."""

from __future__ import annotations

from time import perf_counter
from typing import Callable, Coroutine

from fastapi import FastAPI, Request, Response

from .responses import cache_header
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)


REQUEST_COUNTER = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint"]
)
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


def register_metrics(app: FastAPI) -> None:
    """Attach metrics middleware and /metrics endpoint to ``app``."""

    @app.middleware("http")
    async def _record_metrics(
        request: Request,
        call_next: Callable[[Request], Coroutine[None, None, Response]],
    ) -> Response:
        start = perf_counter()
        response = await call_next(request)
        duration = perf_counter() - start
        REQUEST_COUNTER.labels(request.method, request.url.path).inc()
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
        return response

    @app.get("/metrics")
    async def metrics() -> Response:
        data = generate_latest()
        headers = cache_header()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST, headers=headers)
