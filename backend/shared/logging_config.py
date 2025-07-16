"""Shared JSON logging configuration with optional CloudWatch handler."""

from __future__ import annotations

import json
import logging
import os
from logging.config import dictConfig
from typing import Any, Dict

try:
    import watchtower
except Exception:  # pragma: no cover - optional dependency may not be installed
    watchtower = None


class CorrelationIdFilter(logging.Filter):
    """Attach correlation IDs to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = getattr(record, "correlation_id", "-")
        return True


class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        log_record: Dict[str, Any] = {
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
        }
        return json.dumps(log_record)


def _cloudwatch_handler() -> dict[str, Any]:
    if watchtower is not None and os.getenv("CLOUDWATCH_LOG_GROUP"):
        return {
            "class": "watchtower.CloudWatchLogHandler",
            "log_group": os.environ["CLOUDWATCH_LOG_GROUP"],
            "stream_name": os.getenv("CLOUDWATCH_LOG_STREAM", "application"),
            "formatter": "json",
            "filters": ["correlation"],
        }
    return {
        "class": "logging.StreamHandler",
        "formatter": "json",
        "filters": ["correlation"],
    }


def configure_logging() -> None:
    """Configure JSON logging with correlation IDs and optional CloudWatch."""

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"correlation": {"()": CorrelationIdFilter}},
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {"default": _cloudwatch_handler()},
        "root": {"handlers": ["default"], "level": "INFO"},
    }
    dictConfig(log_config)
