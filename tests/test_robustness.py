"""
Tests for the JESI robustness testing module.
JAS Unified Economic Strength Index (JESI)
Master Version 1.0
"""

import math

from src.robustness_tests import (
    calculate_weighted_geometric_index,
    compare_weighting_methods,
    sensitivity_test,
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


def test_weighted_geometric_index_rejects_invalid_score():
    """
    The index should reject pillar scores outside the 0–1 range.
    """

    pillars = {
        "G": 1.1,
        "P": 0.8,
        "C": 0.8,
        "R": 0.8,
        "A": 0.8,
    }

    weights = {
        "G": 0.20,
        "P": 0.25,
        "C": 0.20,
        "R": 0.20,
        "A": 0.15,
    }

    try:
        calculate_weighted_geometric_index(
            pillars,
            weights,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "The index should reject scores outside the 0–1 range."
        )


def test_weighted_geometric_index_rejects_invalid_weights():
    """
    The index should reject weights that do not sum to 1.
    """

    pillars = {
        "G": 0.8,
        "P": 0.8,
        "C": 0.8,
        "R": 0.8,
        "A": 0.8,
    }

    weights = {
        "G": 0.20,
        "P": 0.25,
        "C": 0.20,
        "R": 0.20,
        "A": 0.20,
    }

    try:
        calculate_weighted_geometric_index(
            pillars,
            weights,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "The index should reject weights that do not sum to 1."
        )


def test_compare_weighting_methods():
    """
    The weighting comparison should return both JESI scores
    and their difference.
    """

    pillars = {
        "G": 0.9,
        "P": 0.7,
        "C": 0.8,
        "R": 0.6,
        "A": 0.5,
    }

    result = compare_weighting_methods(pillars)

    assert "JAS_baseline" in result
    assert "equal_weight" in result
    assert "difference" in result

    assert math.isclose(
        result["difference"],
        result["JAS_baseline"] - result["equal_weight"],
        rel_tol=1e-9,
    )
def test_sensitivity_decreases_jesi_when_pillar_decreases():
    """
    Decreasing a pillar score should decrease the JESI score.
    """

    pillars = {
        "G": 0.8,
        "P": 0.7,
        "C": 0.6,
        "R": 0.5,
        "A": 0.4,
    }

    result = sensitivity_test(
        pillars,
        pillar="G",
        change=-0.10,
    )

    assert result["modified_jesi"] < result["baseline_jesi"]

    assert math.isclose(
        result["change_in_jesi"],
        result["modified_jesi"] - result["baseline_jesi"],
        rel_tol=1e-9,
    )

def test_sensitivity_increases_jesi_when_pillar_increases():
    """
    Increasing a pillar score should increase the JESI score.
    """

    pillars = {
        "G": 0.8,
        "P": 0.7,
        "C": 0.6,
        "R": 0.5,
        "A": 0.4,
    }

    result = sensitivity_test(
        pillars,
        pillar="G",
        change=0.10,
    )

    assert result["modified_jesi"] > result["baseline_jesi"]

    assert math.isclose(
        result["change_in_jesi"],
        result["modified_jesi"] - result["baseline_jesi"],
        rel_tol=1e-9,
    )
