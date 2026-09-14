import pytest

from src.connectivity_pillar import (
    normalize_positive,
    construct_connectivity_score,
)


def test_normalize_positive():
    assert normalize_positive(
        50,
        0,
        100,
    ) == 0.5


def test_normalize_positive_minimum():
    assert normalize_positive(
        0,
        0,
        100,
    ) == 0.0


def test_normalize_positive_maximum():
    assert normalize_positive(
        100,
        0,
        100,
    ) == 1.0


def test_normalize_rejects_equal_bounds():
    with pytest.raises(ValueError):
        normalize_positive(
            50,
            50,
            50,
        )


def test_connectivity_score():
    score = construct_connectivity_score(
        trade_openness=0.6,
        fdi_inflows=0.8,
        internet_use=1.0,
    )

    assert score == pytest.approx(
        0.8
    )


def test_connectivity_score_zero():
    assert construct_connectivity_score(
        0.0,
        0.0,
        0.0,
    ) == 0.0


def test_connectivity_requires_all_indicators():
    with pytest.raises(ValueError):
        construct_connectivity_score(
            0.5,
            None,
            0.7,
        )
