"""Tests for Kafka helper utilities."""

from __future__ import annotations

from typing import Any, Dict

import pytest
from jsonschema.exceptions import ValidationError

from backend.shared.kafka.schema_registry import SchemaRegistryClient
from backend.shared.kafka.utils import KafkaProducerWrapper


class DummyProducer:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.sent: Dict[str, Any] = {}

    def send(self, topic: str, value: Dict[str, Any]) -> None:  # type: ignore[override]
        self.sent[topic] = value

    def flush(self) -> None:  # pragma: no cover
        pass


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

    with pytest.raises(ValidationError):
        producer.produce("signals", {"bad": "data"})
