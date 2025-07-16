"""Tests for sample module."""

from desAInz.sample import add_numbers


def test_add_numbers() -> None:
    """Verify that add_numbers sums values correctly."""
    assert add_numbers([1, 2, 3]) == 6
