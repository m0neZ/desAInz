"""API Gateway FastAPI application."""

from fastapi import FastAPI

from backend.shared.tracing import configure_tracing

from .routes import router

app = FastAPI(title="API Gateway")
configure_tracing("api-gateway", app)
app.include_router(router)
