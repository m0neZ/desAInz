"""Tests for trademark checking utilities."""

from __future__ import annotations

import requests

import pytest

from marketplace_publisher.trademark import is_trademarked


class DummyResponse:
    """Minimal response stub for ``requests``."""

    def __init__(self, json_data: dict[str, int]):
        """Store ``json_data`` for later retrieval."""
        self._json_data = json_data

    def raise_for_status(self) -> None:
        """Mimic ``requests.Response.raise_for_status``."""
        return None

    def json(self) -> dict[str, int]:
        """Return the stored JSON payload."""
        return self._json_data


@pytest.mark.parametrize("total", [0, 1])
def test_is_trademarked(monkeypatch: pytest.MonkeyPatch, total: int) -> None:
    """Check trademark detection based on API response."""

    def fake_get(*args: str, **kwargs: str) -> DummyResponse:  # noqa: ANN001
        return DummyResponse({"totalRows": total})

    monkeypatch.setattr(requests, "get", fake_get)
    assert is_trademarked("test") is (total > 0)
