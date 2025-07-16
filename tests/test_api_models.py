"""Tests for model management API endpoints."""

from pathlib import Path
import sys

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "api-gateway" / "src")
)  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
from api_gateway.main import app  # noqa: E402
from backend.shared.db import session_scope  # noqa: E402
from backend.shared.db.models import AIModel, UserRole  # noqa: E402
from api_gateway.auth import create_access_token  # noqa: E402

client = TestClient(app)


def test_switch_default_model() -> None:
    """Switch active model via the API and verify database state."""
    token = create_access_token({"sub": "admin"})
    with session_scope() as session:
        session.add(UserRole(username="admin", role="admin"))
        session.add(
            AIModel(id=1, name="base", version="1", model_id="model/a", is_default=True)
        )
        session.add(
            AIModel(id=2, name="new", version="2", model_id="model/b", is_default=False)
        )
        session.flush()

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/models", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.post("/models/2/default", headers=headers)
    assert response.status_code == 200
    with session_scope() as session:
        model2 = session.get(AIModel, 2)
        assert model2 is not None and model2.is_default
