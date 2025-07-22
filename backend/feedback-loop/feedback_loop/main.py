"""HTTP service for the feedback loop scheduler."""

from __future__ import annotations

import logging
import os
import sys
import uuid
from typing import Any, Callable, Coroutine, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from backend.shared.security import require_status_api_key
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from backend.shared.metrics import register_metrics
from backend.shared.security import add_security_headers
from backend.shared.responses import json_cached
from backend.shared.tracing import configure_tracing
from pydantic import BaseModel

from .ab_testing import ABTestManager
from .auth import require_role
from backend.shared.config import settings as shared_settings
from .settings import settings

app = FastAPI(title="Feedback Loop")
app.add_middleware(
    CORSMiddleware,
    allow_origins=shared_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
configure_tracing(app, "feedback-loop")
register_metrics(app)
add_security_headers(app)
logger = logging.getLogger(__name__)

# BackgroundScheduler instance running application tasks
scheduler: Optional[BackgroundScheduler] = None


class AllocationResponse(BaseModel):
    """Budget allocation response payload."""

    variant_a: float
    variant_b: float


class StatsResponse(BaseModel):
    """Conversion totals for A/B test variants."""

    conversions_a: int
    conversions_b: int


manager = ABTestManager(
    database_url=os.environ.get("ABTEST_DB_URL", "sqlite:///abtest.db")
)


async def startup() -> None:
    """Start background scheduler and setup exception logging."""
    global scheduler
    # Import here to avoid heavy dependencies at module import time
    from .scheduler import setup_scheduler
    from .ingestion import schedule_marketplace_ingestion

    listing_env = os.environ.get("MARKETPLACE_LISTING_IDS", "")
    listing_ids = [int(i) for i in listing_env.split(",") if i.strip()]
    scoring_api = os.environ.get("SCORING_ENGINE_URL", "")
    scheduler = setup_scheduler([], scoring_api)
    if listing_ids:
        schedule_marketplace_ingestion(
            scheduler,
            listing_ids,
            scoring_api,
            interval_minutes=settings.publisher_metrics_interval_minutes,
        )
    scheduler.start()

    def log_unhandled(
        exc_type: type[BaseException], exc: BaseException, tb: object
    ) -> None:
        """Log any unhandled exception before exiting."""
        logger.exception("Unhandled exception", exc_info=(exc_type, exc, tb))

    sys.excepthook = log_unhandled


async def shutdown() -> None:
    """Stop the background scheduler."""
    if scheduler:
        scheduler.shutdown()


app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)


@app.middleware("http")
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Ensure each request has a correlation ID."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    logger.info("request received", extra={"correlation_id": correlation_id})
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.get("/health")
async def health() -> Response:
    """Return service liveness."""
    return json_cached({"status": "ok"})


@app.get("/ready")
async def ready(request: Request) -> Response:
    """Return service readiness."""
    require_status_api_key(request)
    return json_cached({"status": "ready"})


def _validate_variant(variant: str) -> None:
    """Ensure the variant parameter is valid."""
    if variant not in {"A", "B"}:
        raise HTTPException(status_code=400, detail="invalid variant")


@app.post("/impression")
async def record_impression(
    variant: str,
    payload: dict[str, Any] = Depends(require_role("editor")),
) -> dict[str, str]:
    """Persist a variant impression."""
    _validate_variant(variant)
    manager.record_result(variant, success=False)
    return {"status": "recorded"}


@app.post("/conversion")
async def record_conversion(
    variant: str,
    payload: dict[str, Any] = Depends(require_role("editor")),
) -> dict[str, str]:
    """Persist a variant conversion."""
    _validate_variant(variant)
    manager.record_result(variant, success=True)
    return {"status": "recorded"}


@app.get("/allocation", response_model=AllocationResponse)
async def get_allocation(
    total_budget: float = 100.0,
    payload: dict[str, Any] = Depends(require_role("admin")),
) -> AllocationResponse:
    """Return promotion budget allocation using Thompson Sampling."""
    allocation = manager.allocate_budget(total_budget)
    return AllocationResponse(
        variant_a=allocation.variant_a, variant_b=allocation.variant_b
    )


@app.get("/stats", response_model=StatsResponse)
async def get_stats(
    payload: dict[str, Any] = Depends(require_role("admin")),
) -> StatsResponse:
    """Return total conversions for both variants."""
    totals = manager.conversion_totals()
    return StatsResponse(
        conversions_a=totals["A"],
        conversions_b=totals["B"],
    )


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "feedback_loop.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
