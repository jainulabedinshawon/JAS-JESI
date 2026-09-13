"""
Tests for the JESI calculation module.
JAS Unified Economic Strength Index (JESI)
Master Version 1.0
"""

import math

from src.jesi_calculation import (
    calculate_jesi,
    calculate_jesi_from_values,
)


def test_jesi_equal_pillars():
    """
    If all five pillars are equal, JESI should
    return that common value multiplied by 100.
    """
    pillars = {
        "G": 0.8,
        "P": 0.8,
        "C": 0.8,
        "R": 0.8,
        "A": 0.8,
    }

    result = calculate_jesi(pillars)

    assert math.isclose(result, 80.0, rel_tol=1e-9)


def test_jesi_from_values():
    """
    Test direct JESI calculation from five pillar values.
    """
    result = calculate_jesi_from_values(
        growth=1.0,
        productivity=1.0,
        connectivity=1.0,
        resilience=1.0,
        autonomy=1.0,
    )

    assert math.isclose(result, 100.0, rel_tol=1e-9)


def test_jesi_rejects_invalid_score():
    """
    JESI should reject pillar scores outside 0–1.
    """
    pillars = {
        "G": 1.1,
        "P": 0.8,
        "C": 0.8,
        "R": 0.8,
        "A": 0.8,
    }

    try:
        calculate_jesi(pillars)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "JESI should reject scores outside the 0–1 range."
        )
