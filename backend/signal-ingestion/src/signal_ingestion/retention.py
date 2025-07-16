"""Data retention utilities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Signal


async def purge_old_signals(session: AsyncSession, days: int) -> None:
    """Delete ``Signal`` rows older than ``days`` days."""
    threshold = datetime.now(timezone.utc) - timedelta(days=days)
    await session.execute(delete(Signal).where(Signal.timestamp < threshold))
    await session.commit()
