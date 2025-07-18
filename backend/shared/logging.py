"""Shared JSON logging configuration with correlation IDs."""

# mypy: ignore-errors

from __future__ import annotations

import json
import logging
import os
from logging.config import dictConfig
from typing import Any, Dict, Optional, Type

try:
    from watchtower import CloudWatchLogHandler as CWHandler
except Exception:  # pragma: no cover - optional dependency
    CWHandler = None

CloudWatchLogHandler: Optional[Type[logging.Handler]] = CWHandler


class CorrelationIdFilter(logging.Filter):
    """Attach correlation IDs to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Ensure ``correlation_id`` field is present."""
        record.correlation_id = getattr(record, "correlation_id", "-")
        return True


class RequestInfoFilter(logging.Filter):
    """Attach request context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Ensure user and request fields are present."""
        record.user = getattr(record, "user", None)
        record.path = getattr(record, "path", None)
        record.method = getattr(record, "method", None)
        return True


class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Return the JSON representation of ``record``."""
        log_record: Dict[str, Any] = {
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
            "user": getattr(record, "user", None),
            "path": getattr(record, "path", None),
            "method": getattr(record, "method", None),
        }
        return json.dumps(log_record)


def _additional_handlers() -> list[logging.Handler]:
    """Return optional log handlers for aggregation."""
    handlers: list[logging.Handler] = []
    if os.getenv("LOG_AGGREGATOR") == "cloudwatch" and CloudWatchLogHandler:
        group = os.getenv("CLOUDWATCH_GROUP", "desAInz")
        stream = os.getenv("CLOUDWATCH_STREAM", "app")
        handlers.append(CloudWatchLogHandler(log_group=group, stream_name=stream))
    return handlers


def configure_logging() -> None:
    """Configure JSON logging and aggregation."""
    handlers: dict[str, Any] = {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["correlation", "request"],
        }
    }
    for idx, handler in enumerate(_additional_handlers()):
        handlers[f"agg{idx}"] = {
            "class": handler.__class__.__name__,
            "()": handler,
            "formatter": "json",
            "filters": ["correlation", "request"],
        }

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation": {"()": CorrelationIdFilter},
            "request": {"()": RequestInfoFilter},
        },
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": handlers,
        "root": {"handlers": list(handlers.keys()), "level": "INFO"},
    }
    dictConfig(log_config)
