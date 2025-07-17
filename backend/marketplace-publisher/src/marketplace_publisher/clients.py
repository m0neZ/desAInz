"""Marketplace API clients with Selenium fallback and OAuth support."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import os
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from .db import Marketplace


class BaseClient:
    """Base class for marketplace API clients with OAuth helpers."""

    def __init__(
        self,
        base_url: str,
        token_url: str | None = None,
        client_id_env: str | None = None,
        client_secret_env: str | None = None,
        api_key_env: str | None = None,
    ) -> None:
        """Initialize API configuration and credentials."""
        self.base_url = base_url.rstrip("/")
        self.token_url = token_url
        self._client_id = os.getenv(client_id_env or "")
        self._client_secret = os.getenv(client_secret_env or "")
        self._api_key = os.getenv(api_key_env or "")
        self._token: str | None = None

    def _get_token(self) -> str | None:
        """Retrieve an OAuth token if configuration is provided."""
        if self._token:
            return self._token
        if self.token_url and self._client_id and self._client_secret:
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                timeout=30,
            )
            response.raise_for_status()
            self._token = response.json().get("access_token")
            return self._token
        return None

    def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
        """Upload a design and return the created listing ID."""
        headers = {}
        token = self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        with open(design_path, "rb") as file:
            files = {"file": file}
            response = requests.post(
                f"{self.base_url}/publish",
                files=files,
                data=metadata,
                headers=headers,
                timeout=30,
            )
        response.raise_for_status()
        data = response.json()
        return str(data["id"])


class RedbubbleClient(BaseClient):
    """Client for the Redbubble API."""

    def __init__(self) -> None:
        """Configure endpoints and credentials from the environment."""
        super().__init__(
            "https://api.redbubble.com/v1",
            os.getenv("REDBUBBLE_TOKEN_URL"),
            "REDBUBBLE_CLIENT_ID",
            "REDBUBBLE_CLIENT_SECRET",
            "REDBUBBLE_API_KEY",
        )


class AmazonMerchClient(BaseClient):
    """Client for the Amazon Merch API."""

    def __init__(self) -> None:
        """Configure endpoints and credentials from the environment."""
        super().__init__(
            "https://api.amazonmerch.com/v1",
            os.getenv("AMAZON_MERCH_TOKEN_URL"),
            "AMAZON_MERCH_CLIENT_ID",
            "AMAZON_MERCH_CLIENT_SECRET",
            "AMAZON_MERCH_API_KEY",
        )


class EtsyClient(BaseClient):
    """Client for the Etsy API."""

    def __init__(self) -> None:
        """Configure endpoints and credentials from the environment."""
        super().__init__(
            "https://api.etsy.com/v3",
            os.getenv("ETSY_TOKEN_URL"),
            "ETSY_CLIENT_ID",
            "ETSY_CLIENT_SECRET",
            "ETSY_API_KEY",
        )


class Society6Client(BaseClient):
    """Client for the Society6 API."""

    def __init__(self) -> None:
        """Configure endpoints and credentials from the environment."""
        super().__init__(
            "https://api.society6.com/v1",
            os.getenv("SOCIETY6_TOKEN_URL"),
            "SOCIETY6_CLIENT_ID",
            "SOCIETY6_CLIENT_SECRET",
            "SOCIETY6_API_KEY",
        )


class SeleniumFallback:
    """Publish a design using browser automation if APIs fail."""

    def __init__(self) -> None:
        """Start a headless Firefox driver."""
        options = Options()
        options.add_argument("--headless")
        if os.getenv("SELENIUM_SKIP") == "1":
            self.driver = None
        else:
            self.driver = webdriver.Firefox(options=options)

    def publish(
        self, marketplace: Marketplace, design_path: Path, metadata: dict[str, Any]
    ) -> None:
        """Automate browser interactions for publishing a design."""
        url = {
            Marketplace.redbubble: "https://www.redbubble.com/upload",
            Marketplace.amazon_merch: "https://merch.amazon.com/create",
            Marketplace.etsy: "https://www.etsy.com/new",
        }[marketplace]
        if self.driver is None:
            return
        self.driver.get(url)
        # This is a placeholder; real implementation would interact with the page.
        upload = self.driver.find_element("id", "upload")
        upload.send_keys(str(design_path))
        title = self.driver.find_element("id", "title")
        title.send_keys(metadata.get("title", ""))
        submit = self.driver.find_element("id", "submit")
        submit.click()
