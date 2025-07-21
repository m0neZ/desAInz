#!/usr/bin/env python
"""Generate a daily summary report for desAInz."""

from __future__ import annotations

import sys
from pathlib import Path

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Callable, ContextManager, Mapping

from sqlalchemy import func, select

from backend.shared.db import session_scope
from sqlalchemy.orm import Session
from backend.shared.db.models import Idea, Mockup


def _ideas_count(session: Session, since: datetime) -> int:
    """Return number of ideas created since ``since`` using ``session``."""
    stmt = select(func.count()).select_from(Idea).where(Idea.created_at >= since)
    return session.scalar(stmt) or 0


def _mockups_count(session: Session, since: datetime) -> int:
    """Return number of mockups created since ``since`` using ``session``."""
    stmt = select(func.count()).select_from(Mockup).where(Mockup.created_at >= since)
    return session.scalar(stmt) or 0


async def _marketplace_stats(since: datetime) -> Mapping[str, int]:
    """Return count of successful publish tasks per marketplace."""
    stats: dict[str, int] = defaultdict(int)
    sys.path.append(
        str(
            Path(__file__).resolve().parents[1]
            / "backend"
            / "marketplace-publisher"
            / "src"
        )
    )
    from marketplace_publisher.db import (
        PublishStatus,
        PublishTask,
        SessionLocal,
    )

    async with SessionLocal() as session:
        stmt = (
            select(PublishTask.marketplace, func.count())
            .where(
                PublishTask.status == PublishStatus.success,
                PublishTask.created_at >= since,
            )
            .group_by(PublishTask.marketplace)
        )
        result = await session.execute(stmt)
        for marketplace, count in result.all():
            stats[marketplace.value] = count
    return stats


async def generate_daily_summary(
    session_provider: Callable[[], ContextManager[Session]] = session_scope,
) -> Mapping[str, object]:
    """Return metrics on ideas and mockups from the last 24 hours."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=1)

    with session_provider() as session:
        ideas = _ideas_count(session, since)
        mockups = _mockups_count(session, since)
    mockup_rate = float(mockups / ideas) if ideas else 0.0
    stats = await _marketplace_stats(since)
    return {
        "ideas_generated": ideas,
        "mockup_success_rate": mockup_rate,
        "marketplace_stats": stats,
    }


if __name__ == "__main__":  # pragma: no cover
    import asyncio
    import json

    summary = asyncio.run(generate_daily_summary())
    print(json.dumps(summary, indent=2))
