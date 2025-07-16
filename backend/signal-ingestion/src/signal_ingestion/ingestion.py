"""Ingestion orchestration."""

from __future__ import annotations


import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from .retention import purge_old_signals
from .settings import settings
from .tasks import ADAPTERS as TASK_ADAPTERS, schedule_ingestion


async def ingest(session: AsyncSession) -> None:
    """Schedule ingestion tasks for all adapters."""
    await purge_old_signals(session, settings.signal_retention_days)
    adapter_names = list(TASK_ADAPTERS.keys())
    await asyncio.to_thread(schedule_ingestion, adapter_names)
