"""Schema registry client utilities."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, cast

import requests  # type: ignore[import-untyped]
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class SchemaRegistryClient:
    """Simple client for interacting with a schema registry."""

    def __init__(self, url: str, token: str | None = None) -> None:
        """Initialize the client with the registry ``url`` and optional ``token``."""
        self._url = url.rstrip("/")
        self._token = token or os.getenv("SCHEMA_REGISTRY_TOKEN")

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )
    def register(self, subject: str, schema: Dict[str, Any]) -> None:
        """Register ``schema`` for ``subject`` with optional retries."""
        payload = {"schema": json.dumps(schema)}
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        response = requests.post(
            f"{self._url}/subjects/{subject}/versions",
            json=payload,
            headers=headers,
            timeout=5,
        )
        response.raise_for_status()

    def fetch(self, subject: str) -> Dict[str, Any]:
        """Retrieve latest schema for ``subject``."""
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        response = requests.get(
            f"{self._url}/subjects/{subject}/versions/latest/schema",
            headers=headers,
            timeout=5,
        )
        response.raise_for_status()
        return cast(Dict[str, Any], json.loads(response.text))
