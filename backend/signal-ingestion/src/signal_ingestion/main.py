"""Entrypoint for the signal ingestion service application."""

from __future__ import annotations

import logging
import uuid
from typing import Callable, Coroutine, cast

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .database import get_session, init_db
from .scheduler import create_scheduler
from .ingestion import ingest
from .logging_config import configure_logging
from .settings import settings
from backend.shared.config import settings as shared_settings
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared.metrics import register_metrics

from backend.shared import add_error_handlers, configure_sentry

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
register_metrics(app)
scheduler = create_scheduler()


def _identify_user(request: Request) -> str:
    """Return identifier for logging, header ``X-User`` or client IP."""
    return cast(str, request.headers.get("X-User", request.client.host))


@app.on_event("startup")
async def startup() -> None:
    """Initialize resources."""
    await init_db()
    scheduler.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    """Stop background tasks."""
    scheduler.shutdown()


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


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}


@app.post("/ingest")
async def ingest_signals(
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Trigger signal ingestion."""
    await ingest(session)
    return {"status": "ingested"}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "signal_ingestion.main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level,
    )
