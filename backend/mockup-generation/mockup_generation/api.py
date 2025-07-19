"""FastAPI routes for managing diffusion models."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Callable, Coroutine

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.shared.logging import configure_logging
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared import add_error_handlers, configure_sentry
from backend.shared.config import settings as shared_settings
from backend.shared.metrics import register_metrics

from .model_repository import list_models, register_model, set_default
from .celery_app import app as celery_app

configure_logging()
logger = logging.getLogger(__name__)

SERVICE_NAME = os.getenv("SERVICE_NAME", "mockup-generation")
app = FastAPI(title="Mockup Generation Service")
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


class ModelCreate(BaseModel):  # type: ignore[misc]
    """Schema for registering a new model."""

    name: str
    version: str
    model_id: str
    details: dict[str, object] | None = None
    is_default: bool = False


def _identify_user(request: Request) -> str:
    """Return identifier for logging, header ``X-User`` or client IP."""
    return str(request.headers.get("X-User", request.client.host))


@app.middleware("http")
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Ensure each request includes a correlation ID."""
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


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}


@app.get("/models")
async def get_models() -> list[dict[str, object]]:
    """Return all registered models."""
    return [m.__dict__ for m in list_models()]


@app.post("/models")
async def create_model(payload: ModelCreate) -> dict[str, int]:
    """Register a new diffusion model."""
    model_id = register_model(
        payload.name,
        payload.version,
        payload.model_id,
        details=payload.details,
        is_default=payload.is_default,
    )
    return {"id": model_id}


@app.post("/models/{model_id}/default")
async def switch_default(model_id: int) -> dict[str, str]:
    """Switch the default diffusion model."""
    try:
        set_default(model_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "ok"}


class GeneratePayload(BaseModel):  # type: ignore[misc]
    """Request body for the ``/generate`` endpoint."""

    batches: list[list[str]]
    output_dir: str


@app.post("/generate")
async def generate(payload: GeneratePayload) -> dict[str, list[str]]:
    """Schedule mockup generation tasks and return Celery task IDs."""
    task_ids = [
        celery_app.send_task(
            "mockup_generation.tasks.generate_mockup",
            args=[batch, payload.output_dir],
        ).id
        for batch in payload.batches
    ]
    return {"tasks": task_ids}
