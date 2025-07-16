"""Logging configuration for the service template."""

from __future__ import annotations

import json
import logging
from logging.config import dictConfig
from typing import Any, Dict


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


def configure_logging() -> None:
    """Configure JSON logging with correlation IDs."""
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"correlation": {"()": CorrelationIdFilter}},
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["correlation"],
            }
        },
        "root": {"handlers": ["default"], "level": "INFO"},
    }
    dictConfig(log_config)
