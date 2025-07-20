"""APScheduler scheduler for signal ingestion jobs."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from . import tasks
from .settings import settings
from .trending import trim_keywords

logger = logging.getLogger(__name__)


def ingest_job() -> None:
    """Enqueue ingestion tasks for enabled adapters."""
    if settings.enabled_adapters is None:
        adapter_names = list(tasks.ADAPTERS.keys())
    else:
        adapter_names = [
            name for name in tasks.ADAPTERS.keys() if name in settings.enabled_adapters
        ]
    for name in adapter_names:
        tasks.app.send_task(
            "signal_ingestion.ingest_adapter", args=[name], queue=tasks.queue_for(name)
        )


def create_scheduler() -> AsyncIOScheduler:
    """Return scheduler configured to run ingestion periodically."""
    scheduler = AsyncIOScheduler()
    if settings.enabled_adapters is not None and not settings.enabled_adapters:
        return scheduler
    trigger = (
        CronTrigger.from_crontab(settings.ingest_cron)
        if settings.ingest_cron
        else IntervalTrigger(minutes=settings.ingest_interval_minutes)
    )
    scheduler.add_job(
        ingest_job,
        trigger=trigger,
        id="ingest",
        replace_existing=True,
    )
    scheduler.add_job(
        trim_trending_job,
        trigger=IntervalTrigger(minutes=5),
        id="trim_trending",
        replace_existing=True,
    )
    return scheduler


def trim_trending_job() -> None:
    """Trim trending keywords to maximum size."""
    trim_keywords(settings.trending_max_keywords)
