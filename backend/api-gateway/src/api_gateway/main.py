"""API Gateway FastAPI application."""

from fastapi import FastAPI

from .routes import router

app = FastAPI(title="API Gateway")
app.include_router(router)
