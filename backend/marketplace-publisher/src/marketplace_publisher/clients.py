"""Marketplace API clients with Selenium fallback and OAuth support."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import os
import requests
from backend.shared.http import request_with_retry
from requests_oauthlib import OAuth2Session
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import asyncio

from datetime import datetime

from .settings import settings

from .db import (
    Marketplace,
    get_oauth_token_sync,
    upsert_oauth_token_sync,
)
from . import rules


class BaseClient:
    """Base class for marketplace API clients with OAuth helpers."""

    def __init__(
        self,
        marketplace: Marketplace,
        base_url: str,
        token_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        api_key: str | None = None,
        authorize_url: str | None = None,
        redirect_uri: str | None = None,
        scope: str | None = None,
        publish_path: str = "/publish",
        metrics_path_template: str = "/listings/{listing_id}/metrics",
    ) -> None:
        """Initialize API configuration and credentials."""
        self.marketplace = marketplace
        self.base_url = base_url.rstrip("/")
        self.token_url = token_url
        self.publish_url = f"{self.base_url}{publish_path}"
        self.metrics_path_template = f"{self.base_url}{metrics_path_template}"
        self.authorize_url = authorize_url
        self.redirect_uri = redirect_uri or ""
        self.scope: list[str] | None = scope.split() if scope else None
        self._client_id = client_id or ""
        self._client_secret = client_secret or ""
        self._api_key = api_key or ""
        self._token: str | None = None
        self._refresh_token: str | None = None
        self._expiry: float | None = None
        self._state: str | None = None
        stored = get_oauth_token_sync(self.marketplace)
        if stored is not None:
            self._token = stored.access_token
            self._refresh_token = stored.refresh_token
            self._expiry = stored.expires_at.timestamp() if stored.expires_at else None

    def _fetch_new_token(self, grant_data: dict[str, str]) -> None:
        """Retrieve a token from ``token_url`` using ``grant_data``."""
        if not (self.token_url and self._client_id and self._client_secret):
            return
        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            **grant_data,
        }
        response = request_with_retry("POST", self.token_url, data=data, timeout=30)
        payload = response.json()
        self._token = payload.get("access_token")
        self._refresh_token = payload.get("refresh_token", self._refresh_token)
        expires_in = int(payload.get("expires_in", 0))
        self._expiry = time.time() + expires_in if expires_in else None
        upsert_oauth_token_sync(
            self.marketplace,
            self._token,
            self._refresh_token,
            datetime.fromtimestamp(self._expiry) if self._expiry else None,
        )

    def _get_token(self) -> str | None:
        """Return a cached token refreshing if expired."""
        if not self._token or (self._expiry and self._expiry <= time.time()):
            self._fetch_new_token({"grant_type": "client_credentials"})
        return self._token

    def _refresh_token_if_needed(self) -> None:
        """Refresh token using ``refresh_token`` or client credentials."""
        if self._refresh_token:
            self._fetch_new_token(
                {"grant_type": "refresh_token", "refresh_token": self._refresh_token}
            )
        else:
            self._fetch_new_token({"grant_type": "client_credentials"})

    def get_authorization_url(self) -> str:
        """Return the authorization URL for user consent."""
        if not (self.authorize_url and self._client_id and self.redirect_uri):
            msg = "OAuth flow not configured"
            raise RuntimeError(msg)
        oauth = OAuth2Session(
            self._client_id, redirect_uri=self.redirect_uri, scope=self.scope
        )
        url, state = cast(tuple[str, str], oauth.authorization_url(self.authorize_url))
        self._state = state
        return url

    def fetch_token(self, authorization_response: str) -> None:
        """Exchange the authorization response URL for an access token."""
        if not (self.token_url and self._client_id and self._client_secret):
            msg = "OAuth flow not configured"
            raise RuntimeError(msg)
        oauth = OAuth2Session(
            self._client_id,
            redirect_uri=self.redirect_uri,
            state=self._state,
        )
        token = oauth.fetch_token(
            self.token_url,
            authorization_response=authorization_response,
            client_secret=self._client_secret,
        )
        self._token = token.get("access_token")
        self._refresh_token = token.get("refresh_token", self._refresh_token)
        expires_in = int(token.get("expires_in", 0))
        self._expiry = time.time() + expires_in if expires_in else None
        upsert_oauth_token_sync(
            self.marketplace,
            self._token,
            self._refresh_token,
            datetime.fromtimestamp(self._expiry) if self._expiry else None,
        )

    def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
        """Upload a design and return the created listing ID."""
        headers: dict[str, str] = {}
        token = self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        with open(design_path, "rb") as file:
            files = {"file": file}
            response = request_with_retry(
                "POST",
                self.publish_url,
                files=files,
                data=metadata,
                headers=headers,
                timeout=30,
            )
        if response.status_code == 401:
            self._refresh_token_if_needed()
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            with open(design_path, "rb") as file:
                files = {"file": file}
                response = request_with_retry(
                    "POST",
                    self.publish_url,
                    files=files,
                    data=metadata,
                    headers=headers,
                    timeout=30,
                )
        response.raise_for_status()
        data = response.json()
        return str(data["id"])

    def get_listing_metrics(self, listing_id: int) -> dict[str, Any]:
        """Return performance metrics for a listing."""
        headers: dict[str, str] = {}
        token = self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        metrics_url = self.metrics_path_template.format(listing_id=listing_id)
        response = request_with_retry("GET", metrics_url, headers=headers, timeout=30)
        if response.status_code == 401:
            self._refresh_token_if_needed()
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            response = request_with_retry(
                "GET", metrics_url, headers=headers, timeout=30
            )
        return cast(dict[str, Any], response.json())


class RedbubbleClient(BaseClient):
    """Client for the Redbubble API."""

    def __init__(self) -> None:
        """Configure endpoints and credentials from settings."""
        super().__init__(
            Marketplace.redbubble,
            "https://api.redbubble.com/v1",
            settings.redbubble_token_url,
            settings.redbubble_client_id,
            settings.redbubble_client_secret,
            settings.redbubble_api_key,
            settings.redbubble_authorize_url,
            settings.redbubble_redirect_uri,
            settings.redbubble_scope,
            publish_path="/works",
            metrics_path_template="/works/{listing_id}/metrics",
        )


class AmazonMerchClient(BaseClient):
    """Client for the Amazon Merch API."""

    def __init__(self) -> None:
        """Configure endpoints and credentials from settings."""
        super().__init__(
            Marketplace.amazon_merch,
            "https://merch.amazon.com/api",
            settings.amazon_merch_token_url,
            settings.amazon_merch_client_id,
            settings.amazon_merch_client_secret,
            settings.amazon_merch_api_key,
            settings.amazon_merch_authorize_url,
            settings.amazon_merch_redirect_uri,
            settings.amazon_merch_scope,
            publish_path="/listings",
            metrics_path_template="/listings/{listing_id}/metrics",
        )


class EtsyClient(BaseClient):
    """Client for the Etsy API."""

    def __init__(self) -> None:
        """Configure endpoints and credentials from settings."""
        super().__init__(
            Marketplace.etsy,
            "https://openapi.etsy.com/v3/application",
            settings.etsy_token_url,
            settings.etsy_client_id,
            settings.etsy_client_secret,
            settings.etsy_api_key,
            settings.etsy_authorize_url,
            settings.etsy_redirect_uri,
            settings.etsy_scope,
            publish_path="/listings",
            metrics_path_template="/listings/{listing_id}/stats",
        )


class Society6Client(BaseClient):
    """Client for the Society6 API."""

    def __init__(self) -> None:
        """Configure endpoints and credentials from settings."""
        super().__init__(
            Marketplace.society6,
            "https://api.society6.com/v1",
            settings.society6_token_url,
            settings.society6_client_id,
            settings.society6_client_secret,
            settings.society6_api_key,
            settings.society6_authorize_url,
            settings.society6_redirect_uri,
            settings.society6_scope,
            publish_path="/products",
            metrics_path_template="/products/{listing_id}/stats",
        )


class ZazzleClient(BaseClient):
    """Client for the Zazzle API."""

    def __init__(self) -> None:
        """Configure endpoints and credentials from settings."""
        super().__init__(
            Marketplace.zazzle,
            "https://api.zazzle.com/v1",
            settings.zazzle_token_url,
            settings.zazzle_client_id,
            settings.zazzle_client_secret,
            settings.zazzle_api_key,
            settings.zazzle_authorize_url,
            settings.zazzle_redirect_uri,
            settings.zazzle_scope,
            publish_path="/products",
            metrics_path_template="/products/{listing_id}/metrics",
        )


class SeleniumFallback:
    """Publish a design using browser automation if APIs fail."""

    def __init__(self, screenshot_dir: Path | None = None) -> None:
        """Start a headless Firefox driver."""
        options = Options()
        options.add_argument("--headless")
        if os.getenv("SELENIUM_SKIP") == "1":
            self.driver = None
        else:
            self.driver = webdriver.Firefox(options=options)
        self.screenshot_dir = screenshot_dir or Path("screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    async def publish(
        self,
        marketplace: Marketplace,
        design_path: Path,
        metadata: dict[str, Any],
        max_attempts: int = 3,
    ) -> None:
        """
        Publish a design using browser automation.

        The function fills the configured form fields, submitting the design
        when all interactions succeed. Failures trigger retries using
        exponential backoff. Each failed attempt stores a screenshot and
        captured browser logs in ``screenshot_dir``.
        """
        if self.driver is None:
            return
        selectors = rules.get_selectors(marketplace)
        if selectors is None:
            msg = f"selectors not configured for {marketplace.value}"
            raise RuntimeError(msg)

        url = selectors.get("url")
        if not url:
            msg = f"url selector missing for {marketplace.value}"
            raise RuntimeError(msg)

        attempts = 0
        while True:
            try:
                self.driver.get(url)
                self.driver.find_element(
                    "css selector", selectors["upload_input"]
                ).send_keys(str(design_path))
                self.driver.find_element(
                    "css selector", selectors["title_input"]
                ).send_keys(metadata.get("title", ""))
                if "description_input" in selectors:
                    self.driver.find_element(
                        "css selector", selectors["description_input"]
                    ).send_keys(metadata.get("description", ""))
                if "tags_input" in selectors and metadata.get("tags"):
                    tags = metadata.get("tags")
                    joined = ",".join(cast(list[str], tags))
                    self.driver.find_element(
                        "css selector", selectors["tags_input"]
                    ).send_keys(joined)
                if "price_input" in selectors and "price" in metadata:
                    el = self.driver.find_element(
                        "css selector", selectors["price_input"]
                    )
                    el.clear()
                    el.send_keys(str(metadata["price"]))
                self.driver.find_element(
                    "css selector", selectors["submit_button"]
                ).click()
                break
            except Exception:
                attempts += 1
                ts = int(time.time())
                screenshot_path = (
                    self.screenshot_dir / f"{marketplace.value}_{ts}_{attempts}.png"
                )
                log_path = (
                    self.screenshot_dir / f"{marketplace.value}_{ts}_{attempts}.log"
                )
                await asyncio.to_thread(
                    self.driver.save_screenshot, str(screenshot_path)
                )
                try:
                    logs = await asyncio.to_thread(self.driver.get_log, "browser")
                    log_path.write_text("\n".join(str(entry) for entry in logs))
                except Exception:  # pragma: no cover - logging optional
                    pass
                if attempts >= max_attempts:
                    raise
                time.sleep(min(2**attempts, 30))
