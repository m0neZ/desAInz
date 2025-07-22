"""
Utilities for loading CLIP models.

This module caches initialized CLIP models so workers can reuse the heavy
weights without repeated startup cost. The underlying ``open_clip`` and
``torch`` packages are imported lazily, remaining ``None`` when unavailable.
"""

from __future__ import annotations

from threading import Lock
from typing import Any, Callable, Dict, Tuple
from pathlib import Path
import os

from .config import settings as shared_settings

open_clip = None
torch = None

# Cache loaded models keyed by "model:pretrained"
_models: Dict[str, Tuple[Any, Callable[[Any], Any], Callable[[Any], Any]]] = {}
_lock = Lock()


def load_clip(
    model_name: str, pretrained: str = "openai"
) -> Tuple[Any, Callable[[Any], Any], Callable[[Any], Any]] | None:
    """Return a cached CLIP model, preprocess function and tokenizer."""
    global open_clip, torch
    if open_clip is None or torch is None:
        try:  # pragma: no cover - optional heavy dependency
            import open_clip as _open_clip
            import torch as _torch
        except Exception:  # pragma: no cover - fallback when open_clip unavailable
            return None
        open_clip = _open_clip
        torch = _torch
        os.environ.setdefault("TORCH_HOME", shared_settings.model_cache_dir)

    key = f"{model_name}:{pretrained}"
    with _lock:
        if key not in _models:
            model, _, preprocess = open_clip.create_model_and_transforms(
                model_name, pretrained=pretrained
            )
            tokenizer = open_clip.get_tokenizer(model_name)
            model.eval()
            _models[key] = (model, preprocess, tokenizer)
    return _models[key]
