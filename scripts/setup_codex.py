"""Prepare the desAInz environment when running in Codex."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def main() -> None:
    """Install dependencies and build the documentation."""
    root_dir = Path(__file__).resolve().parents[1]
    subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run(
        [
            "python",
            "-m",
            "pip",
            "install",
            "-r",
            str(root_dir / "requirements.txt"),
            "-r",
            str(root_dir / "requirements-dev.txt"),
        ],
        check=True,
    )
    if shutil.which("npm"):
        subprocess.run(["npm", "ci", "--legacy-peer-deps"], check=True)
    subprocess.run(
        [
            "python",
            "-m",
            "pip",
            "install",
            "sphinx",
            "myst-parser",
            "sphinxcontrib-mermaid",
        ],
        check=True,
    )
    env = os.environ.copy()
    env.setdefault("SKIP_APIDOC", "1")
    env.setdefault("SKIP_OPENAPI", "1")
    subprocess.run(
        ["python", "-m", "sphinx", "-W", "-b", "html", "docs", "docs/_build/html"],
        check=True,
        env=env,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
