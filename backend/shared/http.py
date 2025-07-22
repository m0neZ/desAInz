"""HTTP request helpers with retry support."""

from __future__ import annotations

import os
from typing import Any

import requests

import httpx

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

DEFAULT_RETRIES = int(os.getenv("HTTP_RETRIES", "3"))
DEFAULT_TIMEOUT = httpx.Timeout(10.0)

__all__ = ["request_with_retry", "DEFAULT_TIMEOUT"]


def request_with_retry(
    method: str,
    url: str,
    *,
    retries: int | None = None,
    session: requests.Session | None = None,
    **kwargs: Any,
) -> requests.Response:
    """Return the response from ``requests`` with exponential backoff.

    Parameters
    ----------
    method:
        HTTP method to use for the request.
    url:
        Target URL for the request.
    retries:
        Maximum number of attempts before giving up. Defaults to
        ``DEFAULT_RETRIES`` when ``None``.
    session:
        Optional :class:`requests.Session` to use for sending the request.
    **kwargs:
        Additional keyword arguments forwarded to ``requests``.
    """
    attempts = retries or DEFAULT_RETRIES

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(attempts),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )
    def _send() -> requests.Response:
        requester = session or requests
        resp = requester.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp

    return _send()
