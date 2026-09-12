"""
JESI Robustness Testing Module
JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This module provides basic robustness tests for:
- JAS baseline weights
- Equal weights
- Alternative pillar scores
"""

import math


JAS_WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}


EQUAL_WEIGHTS = {
    "G": 0.20,
    "P": 0.20,
    "C": 0.20,
    "R": 0.20,
    "A": 0.20,
}


def calculate_weighted_geometric_index(
    pillars,
    weights,
):
    """
    Calculate a weighted geometric index
    from normalized pillar scores.
    """

    if set(pillars.keys()) != set(weights.keys()):
        raise ValueError(
            "Pillar names must match weight names."
        )

    for name, score in pillars.items():
        if not 0 <= score <= 1:
            raise ValueError(
                f"{name} score must be between 0 and 1."
            )

    if not math.isclose(
        sum(weights.values()),
        1.0,
        rel_tol=1e-9,
    ):
        raise ValueError(
            "Weights must sum to 1."
        )

    result = 1.0

    for name, weight in weights.items():
        result *= pillars[name] ** weight

    return 100 * result


def calculate_baseline_jesi(pillars):
    """
    Calculate JESI using the Master Version 1.0
    JAS strategic weights.
    """
    return calculate_weighted_geometric_index(
        pillars,
        JAS_WEIGHTS,
    )


def calculate_equal_weight_jesi(pillars):
    """
    Calculate JESI using equal pillar weights.
    """
    return calculate_weighted_geometric_index(
        pillars,
        EQUAL_WEIGHTS,
    )


def compare_weighting_methods(pillars):
    """
    Compare JAS strategic weighting with equal weighting.
    """

    baseline = calculate_baseline_jesi(pillars)
    equal_weight = calculate_equal_weight_jesi(pillars)

    return {
        "JAS_baseline": baseline,
        "equal_weight": equal_weight,
        "difference": baseline - equal_weight,
    }


def sensitivity_test(
    pillars,
    pillar,
    change=0.10,
):
    """
    Test the effect of changing one pillar score.

    Parameters
    ----------
    pillars : dict
        Normalized G/P/C/R/A pillar scores.

    pillar : str
        Pillar to modify.

    change : float
        Relative change, e.g. 0.10 = +10%.
    """

    if pillar not in pillars:
        raise ValueError(
            f"Unknown pillar: {pillar}"
        )

    baseline = calculate_baseline_jesi(
        pillars
    )

    modified = pillars.copy()

    modified[pillar] = min(
        1.0,
        modified[pillar] * (1 + change),
    )

    new_score = calculate_baseline_jesi(
        modified
    )

    return {
        "baseline_jesi": baseline,
        "modified_jesi": new_score,
        "change_in_jesi": new_score - baseline,
    }
