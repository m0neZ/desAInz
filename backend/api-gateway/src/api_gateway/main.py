"""API Gateway FastAPI application."""

from fastapi import FastAPI

from .routes import router
from backend.shared.tracing import configure_tracing
from backend.shared.error_handling import add_fastapi_error_handlers

app = FastAPI(title="API Gateway")
configure_tracing(app, "api-gateway")
add_fastapi_error_handlers(app)
app.include_router(router)
