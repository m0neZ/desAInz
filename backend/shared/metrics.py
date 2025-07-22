"""Prometheus metrics utilities."""

from __future__ import annotations

from time import perf_counter
from typing import Callable, Coroutine, DefaultDict
from collections import defaultdict
import re

from fastapi import FastAPI, Request, Response

from .responses import cache_header
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

METRICS_CACHE_TTL = 3600


REQUEST_COUNTER = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint"]
)
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


_BUFFER: DefaultDict[tuple[str, str], list[float]] = defaultdict(list)
_BATCH_SIZE = 100


_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _normalize_path(path: str) -> str:
    """Return ``path`` with dynamic segments replaced by ``:id``."""
    segments = []
    for part in path.strip("/").split("/"):
        if part.isdigit() or _UUID_RE.match(part):
            segments.append(":id")
        else:
            segments.append(part)
    return "/" + "/".join(segments)


def _flush_metrics() -> None:
    """Update Prometheus metrics and clear in-memory buffers."""
    for (method, endpoint), durations in list(_BUFFER.items()):
        REQUEST_COUNTER.labels(method, endpoint).inc(len(durations))
        for dur in durations:
            REQUEST_LATENCY.labels(method, endpoint).observe(dur)
    _BUFFER.clear()


def register_metrics(app: FastAPI) -> None:
    """Attach metrics middleware and /metrics endpoint to ``app``."""

    @app.middleware("http")  # type: ignore[misc]
    async def _record_metrics(
        request: Request,
        call_next: Callable[[Request], Coroutine[None, None, Response]],
    ) -> Response:
        """Store request duration in the in-memory buffer."""
        start = perf_counter()
        response = await call_next(request)
        duration = perf_counter() - start
        key = (request.method, _normalize_path(request.url.path))
        _BUFFER[key].append(duration)
        if len(_BUFFER) >= _BATCH_SIZE:
            _flush_metrics()
        return response

    @app.get("/metrics")  # type: ignore[misc]
    async def metrics() -> Response:
        """Return Prometheus metrics with aggressive caching."""
        _flush_metrics()
        data = generate_latest()
        headers = cache_header(ttl=METRICS_CACHE_TTL)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST, headers=headers)
