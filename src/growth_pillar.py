"""
JESI Growth Pillar Module
JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This module provides reusable functions for
constructing the Growth (G) pillar.
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


def construct_growth_score(
    gdp_growth,
    gni_pc_growth,
):
    """
    Construct the Growth (G) pillar score
    from two normalized indicators.

    Parameters
    ----------
    gdp_growth : float
        Normalized real GDP growth score.

    gni_pc_growth : float
        Normalized GNI per capita growth score.

    Returns
    -------
    float
        Growth pillar score between 0 and 1.
    """

    if gdp_growth is None:
        raise ValueError(
            "GDP growth score is required."
        )

    if gni_pc_growth is None:
        raise ValueError(
            "GNI per capita growth score is required."
        )

    return (
        gdp_growth
        + gni_pc_growth
    ) / 2
