"""Fetch pre-built models and datasets for offline use."""

from __future__ import annotations

import os
from pathlib import Path
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
MODEL_CACHE = ROOT / "prebuilt" / "models"
DATASET_DIR = ROOT / "prebuilt" / "datasets"

MODELS = {
    "stable-diffusion-xl-base-1.0": "stabilityai/stable-diffusion-xl-base-1.0",
}


def download_models() -> None:
    """Download all configured models into ``MODEL_CACHE``."""
    MODEL_CACHE.mkdir(parents=True, exist_ok=True)
    token = os.getenv("HUGGINGFACE_TOKEN")
    for name, repo in MODELS.items():
        target = MODEL_CACHE / name
        if target.exists():
            continue
        snapshot_download(repo_id=repo, cache_dir=target, token=token)


def ensure_datasets() -> None:
    """Create dataset directory if missing."""
    DATASET_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Download models and prepare dataset directory."""
    download_models()
    ensure_datasets()


if __name__ == "__main__":  # pragma: no cover
    main()
