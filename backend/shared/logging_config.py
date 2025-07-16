"""Shared logging utilities."""

from __future__ import annotations

import json
import logging
import os
import uuid
from logging.config import dictConfig
from typing import Any, Callable, Coroutine, Dict

import watchtower  # noqa: F401
from fastapi import FastAPI, Request, Response
from flask import Flask, request, g


class CorrelationIdFilter(logging.Filter):
    """Attach correlation IDs to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add the ``correlation_id`` attribute if missing."""
        record.correlation_id = getattr(record, "correlation_id", "-")
        return True


class JsonFormatter(logging.Formatter):
    """Format log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        """Return the JSON representation of ``record``."""
        log_record: Dict[str, Any] = {
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
        }
        return json.dumps(log_record)


def configure_logging(service_name: str) -> None:
    """Configure JSON logging with optional CloudWatch aggregation."""
    handlers: Dict[str, Dict[str, Any]] = {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["correlation"],
        }
    }
    root_handlers = ["default"]
    log_group = os.getenv("CLOUDWATCH_LOG_GROUP")
    if log_group:
        handlers["cloudwatch"] = {
            "class": "watchtower.CloudWatchLogHandler",
            "log_group": log_group,
            "stream_name": os.getenv("CLOUDWATCH_LOG_STREAM", service_name),
        }
        root_handlers.append("cloudwatch")
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"correlation": {"()": CorrelationIdFilter}},
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": handlers,
        "root": {"handlers": root_handlers, "level": "INFO"},
    }
    dictConfig(log_config)


def add_correlation_middleware(app: FastAPI | Flask) -> None:
    """Attach correlation ID middleware to ``app``."""
    logger = logging.getLogger(__name__)

    if isinstance(app, FastAPI):
        @app.middleware("http")
        async def _middleware(
            request: Request,
            call_next: Callable[[Request], Coroutine[None, None, Response]],
        ) -> Response:
            correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
            request.state.correlation_id = correlation_id
            logger.info("request received", extra={"correlation_id": correlation_id})
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
    else:
        @app.before_request
        def _before_request() -> None:
            cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
            g.correlation_id = cid
            logger.info("request received", extra={"correlation_id": cid})

        @app.after_request
        def _after_request(response: Response) -> Response:  # type: ignore[type-var]
            response.headers["X-Correlation-ID"] = getattr(g, "correlation_id", "-")
            return response
