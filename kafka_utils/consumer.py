"""Kafka message consumer with JSON Schema support."""

from __future__ import annotations

from typing import Any, Callable

from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.serialization import MessageField, SerializationContext


class MessageConsumer:
    """Consume typed messages from Kafka topics."""

    def __init__(
        self, brokers: str, schema_registry_url: str, group_id: str
    ) -> None:
        """Initialize consumer and schema registry."""
        self._consumer = Consumer(
            {
                "bootstrap.servers": brokers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
            }
        )
        self._schema_registry = SchemaRegistryClient(
            {"url": schema_registry_url}
        )

    def consume(self, topic: str, handler: Callable[[Any], None]) -> None:
        """Consume messages from the given topic and process using handler."""
        self._consumer.subscribe([topic])
        schema = self._schema_registry.get_latest_version(
            f"{topic}-value"
        ).schema
        deserializer = JSONDeserializer(
            schema.schema_str, self._schema_registry
        )
        try:
            while True:
                msg = self._consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    raise RuntimeError(msg.error())
                value = deserializer(
                    msg.value(),
                    SerializationContext(msg.topic(), MessageField.VALUE),
                )
                handler(value)
        finally:
            self._consumer.close()
