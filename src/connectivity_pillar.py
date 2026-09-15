"""
JESI Connectivity Pillar Module
JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This module provides reusable functions for constructing
the Connectivity (C) pillar.
"""


def normalize_positive(value, minimum, maximum):
    """
    Normalize a positive-direction indicator to a 0–1 scale.
    """

    if maximum == minimum:
        raise ValueError(
            "Maximum and minimum cannot be equal."
        )

    score = (
        (value - minimum)
        / (maximum - minimum)
    )

    return max(0.0, min(1.0, score))


def construct_connectivity_score(
    trade_openness,
    fdi_inflows,
    internet_use,
):
    """
    Construct the Connectivity (C) pillar score
    from three normalized indicators.

    A geometric mean is used so that weakness
    in one dimension is not completely hidden
    by stronger performance in other dimensions.
    """

    values = [
        trade_openness,
        fdi_inflows,
        internet_use,
    ]

    if any(value is None for value in values):
        raise ValueError(
            "All Connectivity indicator scores are required."
        )

    if any(value < 0 or value > 1 for value in values):
        raise ValueError(
            "All Connectivity scores must be between 0 and 1."
        )

    product = 1.0

    for value in values:
        product *= float(value)

    return product ** (1.0 / 3.0)
