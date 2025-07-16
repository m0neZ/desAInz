"""Run the marketplace publisher service."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, Callable, Coroutine
import json

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

from .logging_config import configure_logging
from .settings import settings
from .db import (
    AuditAction,
    Marketplace,
    PublishStatus,
    SessionLocal,
    create_task,
    get_task,
    init_db,
    log_audit,
    PublishTask,
)
from sqlalchemy import select
from .publisher import publish_with_retry
from backend.shared.tracing import configure_tracing

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
configure_tracing(app, settings.app_name)


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


class PublishTaskOut(BaseModel):
    """Representation of a publish task."""

    id: int
    marketplace: Marketplace
    design_path: str
    metadata: dict[str, Any] | None
    status: PublishStatus
    attempts: int


class UpdateMetadataRequest(BaseModel):
    """Request body for editing publish metadata."""

    metadata: dict[str, Any]


async def _background_publish(task_id: int, req: PublishRequest) -> None:
    """Wrap background publishing."""
    async with SessionLocal() as session:
        await publish_with_retry(
            session, task_id, req.marketplace, req.design_path, req.metadata
        )


@app.post("/publish")
async def publish(req: PublishRequest, background: BackgroundTasks) -> dict[str, int]:
    """Create a publish task and run it in the background."""
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


@app.get("/tasks")
async def list_tasks() -> list[PublishTaskOut]:
    """Return all publish tasks."""
    async with SessionLocal() as session:
        result = await session.execute(select(PublishTask))
        tasks = result.scalars().all()
        return [
            PublishTaskOut(
                id=t.id,
                marketplace=t.marketplace,
                design_path=t.design_path,
                metadata=json.loads(t.metadata_json) if t.metadata_json else None,
                status=t.status,
                attempts=t.attempts,
            )
            for t in tasks
        ]


@app.put("/tasks/{task_id}")
async def update_task_metadata(
    task_id: int, req: UpdateMetadataRequest
) -> dict[str, str]:
    """Update task metadata manually."""
    async with SessionLocal() as session:
        task = await get_task(session, task_id)
        if task is None:
            raise HTTPException(status_code=404)
        old_data = json.loads(task.metadata_json) if task.metadata_json else None
        task.metadata_json = json.dumps(req.metadata)
        task.status = PublishStatus.pending
        await session.commit()
        await log_audit(
            session, task_id, AuditAction.metadata_update, old_data, req.metadata
        )
    return {"status": "updated"}


@app.post("/tasks/{task_id}/retry")
async def retry_task(task_id: int, background: BackgroundTasks) -> dict[str, str]:
    """Re-trigger publishing for a task."""
    async with SessionLocal() as session:
        task = await get_task(session, task_id)
        if task is None:
            raise HTTPException(status_code=404)
        task.status = PublishStatus.pending
        task.attempts = 0
        await session.commit()
        await log_audit(session, task_id, AuditAction.retry, None, None)

        req = PublishRequest(
            marketplace=task.marketplace,
            design_path=Path(task.design_path),
            metadata=json.loads(task.metadata_json) if task.metadata_json else {},
        )
    background.add_task(_background_publish, task_id, req)
    return {"status": "queued"}


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
