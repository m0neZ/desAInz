"""
Kafka publisher using typed schemas.

Environment variables
---------------------
KAFKA_SKIP:
    When set to ``"1"`` Kafka connections are skipped. Defaults to ``"0"``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from backend.shared.config import settings
from backend.shared.kafka import KafkaProducerWrapper, SchemaRegistryClient

SCHEMA_DIR = Path(__file__).resolve().parents[4] / "schemas"

if os.getenv("KAFKA_SKIP") == "1":  # pragma: no cover - used for docs generation
    producer: KafkaProducerWrapper | None = None
else:
    registry = SchemaRegistryClient(settings.schema_registry_url)
    for path in SCHEMA_DIR.glob("*.json"):
        with open(path) as fh:
            schema = json.load(fh)
        try:
            registry.register(path.stem, schema)
        except Exception:  # pragma: no cover - ignore duplicate errors
            pass
    producer = KafkaProducerWrapper(settings.kafka_bootstrap_servers, registry)


def publish(
    topic: str,
    message: Dict[str, Any] | str,
    *,
    prod: KafkaProducerWrapper | None = None,
) -> None:
    """Publish ``message`` to ``topic`` using the configured Kafka producer."""
    chosen = prod or producer
    if chosen is None:  # pragma: no cover - skipped when generating docs
        return

    payload: Dict[str, Any]
    if isinstance(message, dict):
        payload = message
    else:
        try:
            loaded = json.loads(message)
            payload = loaded if isinstance(loaded, dict) else {"value": message}
        except json.JSONDecodeError:
            payload = {"value": message}

    chosen.produce(topic, payload)
