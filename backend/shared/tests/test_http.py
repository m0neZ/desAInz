"""Tests for HTTP retry helpers."""

from __future__ import annotations

import asyncio
import pytest
import requests

from backend.shared import http as http_module
from backend.shared.http import get_async_http_client, request_with_retry


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


@pytest.mark.asyncio()
async def test_cached_client_same_loop() -> None:
    """Calling helper twice in the same loop should return the same client."""

    client1 = await get_async_http_client()
    client2 = await get_async_http_client()
    assert client1 is client2
    await http_module.close_async_clients()


def test_clients_unique_per_loop() -> None:
    """Each event loop should receive its own ``AsyncClient`` instance."""

    loop1 = asyncio.new_event_loop()
    asyncio.set_event_loop(loop1)
    client1 = loop1.run_until_complete(get_async_http_client())
    loop2 = asyncio.new_event_loop()
    asyncio.set_event_loop(loop2)
    client2 = loop2.run_until_complete(get_async_http_client())
    loop2.run_until_complete(http_module.close_async_clients())
    loop1.run_until_complete(loop1.shutdown_asyncgens())
    loop2.run_until_complete(loop2.shutdown_asyncgens())
    loop1.close()
    loop2.close()
    asyncio.set_event_loop(asyncio.new_event_loop())

    assert client1 is not client2
