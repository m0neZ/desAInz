"""WebSocket metrics integration test."""

from __future__ import annotations

import asyncio
import importlib
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any

import fakeredis.aioredis
import pytest
import uvicorn
import websockets
from fastapi import FastAPI
import warnings

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402
sys.path.append(
    str(Path(__file__).resolve().parents[2] / "signal-ingestion" / "src")
)  # noqa: E402


def _start_server(app: FastAPI, port: int) -> tuple[uvicorn.Server, threading.Thread]:
    """Start ``app`` using Uvicorn on ``port`` and return server and thread."""
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        with socket.socket() as sock:
            try:
                sock.connect(("127.0.0.1", port))
                break
            except OSError:
                time.sleep(0.1)
    return server, thread


@pytest.mark.asyncio  # type: ignore[misc]
async def test_metrics_ws(monkeypatch: Any) -> None:
    """Verify metrics are streamed over websockets."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import backend.shared.config as shared_config

    shared_config.settings.redis_url = "redis://localhost:6379/0"
    monkeypatch.setattr(
        "backend.shared.cache.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
    import api_gateway.main as main_module
    import api_gateway.routes as routes

    monkeypatch.setattr(
        "api_gateway.routes.get_async_client", lambda: fakeredis.aioredis.FakeRedis()
    )
    os.environ["MONITORING_URL"] = "http://127.0.0.1:9002"
    if hasattr(main_module, "REQUEST_LATENCY"):
        import prometheus_client

        prometheus_client.REGISTRY.unregister(main_module.REQUEST_LATENCY)
        prometheus_client.REGISTRY.unregister(main_module.ERROR_COUNTER)
    importlib.reload(main_module)
    importlib.reload(routes)
    main_module.rate_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.optimization_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.monitoring_limiter._redis = fakeredis.aioredis.FakeRedis()
    routes.analytics_limiter._redis = fakeredis.aioredis.FakeRedis()

    monitoring_app = FastAPI()

    @monitoring_app.get("/overview")  # type: ignore[misc]
    async def overview() -> dict[str, int]:
        return {"cpu_percent": 1}

    @monitoring_app.get("/analytics")  # type: ignore[misc]
    async def analytics() -> dict[str, int]:
        return {"active_users": 2}

    mon_server, mon_thread = _start_server(monitoring_app, 9002)
    gw_server, gw_thread = _start_server(main_module.app, 9001)

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    try:
        async with websockets.connect("ws://127.0.0.1:9001/ws/metrics") as ws:
            data = json.loads(await ws.recv())
            assert data == {"cpu_percent": 1, "active_users": 2}
    finally:
        gw_server.should_exit = True
        mon_server.should_exit = True
        gw_thread.join()
        mon_thread.join()
