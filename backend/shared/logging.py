"""Shared JSON logging configuration with correlation IDs."""

# mypy: ignore-errors

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from logging.config import dictConfig
from typing import Any, Dict, MutableMapping, Optional, Type

import requests

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


class LokiHandler(logging.Handler):
    """Send log records to Loki via HTTP."""

    def __init__(
        self, url: str, labels: MutableMapping[str, str] | None = None
    ) -> None:
        """Initialize handler with Loki endpoint and labels."""
        super().__init__()
        self.url = url.rstrip("/")
        self.labels = labels or {"app": os.getenv("SERVICE_NAME", "app")}

    def emit(self, record: logging.LogRecord) -> None:
        """Push a log entry to Loki."""
        payload = {
            "streams": [
                {
                    "stream": self.labels,
                    "values": [
                        [
                            str(int(datetime.utcnow().timestamp() * 1_000_000_000)),
                            self.format(record),
                        ]
                    ],
                }
            ]
        }
        try:
            requests.post(f"{self.url}/loki/api/v1/push", json=payload, timeout=2)
        except Exception:
            pass


def _additional_handlers() -> list[logging.Handler]:
    """Return optional log handlers for aggregation."""
    handlers: list[logging.Handler] = []
    if os.getenv("LOG_AGGREGATOR") == "cloudwatch" and CloudWatchLogHandler:
        group = os.getenv("CLOUDWATCH_GROUP", "desAInz")
        stream = os.getenv("CLOUDWATCH_STREAM", "app")
        handlers.append(CloudWatchLogHandler(log_group=group, stream_name=stream))
    loki = os.getenv("LOKI_URL")
    if loki:
        handlers.append(LokiHandler(loki))
    return handlers


def configure_logging() -> None:
    """
    Configure JSON logging and optional aggregation.

    A ``LokiHandler`` is added when ``LOKI_URL`` is defined, allowing
    structured logs with correlation IDs and user info to be pushed to
    Loki.
    """
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
