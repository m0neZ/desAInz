"""Entry point to start scheduled jobs."""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from feedback_loop import schedule_ingestion_jobs, schedule_score_update_job


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Start scheduler for feedback loop."""
    scheduler = BackgroundScheduler()
    schedule_ingestion_jobs(scheduler)
    schedule_score_update_job(
        "http://scoring-engine/api/weights", {"freshness": 1.0}, scheduler
    )
    scheduler.start()
    LOGGER.info("Scheduler started")


if __name__ == "__main__":
    main()
