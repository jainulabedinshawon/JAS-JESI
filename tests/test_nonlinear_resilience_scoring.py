import math

import pytest

from src.nonlinear_resilience_scoring import (
    DEBT_LOWER,
    DEBT_UPPER,
    CURRENT_ACCOUNT_LOWER,
    CURRENT_ACCOUNT_UPPER,
    reference_zone_score,
    score_government_debt,
    score_current_account,
    score_fx_reserves,
    calculate_resilience_pillar,
)


def test_reference_zone_score_inside_zone():
    assert reference_zone_score(
        (DEBT_LOWER + DEBT_UPPER) / 2,
        DEBT_LOWER,
        DEBT_UPPER,
    ) == 1.0


def test_reference_zone_score_at_boundaries():
    assert reference_zone_score(
        DEBT_LOWER,
        DEBT_LOWER,
        DEBT_UPPER,
    ) == 1.0

    assert reference_zone_score(
        DEBT_UPPER,
        DEBT_LOWER,
        DEBT_UPPER,
    ) == 1.0


def test_reference_zone_score_penalty_is_smooth():
    width = DEBT_UPPER - DEBT_LOWER
    penalty_lambda = math.log(2)

    score_below = reference_zone_score(
        DEBT_LOWER - width,
        DEBT_LOWER,
        DEBT_UPPER,
        lambda_lower=penalty_lambda,
        lambda_upper=penalty_lambda,
    )

    score_above = reference_zone_score(
        DEBT_UPPER + width,
        DEBT_LOWER,
        DEBT_UPPER,
        lambda_lower=penalty_lambda,
        lambda_upper=penalty_lambda,
    )

    assert score_below == pytest.approx(0.5)
    assert score_above == pytest.approx(0.5)


def test_government_debt_inside_reference_zone():
    assert score_government_debt(
        DEBT_LOWER
    ) == 1.0

    assert score_government_debt(
        DEBT_UPPER
    ) == 1.0


def test_current_account_inside_reference_zone():
    assert score_current_account(
        CURRENT_ACCOUNT_LOWER
    ) == 1.0

    assert score_current_account(
        CURRENT_ACCOUNT_UPPER
    ) == 1.0


def test_fx_reserves_minimum_and_maximum():
    assert score_fx_reserves(
        2.0,
        2.0,
        10.0,
    ) == 0.0

    assert score_fx_reserves(
        10.0,
        2.0,
        10.0,
    ) == 1.0


def test_fx_reserves_midpoint():
    assert score_fx_reserves(
        6.0,
        2.0,
        10.0,
    ) == pytest.approx(0.5)


def test_resilience_pillar_uses_arithmetic_mean():
    score = calculate_resilience_pillar(
        0.6,
        0.8,
        1.0,
    )

    assert score == pytest.approx(0.8)


def test_resilience_pillar_zero_is_zero():
    assert calculate_resilience_pillar(
        0.0,
        0.0,
        0.0,
    ) == 0.0


def test_resilience_pillar_requires_all_scores():
    assert calculate_resilience_pillar(
        0.8,
        None,
        0.9,
    ) is None


def test_resilience_pillar_rejects_invalid_scores():
    with pytest.raises(ValueError):
        calculate_resilience_pillar(
            1.2,
            0.8,
            0.9,
        )


def test_reference_zone_rejects_invalid_boundaries():
    with pytest.raises(ValueError):
        reference_zone_score(
            50.0,
            80.0,
            20.0,
        )


def test_reference_zone_rejects_negative_penalty():
    with pytest.raises(ValueError):
        reference_zone_score(
            50.0,
            20.0,
            80.0,
            lambda_lower=-0.1,
        )
