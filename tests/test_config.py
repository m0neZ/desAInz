"""Tests for Kafka topic configuration."""

import warnings

warnings.filterwarnings(
    "ignore",
    message="jsonschema.RefResolver is deprecated*",
    category=DeprecationWarning,
)

from kafka_utils import TOPICS  # noqa: E402


def test_topics_defined() -> None:
    """Ensure all required topics are present."""
    assert set(TOPICS) == {
        "signals",
        "scores",
        "mockups",
        "listings",
        "feedback",
    }
