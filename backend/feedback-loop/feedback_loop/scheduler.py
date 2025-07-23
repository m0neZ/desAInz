"""Scheduler for feedback loop jobs."""

from __future__ import annotations

import logging
from typing import Iterable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .ab_testing import ABTestManager
from .ingestion import ingest_metrics, schedule_marketplace_ingestion
from .weight_updater import update_weights
from .settings import settings

logger = logging.getLogger(__name__)


def setup_scheduler(
    metrics_source: Iterable[dict[str, float]],
    scoring_api: str,
    listing_ids: Iterable[int] | None = None,
    ab_db_url: str = "sqlite:///abtest.db",
) -> BackgroundScheduler:
    """Configure and return the job scheduler."""
    scheduler = BackgroundScheduler()
    ab_manager = ABTestManager(ab_db_url)

    def hourly_ingest() -> None:
        metrics = ingest_metrics(metrics_source)
        logger.info("processed metrics count %s", len(metrics))

    def nightly_update() -> None:
        metrics = ingest_metrics(metrics_source)
        weights = update_weights(scoring_api, metrics)  # type: ignore[arg-type]
        allocation = ab_manager.allocate_budget(total_budget=100.0)
        logger.info("budget allocation %s", allocation)
        logger.info("updated weights payload %s", weights)

    scheduler.add_job(
        hourly_ingest,
        trigger=IntervalTrigger(minutes=settings.publisher_metrics_interval_minutes),
        next_run_time=None,
    )
    scheduler.add_job(
        nightly_update,
        trigger=IntervalTrigger(minutes=settings.weight_update_interval_minutes),
        next_run_time=None,
    )
    if listing_ids:
        schedule_marketplace_ingestion(
            scheduler,
            list(listing_ids),
            scoring_api,
            interval_minutes=settings.publisher_metrics_interval_minutes,
        )
    return scheduler
