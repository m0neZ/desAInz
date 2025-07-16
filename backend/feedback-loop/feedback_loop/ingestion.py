"""Metric ingestion scheduler."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler


LOGGER = logging.getLogger(__name__)


def ingest_metrics() -> None:
    """Ingest metrics from marketplaces."""
    LOGGER.info("Ingesting metrics at %s", datetime.now(UTC).isoformat())
    # Actual ingestion logic would go here


def schedule_ingestion_jobs(
    scheduler: BackgroundScheduler | None = None,
) -> BackgroundScheduler:
    """Schedule hourly metric ingestion jobs.

    Parameters
    ----------
    scheduler:
        Existing scheduler instance. If ``None``, a new one is created.

    Returns
    -------
    BackgroundScheduler
        Scheduler instance with the job added.
    """
    sched = scheduler or BackgroundScheduler()
    sched.add_job(ingest_metrics, "interval", hours=1, id="metric_ingestion")
    return sched
