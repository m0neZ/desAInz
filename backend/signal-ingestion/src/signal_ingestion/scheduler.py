"""APScheduler scheduler for signal ingestion jobs."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .database import SessionLocal
from .ingestion import ingest
from .settings import settings

logger = logging.getLogger(__name__)


async def ingest_job() -> None:
    """Run the ingestion routine in a database session."""
    async with SessionLocal() as session:
        await ingest(session)


def create_scheduler() -> AsyncIOScheduler:
    """Return scheduler configured to run ingestion periodically."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        ingest_job,
        trigger=IntervalTrigger(minutes=settings.ingest_interval_minutes),
        id="ingest",
        replace_existing=True,
    )
    return scheduler
