"""Tests for structured logging configuration."""

# mypy: ignore-errors

import json
import logging

from backend.shared.logging import configure_logging


def test_loki_json_logging(caplog):
    """Logs include correlation and user information in JSON."""
    configure_logging()
    caplog.set_level(logging.INFO)
    logging.getLogger().info("test", extra={"correlation_id": "cid", "user": "alice"})
    log = caplog.text.splitlines()[-1]
    data = json.loads(log)
    assert data["correlation_id"] == "cid"
    assert data["user"] == "alice"
