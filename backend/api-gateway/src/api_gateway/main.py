"""API Gateway FastAPI application."""

from fastapi import FastAPI

from .routes import router
from backend.shared.tracing import configure_tracing

app = FastAPI(title="API Gateway")
configure_tracing(app, "api-gateway")
app.include_router(router)
