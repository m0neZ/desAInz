"""Kafka message producer with JSON Schema support."""

from __future__ import annotations

from typing import Any, Dict

from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from confluent_kafka.serialization import MessageField, SerializationContext


class MessageProducer:
    """Produce typed messages to Kafka topics."""

    def __init__(self, brokers: str, schema_registry_url: str) -> None:
        """Initialize producer and schema registry."""
        self._producer = Producer({"bootstrap.servers": brokers})
        self._schema_registry = SchemaRegistryClient(
            {"url": schema_registry_url}
        )

    def produce(self, topic: str, value: Dict[str, Any]) -> None:
        """Produce a JSON message using the schema from the registry."""
        schema = self._schema_registry.get_latest_version(
            f"{topic}-value"
        ).schema
        serializer = JSONSerializer(schema.schema_str, self._schema_registry)
        serialized = serializer(
            value, SerializationContext(topic, MessageField.VALUE)
        )
        self._producer.produce(topic, serialized)
        self._producer.flush()
