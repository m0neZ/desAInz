# flake8: noqa
"""Tests for standardized error handling utilities."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from flask import Flask, abort

from backend.shared.error_handling import add_exception_handlers


def test_fastapi_error_response_schema() -> None:
    """Ensure FastAPI apps return standardized error responses."""
    app = FastAPI()
    add_exception_handlers(app)

    @app.get("/fail")
    async def fail() -> None:
        raise HTTPException(status_code=400, detail="bad")

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("boom")

    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get("/fail")
    body = resp.json()
    assert resp.status_code == 400
    assert set(body) == {"detail", "correlation_id", "trace_id"}

    resp = client.get("/boom")
    body = resp.json()
    assert resp.status_code == 500
    assert body["detail"] == "Internal Server Error"


def test_flask_error_response_schema() -> None:
    """Ensure Flask apps return standardized error responses."""
    app = Flask(__name__)
    add_exception_handlers(app)

    @app.route("/fail")
    def fail() -> None:  # type: ignore[return-value]
        abort(400, description="bad")

    @app.route("/boom")
    def boom() -> None:  # type: ignore[return-value]
        raise RuntimeError("boom")

    client = app.test_client()

    resp = client.get("/fail")
    body = resp.get_json()
    assert resp.status_code == 400
    assert set(body) == {"detail", "correlation_id", "trace_id"}

    resp = client.get("/boom")
    body = resp.get_json()
    assert resp.status_code == 500
    assert body["detail"] == "Internal Server Error"
