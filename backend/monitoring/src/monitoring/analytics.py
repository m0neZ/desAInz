"""Database analytics helpers."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func

from backend.shared.db import session_scope
from backend.shared.db.models import ABTestResult, MarketplaceMetric


def ab_test_summary() -> list[dict[str, Any]]:
    """Return aggregated A/B test results."""
    with session_scope() as session:
        rows = (
            session.query(
                ABTestResult.ab_test_id,
                func.sum(ABTestResult.impressions),
                func.sum(ABTestResult.conversions),
            )
            .group_by(ABTestResult.ab_test_id)
            .all()
        )
    return [
        {
            "ab_test_id": r[0],
            "impressions": int(r[1] or 0),
            "conversions": int(r[2] or 0),
        }
        for r in rows
    ]


def marketplace_summary() -> list[dict[str, Any]]:
    """Return aggregated marketplace metrics."""
    with session_scope() as session:
        rows = (
            session.query(
                MarketplaceMetric.listing_id,
                func.sum(MarketplaceMetric.revenue),
                func.sum(MarketplaceMetric.impressions),
            )
            .group_by(MarketplaceMetric.listing_id)
            .all()
        )
    return [
        {
            "listing_id": r[0],
            "revenue": float(r[1] or 0),
            "impressions": int(r[2] or 0),
        }
        for r in rows
    ]
