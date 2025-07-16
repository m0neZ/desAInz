"""API Gateway FastAPI application."""

from fastapi import FastAPI

from .routes import router
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import configure_profiling

app = FastAPI(title="API Gateway")
configure_tracing(app, "api-gateway")
configure_profiling(app)
app.include_router(router)
