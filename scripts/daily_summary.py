#!/usr/bin/env python
# flake8: noqa
"""Generate a daily summary report for desAInz."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Mapping

import sys
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).resolve().parents[1]
        / "backend"
        / "marketplace-publisher"
        / "src"
    )
)

from sqlalchemy import func, select

from backend.shared.db import session_scope
from backend.shared.db.models import Idea, Mockup


def _ideas_count(since: datetime) -> int:
    """Return number of ideas created since ``since``."""
    with session_scope() as session:
        stmt = select(func.count()).select_from(Idea).where(Idea.created_at >= since)
        return session.scalar(stmt) or 0


def _mockups_count(since: datetime) -> int:
    """Return number of mockups created since ``since``."""
    with session_scope() as session:
        stmt = (
            select(func.count()).select_from(Mockup).where(Mockup.created_at >= since)
        )
        return session.scalar(stmt) or 0


async def _marketplace_stats(since: datetime) -> Mapping[str, int]:
    """Return count of successful publish tasks per marketplace."""
    stats: dict[str, int] = defaultdict(int)
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


async def generate_daily_summary() -> Mapping[str, object]:
    """Compute idea count, mockup success rate, and marketplace stats."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=1)

    ideas = _ideas_count(since)
    mockups = _mockups_count(since)
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
