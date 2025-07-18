"""Global pytest fixtures for the test suite."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest


class _DummyProducer:
    def __init__(self, *args, **kwargs):
        pass

    def send(self, *args, **kwargs):
        pass

    def flush(self) -> None:  # pragma: no cover
        pass


class _DummyConsumer:
    def __init__(self, *args, **kwargs):
        pass

    def __iter__(self):
        return iter([])


@pytest.fixture(autouse=True)
def _stub_services(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub external dependencies like Kafka and Selenium."""
    os.environ.setdefault("KAFKA_SKIP", "1")
    os.environ.setdefault("SELENIUM_SKIP", "1")

    monkeypatch.setattr("kafka.KafkaProducer", _DummyProducer, raising=False)
    monkeypatch.setattr("kafka.KafkaConsumer", _DummyConsumer, raising=False)
    monkeypatch.setattr(
        "selenium.webdriver.Firefox",
        lambda *a, **k: SimpleNamespace(get=lambda *a, **k: None),
        raising=False,
    )
