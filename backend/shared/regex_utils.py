"""Helper utilities for working with cached regular expressions."""
from __future__ import annotations

from functools import lru_cache

import regex as re


@lru_cache(maxsize=None)
def compile_cached(pattern: str, flags: int = 0) -> re.Pattern[str]:
    """Return a compiled regex pattern cached by ``pattern`` and ``flags``."""
    return re.compile(pattern, flags)
