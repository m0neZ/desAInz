"""Analytics service exposing experiment results."""

from __future__ import annotations

from typing import Any, Callable, Dict, Generator, cast

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import func

from jose import JWTError, jwt
from sqlalchemy import select

from backend.shared.db import SessionLocal, session_scope
from backend.shared.db import models
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling

SECRET_KEY = "change_this"
ALGORITHM = "HS256"
auth_scheme = HTTPBearer()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> Dict[str, Any]:
    """Verify JWT and return payload."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
        ) from exc
    return cast(Dict[str, Any], payload)


def require_role(required_role: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Return dependency ensuring user has ``required_role``."""

    def _checker(payload: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
        username = cast(str | None, payload.get("sub"))
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
            )
        with session_scope() as session:
            role = session.execute(
                select(models.UserRole.role).where(models.UserRole.username == username)
            ).scalar_one_or_none()
        if role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role"
            )
        return payload

    return _checker


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


@app.get("/ab_test_results/{ab_test_id}/csv")  # type: ignore[misc]
def ab_test_results_csv(
    ab_test_id: int,
    payload: Dict[str, Any] = Depends(require_role("editor")),
) -> StreamingResponse:
    """Return raw A/B test results as CSV."""
    with SessionLocal() as session:
        rows = (
            session.query(
                models.ABTestResult.timestamp,
                models.ABTestResult.conversions,
                models.ABTestResult.impressions,
            )
            .filter(models.ABTestResult.ab_test_id == ab_test_id)
            .order_by(models.ABTestResult.timestamp)
            .all()
        )

    def _generate() -> Generator[str, None, None]:
        yield "timestamp,conversions,impressions\n"
        for row in rows:
            yield f"{row.timestamp.isoformat()},{row.conversions},{row.impressions}\n"

    headers = {"Content-Disposition": "attachment; filename=ab_test_results.csv"}
    return StreamingResponse(_generate(), media_type="text/csv", headers=headers)


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


@app.get("/marketplace_metrics/{listing_id}/csv")  # type: ignore[misc]
def marketplace_metrics_csv(
    listing_id: int,
    payload: Dict[str, Any] = Depends(require_role("editor")),
) -> StreamingResponse:
    """Return raw marketplace metrics as CSV."""
    with SessionLocal() as session:
        rows = (
            session.query(
                models.MarketplaceMetric.timestamp,
                models.MarketplaceMetric.clicks,
                models.MarketplaceMetric.purchases,
                models.MarketplaceMetric.revenue,
            )
            .filter(models.MarketplaceMetric.listing_id == listing_id)
            .order_by(models.MarketplaceMetric.timestamp)
            .all()
        )

    def _generate() -> Generator[str, None, None]:
        yield "timestamp,clicks,purchases,revenue\n"
        for row in rows:
            yield (
                f"{row.timestamp.isoformat()},"
                f"{row.clicks},{row.purchases},{row.revenue}\n"
            )

    headers = {
        "Content-Disposition": "attachment; filename=marketplace_metrics.csv",
    }
    return StreamingResponse(_generate(), media_type="text/csv", headers=headers)


@app.get("/health")  # type: ignore[misc]
async def health() -> Dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")  # type: ignore[misc]
async def ready() -> Dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}
