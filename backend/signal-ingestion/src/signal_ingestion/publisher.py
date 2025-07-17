"""Kafka publisher."""

from __future__ import annotations

from kafka import KafkaProducer
import os

from backend.shared.config import settings

if os.getenv("KAFKA_SKIP") == "1":  # pragma: no cover - used for docs generation
    producer = None
else:
    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        value_serializer=lambda v: v.encode(),
    )


def publish(topic: str, message: str) -> None:
    """Publish ``message`` to ``topic``."""
    if producer is None:
        return
    producer.send(topic, message)
    producer.flush()
