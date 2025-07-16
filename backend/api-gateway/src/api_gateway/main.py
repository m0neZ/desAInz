"""API Gateway FastAPI application."""

import logging
import uuid
from typing import Callable, Coroutine

from fastapi import FastAPI, Request, Response

from .routes import router
from backend.shared.logging_config import configure_logging
from backend.shared.tracing import configure_tracing

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title="API Gateway")
configure_tracing(app, "api-gateway")


@app.middleware("http")
async def add_correlation_id(
    request: Request, call_next: Callable[[Request], Coroutine[None, None, Response]]
) -> Response:
    """Ensure every request contains a correlation ID."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    logger.info("request received", extra={"correlation_id": correlation_id})
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.get("/health")  # type: ignore[misc]
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")  # type: ignore[misc]
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}


app.include_router(router)
