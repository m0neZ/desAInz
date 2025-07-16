"""API Gateway FastAPI application."""

from fastapi import FastAPI

from backend.common.tracing import init_fastapi_tracing

from .routes import router

app = FastAPI(title="API Gateway")
init_fastapi_tracing(app, "api-gateway")
app.include_router(router)
