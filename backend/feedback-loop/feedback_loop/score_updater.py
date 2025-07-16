"""Nightly scoring weight updater."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Mapping

import requests
from apscheduler.schedulers.background import BackgroundScheduler


LOGGER = logging.getLogger(__name__)


def update_weights(api_url: str, weights: Mapping[str, float]) -> None:
    """Update scoring weights via API."""
    LOGGER.info("Updating weights at %s", datetime.now(UTC).isoformat())
    response = requests.post(api_url, json={"weights": weights}, timeout=10)
    response.raise_for_status()


def schedule_score_update_job(
    api_url: str,
    weights: Mapping[str, float],
    scheduler: BackgroundScheduler | None = None,
) -> BackgroundScheduler:
    """Schedule nightly weight update job."""
    sched = scheduler or BackgroundScheduler()
    sched.add_job(
        update_weights,
        "cron",
        hour=0,
        minute=0,
        args=[api_url, weights],
        id="score_weight_update",
    )
    return sched
