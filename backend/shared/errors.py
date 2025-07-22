"""Common error handling utilities."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from flask import Flask
from flask import Response as FlaskResponse
from flask import jsonify
from flask import request as flask_request
from opentelemetry import trace
from starlette.responses import Response
from werkzeug.exceptions import HTTPException as FlaskHTTPException

try:  # pragma: no cover - optional dependency
    import sentry_sdk
except Exception:  # pragma: no cover - sentry optional
    sentry_sdk = None  # type: ignore[assignment]


def _trace_id() -> str | None:
    """Return current trace ID if available."""
    get_span = getattr(trace, "get_current_span", None)
    if get_span is None:
        return None
    span = get_span()
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
    app.add_exception_handler(
        HTTPException,
        cast(Callable[[Request, Exception], Response], http_exception_handler),
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)


def add_flask_error_handlers(app: Flask) -> None:
    """Register standard error handlers on a Flask ``app``."""

    @app.errorhandler(FlaskHTTPException)
    def _http_error(exc: FlaskHTTPException) -> FlaskResponse:
        trace_id = _trace_id()
        correlation_id = getattr(flask_request, "correlation_id", None)
        body = {
            "error": exc.description,
            "correlation_id": correlation_id,
            "trace_id": trace_id,
        }
        resp = jsonify(body)
        resp.status_code = int(exc.code or 500)
        return resp

    @app.errorhandler(Exception)
    def _unhandled(exc: Exception) -> FlaskResponse:
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
