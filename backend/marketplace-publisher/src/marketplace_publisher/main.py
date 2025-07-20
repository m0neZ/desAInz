"""Run the marketplace publisher service."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Callable, Coroutine, cast

from backend.shared import (
    add_error_handlers,
    configure_sentry,
    init_feature_flags,
    is_enabled,
)
from backend.shared.config import settings as shared_settings
from backend.shared.db import models as shared_models
from backend.shared.db import session_scope
from backend.shared.metrics import register_metrics
from backend.shared.profiling import add_profiling
from backend.shared.tracing import configure_tracing

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, ConfigDict

from backend.shared.cache import get_async_client

from sqlalchemy import func, update

from . import notifications
from .db import (
    Marketplace,
    PublishStatus,
    PublishTask,
    SessionLocal,
    create_task,
    get_listing,
    get_task,
    init_db,
    update_listing,
)
from .logging_config import configure_logging
from .pricing import create_listing_metadata
from .publisher import publish_with_retry
from .rate_limiter import MarketplaceRateLimiter
from .rules import load_rules, validate_mockup
from .settings import settings

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=shared_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
configure_tracing(app, settings.app_name)
configure_sentry(app, settings.app_name)
add_profiling(app)
add_error_handlers(app)


def _identify_user(request: Request) -> str:
    """Return identifier for logging, header ``X-User`` or client IP."""
    return cast(str, request.headers.get("X-User", request.client.host))


rate_limiter = MarketplaceRateLimiter(
    {
        Marketplace.redbubble: settings.rate_limit_redbubble,
        Marketplace.amazon_merch: settings.rate_limit_amazon_merch,
        Marketplace.etsy: settings.rate_limit_etsy,
        Marketplace.society6: settings.rate_limit_society6,
    },
    settings.rate_limit_window,
    None,
)


@app.on_event("startup")
async def startup() -> None:
    """Initialize database tables and load rules."""
    await init_db()
    rules_path = (
        Path(__file__).resolve().parent.parent.parent
        / "config"
        / "marketplace_rules.yaml"
    )
    load_rules(rules_path, watch=True)
    init_feature_flags()


@app.middleware("http")
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Ensure every request contains a correlation ID."""
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


register_metrics(app)


class PublishRequest(BaseModel):
    """Request body for initiating a publish task."""

    marketplace: Marketplace
    design_path: Path
    score: float = 0.0
    metadata: dict[str, Any] = {}


class WebhookPayload(BaseModel):
    """Payload for marketplace callbacks."""

    task_id: int
    status: str


class MetadataPatch(BaseModel):
    """Arbitrary metadata payload."""

    model_config = ConfigDict(extra="allow")


class ListingPatch(BaseModel):
    """Fields allowed when updating a listing."""

    model_config = ConfigDict(extra="forbid")
    price: float | None = None
    state: str | None = None


async def _background_publish(task_id: int) -> None:
    """Run publishing using the latest task metadata."""
    async with SessionLocal() as session:
        task = await get_task(session, task_id)
        if task is None:
            logger.error("publish task %s not found", task_id)
            return
        metadata = {}
        if task.metadata_json:
            try:
                metadata = json.loads(task.metadata_json)
            except json.JSONDecodeError:
                logger.warning("invalid metadata for task %s", task_id)
        success = await publish_with_retry(
            session,
            task_id,
            task.marketplace,
            Path(task.design_path),
            metadata,
            settings.max_attempts,
        )
        refreshed = await get_task(session, task_id)
        if (
            not success
            and refreshed is not None
            and refreshed.attempts < settings.max_attempts
        ):
            asyncio.create_task(_background_publish(task_id))


@app.post("/publish")
async def publish(req: PublishRequest, background: BackgroundTasks) -> dict[str, int]:
    """Create a publish task and run it in the background."""
    if req.marketplace == Marketplace.society6 and not is_enabled(
        "society6_integration"
    ):
        raise HTTPException(status_code=403, detail="Society6 integration disabled")
    if req.marketplace == Marketplace.zazzle and not is_enabled("zazzle_integration"):
        raise HTTPException(status_code=403, detail="Zazzle integration disabled")
    allowed = await rate_limiter.acquire(req.marketplace)
    if not allowed:
        logger.warning(
            "rate limit exceeded", extra={"marketplace": req.marketplace.value}
        )
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    try:
        validate_mockup(req.marketplace, req.design_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    async with SessionLocal() as session:
        metadata = create_listing_metadata(req.score, req.marketplace, req.metadata)
        task = await create_task(
            session,
            marketplace=req.marketplace,
            design_path=str(req.design_path),
            metadata_json=metadata,
        )
    background.add_task(_background_publish, task.id)
    return {"task_id": task.id}


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: int) -> dict[str, Any]:
    """Return current status of a publish task."""
    async with SessionLocal() as session:
        task = await get_task(session, task_id)
        if task is None:
            raise HTTPException(status_code=404)
        return {"status": task.status, "attempts": task.attempts}


