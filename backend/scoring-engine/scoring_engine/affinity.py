"""Community affinity utilities."""

from __future__ import annotations

import hashlib
from functools import lru_cache

import numpy as np
from numpy.typing import NDArray

DIMENSION = 32


def _hash_embedding(text: str) -> NDArray[np.floating]:
    """Return a deterministic embedding vector for ``text``."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    arr = np.frombuffer(digest, dtype=np.uint8).astype(float)
    return arr[:DIMENSION] / 255.0


def subreddit_embedding(name: str) -> NDArray[np.floating]:
    """Return embedding for a subreddit name."""
    return _hash_embedding(f"subreddit:{name.lower()}")


def hashtag_embedding(tag: str) -> NDArray[np.floating]:
    """Return embedding for a hashtag."""
    return _hash_embedding(f"hashtag:{tag.lower()}")


@lru_cache(maxsize=1024)
def metadata_embedding(metadata: tuple[tuple[str, float], ...]) -> NDArray[np.floating]:
    """
    Aggregate embeddings for keys in ``metadata``.

    Results are cached to avoid repeated hashing of the same metadata.
    """
    if not metadata:
        return np.zeros(DIMENSION, dtype=float)
    total = np.zeros(DIMENSION, dtype=float)
    weight_sum = 0.0
    for key, weight in metadata:
        if key.startswith("r/"):
            vec = subreddit_embedding(key[2:])
        elif key.startswith("#"):
            vec = hashtag_embedding(key[1:])
        else:
            vec = _hash_embedding(key)
        total += vec * float(weight)
        weight_sum += float(weight)
    if weight_sum == 0.0:
        return total
    return total / weight_sum


__all__ = [
    "DIMENSION",
    "subreddit_embedding",
    "hashtag_embedding",
    "metadata_embedding",
]
