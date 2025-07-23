"""Integration tests for Kafka schema helpers."""

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable

import pytest


class LocalSchemaRegistryMock:
    """In-memory registry storing schemas by subject."""

    def __init__(self, url: str, token: str | None = None) -> None:
        self._schemas: dict[str, Dict[str, Any]] = {}

    def register(self, subject: str, schema: Dict[str, Any]) -> None:
        self._schemas[subject] = schema

    def fetch(self, subject: str) -> Dict[str, Any]:
        if subject not in self._schemas and "." in subject:
            alt = subject.split(".", 1)[0] + "-value"
            if alt in self._schemas:
                return self._schemas[alt]
        return self._schemas[subject]


class DummyKafkaProducer:
    """Collect produced messages instead of sending them to Kafka."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.sent: list[tuple[str, Dict[str, Any]]] = []

    def send(self, topic: str, value: Dict[str, Any]) -> None:
        self.sent.append((topic, value))

    def flush(self) -> None:  # pragma: no cover
        pass


def dummy_consumer_factory(messages: list[tuple[str, Dict[str, Any]]]) -> type[object]:
    """Create a dummy Kafka consumer that yields provided messages."""

    class DummyMessage:
        def __init__(self, topic: str, value: Dict[str, Any]) -> None:
            self.topic = topic
            self.value = value

    class DummyKafkaConsumer:
        def __init__(self, *topics: str, **kwargs: Any) -> None:
            self._topics = topics

        def __iter__(self) -> Iterable[DummyMessage]:
            for topic, value in messages:
                if topic in self._topics:
                    yield DummyMessage(topic, value)

        def close(self) -> None:  # pragma: no cover
            pass

    return DummyKafkaConsumer


def test_schema_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    """Messages published by signal ingestion are deserialized by the scoring engine."""

    messages: list[tuple[str, Dict[str, Any]]] = []

    monkeypatch.setenv("KAFKA_SKIP", "0")
    monkeypatch.setattr(
        "backend.shared.kafka.schema_registry.SchemaRegistryClient",
        LocalSchemaRegistryMock,
    )
    monkeypatch.setattr(
        "backend.shared.kafka.SchemaRegistryClient", LocalSchemaRegistryMock
    )
    monkeypatch.setattr("backend.shared.kafka.utils.KafkaProducer", DummyKafkaProducer)
    monkeypatch.setattr(
        "backend.shared.kafka.utils.KafkaConsumer",
        lambda *topics, **kwargs: dummy_consumer_factory(messages)(*topics, **kwargs),
    )
    monkeypatch.setattr(
        "redis.asyncio.Redis.from_url",
        lambda *a, **k: SimpleNamespace(),
        raising=False,
    )

    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "backend" / "signal-ingestion" / "src"))
    sys.path.insert(0, str(root / "backend" / "scoring-engine"))

    if "signal_ingestion.publisher" in sys.modules:
        importlib.reload(sys.modules["signal_ingestion.publisher"])
    else:
        importlib.import_module("signal_ingestion.publisher")

    if "scoring_engine.app" in sys.modules:
        app_module = importlib.reload(sys.modules["scoring_engine.app"])
    else:
        app_module = importlib.import_module("scoring_engine.app")

    from signal_ingestion import publisher

    publisher.publish("signals.ingested", {"id": "1", "value": "test"})
    messages.extend(publisher.producer._producer.sent)

    consumer = app_module._create_consumer()
    topic, payload = next(iter(consumer))

    assert topic == "signals.ingested"
    assert payload == {"id": "1", "value": "test"}
