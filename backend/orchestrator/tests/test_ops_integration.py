"""Integration tests for orchestrator ops."""  # noqa: E402

from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Iterator

from pathlib import Path

from dagster import DagsterInstance
import httpx
import pytest
import types

ROOT = Path(__file__).resolve().parents[3]
import sys

sys.path.append(str(ROOT))  # noqa: E402

from orchestrator.jobs import idea_job
from orchestrator.ops import publish_content


@contextmanager
def run_mock_server(
    generated_items: list[str] | None = None,
) -> Iterator[tuple[str, list[str]]]:
    """
    Run a simple HTTP server collecting request paths.

    Parameters
    ----------
    generated_items:
        Items returned by the ``/generate`` endpoint. Defaults to ``["i1"]``.
    """
    calls: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: D401 - test helper
            calls.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if self.path == "/ingest":
                payload = {"signals": ["s1"]}
            elif self.path == "/score":
                payload = {"score": 1}
            elif self.path == "/generate":
                payload = {"items": generated_items or ["i1"]}
            elif self.path == "/publish":
                payload = {"task_id": 1}
            else:
                payload = {}
            self.wfile.write(json.dumps(payload).encode())

        def do_GET(self) -> None:  # noqa: D401 - test helper
            calls.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"approved": true}')

        def log_message(self, *args: object) -> None:  # noqa: D401 - silence logs
            return

    server = HTTPServer(("localhost", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    url = f"http://localhost:{server.server_port}"
    try:
        yield url, calls
    finally:
        server.shutdown()
        thread.join()


def test_idea_job_integration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the idea job against a mock HTTP server."""
    with run_mock_server() as (url, calls):
        monkeypatch.setenv("SIGNAL_INGESTION_URL", url)
        monkeypatch.setenv("SCORING_ENGINE_URL", url)
        monkeypatch.setenv("MOCKUP_GENERATION_URL", url)
        monkeypatch.setenv("PUBLISHER_URL", url)
        monkeypatch.setenv("APPROVAL_SERVICE_URL", url)
        instance = DagsterInstance.ephemeral()
        result = idea_job.execute_in_process(instance=instance)
        assert result.success
        assert calls == [
            "/ingest",
            "/score",
            "/generate",
            f"/approvals/{result.dagster_run.run_id}",
            "/publish",
        ]


@pytest.mark.asyncio()
async def test_publish_multiple_items(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify multiple items are published concurrently."""

    calls: list[str] = []

    async def fake_post(
        self: object, url: str, *args: object, **kwargs: object
    ) -> object:
        calls.append(url)

        class Resp:
            def raise_for_status(self) -> None:  # noqa: D401 - test helper
                return None

            def json(self) -> dict[str, object]:  # noqa: D401 - test helper
                return {"task_id": len(calls)}

        return Resp()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setenv("PUBLISHER_URL", "http://publisher")
    monkeypatch.setenv("PUBLISH_CONCURRENCY", "2")

    class DummyLog:
        def info(self, *args: object, **kwargs: object) -> None:  # noqa: D401
            return None

        debug = warning = error = info

    ctx = types.SimpleNamespace(run_id="r1", log=DummyLog())

    await publish_content.compute_fn.decorated_fn(ctx, ["a", "b", "c"])

    assert calls == [
        "http://publisher/publish",
        "http://publisher/publish",
        "http://publisher/publish",
    ]
