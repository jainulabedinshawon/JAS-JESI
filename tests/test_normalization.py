"""
Tests for the JESI normalization module.
JAS Unified Economic Strength Index (JESI)
Master Version 1.0
"""

from src.normalization import (
    normalize_positive,
    normalize_negative,
    clip_normalized,
)


def test_normalize_positive():
    """
    Higher values should produce higher normalized scores.
    """

    result = normalize_positive(
        value=75,
        minimum=50,
        maximum=100,
    )

    assert result == 0.5


def test_normalize_negative():
    """
    Lower values should produce higher normalized scores.
    """

    result = normalize_negative(
        value=25,
        minimum=0,
        maximum=50,
    )

    assert result == 0.5


def test_clip_normalized():
    """
    Normalized values should be constrained to the 0–1 range.
    """

    assert clip_normalized(1.2) == 1.0
    assert clip_normalized(-0.2) == 0.0
    assert clip_normalized(0.6) == 0.6
