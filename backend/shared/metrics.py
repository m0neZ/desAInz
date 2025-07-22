"""Prometheus metrics utilities."""

from __future__ import annotations

import re
from collections import defaultdict
from time import perf_counter
from typing import Callable, Coroutine, DefaultDict, Iterable

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .responses import cache_header

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

    def _batch_observe(hist: Histogram, values: Iterable[float]) -> None:
        """Record ``values`` in ``hist`` using a single update."""
        vals = list(values)
        if not vals:
            return
        hist._sum.inc(sum(vals))
        buckets = [0] * len(hist._upper_bounds)
        for v in vals:
            for i, bound in enumerate(hist._upper_bounds):
                if v <= bound:
                    buckets[i] += 1
                    break
        for bucket, inc in zip(hist._buckets, buckets):
            if inc:
                bucket.inc(inc)

    for (method, endpoint), durations in list(_BUFFER.items()):
        REQUEST_COUNTER.labels(method, endpoint).inc(len(durations))
        _batch_observe(REQUEST_LATENCY.labels(method, endpoint), durations)
    _BUFFER.clear()


def register_metrics(app: FastAPI) -> None:
    """Attach metrics middleware and /metrics endpoint to ``app``."""

    @app.middleware("http")
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

    @app.get("/metrics")
    async def metrics() -> Response:
        """Return Prometheus metrics with aggressive caching."""
        _flush_metrics()
        data = generate_latest()
        headers = cache_header(ttl=METRICS_CACHE_TTL)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST, headers=headers)
