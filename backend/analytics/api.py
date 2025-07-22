"""Analytics service exposing experiment results."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Callable, Coroutine, Dict, Iterable, cast
from collections.abc import AsyncIterator

from datetime import datetime

from functools import lru_cache
from fastapi import Depends, FastAPI, Request, Response
from backend.shared.security import require_status_api_key
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select

from backend.shared.db import AsyncSessionLocal
from backend.shared.db import models
from .auth import require_role
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared.metrics import register_metrics
from backend.shared.security import add_security_headers
from backend.shared.responses import json_cached, gzip_aiter
from backend.shared.logging import configure_logging
from backend.shared import ServiceName, add_error_handlers, configure_sentry
from backend.shared.config import settings as shared_settings
from fastapi.middleware.cors import CORSMiddleware


configure_logging()
logger = logging.getLogger(__name__)

SERVICE_NAME = os.getenv("SERVICE_NAME", ServiceName.ANALYTICS.value)
app = FastAPI(title="Analytics Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=shared_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
configure_tracing(app, SERVICE_NAME)
configure_sentry(app, SERVICE_NAME)
add_profiling(app)
add_error_handlers(app)
register_metrics(app)
add_security_headers(app)


@lru_cache(maxsize=256)
def _cached_user(x_user: str | None, client_host: str) -> str:
    """Return user identifier from ``x_user`` or ``client_host``."""
    return x_user or client_host


def _identify_user(request: Request) -> str:
    """Return identifier for logging, header ``X-User`` or client IP."""
    client_host = request.client.host if request.client else "unknown"
    return _cached_user(request.headers.get("X-User"), cast(str, client_host))


@app.middleware("http")  # type: ignore[misc]
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Ensure every request has a correlation ID."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    try:
        import sentry_sdk

        sentry_sdk.set_tag("correlation_id", correlation_id)
    except Exception:  # pragma: no cover - sentry optional
        pass
    logger.info(
        "request received",
        extra={
            "correlation_id": correlation_id,
            "user": _identify_user(request),
            "path": request.url.path,
            "method": request.method,
        },
    )
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
async def ab_test_results(ab_test_id: int) -> ABTestSummary:
    """Return aggregated A/B test results."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                func.coalesce(func.sum(models.ABTestResult.conversions), 0),
                func.coalesce(func.sum(models.ABTestResult.impressions), 0),
            ).filter(models.ABTestResult.ab_test_id == ab_test_id)
        )
        conversions, impressions = result.one()
    return ABTestSummary(
        ab_test_id=ab_test_id,
        conversions=conversions,
        impressions=impressions,
    )


@app.get("/ab_test_results/{ab_test_id}/export")  # type: ignore[misc]
async def export_ab_test_results(
    ab_test_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> StreamingResponse:
    """
    Return all A/B test result rows for ``ab_test_id`` as CSV.

    The optional ``start`` and ``end`` query parameters bound the timestamp
    range of exported rows.
    """

    async def _iter() -> AsyncIterator[str]:
        yield "timestamp,conversions,impressions\n"
        async with AsyncSessionLocal() as session:
            stmt = (
                select(models.ABTestResult)
                .filter(models.ABTestResult.ab_test_id == ab_test_id)
                .order_by(models.ABTestResult.timestamp)
                .execution_options(yield_per=1000)
            )
            if start is not None:
                stmt = stmt.filter(models.ABTestResult.timestamp >= start)
            if end is not None:
                stmt = stmt.filter(models.ABTestResult.timestamp <= end)
            result = await session.stream_scalars(stmt)
            async for r in result:
                yield f"{r.timestamp.isoformat()},{r.conversions},{r.impressions}\n"

    return StreamingResponse(
        gzip_aiter(_iter()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=ab_test_{ab_test_id}.csv",
            "Content-Encoding": "gzip",
        },
    )


@app.get("/marketplace_metrics/{listing_id}")  # type: ignore[misc]
async def marketplace_metrics(listing_id: int) -> MarketplaceSummary:
    """Return aggregated metrics for a listing."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                func.coalesce(func.sum(models.MarketplaceMetric.clicks), 0),
                func.coalesce(func.sum(models.MarketplaceMetric.purchases), 0),
                func.coalesce(func.sum(models.MarketplaceMetric.revenue), 0.0),
            ).filter(models.MarketplaceMetric.listing_id == listing_id)
        )
        clicks, purchases, revenue = result.one()
    return MarketplaceSummary(
        listing_id=listing_id,
        clicks=clicks,
        purchases=purchases,
        revenue=revenue,
    )


@app.get("/low_performers")  # type: ignore[misc]
async def low_performers(limit: int = 10, offset: int = 0) -> list[LowPerformer]:
    """Return listings with the lowest total revenue."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                models.MarketplaceMetric.listing_id,
                func.coalesce(func.sum(models.MarketplaceMetric.revenue), 0.0).label(
                    "rev"
                ),
            )
            .group_by(models.MarketplaceMetric.listing_id)
            .order_by("rev")
            .offset(offset)
            .limit(limit)
        )
        rows = result.all()
    return [LowPerformer(listing_id=row[0], revenue=row[1]) for row in rows]


