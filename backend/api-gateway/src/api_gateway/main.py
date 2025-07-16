"""API Gateway FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from .routes import router
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling

app = FastAPI(title="API Gateway")
app.add_middleware(GZipMiddleware, minimum_size=500)
configure_tracing(app, "api-gateway")
add_profiling(app)


@app.get("/health")  # type: ignore[misc]
async def health() -> dict[str, str]:
    """Return service liveness."""
    return {"status": "ok"}


@app.get("/ready")  # type: ignore[misc]
async def ready() -> dict[str, str]:
    """Return service readiness."""
    return {"status": "ready"}


app.include_router(router)
