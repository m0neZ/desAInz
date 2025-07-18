"""HTTP service for the feedback loop scheduler."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Callable, Coroutine

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

from .ab_testing import ABTestManager

app = FastAPI(title="Feedback Loop")
logger = logging.getLogger(__name__)


class AllocationResponse(BaseModel):
    """Budget allocation response payload."""

    variant_a: float
    variant_b: float


manager = ABTestManager(
    database_url=os.environ.get("ABTEST_DB_URL", "sqlite:///abtest.db")
)


async def startup() -> None:
    """Start background scheduler."""
    # Import here to avoid heavy dependencies at module import time
    from .scheduler import setup_scheduler

    # Setup scheduler with no-op defaults for health endpoints
    scheduler = setup_scheduler([], "")
    scheduler.start()


app.add_event_handler("startup", startup)


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
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}


def _validate_variant(variant: str) -> None:
    """Ensure the variant parameter is valid."""
    if variant not in {"A", "B"}:
        raise HTTPException(status_code=400, detail="invalid variant")


@app.post("/impression")
async def record_impression(variant: str) -> dict[str, str]:
    """Persist a variant impression."""
    _validate_variant(variant)
    manager.record_result(variant, success=False)
    return {"status": "recorded"}


@app.post("/conversion")
async def record_conversion(variant: str) -> dict[str, str]:
    """Persist a variant conversion."""
    _validate_variant(variant)
    manager.record_result(variant, success=True)
    return {"status": "recorded"}


@app.get("/allocation", response_model=AllocationResponse)
async def get_allocation(total_budget: float = 100.0) -> AllocationResponse:
    """Return promotion budget allocation using Thompson Sampling."""
    allocation = manager.allocate_budget(total_budget)
    return AllocationResponse(
        variant_a=allocation.variant_a, variant_b=allocation.variant_b
    )


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "feedback_loop.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
