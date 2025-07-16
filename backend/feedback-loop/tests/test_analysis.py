"""Tests for design performance analysis helpers."""

import pandas as pd
from feedback_loop.analysis import highlight_low_performing


def test_highlight_low_performing() -> None:
    """Ensure low performing designs are correctly identified."""
    df = pd.DataFrame(
        {
            "design_id": [1, 2, 3],
            "engagement_rate": [0.05, 0.2, 0.03],
        }
    )
    result = highlight_low_performing(df, engagement_threshold=0.1)
    assert result == [1, 3]
