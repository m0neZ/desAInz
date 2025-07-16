"""Logging configuration for the monitoring service."""

from __future__ import annotations

from logging.config import dictConfig
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent / "service.log"


def configure_logging() -> None:
    """Configure logging to file and console."""
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "logging.Formatter",
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
            }
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "filename": str(LOG_FILE),
                "formatter": "default",
            },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "root": {"handlers": ["file", "console"], "level": "INFO"},
    }
    dictConfig(log_config)
