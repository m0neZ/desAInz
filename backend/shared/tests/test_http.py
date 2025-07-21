"""Tests for HTTP retry helpers."""

from __future__ import annotations

import pytest
import requests

from backend.shared.http import request_with_retry


def test_request_with_retry_success(requests_mock):
    requests_mock.get(
        "http://example.com",
        [
            {"status_code": 500},
            {"text": "ok"},
        ],
    )
    resp = request_with_retry("GET", "http://example.com", retries=2)
    assert resp.text == "ok"
    assert requests_mock.call_count == 2


def test_request_with_retry_failure(requests_mock):
    requests_mock.get("http://example.com", exc=requests.ConnectionError)
    with pytest.raises(requests.ConnectionError):
        request_with_retry("GET", "http://example.com", retries=2)
