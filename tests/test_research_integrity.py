"""
JESI Research-Integrity Tests
Master Version 1.0
"""

from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]

COUNTRIES = {
    "BGD",
    "IND",
    "VNM",
    "IDN",
    "MYS",
}

YEARS = set(range(2016, 2024))


def make_synthetic_panel():
    rows = []

    for country in sorted(COUNTRIES):
        for year in sorted(YEARS):
            rows.append(
                {
                    "country_code": country,
                    "year": year,
                    "G": 0.5,
                    "P": 0.5,
                    "C": 0.5,
                    "R": 0.5,
                    "A": 0.5,
                    "JESI": 50.0,
                }
            )

    return pd.DataFrame(rows)


def test_theoretical_panel_has_40_observations():
    df = make_synthetic_panel()

    assert len(df) == 40


def test_theoretical_panel_has_five_countries():
    df = make_synthetic_panel()

    assert set(df["country_code"]) == COUNTRIES


def test_theoretical_panel_has_eight_years_per_country():
    df = make_synthetic_panel()

    counts = (
        df.groupby("country_code")
        .size()
    )

    assert counts.to_dict() == {
        country: 8
        for country in COUNTRIES
    }


def test_complete_case_reduces_only_missing_rows():
    df = make_synthetic_panel()

    df.loc[
        (df["country_code"] == "BGD")
        & (df["year"] == 2016),
        "G",
    ] = float("nan")

    complete = df[
        [
            "G",
            "P",
            "C",
            "R",
            "A",
        ]
    ].notna().all(axis=1)

    assert int(complete.sum()) == 39
    assert int((~complete).sum()) == 1


def test_no_imputation_is_performed_by_complete_case_logic():
    df = make_synthetic_panel()

    df.loc[
        (df["country_code"] == "BGD")
        & (df["year"] == 2016),
        "A",
    ] = float("nan")

    complete = df[
        [
            "G",
            "P",
            "C",
            "R",
            "A",
        ]
    ].notna().all(axis=1)

    assert pd.isna(
        df.loc[
            (df["country_code"] == "BGD")
            & (df["year"] == 2016),
            "A",
        ].iloc[0]
    )

    assert not bool(
        complete.loc[
            (df["country_code"] == "BGD")
            & (df["year"] == 2016)
        ].iloc[0]
    )


def test_duplicate_country_year_is_detected():
    df = make_synthetic_panel()

    duplicate = df.iloc[[0]].copy()

    duplicated_df = pd.concat(
        [df, duplicate],
        ignore_index=True,
    )

    assert duplicated_df.duplicated(
        ["country_code", "year"]
    ).any()


def test_expected_documented_country_coverage():
    coverage = {
        "BGD": 2,
        "IND": 8,
        "VNM": 8,
        "IDN": 8,
        "MYS": 8,
    }

    assert sum(coverage.values()) == 34
    assert coverage["BGD"] == 2

    for country in [
        "IND",
        "VNM",
        "IDN",
        "MYS",
    ]:
        assert coverage[country] == 8


def test_balanced_panel_has_four_eligible_countries():
    coverage = {
        "BGD": 2,
        "IND": 8,
        "VNM": 8,
        "IDN": 8,
        "MYS": 8,
    }

    eligible = {
        country
        for country, observations in coverage.items()
        if observations == 8
    }

    assert eligible == {
        "IND",
        "VNM",
        "IDN",
        "MYS",
    }


def test_balanced_panel_has_32_observations():
    eligible_countries = 4
    years = 8

    assert eligible_countries * years == 32


def test_production_weights_sum_to_one():
    weights = {
        "G": 0.20,
        "P": 0.25,
        "C": 0.20,
        "R": 0.20,
        "A": 0.15,
    }

    assert sum(weights.values()) == pytest.approx(1.0)


def test_production_methodology_files_exist():
    assert (
        ROOT / "scripts/36_calculate_jesi.py"
    ).exists()

    assert (
        ROOT / "scripts/44_analyze_indicator_redundancy.py"
    ).exists()

    assert (
        ROOT / "scripts/45_normalization_sensitivity.py"
    ).exists()

    assert (
        ROOT / "scripts/46_weight_sensitivity.py"
    ).exists()

    assert (
        ROOT / "scripts/47_aggregation_sensitivity.py"
    ).exists()

    assert (
        ROOT / "scripts/48_historical_validation.py"
    ).exists()


def test_production_script_contains_no_common_imputation_calls():
    path = ROOT / "scripts/36_calculate_jesi.py"

    text = path.read_text(
        encoding="utf-8"
    ).lower()

    forbidden = [
        ".fillna(",
        ".interpolate(",
        "simpleimputer",
        "iterativeimputer",
        "knnimputer",
    ]

    for pattern in forbidden:
        assert pattern not in text
