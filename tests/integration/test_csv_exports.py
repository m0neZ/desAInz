from __future__ import annotations  # noqa: D100

"""Integration tests for CSV export endpoints."""  # noqa: D400

import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.append(
    str(Path(__file__).resolve().parents[2] / "backend" / "api-gateway" / "src")
)

from api_gateway.auth import create_access_token  # noqa: E402
from backend.analytics import api  # noqa: E402
from backend.shared.db import Base, engine, SessionLocal  # noqa: E402
from backend.shared.db.models import (  # noqa: E402
    UserRole,
    ABTest,
    ABTestResult,
    MarketplaceMetric,
)


def setup_module(module: object) -> None:
    """Populate in-memory database with sample data."""
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        session.add(UserRole(username="editor", role="editor"))
        ab_test = ABTest(listing_id=1, variant="A", conversion_rate=0)
        session.add(ab_test)
        session.commit()
        session.refresh(ab_test)
        session.add_all(
            [
                ABTestResult(ab_test_id=ab_test.id, conversions=1, impressions=2),
                ABTestResult(ab_test_id=ab_test.id, conversions=3, impressions=4),
            ]
        )
        session.add(MarketplaceMetric(listing_id=1, clicks=5, purchases=1, revenue=9.0))
        session.commit()


def teardown_module(module: object) -> None:
    """Clean up tables after tests."""
    Base.metadata.drop_all(engine)


client = TestClient(api.app)
TOKEN = create_access_token({"sub": "editor"})


def test_ab_test_csv_export() -> None:
    """A/B test results CSV is returned with editor role."""
    resp = client.get(
        "/ab_test_results/1/csv",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    body = resp.text.strip().splitlines()
    assert body[0] == "timestamp,conversions,impressions"
    assert len(body) == 3


def test_marketplace_csv_export() -> None:
    """Marketplace metrics CSV is returned with editor role."""
    resp = client.get(
        "/marketplace_metrics/1/csv",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert resp.text.startswith("timestamp,clicks,purchases,revenue")
