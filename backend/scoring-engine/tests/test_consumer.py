"""Tests for the Kafka consumer used by the scoring engine."""

# mypy: ignore-errors

from __future__ import annotations

import warnings
from threading import Event

from fastapi.testclient import TestClient

warnings.filterwarnings("ignore", category=DeprecationWarning)

import pytest
from scoring_engine import app as app_module
from scoring_engine.app import consume_signals
from sqlalchemy import select

from backend.shared.db import session_scope
from backend.shared.db.models import Embedding


class DummyConsumer:
    """Yield predetermined Kafka messages."""

    def __init__(self, messages: list[tuple[str, dict[str, object]]]) -> None:
        self._messages = messages

    def __iter__(self) -> object:
        """Return iterator over stored messages."""
        return iter(self._messages)


def test_consume_signals_batches(monkeypatch: "pytest.MonkeyPatch") -> None:
    """Messages are grouped by ``EMBED_BATCH_SIZE`` and dispatched."""

    class DummyCelery:
        def __init__(self) -> None:
            self.sent: list[list[dict[str, object]]] = []

        def send_task(self, name: str, args: list[list[dict[str, object]]]) -> None:  # type: ignore[override]
            self.sent.append(args[0])

    dummy_celery = DummyCelery()
    monkeypatch.setattr(app_module, "celery_app", dummy_celery)
    monkeypatch.setenv("EMBED_BATCH_SIZE", "2")

    msgs = [("signals.ingested", {"id": i}) for i in range(3)]
    consumer = DummyConsumer(msgs)

    stop = Event()
    consume_signals(stop, consumer)

    assert dummy_celery.sent == [[{"id": 0}, {"id": 1}], [{"id": 2}]]


def test_consumer_closed_on_shutdown(monkeypatch) -> None:
    """Ensure the Kafka consumer is closed on application shutdown."""
    closed = False

    class DummyConsumer:
        def __iter__(self) -> object:
            return iter([])

        def close(self) -> None:
            nonlocal closed
            closed = True

    import scoring_engine.app as app_module

    monkeypatch.setenv("KAFKA_SKIP", "0")
    monkeypatch.setattr(app_module, "_create_consumer", lambda: DummyConsumer())

    class DummyThread:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def start(self) -> None:
            pass

        def join(self, timeout: float | None = None) -> None:
            pass

    monkeypatch.setattr(app_module, "Thread", DummyThread)

    with TestClient(app_module.app):
        pass

    assert closed
