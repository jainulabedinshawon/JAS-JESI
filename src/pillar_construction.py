"""
JESI Pillar Construction Module
JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This module constructs the five JESI pillar scores:
Growth (G), Productivity (P), Connectivity (C),
Resilience (R), and Strategic Autonomy (A).
"""


def arithmetic_mean(values):
    """
    Calculate the arithmetic mean of a collection of values.
    """
    values = list(values)

    if not values:
        raise ValueError("At least one value is required.")

    return sum(values) / len(values)


def construct_growth_score(indicators):
    """
    Construct the Growth (G) pillar score.

    Expected indicators:
        - Real GDP Growth Rate
        - GNI per Capita Growth
    """
    return arithmetic_mean(indicators)


def construct_productivity_score(indicators):
    """
    Construct the Productivity (P) pillar score.

    Expected indicators:
        - GDP per Person Employed
        - Total Factor Productivity (TFP) Growth
    """
    return arithmetic_mean(indicators)


def construct_connectivity_score(indicators):
    """
    Construct the Connectivity (C) pillar score.

    Expected indicators:
        - Trade Openness
        - FDI Inflows
        - ICT and Global Integration
    """
    return arithmetic_mean(indicators)


def construct_resilience_score(indicators):
    """
    Construct the Resilience (R) pillar score.

    Expected indicators:
        - FX Reserves / Import Cover
        - Public Debt / GDP
        - Current Account Position
    """
    return arithmetic_mean(indicators)


def construct_autonomy_score(indicators):
    """
    Construct the Strategic Autonomy (A) pillar score.

    Expected indicators:
        - Economic Complexity Index (ECI)
        - High-Tech Exports
        - Critical Import Concentration
    """
    return arithmetic_mean(indicators)


def construct_all_pillars(
    growth,
    productivity,
    connectivity,
    resilience,
    autonomy,
):
    """
    Construct and return all five JESI pillar scores.
    """
    return {
        "G": construct_growth_score(growth),
        "P": construct_productivity_score(productivity),
        "C": construct_connectivity_score(connectivity),
        "R": construct_resilience_score(resilience),
        "A": construct_autonomy_score(autonomy),
    }
