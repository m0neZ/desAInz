"""Analytics service exposing experiment results."""

from __future__ import annotations

import csv
import io
import logging
import uuid
from typing import Any, Callable, Coroutine, Dict, Iterable

from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func

from backend.shared.db import SessionLocal
from backend.shared.db import models
from .auth import require_role
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared.logging import configure_logging


configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Analytics Service")
configure_tracing(app, "analytics")
add_profiling(app)


@app.middleware("http")
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Ensure every request has a correlation ID."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    logger.info("request received", extra={"correlation_id": correlation_id})
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


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


class LowPerformer(BaseModel):  # type: ignore[misc]
    """Listing with the lowest revenue."""

    listing_id: int
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


@app.get("/ab_test_results/{ab_test_id}/export")  # type: ignore[misc]
def export_ab_test_results(
    ab_test_id: int,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> StreamingResponse:
    """Return all A/B test result rows for ``ab_test_id`` as CSV."""
    with SessionLocal() as session:
        rows = (
            session.query(models.ABTestResult)
            .filter(models.ABTestResult.ab_test_id == ab_test_id)
            .all()
        )

    def _iter() -> Iterable[str]:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["timestamp", "conversions", "impressions"])
        for r in rows:
            writer.writerow([r.timestamp.isoformat(), r.conversions, r.impressions])
        buffer.seek(0)
        yield buffer.read()

    return StreamingResponse(
        _iter(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=ab_test_{ab_test_id}.csv"
        },
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


@app.get("/low_performers")  # type: ignore[misc]
def low_performers(limit: int = 10) -> list[LowPerformer]:
    """Return listings with the lowest total revenue."""
    with SessionLocal() as session:
        rows = (
            session.query(
                models.MarketplaceMetric.listing_id,
                func.coalesce(func.sum(models.MarketplaceMetric.revenue), 0.0).label(
                    "rev"
                ),
            )
            .group_by(models.MarketplaceMetric.listing_id)
            .order_by("rev")
            .limit(limit)
            .all()
        )
    return [LowPerformer(listing_id=row[0], revenue=row[1]) for row in rows]


@app.get("/marketplace_metrics/{listing_id}/export")  # type: ignore[misc]
def export_marketplace_metrics(
    listing_id: int,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> StreamingResponse:
    """Return all marketplace metrics rows for ``listing_id`` as CSV."""
    with SessionLocal() as session:
        rows = (
            session.query(models.MarketplaceMetric)
            .filter(models.MarketplaceMetric.listing_id == listing_id)
            .all()
        )

    def _iter() -> Iterable[str]:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["timestamp", "clicks", "purchases", "revenue"])
        for r in rows:
            writer.writerow([r.timestamp.isoformat(), r.clicks, r.purchases, r.revenue])
        buffer.seek(0)
        yield buffer.read()

    return StreamingResponse(
        _iter(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=listing_{listing_id}.csv"
        },
    )


@app.get("/health")  # type: ignore[misc]
async def health() -> Dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")  # type: ignore[misc]
async def ready() -> Dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}
