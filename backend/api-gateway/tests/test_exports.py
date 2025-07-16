"""Integration tests for CSV export endpoints."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from api_gateway.main import app
from api_gateway.auth import create_access_token
from backend.shared.db import session_scope
from backend.shared.db.models import ABTest, Listing
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

client = TestClient(app)


def setup_module(module: object) -> None:
    """Populate the database with sample data."""
    with session_scope() as session:
        session.query(ABTest).delete()
        session.query(Listing).delete()
        listing = Listing(
            mockup_id=1, price=9.99, created_at=datetime.now(timezone.utc)
        )
        session.add(listing)
        session.flush()
        session.add_all(
            [
                ABTest(listing_id=listing.id, variant="A", conversion_rate=0.1),
                ABTest(listing_id=listing.id, variant="B", conversion_rate=0.2),
            ]
        )
        session.commit()


def _auth_headers() -> dict[str, str]:
    token = create_access_token({"sub": "admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


def test_export_ab_tests() -> None:
    """CSV export of A/B tests should include header and rows."""
    resp = client.get("/export/ab_tests", headers=_auth_headers())
    assert resp.status_code == 200
    body = resp.text.splitlines()
    assert body[0] == "id,listing_id,variant,conversion_rate"
    assert len(body) == 3


def test_export_marketplace_stats() -> None:
    """CSV export of marketplace stats should aggregate tests."""
    resp = client.get("/export/marketplace_stats", headers=_auth_headers())
    assert resp.status_code == 200
    body = resp.text.splitlines()
    assert body[0] == "listing_id,price,num_tests"
    assert body[1].endswith(",2")
