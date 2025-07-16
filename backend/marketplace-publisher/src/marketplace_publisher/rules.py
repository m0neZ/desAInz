"""Marketplace-specific validation and rate limit rules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping

import yaml
from PIL import Image

from .db import Marketplace


@dataclass(frozen=True)
class MarketplaceRule:
    """Validation and rate-limit configuration for a marketplace."""

    max_file_size: int
    max_width: int
    max_height: int
    daily_upload_limit: int


def load_rules(path: Path | None = None) -> Mapping[Marketplace, MarketplaceRule]:
    """Load rules from the given YAML ``path``."""
    if path is None:
        path = Path(__file__).with_name("rules.yaml")
    data: Dict[str, Any] = yaml.safe_load(path.read_text())
    return {Marketplace(key): MarketplaceRule(**value) for key, value in data.items()}


RULES = load_rules()


def validate_design(marketplace: Marketplace, design_path: Path) -> None:
    """Validate ``design_path`` using the rules for ``marketplace``."""
    rule = RULES[marketplace]
    size = design_path.stat().st_size
    if size > rule.max_file_size:
        raise ValueError(f"file too large: {size} > {rule.max_file_size}")
    with Image.open(design_path) as img:
        width, height = img.size
    if width > rule.max_width or height > rule.max_height:
        raise ValueError(
            f"invalid dimensions: {width}x{height} exceeds"
            f" {rule.max_width}x{rule.max_height}"
        )
