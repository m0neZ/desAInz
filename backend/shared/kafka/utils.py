"""Typed Kafka producer and consumer utilities."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Iterator, Tuple

from jsonschema import validate
from kafka import KafkaConsumer, KafkaProducer

from .schema_registry import SchemaRegistryClient


class KafkaProducerWrapper:
    """Kafka producer that validates messages against schemas."""

    def __init__(self, bootstrap_servers: str, registry: SchemaRegistryClient) -> None:
        """Create producer connected to ``bootstrap_servers`` using ``registry``."""
        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        self._registry = registry

    def produce(self, topic: str, message: Dict[str, Any]) -> None:
        """Validate and send ``message`` to ``topic`` without flushing."""
        schema = self._registry.fetch(f"{topic}-value")
        validate(message, schema)
        self._producer.send(topic, message)

    def flush(self) -> None:
        """Flush buffered messages to Kafka."""
        self._producer.flush()


class KafkaConsumerWrapper:
    """Kafka consumer that yields validated messages."""

    def __init__(
        self,
        bootstrap_servers: str,
        registry: SchemaRegistryClient,
        topics: Iterable[str],
    ) -> None:
        """Initialize consumer subscribed to ``topics``."""
        self._consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda b: json.loads(b.decode()),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        self._registry = registry
        self._schemas = {topic: registry.fetch(f"{topic}-value") for topic in topics}

    def __iter__(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """Iterate over validated messages."""
        for message in self._consumer:
            value = message.value
            schema = self._schemas[message.topic]
            validate(value, schema)
            yield message.topic, value

    def close(self) -> None:
        """Close the underlying Kafka consumer."""
        self._consumer.close()
