"""Kafka publisher."""

from __future__ import annotations

from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"], value_serializer=lambda v: v.encode()
)


def publish(topic: str, message: str) -> None:
    """Publish ``message`` to ``topic``."""
    producer.send(topic, message)
    producer.flush()
