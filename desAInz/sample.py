"""Sample module for demonstration purposes."""

from typing import List


def add_numbers(values: List[int]) -> int:
    """Return the sum of a list of integers.

    Parameters
    ----------
    values : List[int]
        The integers to sum.

    Returns
    -------
    int
        The computed sum.
    """
    return sum(values)
