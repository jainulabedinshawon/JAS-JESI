"""
Tests for the JESI Growth pillar module.
JAS Unified Economic Strength Index (JESI)
Master Version 1.0
"""

import pytest

from src.growth_pillar import (
    normalize_positive,
    construct_growth_score,
)


def test_normalize_positive():
    """
    Positive indicators should normalize correctly.
    """

    result = normalize_positive(
        value=5,
        minimum=0,
        maximum=10,
    )

    assert result == 0.5


def test_normalize_positive_minimum():
    """
    Minimum value should normalize to zero.
    """

    result = normalize_positive(
        value=0,
        minimum=0,
        maximum=10,
    )

    assert result == 0.0


def test_normalize_positive_maximum():
    """
    Maximum value should normalize to one.
    """

    result = normalize_positive(
        value=10,
        minimum=0,
        maximum=10,
    )

    assert result == 1.0


def test_normalize_positive_rejects_equal_bounds():
    """
    Equal minimum and maximum should raise an error.
    """

    with pytest.raises(ValueError):
        normalize_positive(
            value=5,
            minimum=5,
            maximum=5,
        )


def test_construct_growth_score():
    """
    Growth pillar should equal the arithmetic mean
    of the two normalized indicators.
    """

    result = construct_growth_score(
        gdp_growth=0.6,
        gni_pc_growth=0.8,
    )

    assert result == 0.7


def test_construct_growth_score_requires_gdp():
    """
    Missing GDP growth score should raise an error.
    """

    with pytest.raises(ValueError):
        construct_growth_score(
            gdp_growth=None,
            gni_pc_growth=0.8,
        )


def test_construct_growth_score_requires_gni():
    """
    Missing GNI per capita growth score should raise an error.
    """

    with pytest.raises(ValueError):
        construct_growth_score(
            gdp_growth=0.6,
            gni_pc_growth=None,
        )
