"""API Gateway FastAPI application."""

from fastapi import FastAPI

from backend.shared.profiling import add_fastapi_profiler

from .routes import router
from backend.shared.tracing import configure_tracing

app = FastAPI(title="API Gateway")
configure_tracing(app, "api-gateway")
add_fastapi_profiler(app)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}


app.include_router(router)
