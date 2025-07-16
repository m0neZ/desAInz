"""Analytics service exposing experiment results."""

from __future__ import annotations

from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import func

from backend.shared.db import SessionLocal
from backend.shared.db import models
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling

app = FastAPI(title="Analytics Service")
configure_tracing(app, "analytics")
add_profiling(app)


class ABTestSummary(BaseModel):  # type: ignore[misc]
    """Summary of results for an A/B test."""

    ab_test_id: int
    conversions: int
    impressions: int


class MarketplaceSummary(BaseModel):  # type: ignore[misc]
    """Aggregated metrics for a listing."""

    listing_id: int
    clicks: int
    purchases: int
    revenue: float


@app.get("/ab_test_results/{ab_test_id}")  # type: ignore[misc]
def ab_test_results(ab_test_id: int) -> ABTestSummary:
    """Return aggregated A/B test results."""
    with SessionLocal() as session:
        conversions, impressions = (
            session.query(
                func.coalesce(func.sum(models.ABTestResult.conversions), 0),
                func.coalesce(func.sum(models.ABTestResult.impressions), 0),
            )
            .filter(models.ABTestResult.ab_test_id == ab_test_id)
            .one()
        )
    return ABTestSummary(
        ab_test_id=ab_test_id,
        conversions=conversions,
        impressions=impressions,
    )


@app.get("/marketplace_metrics/{listing_id}")  # type: ignore[misc]
def marketplace_metrics(listing_id: int) -> MarketplaceSummary:
    """Return aggregated metrics for a listing."""
    with SessionLocal() as session:
        clicks, purchases, revenue = (
            session.query(
                func.coalesce(func.sum(models.MarketplaceMetric.clicks), 0),
                func.coalesce(func.sum(models.MarketplaceMetric.purchases), 0),
                func.coalesce(func.sum(models.MarketplaceMetric.revenue), 0.0),
            )
            .filter(models.MarketplaceMetric.listing_id == listing_id)
            .one()
        )
    return MarketplaceSummary(
        listing_id=listing_id,
        clicks=clicks,
        purchases=purchases,
        revenue=revenue,
    )


@app.get("/health")  # type: ignore[misc]
async def health() -> Dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")  # type: ignore[misc]
async def ready() -> Dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}
