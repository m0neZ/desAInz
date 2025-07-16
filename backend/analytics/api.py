"""Analytics service exposing experiment results."""

from __future__ import annotations

import logging
import uuid
from typing import Callable, Coroutine, Dict

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

from backend.shared.db import SessionLocal, models
from backend.shared.logging_config import configure_logging
from backend.shared.tracing import configure_tracing

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title="Analytics Service")
configure_tracing(app, "analytics")


@app.middleware("http")
async def add_correlation_id(
    request: Request, call_next: Callable[[Request], Coroutine[None, None, Response]]
) -> Response:
    """Ensure every request contains a correlation ID."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    logger.info("request received", extra={"correlation_id": correlation_id})
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


class ABTestSummary(BaseModel):
    """Summary of results for an A/B test."""

    ab_test_id: int
    conversions: int
    impressions: int


class MarketplaceSummary(BaseModel):
    """Aggregated metrics for a listing."""

    listing_id: int
    clicks: int
    purchases: int
    revenue: float


@app.get("/ab_test_results/{ab_test_id}")
def ab_test_results(ab_test_id: int) -> ABTestSummary:
    """Return aggregated A/B test results."""
    with SessionLocal() as session:
        rows = (
            session.query(models.ABTestResult)
            .filter(models.ABTestResult.ab_test_id == ab_test_id)
            .all()
        )
    conversions = sum(r.conversions for r in rows)
    impressions = sum(r.impressions for r in rows)
    return ABTestSummary(
        ab_test_id=ab_test_id,
        conversions=conversions,
        impressions=impressions,
    )


@app.get("/marketplace_metrics/{listing_id}")
def marketplace_metrics(listing_id: int) -> MarketplaceSummary:
    """Return aggregated metrics for a listing."""
    with SessionLocal() as session:
        rows = (
            session.query(models.MarketplaceMetric)
            .filter(models.MarketplaceMetric.listing_id == listing_id)
            .all()
        )
    clicks = sum(r.clicks for r in rows)
    purchases = sum(r.purchases for r in rows)
    revenue = sum(r.revenue for r in rows)
    return MarketplaceSummary(
        listing_id=listing_id,
        clicks=clicks,
        purchases=purchases,
        revenue=revenue,
    )


@app.get("/health")
async def health() -> Dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> Dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}
