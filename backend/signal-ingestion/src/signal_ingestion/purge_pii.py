"""Utilities to purge PII from stored signals."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Signal
from .privacy import purge_row


async def purge_pii(session: AsyncSession, limit: int | None = None) -> int:
    """Remove PII from existing ``Signal`` rows."""
    stmt = select(Signal)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    signals = result.scalars().all()
    count = 0
    for sig in signals:
        cleaned = purge_row({"content": sig.content})["content"]
        if cleaned != sig.content:
            await session.execute(
                update(Signal).where(Signal.id == sig.id).values(content=cleaned)
            )
            count += 1
    await session.commit()
    return count
