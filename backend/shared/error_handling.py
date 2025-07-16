"""Shared error response models and exception handlers."""

from __future__ import annotations

import logging


from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from flask import Flask, jsonify, request, Response as FlaskResponse
from werkzeug.exceptions import HTTPException as FlaskHTTPException


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    trace_id: str


async def _fastapi_http_exception_handler(
    request: Request, exc: HTTPException
) -> Response:
    trace_id = getattr(request.state, "correlation_id", "")
    content = ErrorResponse(error=str(exc.detail), trace_id=trace_id).model_dump()
    return JSONResponse(status_code=exc.status_code, content=content)


async def _fastapi_general_exception_handler(
    request: Request, exc: Exception
) -> Response:
    trace_id = getattr(request.state, "correlation_id", "")
    logging.getLogger(__name__).error(
        "unhandled exception",
        exc_info=exc,
        extra={"correlation_id": trace_id},
    )
    content = ErrorResponse(
        error="Internal server error", trace_id=trace_id
    ).model_dump()
    return JSONResponse(status_code=500, content=content)


def add_fastapi_error_handlers(app: FastAPI) -> None:
    """Register standard exception handlers on a FastAPI app."""
    app.add_exception_handler(
        HTTPException,
        _fastapi_http_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(Exception, _fastapi_general_exception_handler)


def _flask_handle_exception(exc: Exception) -> tuple[FlaskResponse, int]:
    """Return standardized JSON for all Flask exceptions."""
    trace_id = request.headers.get("X-Correlation-ID", "")
    logging.getLogger(__name__).error(
        "unhandled exception",
        exc_info=exc,
        extra={"correlation_id": trace_id},
    )
    if isinstance(exc, FlaskHTTPException):
        status = int(exc.code or 500)
        message = str(exc.description or "")
    else:
        status = 500
        message = "Internal server error"
    resp = ErrorResponse(error=message, trace_id=trace_id).model_dump()
    return jsonify(resp), status


def add_flask_error_handlers(app: Flask) -> None:
    """Register standard exception handlers on a Flask app."""
    app.register_error_handler(Exception, _flask_handle_exception)
