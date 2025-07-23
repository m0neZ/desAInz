"""Tests for Kafka helper utilities."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator

import pytest
from jsonschema.exceptions import ValidationError

from backend.shared.kafka.schema_registry import SchemaRegistryClient
from backend.shared.kafka.utils import KafkaConsumerWrapper, KafkaProducerWrapper


class DummyProducer:
    """Collect messages instead of sending them to Kafka."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the dummy producer."""
        self.sent: Dict[str, Any] = {}
        self.flush_called = False

    def send(self, topic: str, value: Dict[str, Any]) -> None:
        """Record the produced message."""
        self.sent[topic] = value

    def flush(self) -> None:  # pragma: no cover
        """Record that a flush was requested."""
        self.flush_called = True


def test_producer_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure messages are validated before being sent."""
    registry = SchemaRegistryClient("http://registry")
    monkeypatch.setattr(
        registry,
        "fetch",
        lambda _: {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    )

    monkeypatch.setattr("backend.shared.kafka.utils.KafkaProducer", DummyProducer)
    producer = KafkaProducerWrapper("kafka:9092", registry)
    producer.produce("signals", {"id": "1"})
    assert producer._producer.sent["signals"] == {"id": "1"}
    assert not producer._producer.flush_called
    producer.flush()
    assert producer._producer.flush_called

    with pytest.raises(ValidationError):
        producer.produce("signals", {"bad": "data"})


class DummyMessage:
    """Container for a consumed Kafka message."""

    def __init__(self, topic: str, value: Dict[str, Any]) -> None:
        """Initialize with a ``topic`` and ``value``."""
        self.topic = topic
        self.value = value


class DummyConsumer:
    """Yield predetermined messages instead of reading from Kafka."""

    def __init__(self, messages: list[DummyMessage]) -> None:
        """Store ``messages`` to be iterated over."""
        self._messages = messages

    def __iter__(self) -> Iterable[DummyMessage]:
        """Yield each stored message."""
        yield from self._messages


def test_consumer_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure consumed messages are validated."""
    registry = SchemaRegistryClient("http://registry")
    schema = {
        "type": "object",
        "properties": {"id": {"type": "string"}},
        "required": ["id"],
    }
    monkeypatch.setattr(registry, "fetch", lambda *_: schema)

    messages = [
        DummyMessage("signals", {"id": "1"}),
        DummyMessage("signals", {"bad": "data"}),
    ]

    monkeypatch.setattr(
        "backend.shared.kafka.utils.KafkaConsumer",
        lambda *_, **__: DummyConsumer(messages),
    )

    consumer = KafkaConsumerWrapper("kafka:9092", registry, ["signals"])
    iterator: Iterator[tuple[str, Dict[str, Any]]] = iter(consumer)
    topic, value = next(iterator)
    assert (topic, value) == ("signals", {"id": "1"})
    with pytest.raises(ValidationError):
        next(iterator)
