"""Sentry integration utilities."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from fastapi import FastAPI
from sentry_sdk import init
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger(__name__)


def configure_sentry(app: FastAPI, service_name: str) -> None:
    """Initialize Sentry for ``app`` if ``SENTRY_DSN`` is configured."""
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        logger.debug("Sentry DSN not provided; skipping setup")
        return

    def _before_send(event: Any, hint: Dict[str, Any] | None) -> Any:
        request = hint.get("request") if hint else None
        if request is not None:
            correlation_id = getattr(request.state, "correlation_id", None)
            if correlation_id:
                event.setdefault("tags", {})["correlation_id"] = correlation_id
        return event

    sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
    init(
        dsn=dsn,
        before_send=_before_send,
        integrations=[sentry_logging],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        release=os.getenv("SENTRY_RELEASE"),
        environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
    )
    app.add_middleware(SentryAsgiMiddleware)
    logger.info("Sentry initialized for %s", service_name)
