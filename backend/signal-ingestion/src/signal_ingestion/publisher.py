"""Kafka publisher."""

from __future__ import annotations

from kafka import KafkaProducer
import os

from backend.shared.config import settings

if os.getenv("KAFKA_SKIP") == "1":  # pragma: no cover - used for docs generation
    _producer = None
else:
    _producer = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        value_serializer=lambda v: v.encode(),
    )


def publish(topic: str, message: str, producer: KafkaProducer | None = None) -> None:
    """
    Publish ``message`` to ``topic`` using ``producer``.

    Parameters
    ----------
    topic:
        Kafka topic to publish to.
    message:
        Serialized message payload.
    producer:
        Optional :class:`KafkaProducer` instance. When ``None``, the module
        level producer is used.
    """

    chosen = producer or _producer
    if chosen is None:
        return
    chosen.send(topic, message)
    chosen.flush()
