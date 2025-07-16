"""Tests for message producer and consumer instantiation."""

import warnings

warnings.filterwarnings(
    "ignore",
    message="jsonschema.RefResolver is deprecated*",
    category=DeprecationWarning,
)

from kafka_utils import MessageConsumer, MessageProducer  # noqa: E402


def test_producer_init() -> None:
    """Producer initializes with given brokers and schema registry."""
    producer = MessageProducer("localhost:9092", "http://localhost:8081")
    assert producer is not None


def test_consumer_init() -> None:
    """Consumer initializes with given parameters."""
    consumer = MessageConsumer(
        "localhost:9092", "http://localhost:8081", "test"
    )
    assert consumer is not None
