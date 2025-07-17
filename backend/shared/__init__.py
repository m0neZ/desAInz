"""Shared utilities for backend services."""

from .profiling import add_profiling
from .tracing import configure_tracing
from .logging import configure_logging
from .sentry import configure_sentry
from .feature_flags import initialize as init_feature_flags, is_enabled

from .errors import add_error_handlers, add_flask_error_handlers
from .currency import convert_price, start_rate_updater
from .config import settings

__all__ = [
    "add_profiling",
    "configure_tracing",
    "configure_logging",
    "configure_sentry",
    "init_feature_flags",
    "add_error_handlers",
    "add_flask_error_handlers",
    "is_enabled",
    "convert_price",
    "start_rate_updater",
    "settings",
]
