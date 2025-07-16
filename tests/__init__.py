"""Test package for feedback loop."""

import sys
from pathlib import Path

# Ensure feedback_loop package is discoverable
sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "backend" / "feedback-loop")
)
