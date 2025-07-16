"""API Gateway FastAPI application."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from .audit import scheduler, start_retention_scheduler

from .routes import router
from backend.shared.tracing import configure_tracing


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan."""
    start_retention_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(title="API Gateway", lifespan=lifespan)
configure_tracing(app, "api-gateway")
app.include_router(router)
