"""Prometheus metrics utilities for the monitoring service."""

from __future__ import annotations

from prometheus_client import (
    REGISTRY,
    Counter,
    Summary,
    generate_latest,
)

registry = REGISTRY
REQUEST_COUNT = Counter(
    "request_count",
    "Total number of HTTP requests",
    registry=registry,
)
REQUEST_LATENCY = Summary(
    "request_latency_seconds",
    "Latency of HTTP requests in seconds",
    registry=registry,
)


def prometheus_metrics() -> bytes:
    """Return current metrics in Prometheus text format."""
    return bytes(generate_latest(registry))
