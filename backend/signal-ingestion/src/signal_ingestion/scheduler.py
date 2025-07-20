"""APScheduler scheduler for signal ingestion jobs."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from . import tasks
from .settings import settings

logger = logging.getLogger(__name__)


def _enqueue_ingest(adapter_name: str) -> None:
    """Dispatch Celery task for ``adapter_name``."""

    tasks.app.send_task(
        "signal_ingestion.ingest_adapter",
        args=[adapter_name],
        queue=tasks.queue_for(adapter_name),
    )


def create_scheduler() -> AsyncIOScheduler:
    """Return scheduler configured to run ingestion periodically."""
    scheduler = AsyncIOScheduler()
    if settings.enabled_adapters is not None and not settings.enabled_adapters:
        return scheduler

    adapter_names = (
        list(tasks.ADAPTERS.keys())
        if settings.enabled_adapters is None
        else [
            name
            for name in tasks.ADAPTERS.keys()
            if name in settings.enabled_adapters
        ]
    )

    if settings.ingest_cron_schedule:
        trigger = CronTrigger.from_crontab(settings.ingest_cron_schedule)
    else:
        trigger = IntervalTrigger(minutes=settings.ingest_interval_minutes)

    for name in adapter_names:
        scheduler.add_job(
            _enqueue_ingest,
            args=[name],
            trigger=trigger,
            id=f"ingest_{name}",
            replace_existing=True,
        )

    return scheduler
