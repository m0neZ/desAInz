"""Integration test for end-to-end workflow via orchestrator."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend" / "orchestrator"))

import types

otel_mod = types.ModuleType("opentelemetry.exporter.otlp.proto.http.trace_exporter")
otel_mod.OTLPSpanExporter = object  # type: ignore[attr-defined]
sys.modules.setdefault(
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    otel_mod,
)
os.makedirs("/run/secrets", exist_ok=True)

from orchestrator import idea_job
from orchestrator import ops


class DummyResponse:
    """Simple stand-in for :class:`requests.Response`."""

    def __init__(self, data: dict[str, object]) -> None:
        self._data = data
        self.status_code = 200

    def json(self) -> dict[str, object]:
        """Return payload."""
        return self._data

    def raise_for_status(self) -> None:  # pragma: no cover
        """Do nothing as errors are not simulated."""
        return None


def _mock_post(url: str, *args: object, **kwargs: object) -> DummyResponse:
    if url.endswith("/ingest"):
        return DummyResponse({"signals": ["s1"]})
    if url.endswith("/score"):
        return DummyResponse({"score": 0.5})
    if url.endswith("/generate"):
        return DummyResponse({"items": ["mockup.png"]})
    if url.endswith("/publish"):
        return DummyResponse({"task_id": 1})
    raise ValueError(f"unexpected url {url}")


@pytest.mark.usefixtures("monkeypatch")
def test_full_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Execute the orchestrator job through all stages."""

    class MockClient:
        async def __aenter__(self) -> "MockClient":
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: type[BaseException] | None,
        ) -> None:
            return None

        async def get(self, url: str, *args: object, **kwargs: object) -> DummyResponse:
            return DummyResponse({"approved": True})

    monkeypatch.setattr(
        ops,
        "requests",
        SimpleNamespace(post=_mock_post),
    )
    monkeypatch.setattr(ops.httpx, "AsyncClient", MockClient)
    os.environ["APPROVAL_SERVICE_URL"] = "http://approval"
    result = idea_job.execute_in_process()
    assert result.success
