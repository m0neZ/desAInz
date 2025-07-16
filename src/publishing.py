"""Publishing module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List


def publish(mockups: List[dict[str, Any]], path: str) -> None:
    """Publish mockups by storing them in ``path``.

    Parameters
    ----------
    mockups:
        Generated mockups.
    path:
        Destination path for serialized data.
    """
    file_path = Path(path)
    file_path.write_text(str(mockups))
