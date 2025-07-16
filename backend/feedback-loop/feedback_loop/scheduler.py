"""Scheduler for feedback loop jobs."""

from __future__ import annotations

import logging
from typing import Iterable

from apscheduler.schedulers.background import BackgroundScheduler

from .ab_testing import ABTestManager
from .ingestion import ingest_metrics
from .weight_updater import update_weights
from .highlighting import highlight_low_performing_designs

logger = logging.getLogger(__name__)


def setup_scheduler(
    metrics_source: Iterable[dict[str, float]],
    scoring_api: str,
    ab_db_url: str = "sqlite:///abtest.db",
) -> BackgroundScheduler:
    """Configure and return the job scheduler."""
    scheduler = BackgroundScheduler()
    ab_manager = ABTestManager(ab_db_url)

    def hourly_ingest() -> None:
        df = ingest_metrics(metrics_source)
        logger.info("processed metrics frame size %s", len(df))
        low = highlight_low_performing_designs(df, "engagement", threshold=0.2)
        if low:
            logger.info("low performing designs %s", low)

    def nightly_update() -> None:
        weights = {
            "freshness": 1.0,
            "engagement": 1.0,
            "novelty": 1.0,
            "community_fit": 1.0,
            "seasonality": 1.0,
        }
        update_weights(scoring_api, weights)
        allocation = ab_manager.allocate_budget(total_budget=100.0)
        logger.info("budget allocation %s", allocation)

    scheduler.add_job(hourly_ingest, "interval", hours=1, next_run_time=None)
    scheduler.add_job(nightly_update, "cron", hour=0, minute=0, next_run_time=None)
    return scheduler
