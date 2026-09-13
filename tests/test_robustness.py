"""
Tests for the JESI robustness testing module.
JAS Unified Economic Strength Index (JESI)
Master Version 1.0
"""

import math

from src.robustness_tests import (
    calculate_weighted_geometric_index,
)


def test_weighted_geometric_index_all_maximum():
    """
    If all pillar scores are 1.0, the index should equal 100.0.
    """

    pillars = {
        "G": 1.0,
        "P": 1.0,
        "C": 1.0,
        "R": 1.0,
        "A": 1.0,
    }

    weights = {
        "G": 0.20,
        "P": 0.25,
        "C": 0.20,
        "R": 0.20,
        "A": 0.15,
    }

    result = calculate_weighted_geometric_index(
        pillars,
        weights,
    )

    assert math.isclose(
        result,
        100.0,
        rel_tol=1e-9,
    )
def test_weighted_geometric_index_all_zero():
    """
    If all pillar scores are 0.0, the index should equal 0.0.
    """

    pillars = {
        "G": 0.0,
        "P": 0.0,
        "C": 0.0,
        "R": 0.0,
        "A": 0.0,
    }

    weights = {
        "G": 0.20,
        "P": 0.25,
        "C": 0.20,
        "R": 0.20,
        "A": 0.15,
    }

    result = calculate_weighted_geometric_index(
        pillars,
        weights,
    )

    assert math.isclose(
        result,
        0.0,
        rel_tol=1e-9,
    )
