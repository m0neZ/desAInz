"""Schema registry client utilities."""

from __future__ import annotations

import json
from typing import Any, Dict

import requests


class SchemaRegistryClient:
    """Simple client for interacting with a schema registry."""

    def __init__(self, url: str) -> None:
        self._url = url.rstrip("/")

    def register(self, subject: str, schema: Dict[str, Any]) -> None:
        """Register ``schema`` for ``subject``."""
        payload = {"schema": json.dumps(schema)}
        response = requests.post(
            f"{self._url}/subjects/{subject}/versions",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()

    def fetch(self, subject: str) -> Dict[str, Any]:
        """Retrieve latest schema for ``subject``."""
        response = requests.get(
            f"{self._url}/subjects/{subject}/versions/latest/schema",
            timeout=5,
        )
        response.raise_for_status()
        return json.loads(response.text)
