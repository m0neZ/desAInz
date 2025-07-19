"""Scheduler for feedback loop jobs."""

from __future__ import annotations

import logging
from typing import Iterable

from apscheduler.schedulers.background import BackgroundScheduler

from .ab_testing import ABTestManager
from .ingestion import (
    ingest_metrics,
    schedule_marketplace_ingestion,
    update_weights_from_db,
)
from .weight_updater import update_weights

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
        df = ingest_metrics(metrics_source)
        logger.info("processed metrics frame size %s", len(df))

    def nightly_update() -> None:
        df = ingest_metrics(metrics_source)
        weights = update_weights(scoring_api, df.to_dict("records"))
        allocation = ab_manager.allocate_budget(total_budget=100.0)
        logger.info("budget allocation %s", allocation)
        logger.info("updated weights payload %s", weights)

    def nightly_marketplace_update() -> None:
        weights = update_weights_from_db(scoring_api)
        logger.info("updated marketplace weights %s", weights)

    scheduler.add_job(hourly_ingest, "interval", hours=1, next_run_time=None)
    # Run weight update a few minutes after the midnight ingestion so the
    # latest metrics are available before updating the scoring engine.
    scheduler.add_job(nightly_update, "cron", hour=0, minute=5, next_run_time=None)
    scheduler.add_job(
        nightly_marketplace_update,
        "cron",
        hour=1,
        minute=0,
        next_run_time=None,
    )
    if listing_ids:
        schedule_marketplace_ingestion(
            scheduler, list(listing_ids), interval_minutes=60
        )
    return scheduler
