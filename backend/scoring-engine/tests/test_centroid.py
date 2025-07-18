"""Tests for centroid scheduler and endpoint."""

# mypy: ignore-errors

from fastapi.testclient import TestClient

from scoring_engine.app import app as scoring_app
from scoring_engine.centroid_job import compute_and_store_centroids
from scoring_engine.weight_repository import get_centroid
from backend.shared.db import session_scope
from backend.shared.db.models import Embedding


def test_centroid_computation(tmp_path) -> None:
    """Compute centroid from stored embeddings."""
    with session_scope() as session:
        dim_vec1 = [1.0] + [0.0] * 767
        dim_vec2 = [0.0] * 767 + [1.0]
        session.add_all(
            [
                Embedding(source="src", embedding=dim_vec1),
                Embedding(source="src", embedding=dim_vec2),
            ]
        )
        session.flush()
    compute_and_store_centroids()
    centroid = get_centroid("src")
    expected = [0.5] + [0.0] * 766 + [0.5]
    assert centroid == expected
    client = TestClient(scoring_app)
    resp = client.get("/centroid/src")
    assert resp.status_code == 200
    assert resp.json()["centroid"] == expected
