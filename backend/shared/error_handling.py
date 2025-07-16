"""Exception handling utilities for services."""

# mypy: ignore-errors

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException as FlaskHTTPException
from opentelemetry import trace
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Schema for API error responses."""

    detail: str
    correlation_id: str
    trace_id: str | None = None


def _get_trace_id() -> str | None:
    span = trace.get_current_span()
    if span is not None:
        ctx = span.get_span_context()
        if ctx.trace_id:
            return f"{ctx.trace_id:032x}"
    return None


def _fastapi_http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "-")
    trace_id = _get_trace_id()
    logger.warning(
        "http error",
        extra={
            "correlation_id": correlation_id,
            "trace_id": trace_id,
            "status_code": exc.status_code,
        },
    )
    body = ErrorResponse(
        detail=str(exc.detail), correlation_id=correlation_id, trace_id=trace_id
    )
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


async def _fastapi_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "-")
    trace_id = _get_trace_id()
    logger.exception(
        "unhandled exception",
        exc_info=exc,
        extra={"correlation_id": correlation_id, "trace_id": trace_id},
    )
    body = ErrorResponse(
        detail="Internal Server Error", correlation_id=correlation_id, trace_id=trace_id
    )
    return JSONResponse(status_code=500, content=body.model_dump())


def _flask_http_exception_handler(exc: FlaskHTTPException) -> Any:
    correlation_id = getattr(request, "correlation_id", "-")
    trace_id = _get_trace_id()
    logger.warning(
        "http error",
        extra={
            "correlation_id": correlation_id,
            "trace_id": trace_id,
            "status_code": exc.code,
        },
    )
    body = ErrorResponse(
        detail=str(exc.description), correlation_id=correlation_id, trace_id=trace_id
    )
    response = jsonify(body.model_dump())
    response.status_code = int(exc.code or 500)
    return response


def _flask_exception_handler(exc: Exception) -> Any:
    correlation_id = getattr(request, "correlation_id", "-")
    trace_id = _get_trace_id()
    logger.exception(
        "unhandled exception",
        exc_info=exc,
        extra={"correlation_id": correlation_id, "trace_id": trace_id},
    )
    body = ErrorResponse(
        detail="Internal Server Error", correlation_id=correlation_id, trace_id=trace_id
    )
    response = jsonify(body.model_dump())
    response.status_code = 500
    return response


def add_exception_handlers(app: FastAPI | Flask) -> None:
    """Attach standardized exception handlers to ``app``."""
    if isinstance(app, FastAPI):
        app.add_exception_handler(HTTPException, _fastapi_http_exception_handler)
        app.add_exception_handler(Exception, _fastapi_exception_handler)
    else:
        app.register_error_handler(FlaskHTTPException, _flask_http_exception_handler)
        app.register_error_handler(Exception, _flask_exception_handler)