@app.get("/marketplace_metrics/{listing_id}/export")  # type: ignore[misc]
async def export_marketplace_metrics(
    listing_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> StreamingResponse:
    """
    Return all marketplace metrics rows for ``listing_id`` as CSV.

    ``start`` and ``end`` bound the timestamp range of exported rows.
    """

    async def _iter() -> AsyncIterator[str]:
        yield "timestamp,clicks,purchases,revenue\n"
        async with AsyncSessionLocal() as session:
            stmt = (
                select(models.MarketplaceMetric)
                .filter(models.MarketplaceMetric.listing_id == listing_id)
                .order_by(models.MarketplaceMetric.timestamp)
                .execution_options(yield_per=1000)
            )
            if start is not None:
                stmt = stmt.filter(models.MarketplaceMetric.timestamp >= start)
            if end is not None:
                stmt = stmt.filter(models.MarketplaceMetric.timestamp <= end)
            result = await session.stream_scalars(stmt)
            async for r in result:
                yield (
                    f"{r.timestamp.isoformat()},{r.clicks},{r.purchases},{r.revenue}\n"
                )

    return StreamingResponse(
        gzip_aiter(_iter()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=listing_{listing_id}.csv",
            "Content-Encoding": "gzip",
        },
    )


@app.get("/performance_metrics/{listing_id}/export")  # type: ignore[misc]
async def export_performance_metrics(
    listing_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> StreamingResponse:
    """
    Return all performance metrics rows for ``listing_id`` as CSV.

    Use ``start`` and ``end`` to bound the timestamp range.
    """

    async def _iter() -> AsyncIterator[str]:
        yield "timestamp,views,favorites,orders,revenue\n"
        async with AsyncSessionLocal() as session:
            stmt = (
                select(models.MarketplacePerformanceMetric)
                .filter(models.MarketplacePerformanceMetric.listing_id == listing_id)
                .order_by(models.MarketplacePerformanceMetric.timestamp)
                .execution_options(yield_per=1000)
            )
            if start is not None:
                stmt = stmt.filter(
                    models.MarketplacePerformanceMetric.timestamp >= start
                )
            if end is not None:
                stmt = stmt.filter(models.MarketplacePerformanceMetric.timestamp <= end)
            result = await session.stream_scalars(stmt)
            async for r in result:
                yield (
                    f"{r.timestamp.isoformat()},{r.views},{r.favorites},{r.orders},{r.revenue}\n"
                )

    return StreamingResponse(
        gzip_aiter(_iter()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=performance_{listing_id}.csv",
            "Content-Encoding": "gzip",
        },
    )


@app.get("/health")  # type: ignore[misc]
async def health() -> Response:
    """Return service liveness."""
    return json_cached({"status": "ok"})


@app.get("/ready")  # type: ignore[misc]
async def ready(request: Request) -> Response:
    """Return service readiness."""
    require_status_api_key(request)
    return json_cached({"status": "ready"})
