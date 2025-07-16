"""Register JSON schemas with the schema registry."""

from __future__ import annotations

import json
import pathlib
from typing import Iterable

import requests


SCHEMAS_DIR = pathlib.Path(__file__).resolve().parent.parent / "schemas"
REGISTRY_URL = "http://schema-registry:8081"


def _register(schema_path: pathlib.Path) -> None:
    subject = schema_path.stem
    schema = json.loads(schema_path.read_text())
    payload = {"schema": json.dumps(schema)}
    url = f"{REGISTRY_URL}/subjects/{subject}/versions"
    response = requests.post(url, json=payload, timeout=5)
    response.raise_for_status()


def register_all() -> None:
    """Register every schema in the schemas directory."""
    for path in SCHEMAS_DIR.glob("*.json"):
        _register(path)


if __name__ == "__main__":
    register_all()
