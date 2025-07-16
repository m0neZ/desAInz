from pathlib import Path
import sys

# flake8: noqa

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from fastapi.testclient import TestClient

from api_gateway.auth import create_access_token
from api_gateway.main import app
from pytest import MonkeyPatch

client = TestClient(app)


def test_run_maintenance(monkeypatch: MonkeyPatch) -> None:
    called = {"archive": False, "purge": False}

    def archive() -> None:
        called["archive"] = True

    def purge() -> None:
        called["purge"] = True

    monkeypatch.setattr("api_gateway.routes.archive_old_mockups", archive)
    monkeypatch.setattr("api_gateway.routes.purge_stale_records", purge)

    token = create_access_token({"sub": "tester"})
    response = client.post(
        "/maintenance/run",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert called["archive"]
    assert called["purge"]
