"""Run the marketplace publisher service."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, Callable, Coroutine
import json

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from redis.asyncio import Redis

from .logging_config import configure_logging
from .settings import settings
from .rate_limiter import MarketplaceRateLimiter
from sqlalchemy import update

from .db import (
    Marketplace,
    PublishStatus,
    PublishTask,
    SessionLocal,
    create_task,
    get_task,
    init_db,
    update_task_status,
)
from .rules import load_rules, validate_mockup
from .publisher import publish_with_retry
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared import init_feature_flags, is_enabled
from backend.shared import add_error_handlers, configure_sentry

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
configure_tracing(app, settings.app_name)
configure_sentry(app, settings.app_name)
add_profiling(app)
add_error_handlers(app)

rate_limiter = MarketplaceRateLimiter(
    Redis.from_url(settings.redis_url),
    {
        Marketplace.redbubble: settings.rate_limit_redbubble,
        Marketplace.amazon_merch: settings.rate_limit_amazon_merch,
        Marketplace.etsy: settings.rate_limit_etsy,
        Marketplace.society6: settings.rate_limit_society6,
    },
    settings.rate_limit_window,
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
    load_rules(rules_path)
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

    logger.info("request received", extra={"correlation_id": correlation_id})
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


class PublishRequest(BaseModel):
    """Request body for initiating a publish task."""

    marketplace: Marketplace
    design_path: Path
    metadata: dict[str, Any] = {}


class WebhookPayload(BaseModel):
    """Payload for marketplace callbacks."""

    task_id: int
    status: str


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
        await publish_with_retry(
            session,
            task_id,
            task.marketplace,
            Path(task.design_path),
            metadata,
        )


@app.post("/publish")
async def publish(req: PublishRequest, background: BackgroundTasks) -> dict[str, int]:
    """Create a publish task and run it in the background."""
    if req.marketplace == Marketplace.society6 and not is_enabled(
        "society6_integration"
    ):
        raise HTTPException(status_code=403, detail="Society6 integration disabled")
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
        task = await create_task(
            session,
            marketplace=req.marketplace,
            design_path=str(req.design_path),
            metadata_json=req.metadata,
        )
    background.add_task(_background_publish, task.id)
    return {"task_id": task.id}


@app.get("/progress/{task_id}")
async def progress(task_id: int) -> dict[str, Any]:
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
        await update_task_status(
            session, payload.task_id, PublishStatus(payload.status)
        )
    return {"status": "updated"}


@app.patch("/tasks/{task_id}")
async def update_task_metadata(task_id: int, body: dict[str, Any]) -> dict[str, str]:
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
            .values(metadata_json=json.dumps(body))
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


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level,
    )
