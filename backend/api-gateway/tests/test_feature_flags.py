import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
import importlib  # noqa: E402
import fakeredis.aioredis  # noqa: E402

from api_gateway.auth import create_access_token  # noqa: E402
from backend.shared import feature_flags  # noqa: E402


def setup_module(module: object) -> None:
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    feature_flags.redis.Redis = lambda *a, **k: fakeredis.aioredis.FakeRedis(
        decode_responses=True
    )
    import api_gateway.routes as routes
    routes.get_async_client = lambda: fakeredis.aioredis.FakeRedis()
    import api_gateway.main as main_module
    importlib.reload(main_module)
    importlib.reload(feature_flags)
    feature_flags.initialize()
    global client
    client = TestClient(main_module.app)


def test_toggle_flag() -> None:
    token = create_access_token({"sub": "admin"})
    resp = client.post(
        "/feature-flags/demo",
        json={"enabled": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    resp = client.get("/feature-flags", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json().get("demo") is True

