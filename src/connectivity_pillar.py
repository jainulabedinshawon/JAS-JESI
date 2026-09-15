"""
JESI Connectivity Pillar Module
JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This module provides reusable functions for constructing
the Connectivity (C) pillar.
"""


def normalize_positive(value, minimum, maximum):
    """
    Normalize a higher-is-better indicator to a 0–1 scale.

    Formula:
        score = (value - minimum) / (maximum - minimum)
    """

    if value is None:
        return None

    if maximum <= minimum:
        raise ValueError(
            "Maximum must be greater than minimum."
        )

    score = (
        (value - minimum)
        / (maximum - minimum)
    )

    return max(0.0, min(1.0, score))


def construct_connectivity_score(
    trade_openness,
    fdi_inflows,
    ict_global_integration,
):
    """
    Construct the Connectivity (C) pillar score.

    The three normalized indicators are aggregated
    using a geometric mean.

    C = (C1 × C2 × C3)^(1/3)
    """

    values = [
        trade_openness,
        fdi_inflows,
        ict_global_integration,
    ]

    if any(value is None for value in values):
        raise ValueError(
            "All Connectivity indicator scores are required."
        )

    if any(value < 0 or value > 1 for value in values):
        raise ValueError(
            "All Connectivity scores must be between 0 and 1."
        )

    epsilon = 1e-12

    product = 1.0

    for value in values:
        product *= max(float(value), epsilon)

    return product ** (1.0 / 3.0)
