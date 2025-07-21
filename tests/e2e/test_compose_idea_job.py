"""End-to-end pipeline test running against Docker Compose services."""

import os
import subprocess
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Iterator

import psycopg2
import pytest
import requests
from dagster import DagsterInstance

from orchestrator import idea_job

COMPOSE_FILES = ["docker-compose.dev.yml", "docker-compose.test.yml"]
DB_DSN = "postgresql://user:password@localhost:5432/app_test"


class _ApprovalHandler(BaseHTTPRequestHandler):
    """Respond with approval for any request."""

    def do_GET(self) -> None:  # noqa: D401
        """Return a simple approval payload."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"approved": true}')

    def log_message(self, *args: object) -> None:  # noqa: D401
        """Silence default request logging."""
        return None


@pytest.fixture(scope="module")
def approval_server() -> Iterator[str]:
    """Run a tiny HTTP server that always approves runs."""

    server = HTTPServer(("localhost", 0), _ApprovalHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    url = f"http://localhost:{server.server_port}"
    try:
        yield url
    finally:
        server.shutdown()
        thread.join()


@pytest.fixture(scope="module")
def compose_services(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """Start required Docker Compose services."""

    override = tmp_path_factory.mktemp("compose") / "override.yml"
    override.write_text(
        """
services:
  scoring-engine:
    environment:
      METRICS_DB_URL: postgresql://user:password@postgres:5432/app_test
  monitoring:
    environment:
      METRICS_DB_URL: postgresql://user:password@postgres:5432/app_test
""",
    )
    cmd = [
        "docker-compose",
        *sum([["-f", f] for f in COMPOSE_FILES + [str(override)]], []),
        "up",
        "-d",
        "postgres",
        "redis",
        "scoring-engine",
        "signal-ingestion",
        "marketplace-publisher",
        "mockup-generation",
        "monitoring",
    ]
    subprocess.run(cmd, check=True)
    try:
        subprocess.run(["scripts/wait-for-services.sh"], check=True)
        yield
    finally:
        subprocess.run(
            [
                "docker-compose",
                *sum([["-f", f] for f in COMPOSE_FILES + [str(override)]], []),
                "down",
                "-v",
            ],
            check=True,
        )


def _wait(url: str, timeout: int = 60) -> None:
    """Block until ``url`` responds or ``timeout`` expires."""

    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code < 500:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"timed out waiting for {url}")


def test_idea_job_end_to_end(compose_services: None, approval_server: str) -> None:
    """Run ``idea_job`` against real services and verify side effects."""
    os.environ.update(
        {
            "SIGNAL_INGESTION_URL": "http://localhost:8004",
            "SCORING_ENGINE_URL": "http://localhost:5002",
            "MOCKUP_GENERATION_URL": "http://localhost:8000",
            "PUBLISHER_URL": "http://localhost:8003",
            "APPROVAL_SERVICE_URL": approval_server,
        }
    )
    _wait("http://localhost:8004/ready")
    _wait("http://localhost:5002/ready")
    _wait("http://localhost:8003/ready")

    instance = DagsterInstance.ephemeral()
    result = idea_job.execute_in_process(instance=instance)
    assert result.success

    with psycopg2.connect(DB_DSN) as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM listings")
        listings = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM scores")
        scores = cur.fetchone()[0]
    assert listings > 0
    assert scores > 0
