"""VCR tests for HTTP interactions."""

from __future__ import annotations

import pytest
import requests


@pytest.mark.vcr()
def test_httpbin() -> None:
    """Record GET request to httpbin and assert response."""
    response = requests.get("https://httpbin.org/get", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://httpbin.org/get"
