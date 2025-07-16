"""API Gateway FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from .routes import router
from backend.shared.tracing import configure_tracing

app = FastAPI(title="API Gateway")
app.add_middleware(GZipMiddleware, minimum_size=500)
configure_tracing(app, "api-gateway")
app.include_router(router)
