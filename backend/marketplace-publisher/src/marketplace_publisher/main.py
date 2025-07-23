"""Run the marketplace publisher service."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import logging
import os
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Coroutine, cast

from backend.shared import (
    add_error_handlers,
    configure_sentry,
    init_feature_flags,
    is_enabled,
)
from backend.shared.cache import get_async_client
from backend.shared.config import settings as shared_settings
from backend.shared.db import models as shared_models
from backend.shared.db import run_migrations_if_needed, session_scope
from backend.shared.metrics import register_metrics
from backend.shared.profiling import add_profiling
from backend.shared.responses import json_cached
from backend.shared.http import close_async_clients
from backend.shared.security import add_security_headers
from backend.shared.tracing import configure_tracing

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from backend.shared.security import require_status_api_key
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict  # noqa: I201

from sqlalchemy import func, update

from . import notifications, publisher
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
from .publisher import publish_with_retry, validate_mockup
from .rate_limiter import MarketplaceRateLimiter
from .rules import load_default_rules
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


@lru_cache(maxsize=256)
def _cached_user(x_user: str | None, client_host: str) -> str:
    """Return user identifier from ``x_user`` or ``client_host``."""
    return x_user or client_host


def _identify_user(request: Request) -> str:
    """Return identifier for logging, header ``X-User`` or client IP."""
    client_host = cast(str, request.client.host)
    return _cached_user(request.headers.get("X-User"), client_host)


async def _verify_signature(request: Request, marketplace: Marketplace) -> None:
    """Validate the ``X-Signature`` header for ``marketplace``."""
    secret = settings.webhook_secrets.get(marketplace)
    if secret is None:
        raise HTTPException(status_code=500, detail="Webhook secret missing")
    signature = request.headers.get("X-Signature")
    if signature is None:
        raise HTTPException(status_code=403, detail="Missing signature")
    body = await request.body()
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=403, detail="Invalid signature")


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
    await run_migrations_if_needed(
        "backend/shared/db/alembic_marketplace_publisher.ini"
    )
    await init_db()
    load_default_rules(watch=True)
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
add_security_headers(app)


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
        listing_id = await publish_with_retry(
            session,
            task_id,
            task.marketplace,
            Path(task.design_path),
            metadata,
            settings.max_attempts,
        )
        refreshed = await get_task(session, task_id)
        if (
            listing_id is None
            and refreshed is not None
            and refreshed.attempts < settings.max_attempts
        ):
            asyncio.create_task(_background_publish(task_id))
        if listing_id is not None and listing_id not in {"nsfw", "trademarked"}:
            client = publisher.CLIENTS[task.marketplace]
            data = await asyncio.to_thread(client.get_listing_metrics, int(listing_id))
            with session_scope() as sync:
                sync.add(
                    shared_models.MarketplacePerformanceMetric(
                        listing_id=int(listing_id),
                        views=int(data.get("views", 0)),
                        favorites=int(data.get("favorites", 0)),
                        orders=int(data.get("orders", 0)),
                        revenue=float(data.get("revenue", 0.0)),
                    )
                )
        elif listing_id in {"nsfw", "trademarked"}:
            try:
                from monitoring.pagerduty import notify_listing_issue

                await asyncio.to_thread(notify_listing_issue, task_id, "flagged")
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("listing flag notification failed: %s", exc)


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
        reason = validate_mockup(req.marketplace, req.design_path, req.metadata or {})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if reason is not None:
        raise HTTPException(status_code=400, detail=reason)
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
    marketplace: Marketplace, request: Request, payload: WebhookPayload
) -> dict[str, str]:
    """Process listing status callbacks."""
    await _verify_signature(request, marketplace)
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
async def health() -> Response:
    """Return service liveness."""
    return json_cached({"status": "ok"})


@app.get("/ready")
async def ready(request: Request) -> Response:
    """Return service readiness."""
    require_status_api_key(request)
    return json_cached({"status": "ready"})


@app.get("/oauth/{marketplace}")
async def oauth_login(marketplace: Marketplace) -> dict[str, str]:
    """Return the authorization URL for ``marketplace``."""
    client = publisher.CLIENTS[marketplace]
    url = await asyncio.to_thread(client.get_authorization_url)
    return {"authorization_url": url}


@app.get("/oauth/{marketplace}/callback")
async def oauth_callback(marketplace: Marketplace, request: Request) -> dict[str, str]:
    """Handle OAuth redirect and persist tokens."""
    client = publisher.CLIENTS[marketplace]
    await asyncio.to_thread(client.fetch_token, str(request.url))
    return {"status": "authorized"}


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Release HTTP clients on application shutdown."""
    await close_async_clients()


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

    import uvloop
    import uvicorn

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level,
    )
