"""Collect license information for Python and Node packages."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _python_licenses() -> list[str]:
    """Return formatted license lines for installed Python packages."""
    result = subprocess.run(
        ["pip-licenses", "--format=json"],
        check=True,
        capture_output=True,
        text=True,
    )
    packages: list[dict[str, str]] = json.loads(result.stdout)
    return [f"{p['Name']} {p['Version']} - {p['License']}" for p in packages]


def _node_licenses() -> list[str]:
    """Return formatted license lines for installed Node packages."""
    try:
        result = subprocess.run(
            ["license-checker", "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ["license-checker not found"]

    packages: dict[str, dict[str, str]] = json.loads(result.stdout)
    lines = []
    for name, info in packages.items():
        version = info.get("version", "UNKNOWN")
        license_ = info.get("licenses", "UNKNOWN")
        lines.append(f"{name} {version} - {license_}")
    return lines


def main() -> None:
    """Generate the LICENSES file."""
    content = (
        ["Python packages:"]
        + _python_licenses()
        + ["", "Node packages:"]
        + _node_licenses()
    )
    Path("LICENSES").write_text("\n".join(content) + "\n")


if __name__ == "__main__":  # pragma: no cover
    main()
