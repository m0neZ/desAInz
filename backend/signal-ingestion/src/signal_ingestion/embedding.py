"""Utilities for computing text embeddings."""

from __future__ import annotations

import hashlib
from typing import List

import numpy as np

try:  # pragma: no cover - optional heavy dependency
    import open_clip
    import torch
except Exception:  # pragma: no cover - fallback when open_clip unavailable
    open_clip = None
    torch = None

_model = None
_tokenizer = None


def _load_clip() -> None:
    """Load CLIP model on first use."""
    global _model, _tokenizer
    if open_clip is None or torch is None:
        return
    if _model is None:
        _model, _, _ = open_clip.create_model_and_transforms(
            "ViT-L-14", pretrained="openai"
        )
        _tokenizer = open_clip.get_tokenizer("ViT-L-14")
        _model.eval()


def _clip_embedding(text: str) -> List[float]:
    assert open_clip is not None and torch is not None
    assert _tokenizer is not None and _model is not None
    tokens = _tokenizer([text])
    with torch.no_grad():
        vec = _model.encode_text(tokens)[0].float().cpu().numpy()
    return vec.tolist()


def _fallback_embedding(text: str, dim: int = 768) -> List[float]:
    seed = int.from_bytes(hashlib.sha1(text.encode()).digest()[:8], "little")
    rng = np.random.default_rng(seed)
    return rng.random(dim).astype(float).tolist()


def generate_embedding(text: str) -> List[float]:
    """Return an embedding vector for ``text``."""
    if open_clip is not None and torch is not None:
        _load_clip()
        if _model is not None and _tokenizer is not None:
            return _clip_embedding(text)
    return _fallback_embedding(text)
