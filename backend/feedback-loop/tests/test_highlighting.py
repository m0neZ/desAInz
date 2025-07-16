"""Tests for highlighting low-performing designs."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
from feedback_loop.highlighting import highlight_low_performing_designs


def test_highlight_low_performing_designs() -> None:
    df = pd.DataFrame({"design_id": [1, 2, 3], "engagement": [0.1, 0.5, 0.05]})
    low = highlight_low_performing_designs(df, "engagement", 0.2)
    assert low == [1, 3]
