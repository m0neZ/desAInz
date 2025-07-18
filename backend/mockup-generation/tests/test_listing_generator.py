"""Tests for :mod:`mockup_generation.listing_generator`."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))  # noqa: E402

from mockup_generation.listing_generator import ListingGenerator  # noqa: E402


class DummyResponse:
    """Minimal :class:`requests.Response` replacement."""

    def __init__(self, data: dict[str, object]) -> None:
        """Store ``data`` as JSON payload."""
        self._data = data
        self.status_code = 200

    def json(self) -> dict[str, object]:
        """Return JSON payload."""
        return self._data

    def raise_for_status(self) -> None:  # pragma: no cover
        """Pretend the request succeeded."""
        return None


@pytest.fixture()
def fake_post(monkeypatch: pytest.MonkeyPatch):
    """Fixture patching :func:`requests.Session.post`."""
    calls: dict[str, object] = {}

    def _fake(url: str, **kwargs: object) -> DummyResponse:
        calls["url"] = url
        return DummyResponse(kwargs.get("payload", {}))

    monkeypatch.setattr("requests.Session.post", _fake)
    return calls


def test_generate_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """Metadata should be parsed from the OpenAI response."""
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "title": "T",
                            "description": "D",
                            "tags": ["a"],
                        }
                    )
                }
            }
        ]
    }

    def _post(url: str, **kwargs: object) -> DummyResponse:
        return DummyResponse(payload)

    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr("requests.Session.post", _post)
    gen = ListingGenerator()
    result = gen.generate(["cat"])
    assert result.title == "T"
    assert result.description == "D"
    assert result.tags == ["a"]


def test_generate_claude(monkeypatch: pytest.MonkeyPatch) -> None:
    """Metadata should be parsed from the Claude response."""
    payload = {
        "content": [
            {
                "text": json.dumps(
                    {
                        "title": "T2",
                        "description": "D2",
                        "tags": ["b"],
                    }
                )
            }
        ]
    }

    def _post(url: str, **kwargs: object) -> DummyResponse:
        return DummyResponse(payload)

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("CLAUDE_API_KEY", "x")
    monkeypatch.setattr("requests.Session.post", _post)
    gen = ListingGenerator()
    result = gen.generate(["dog"])
    assert result.title == "T2"
    assert result.description == "D2"
    assert result.tags == ["b"]
