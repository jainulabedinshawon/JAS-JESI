"""
JESI Connectivity Pillar Module
JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This module provides reusable functions for
constructing the Connectivity (C) pillar.
"""


def normalize_positive(
    value,
    minimum,
    maximum,
):
    """
    Normalize a positive-direction indicator
    to a 0–1 scale.
    """

    if maximum == minimum:
        raise ValueError(
            "Maximum and minimum cannot be equal."
        )

    return (
        (value - minimum)
        / (maximum - minimum)
    )


def construct_connectivity_score(
    trade_openness,
    fdi_inflows,
    internet_use,
):
    """
    Construct the Connectivity (C) pillar score
    from three normalized indicators.

    Parameters
    ----------
    trade_openness : float
        Normalized trade openness score.

    fdi_inflows : float
        Normalized FDI inflows score.

    internet_use : float
        Normalized internet-use score.

    Returns
    -------
    float
        Connectivity pillar score between 0 and 1.
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

    return sum(values) / len(values)
