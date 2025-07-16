"""Run the marketplace publisher service."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, Callable, Coroutine

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from redis.asyncio import Redis

from .logging_config import configure_logging
from .settings import settings
from .rate_limiter import MarketplaceRateLimiter
from .db import Marketplace, SessionLocal, create_task, get_task, init_db
from .publisher import publish_with_retry
from backend.shared.tracing import configure_tracing

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
configure_tracing(app, settings.app_name)

rate_limiter = MarketplaceRateLimiter(
    Redis.from_url(settings.redis_url),
    {
        Marketplace.redbubble: settings.rate_limit_redbubble,
        Marketplace.amazon_merch: settings.rate_limit_amazon_merch,
        Marketplace.etsy: settings.rate_limit_etsy,
    },
    settings.rate_limit_window,
)


@app.on_event("startup")
async def startup() -> None:
    """Initialize database tables."""
    await init_db()


@app.middleware("http")
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Ensure every request contains a correlation ID."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    logger.info("request received", extra={"correlation_id": correlation_id})
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


class PublishRequest(BaseModel):
    """Request body for initiating a publish task."""

    marketplace: Marketplace
    design_path: Path
    metadata: dict[str, Any] = {}


async def _background_publish(task_id: int, req: PublishRequest) -> None:
    """Wrap background publishing."""
    async with SessionLocal() as session:
        await publish_with_retry(
            session, task_id, req.marketplace, req.design_path, req.metadata
        )


@app.post("/publish")
async def publish(req: PublishRequest, background: BackgroundTasks) -> dict[str, int]:
    """Create a publish task and run it in the background."""
    allowed = await rate_limiter.acquire(req.marketplace)
    if not allowed:
        logger.warning("rate limit exceeded", extra={"marketplace": req.marketplace.value})
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    async with SessionLocal() as session:
        task = await create_task(
            session,
            marketplace=req.marketplace,
            design_path=str(req.design_path),
            metadata_json=req.metadata,
        )
    background.add_task(_background_publish, task.id, req)
    return {"task_id": task.id}


@app.get("/progress/{task_id}")
async def progress(task_id: int) -> dict[str, Any]:
    """Return current status of a publish task."""
    async with SessionLocal() as session:
        task = await get_task(session, task_id)
        if task is None:
            raise HTTPException(status_code=404)
        return {"status": task.status, "attempts": task.attempts}


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
