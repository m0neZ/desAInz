"""Shared metrics utilities."""

from __future__ import annotations

import logging
import os
from typing import List

from prometheus_client import Histogram


IDEA_LATENCY = Histogram(
    "idea_latency_seconds",
    "Time from signal ingestion to publishing",
)

_latency_values: List[float] = []
_ALERT_THRESHOLD_SECONDS = float(os.getenv("IDEA_LATENCY_THRESHOLD", "60"))


def record_idea_latency(seconds: float) -> None:
    """Record ``seconds`` to histogram and trigger alerts."""
    IDEA_LATENCY.observe(seconds)
    _latency_values.append(seconds)
    average = sum(_latency_values) / len(_latency_values)
    if average > _ALERT_THRESHOLD_SECONDS:
        logging.getLogger(__name__).warning(
            "Average idea latency %.2fs exceeds threshold %.2fs",
            average,
            _ALERT_THRESHOLD_SECONDS,
        )


def get_average_latency() -> float:
    """Return the average recorded idea latency."""
    if not _latency_values:
        return 0.0
    return sum(_latency_values) / len(_latency_values)
