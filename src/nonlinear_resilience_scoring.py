"""
JESI Nonlinear Resilience Scoring
Version 1.0

Scores nonlinear resilience indicators using smooth
reference-zone penalties.

Indicators:
    R1: FX Reserves / Import Cover
    R2: Government Gross Debt / GDP
    R3: Current Account Balance / GDP
"""

import math


# Empirically calibrated P10-P90 reference zones
DEBT_LOWER = 29.287000
DEBT_UPPER = 77.458300

CURRENT_ACCOUNT_LOWER = -2.427516
CURRENT_ACCOUNT_UPPER = 3.881556

# Baseline penalty parameter.
# One reference-zone width outside the zone
# reduces the score to 0.5.
DEFAULT_LAMBDA = math.log(2)


def reference_zone_score(
    value,
    lower,
    upper,
    lambda_lower=DEFAULT_LAMBDA,
    lambda_upper=DEFAULT_LAMBDA,
):
    """
    Calculate a smooth reference-zone score.

    Score = 1.0 inside the reference zone.

    Outside the zone, the score declines exponentially
    according to normalized distance from the boundary.

    The reference-zone width is used to normalize the
    distance so that lambda is dimensionless.

    Parameters
    ----------
    value : float
        Observed indicator value.

    lower : float
        Lower reference-zone boundary.

    upper : float
        Upper reference-zone boundary.

    lambda_lower : float
        Penalty strength below the lower boundary.

    lambda_upper : float
        Penalty strength above the upper boundary.

    Returns
    -------
    float
        Score bounded between 0 and 1.
    """

    if value is None:
        return None

    value = float(value)
    lower = float(lower)
    upper = float(upper)

    if lower > upper:
        raise ValueError(
            "Lower boundary cannot exceed upper boundary."
        )

    if lambda_lower < 0 or lambda_upper < 0:
        raise ValueError(
            "Penalty parameters must be non-negative."
        )

    if lower <= value <= upper:
        return 1.0

    width = upper - lower

    if width <= 0:
        raise ValueError(
            "Reference-zone width must be positive."
        )

    if value < lower:
        normalized_distance = (
            lower - value
        ) / width

        score = math.exp(
            -lambda_lower
            * normalized_distance
        )

    else:
        normalized_distance = (
            value - upper
        ) / width

        score = math.exp(
            -lambda_upper
            * normalized_distance
        )

    return max(0.0, min(1.0, score))


def score_government_debt(
    debt_gdp,
    lambda_lower=DEFAULT_LAMBDA,
    lambda_upper=DEFAULT_LAMBDA,
):
    """
    Score Government Gross Debt (% of GDP).

    The empirical P10-P90 zone is treated as the
    baseline reference zone.
    """

    return reference_zone_score(
        debt_gdp,
        lower=DEBT_LOWER,
        upper=DEBT_UPPER,
        lambda_lower=lambda_lower,
        lambda_upper=lambda_upper,
    )


def score_current_account(
    current_account_gdp,
    lambda_lower=DEFAULT_LAMBDA,
    lambda_upper=DEFAULT_LAMBDA,
):
    """
    Score Current Account Balance (% of GDP).

    The empirical P10-P90 zone is treated as the
    baseline reference zone.
    """

    return reference_zone_score(
        current_account_gdp,
        lower=CURRENT_ACCOUNT_LOWER,
        upper=CURRENT_ACCOUNT_UPPER,
        lambda_lower=lambda_lower,
        lambda_upper=lambda_upper,
    )


def score_fx_reserves(
    reserves_months,
    minimum,
    maximum,
):
    """
    Positive min-max score for FX Reserves / Import Cover.

    Higher reserve coverage receives a higher score.
    """

    if reserves_months is None:
        return None

    if maximum <= minimum:
        raise ValueError(
            "Maximum must be greater than minimum."
        )

    score = (
        (float(reserves_months) - minimum)
        / (maximum - minimum)
    )

    return max(0.0, min(1.0, score))


def calculate_resilience_pillar(
    fx_reserves_score,
    debt_score,
    current_account_score,
):
    """
    Calculate the Resilience pillar using an equal-weight
    arithmetic aggregation of the three resilience indicators.

    R = (R1 + R2 + R3) / 3

    Returns
    -------
    float
        Resilience pillar score between 0 and 1.
    """

    scores = [
        fx_reserves_score,
        debt_score,
        current_account_score,
    ]

    if any(score is None for score in scores):
        return None

    if any(
        score < 0 or score > 1
        for score in scores
    ):
        raise ValueError(
            "All indicator scores must be between 0 and 1."
        )

    return sum(
        float(score)
        for score in scores
    ) / len(scores)
