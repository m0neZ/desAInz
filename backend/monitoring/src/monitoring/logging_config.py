"""Logging configuration for the monitoring service."""

from __future__ import annotations

import json
import logging
from logging.config import dictConfig
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Return the JSON representation of ``record``."""
        log_record: Dict[str, Any] = {
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(log_record)


def configure_logging() -> None:
    """Configure application logging."""
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "default": {"class": "logging.StreamHandler", "formatter": "json"}
        },
        "root": {"handlers": ["default"], "level": "INFO"},
    }
    dictConfig(config)
