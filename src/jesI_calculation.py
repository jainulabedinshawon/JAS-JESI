"""
JESI Calculation Module
JAS Unified Economic Strength Index (JESI)
Master Version 1.0

Core equation:

JESI = 100 × G^0.20 × P^0.25 × C^0.20 × R^0.20 × A^0.15
"""


# Master Version 1.0 pillar weights
WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}


def validate_pillar_scores(pillars):
    """
    Validate that all five pillar scores exist
    and fall within the 0–1 range.
    """
    required = set(WEIGHTS.keys())

    if set(pillars.keys()) != required:
        raise ValueError(
            "Pillar scores must contain exactly G, P, C, R, and A."
        )

    for name, score in pillars.items():
        if not 0 <= score <= 1:
            raise ValueError(
                f"{name} score must be between 0 and 1."
            )


def calculate_jesi(pillars):
    """
    Calculate the JESI Master Version 1.0 score.

    Formula:
        JESI = 100 × G^0.20 × P^0.25 ×
               C^0.20 × R^0.20 × A^0.15
    """
    validate_pillar_scores(pillars)

    G = pillars["G"]
    P = pillars["P"]
    C = pillars["C"]
    R = pillars["R"]
    A = pillars["A"]

    return (
        100
        * (G ** WEIGHTS["G"])
        * (P ** WEIGHTS["P"])
        * (C ** WEIGHTS["C"])
        * (R ** WEIGHTS["R"])
        * (A ** WEIGHTS["A"])
    )


def calculate_jesi_from_values(
    growth,
    productivity,
    connectivity,
    resilience,
    autonomy,
):
    """
    Calculate JESI directly from the five pillar scores.
    """
    pillars = {
        "G": growth,
        "P": productivity,
        "C": connectivity,
        "R": resilience,
        "A": autonomy,
    }

    return calculate_jesi(pillars)
