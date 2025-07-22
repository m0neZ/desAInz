"""Utilities for computing text embeddings."""

from __future__ import annotations

import hashlib
from typing import List, cast

import numpy as np

from backend.shared.clip import load_clip, open_clip, torch


def _fallback_embedding(text: str, dim: int = 768) -> List[float]:
    seed = int.from_bytes(hashlib.sha1(text.encode()).digest()[:8], "little")
    rng = np.random.default_rng(seed)
    return cast(List[float], rng.random(dim).astype(float).tolist())


def generate_embedding(text: str) -> List[float]:
    """Return an embedding vector for ``text``."""
    loaded = load_clip("ViT-L-14")
    if loaded and open_clip is not None and torch is not None:
        model, _preprocess, tokenizer = loaded
        tokens = tokenizer([text])
        with torch.no_grad():
            vec = model.encode_text(tokens)[0].float().cpu().numpy()
        return cast(List[float], vec.tolist())
    return _fallback_embedding(text)
