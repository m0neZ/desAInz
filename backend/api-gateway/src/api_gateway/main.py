"""API Gateway FastAPI application."""

import logging
import uuid
from typing import Callable, Coroutine

from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware

from .routes import router
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared.logging import configure_logging
from backend.shared import add_error_handlers, configure_sentry


configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway")
app.add_middleware(GZipMiddleware, minimum_size=1000)
configure_tracing(app, "api-gateway")
configure_sentry(app, "api-gateway")
add_profiling(app)
add_error_handlers(app)


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


app.include_router(router)
