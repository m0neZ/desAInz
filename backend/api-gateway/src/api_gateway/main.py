"""API Gateway FastAPI application."""

import logging
from fastapi import FastAPI

from .routes import router
from backend.shared.tracing import configure_tracing
from backend.shared.logging_config import (
    add_correlation_middleware,
    configure_logging,
)

configure_logging("api-gateway")
logger = logging.getLogger(__name__)
app = FastAPI(title="API Gateway")
configure_tracing(app, "api-gateway")
add_correlation_middleware(app)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}


app.include_router(router)
