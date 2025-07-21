"""Tests for the Sentry integration utilities."""

from __future__ import annotations

from unittest import mock

from fastapi import FastAPI

from backend.shared import sentry


def test_configure_sentry_adds_middleware(monkeypatch: mock.MagicMock) -> None:
    """Middleware is attached when a DSN is provided."""
    monkeypatch.setenv("SENTRY_DSN", "http://example@localhost/1")
    app = FastAPI()
    monkeypatch.setattr(sentry, "init", mock.Mock())
    monkeypatch.setattr(sentry, "SentryAsgiMiddleware", mock.MagicMock())
    sentry.configure_sentry(app, "service")
    middleware_classes = [mw.cls for mw in app.user_middleware]
    assert sentry.SentryAsgiMiddleware in middleware_classes
    sentry.init.assert_called_once()
