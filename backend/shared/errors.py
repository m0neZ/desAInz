"""Common error handling utilities for FastAPI services."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from opentelemetry.trace import get_current_span
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    message: str
    trace_id: str


def _get_trace_id(request: Request) -> str:
    """Return the current trace or correlation ID."""
    span = get_current_span()
    ctx = span.get_span_context()
    if ctx.trace_id:
        return format(ctx.trace_id, "032x")
    return str(getattr(request.state, "correlation_id", "-"))


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle ``HTTPException`` and return a standardized response."""
    assert isinstance(exc, HTTPException)
    trace_id = _get_trace_id(request)
    logger.warning(
        "handled http exception",
        extra={"trace_id": trace_id, "status_code": exc.status_code},
    )
    body = ErrorResponse(
        error=str(exc.status_code),
        message=str(exc.detail),
        trace_id=trace_id,
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions and return a standardized response."""
    trace_id = _get_trace_id(request)
    logger.error("unhandled exception", exc_info=exc, extra={"trace_id": trace_id})
    body = ErrorResponse(
        error="internal_server_error",
        message="Internal Server Error",
        trace_id=trace_id,
    )
    return JSONResponse(status_code=500, content=body.model_dump())


def add_exception_handlers(app: FastAPI) -> None:
    """Register common exception handlers on ``app``."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