@app.post("/webhooks/{marketplace}")
async def handle_webhook(
    marketplace: Marketplace, payload: WebhookPayload
) -> dict[str, str]:
    """Process listing status callbacks."""
    async with SessionLocal() as session:
        task = await get_task(session, payload.task_id)
        if task is None or task.marketplace != marketplace:
            raise HTTPException(status_code=404)
        await notifications.record_webhook(session, payload.task_id, payload.status)
    return {"status": "updated"}


@app.patch("/tasks/{task_id}")
async def update_task_metadata(task_id: int, body: MetadataPatch) -> dict[str, str]:
    """Update metadata for a pending publish task."""
    async with SessionLocal() as session:
        task = await get_task(session, task_id)
        if task is None:
            raise HTTPException(status_code=404)
        if task.status != PublishStatus.pending:
            raise HTTPException(status_code=400, detail="Task already started")
        await session.execute(
            update(PublishTask)
            .where(PublishTask.id == task_id)
            .values(metadata_json=json.dumps(body.model_dump()))
        )
        await session.commit()
    return {"status": "updated"}


@app.post("/tasks/{task_id}/retry")
async def retry_task(task_id: int, background: BackgroundTasks) -> dict[str, str]:
    """Re-trigger publishing for a task."""
    async with SessionLocal() as session:
        task = await get_task(session, task_id)
        if task is None:
            raise HTTPException(status_code=404)
    background.add_task(_background_publish, task_id)
    return {"status": "scheduled"}


@app.get("/listings/{listing_id}")
async def get_listing_details(listing_id: int) -> dict[str, Any]:
    """Return listing information for ``listing_id``."""
    async with SessionLocal() as session:
        listing = await get_listing(session, listing_id)
        if listing is None:
            raise HTTPException(status_code=404)
        return {
            "id": listing.id,
            "mockup_id": listing.mockup_id,
            "price": listing.price,
            "state": listing.state,
            "created_at": listing.created_at.isoformat(),
        }


@app.patch("/listings/{listing_id}")
async def patch_listing(listing_id: int, body: ListingPatch) -> dict[str, str]:
    """Update fields on ``listing_id``."""
    async with SessionLocal() as session:
        listing = await get_listing(session, listing_id)
        if listing is None:
            raise HTTPException(status_code=404)
        updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
        await update_listing(session, listing_id, **updates)
    return {"status": "updated"}


@app.get("/metrics/{listing_id}")
async def metrics(listing_id: int) -> dict[str, float]:
    """Return aggregated performance metrics for a listing."""
    with session_scope() as session:
        views, favorites, orders, revenue = (
            session.query(
                func.coalesce(
                    func.sum(shared_models.MarketplacePerformanceMetric.views), 0
                ),
                func.coalesce(
                    func.sum(shared_models.MarketplacePerformanceMetric.favorites), 0
                ),
                func.coalesce(
                    func.sum(shared_models.MarketplacePerformanceMetric.orders), 0
                ),
                func.coalesce(
                    func.sum(shared_models.MarketplacePerformanceMetric.revenue), 0.0
                ),
            )
            .filter(shared_models.MarketplacePerformanceMetric.listing_id == listing_id)
            .one()
        )
    if views == 0 and favorites == 0 and orders == 0 and revenue == 0:
        raise HTTPException(status_code=404)
    return {
        "views": float(views),
        "favorites": float(favorites),
        "orders": float(orders),
        "revenue": float(revenue),
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Run the marketplace publisher service."
    )
    parser.add_argument(
        "--no-selenium", action="store_true", help="Disable Selenium fallback"
    )
    args = parser.parse_args()
    if args.no_selenium:
        os.environ["SELENIUM_SKIP"] = "1"

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level,
    )
