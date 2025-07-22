"""Tests for HTTP retry helpers."""

from __future__ import annotations

import pytest
import requests

from backend.shared.http import request_with_retry


def test_request_with_retry_success(requests_mock):
    """Request succeeds after a retry."""
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
    """Retrying request fails and raises an exception."""

    requests_mock.get("http://example.com", exc=requests.ConnectionError)
    with pytest.raises(requests.ConnectionError):
        request_with_retry("GET", "http://example.com", retries=2)


def test_request_with_retry_custom_session(requests_mock):
    """Custom session is used for the request."""

    session = requests.Session()
    requests_mock.get(
        "http://example.com",
        [
            {"status_code": 500},
            {"text": "ok"},
        ],
    )
    resp = request_with_retry(
        "GET",
        "http://example.com",
        retries=2,
        session=session,
    )
    assert resp.text == "ok"
    assert requests_mock.call_count == 2
