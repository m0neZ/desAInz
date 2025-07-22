"""Utilities for computing text embeddings."""

from __future__ import annotations

import hashlib
from typing import Iterable, List, cast

import numpy as np

from backend.shared.clip import load_clip, open_clip, torch


def _fallback_embedding(text: str, dim: int = 768) -> List[float]:
    """Return a deterministic pseudo-random embedding for ``text``."""
    seed = int.from_bytes(hashlib.sha1(text.encode()).digest()[:8], "little")
    rng = np.random.default_rng(seed)
    return cast(List[float], rng.random(dim).astype(float).tolist())


def generate_embeddings(texts: Iterable[str]) -> list[list[float]]:
    """Return embedding vectors for ``texts``."""
    loaded = load_clip("ViT-L-14")
    if loaded and open_clip is not None and torch is not None:
        model, _preprocess, tokenizer = loaded
        tokens = tokenizer(list(texts))
        with torch.no_grad():
            vecs = model.encode_text(tokens).float().cpu().numpy()
        return [cast(List[float], vec.tolist()) for vec in vecs]
    return [_fallback_embedding(text) for text in texts]


def generate_embedding(text: str) -> List[float]:
    """Return an embedding vector for ``text``."""
    return generate_embeddings([text])[0]
