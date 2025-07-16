"""Marketplace API clients with Selenium fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from .db import Marketplace


class BaseClient:
    """Base class for marketplace API clients."""

    def __init__(self, base_url: str) -> None:
        """Store the base URL for the API."""
        self.base_url = base_url.rstrip("/")

    def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
        """Upload design to the marketplace API and return listing ID."""
        files = {"file": open(design_path, "rb")}
        response = requests.post(
            f"{self.base_url}/publish", files=files, data=metadata, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return str(data["id"])


class RedbubbleClient(BaseClient):
    """Client for the Redbubble API."""

    def __init__(self) -> None:
        """Initialize the API endpoint."""
        super().__init__("https://api.redbubble.com")


class AmazonMerchClient(BaseClient):
    """Client for the Amazon Merch API."""

    def __init__(self) -> None:
        """Initialize the API endpoint."""
        super().__init__("https://api.amazonmerch.com")


class EtsyClient(BaseClient):
    """Client for the Etsy API."""

    def __init__(self) -> None:
        """Initialize the API endpoint."""
        super().__init__("https://api.etsy.com")


class SeleniumFallback:
    """Publish a design using browser automation if APIs fail."""

    def __init__(self) -> None:
        """Start a headless Firefox driver."""
        options = Options()
        options.add_argument("--headless")
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
        self.driver.get(url)
        # This is a placeholder; real implementation would interact with the page.
        upload = self.driver.find_element("id", "upload")
        upload.send_keys(str(design_path))
        title = self.driver.find_element("id", "title")
        title.send_keys(metadata.get("title", ""))
        submit = self.driver.find_element("id", "submit")
        submit.click()
