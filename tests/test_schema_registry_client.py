"""Tests for SchemaRegistryClient authentication and retry logic."""

import importlib.util
import pathlib
import sys
from types import ModuleType

import requests
import pytest

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "backend"
    / "shared"
    / "kafka"
    / "schema_registry.py"
)
spec = importlib.util.spec_from_file_location("schema_registry", MODULE_PATH)
assert spec is not None
schema_registry = importlib.util.module_from_spec(spec)
sys.modules["schema_registry"] = schema_registry
assert spec.loader
spec.loader.exec_module(schema_registry)
SchemaRegistryClient = schema_registry.SchemaRegistryClient


class DummyResponse:
    """Minimal response object for simulating ``requests`` replies."""

    def __init__(self) -> None:
        self.status_code = 200

    def raise_for_status(self) -> None:
        """Pretend the request succeeded."""
        pass


def test_register_includes_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Authorization header is sent when a token is provided."""

    client = SchemaRegistryClient("http://registry", token="tkn")

    def fake_post(url: str, json: dict, headers: dict | None = None, timeout: int = 5):
        assert headers == {"Authorization": "Bearer tkn"}
        return DummyResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    client.register("subject", {})


def test_register_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client retries when the registry is temporarily unavailable."""

    client = SchemaRegistryClient("http://registry")
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise requests.RequestException("boom")
        return DummyResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    client.register("subject", {})
    assert calls["count"] == 3
