from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Iterator

from pathlib import Path

from dagster import DagsterInstance
import pytest

ROOT = Path(__file__).resolve().parents[3]
import sys

sys.path.append(str(ROOT))  # noqa: E402

from orchestrator.jobs import idea_job


@contextmanager
def run_mock_server() -> Iterator[tuple[str, list[str]]]:
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
                payload = {"items": ["i1"]}
            elif self.path == "/publish":
                payload = {"task_id": 1}
            else:
                payload = {}
            self.wfile.write(json.dumps(payload).encode())

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
        monkeypatch.setenv("APPROVE_PUBLISHING", "true")
        instance = DagsterInstance.ephemeral()
        result = idea_job.execute_in_process(instance=instance)
        assert result.success
        assert calls == ["/ingest", "/score", "/generate", "/publish"]
