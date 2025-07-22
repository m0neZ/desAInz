"""Utilities for computing text embeddings."""

from __future__ import annotations

import hashlib
from typing import List, Sequence

from typing import cast

import numpy as np

open_clip = None
torch = None

_model = None
_tokenizer = None


def _load_clip() -> None:
    """Load CLIP model on first use."""
    global _model, _tokenizer, open_clip, torch
    if open_clip is None or torch is None:
        try:  # pragma: no cover - optional heavy dependency
            import open_clip as _open_clip
            import torch as _torch
        except Exception:  # pragma: no cover - fallback when open_clip unavailable
            return
        open_clip = _open_clip
        torch = _torch

    if _model is None:
        _model, _, _ = open_clip.create_model_and_transforms(
            "ViT-L-14", pretrained="openai"
        )
        _tokenizer = open_clip.get_tokenizer("ViT-L-14")
        _model.eval()


def _clip_embedding(text: str) -> List[float]:
    """Return CLIP embedding for ``text``."""
    assert open_clip is not None and torch is not None
    assert _tokenizer is not None and _model is not None
    tokens = _tokenizer([text])
    with torch.no_grad():
        vec = _model.encode_text(tokens)[0].float().cpu().numpy()
    return cast(List[float], vec.tolist())


def _fallback_embedding(text: str, dim: int = 768) -> List[float]:
    seed = int.from_bytes(hashlib.sha1(text.encode()).digest()[:8], "little")
    rng = np.random.default_rng(seed)
    return cast(List[float], rng.random(dim).astype(float).tolist())


def _clip_embeddings(texts: Sequence[str]) -> list[List[float]]:
    """Return CLIP embeddings for ``texts`` as a batch."""
    assert open_clip is not None and torch is not None
    assert _tokenizer is not None and _model is not None
    tokens = _tokenizer(list(texts))
    with torch.no_grad():
        vecs = _model.encode_text(tokens).float().cpu().numpy()
    return cast(list[List[float]], vecs.tolist())


def _fallback_embeddings(texts: Sequence[str]) -> list[List[float]]:
    """Return deterministic random embeddings for ``texts``."""
    return [_fallback_embedding(text) for text in texts]


def generate_embeddings(texts: Sequence[str]) -> list[List[float]]:
    """Return embeddings for each string in ``texts``."""
    _load_clip()
    if (
        open_clip is not None
        and torch is not None
        and _model is not None
        and _tokenizer is not None
    ):
        return _clip_embeddings(texts)
    return _fallback_embeddings(texts)


def generate_embedding(text: str) -> List[float]:
    """Return an embedding vector for ``text``."""
    return generate_embeddings([text])[0]
