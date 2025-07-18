"""Marketplace validation rules and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml

from .db import Marketplace


@dataclass
class MarketplaceRules:
    """Validation rules for a single marketplace."""

    max_file_size_mb: int
    max_width: int
    max_height: int
    upload_limit: int
    allowed_formats: list[str] | None = None


class RulesRegistry:
    """Registry loading rules from a YAML configuration file."""

    def __init__(self, path: Path) -> None:
        """Load rules from ``path``."""
        raw = yaml.safe_load(path.read_text())
        self.rules: Mapping[Marketplace, MarketplaceRules] = {
            Marketplace(key): MarketplaceRules(**val) for key, val in raw.items()
        }

    def get(self, marketplace: Marketplace) -> MarketplaceRules | None:
        """Return rules for ``marketplace`` if available."""
        return self.rules.get(marketplace)


rules_registry: RulesRegistry | None = None


def load_rules(path: Path) -> None:
    """Load marketplace rules from ``path`` into the global registry."""
    global rules_registry  # noqa: PLW0603
    rules_registry = RulesRegistry(path)


def get_upload_limit(marketplace: Marketplace) -> int | None:
    """Return the upload limit for ``marketplace``."""
    if rules_registry is None:
        msg = "rules not loaded"
        raise RuntimeError(msg)
    rules = rules_registry.get(marketplace)
    return rules.upload_limit if rules else None


def validate_mockup(marketplace: Marketplace, path: Path) -> None:
    """Validate ``path`` against marketplace-specific rules."""
    if rules_registry is None:
        msg = "rules not loaded"
        raise RuntimeError(msg)
    rules = rules_registry.get(marketplace)
    if rules is None:
        return
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > rules.max_file_size_mb:
        msg = f"file size {size_mb:.2f} MB exceeds {rules.max_file_size_mb} MB"
        raise ValueError(msg)
    from PIL import Image

    with Image.open(path) as img:
        width, height = img.size
    if width > rules.max_width or height > rules.max_height:
        msg = (
            f"image dimensions {width}x{height} exceed "
            f"{rules.max_width}x{rules.max_height}"
        )
        raise ValueError(msg)
    if rules.allowed_formats is not None:
        ext = path.suffix.lower().lstrip(".")
        if ext not in {e.lower() for e in rules.allowed_formats}:
            allowed = ", ".join(rules.allowed_formats)
            msg = f"extension {ext} not in allowed formats: {allowed}"
            raise ValueError(msg)
