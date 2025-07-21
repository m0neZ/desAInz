#!/usr/bin/env python3
"""Update changelog when OpenAPI specs change.

This script computes a stable hash for each JSON specification under the
``openapi`` directory. The hash ignores the ``x-spec-version`` field so that it
represents the actual specification content. When the current hash differs from
that of the same file in the previous commit, the changelog is updated with a
short entry and the ``x-spec-version`` field in the JSON file is set to the new
hash.
"""
from __future__ import annotations

import hashlib
import json
import pyjson5
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPENAPI_DIR = PROJECT_ROOT / "openapi"
CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"


def _spec_hash(data: dict) -> str:
    """Return stable hash for ``data`` ignoring ``x-spec-version``."""
    stripped = dict(data)
    stripped.pop("x-spec-version", None)
    serialized = json.dumps(stripped, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _hash_from_git(path: Path) -> str | None:
    """Return spec hash for ``path`` from previous commit or ``None``."""
    rel_path = path
    if rel_path.is_absolute():
        rel_path = rel_path.relative_to(PROJECT_ROOT)
    rel = rel_path.as_posix()
    try:
        content = subprocess.check_output(["git", "show", f"HEAD:{rel}"], text=True)
    except subprocess.CalledProcessError:
        return None
    return _spec_hash(pyjson5.decode(content))


def _update_changelog(services: list[str]) -> None:
    """Insert changelog entries for ``services``."""
    if not CHANGELOG.exists():
        return
    lines = CHANGELOG.read_text(encoding="utf-8").splitlines()
    try:
        idx = lines.index("### ⚙️ Miscellaneous Tasks")
    except ValueError:
        return
    insert_at = idx + 1
    for service in services:
        entry = f"- *(openapi)* Update {service} spec"
        if entry not in lines:
            lines.insert(insert_at, entry)
            insert_at += 1
    CHANGELOG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Update spec hashes and changelog."""
    changed: list[str] = []
    for path in sorted(OPENAPI_DIR.glob("*.json")):
        data = pyjson5.decode(path.read_text(encoding="utf-8"))
        current_hash = _spec_hash(data)
        data["x-spec-version"] = current_hash
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        previous_hash = _hash_from_git(path)
        if current_hash != previous_hash:
            changed.append(path.stem)
    if changed:
        _update_changelog(changed)


if __name__ == "__main__":
    main()
