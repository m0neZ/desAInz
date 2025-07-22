"""Marketplace validation rules and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, cast

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import yaml

from .db import Marketplace

_raw_rules_cache: Mapping[str, Any] | None = None
_raw_rules_mtime: float | None = None


def _load_yaml(path: Path) -> Mapping[str, Any]:
    """Return parsed YAML from ``path`` using an in-memory cache."""
    global _raw_rules_cache, _raw_rules_mtime
    mtime = path.stat().st_mtime
    if _raw_rules_cache is not None and _raw_rules_mtime == mtime:
        return _raw_rules_cache

    loaded = yaml.safe_load(path.read_text()) or {}
    if not isinstance(loaded, Mapping):
        msg = "Invalid rules format"
        raise TypeError(msg)

    _raw_rules_cache = cast(Mapping[str, Any], loaded)
    _raw_rules_mtime = mtime
    return _raw_rules_cache


@dataclass(slots=True)
class MarketplaceRules:
    """Validation rules for a single marketplace."""

    max_file_size_mb: int
    max_width: int
    max_height: int
    upload_limit: int
    allowed_formats: list[str] | None = None
    selectors: Mapping[str, str] | None = None


class RulesRegistry:
    """Registry loading rules from a YAML configuration file."""

    def __init__(self, path: Path) -> None:
        """Load rules from ``path`` using the cached YAML."""
        raw = _load_yaml(path)
        self.rules: Mapping[Marketplace, MarketplaceRules] = {
            Marketplace(key): MarketplaceRules(**val) for key, val in raw.items()
        }

    def get(self, marketplace: Marketplace) -> MarketplaceRules | None:
        """Return rules for ``marketplace`` if available."""
        return self.rules.get(marketplace)


rules_registry: RulesRegistry | None = None
_rules_path: Path | None = None
_observer: Observer | None = None

# Path to the repository-wide rules configuration file
DEFAULT_RULES_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "marketplace_rules.yaml"
)


def _reload_rules() -> None:
    """Reload rules from ``_rules_path`` into the global registry."""
    if _rules_path is None:
        msg = "rules path not set"
        raise RuntimeError(msg)
    global rules_registry  # noqa: PLW0603
    rules_registry = RulesRegistry(_rules_path)


class _RulesFileHandler(FileSystemEventHandler):  # type: ignore[misc]
    """Reload rules when the watched file changes."""

    def __init__(self, path: Path) -> None:
        self._path = path.resolve()

    def on_modified(self, event: Any) -> None:
        if Path(event.src_path).resolve() == self._path:
            _reload_rules()


def stop_watching_rules() -> None:
    """Stop watching the rules file for changes."""
    global _observer
    if _observer is not None:
        _observer.stop()
        _observer.join()
        _observer = None


def load_rules(path: Path, watch: bool = False) -> None:
    """Load marketplace rules from ``path`` and optionally watch for changes."""
    global _rules_path, _observer
    _rules_path = path
    _reload_rules()
    if watch and _observer is None:
        handler = _RulesFileHandler(path)
        _observer = Observer()
        _observer.daemon = True
        _observer.schedule(handler, str(path.parent), recursive=False)
        _observer.start()


def load_default_rules(watch: bool = False) -> None:
    """Load rules from :data:`DEFAULT_RULES_PATH`."""
    load_rules(DEFAULT_RULES_PATH, watch=watch)


def get_upload_limit(marketplace: Marketplace) -> int | None:
    """Return the upload limit for ``marketplace``."""
    if rules_registry is None:
        msg = "rules not loaded"
        raise RuntimeError(msg)
    rules = rules_registry.get(marketplace)
    return rules.upload_limit if rules else None


def get_selectors(marketplace: Marketplace) -> Mapping[str, str] | None:
    """Return Selenium selectors for ``marketplace`` if configured."""
    if rules_registry is None:
        msg = "rules not loaded"
        raise RuntimeError(msg)
    rules = rules_registry.get(marketplace)
    return rules.selectors if rules else None


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
