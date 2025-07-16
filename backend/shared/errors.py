"""Common error handling utilities."""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from opentelemetry import trace

try:  # pragma: no cover - optional dependency
    import sentry_sdk
except Exception:  # pragma: no cover - sentry optional
    sentry_sdk = None


def _trace_id() -> str | None:
    """Return current trace ID if available."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.trace_id == 0:
        return None
    return format(ctx.trace_id, "032x")


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle ``HTTPException`` uniformly."""
    body: Dict[str, Any] = {
        "error": exc.detail,
        "correlation_id": getattr(request.state, "correlation_id", None),
        "trace_id": _trace_id(),
    }
    return JSONResponse(status_code=exc.status_code, content=body)


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions and log them."""
    correlation_id = getattr(request.state, "correlation_id", None)
    trace_id = _trace_id()
    logger = logging.getLogger(__name__)
    logger.exception(
        "unhandled exception",
        extra={"correlation_id": correlation_id, "trace_id": trace_id},
    )
    if sentry_sdk and sentry_sdk.Hub.current.client is not None:
        with sentry_sdk.push_scope() as scope:
            if correlation_id:
                scope.set_tag("correlation_id", correlation_id)
            if trace_id:
                scope.set_tag("trace_id", trace_id)
            sentry_sdk.capture_exception(exc)
    body = {
        "error": "Internal Server Error",
        "correlation_id": correlation_id,
        "trace_id": trace_id,
    }
    return JSONResponse(status_code=500, content=body)


def add_error_handlers(app: FastAPI) -> None:
    """Register standard error handlers on ``app``."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


from flask import Flask, jsonify, request as flask_request
from werkzeug.exceptions import HTTPException as FlaskHTTPException


def add_flask_error_handlers(app: Flask) -> None:
    """Register standard error handlers on a Flask ``app``."""

    @app.errorhandler(FlaskHTTPException)
    def _http_error(exc: FlaskHTTPException):
        trace_id = _trace_id()
        correlation_id = getattr(flask_request, "correlation_id", None)
        body = {
            "error": exc.description,
            "correlation_id": correlation_id,
            "trace_id": trace_id,
        }
        resp = jsonify(body)
        resp.status_code = exc.code
        return resp

    @app.errorhandler(Exception)
    def _unhandled(exc: Exception):
        trace_id = _trace_id()
        correlation_id = getattr(flask_request, "correlation_id", None)
        logging.getLogger(__name__).exception(
            "unhandled exception",
            extra={"correlation_id": correlation_id, "trace_id": trace_id},
        )
        resp = jsonify(
            {
                "error": "Internal Server Error",
                "correlation_id": correlation_id,
                "trace_id": trace_id,
            }
        )
        resp.status_code = 500
        return resp
