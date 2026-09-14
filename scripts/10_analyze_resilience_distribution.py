"""
JESI Resilience Distribution Analysis

Purpose:
    Analyze the empirical distribution of the three resilience indicators
    for Bangladesh, India, Viet Nam, Indonesia, and Malaysia over 2015-2024.

This script does NOT calculate final JESI scores.
It provides descriptive statistics and empirical reference zones that can
later be used to calibrate nonlinear resilience scoring.

Input:
    data/raw/resilience_indicators_2015_2024.csv

Expected input columns:
    country
    year
    value
    indicator

Outputs:
    data/processed/resilience_pooled_descriptive_statistics.csv
    data/processed/resilience_country_statistics.csv
    data/processed/resilience_pooled_percentiles.csv
    data/processed/resilience_country_year_extremes.csv
    data/processed/resilience_candidate_reference_zones.csv
    data/processed/resilience_nonlinear_indicator_notes.csv
"""

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = BASE_DIR / "data" / "raw" / (
    "resilience_indicators_2015_2024.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "processed"

EXPECTED_COUNTRIES = {
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
}

EXPECTED_YEARS = set(range(2015, 2025))

EXPECTED_INDICATORS = {
    "FI.RES.TOTL.MO",
    "GGXWDG_NGDP",
    "BN.CAB.XOKA.GD.ZS",
}

INDICATOR_NAMES = {
    "FI.RES.TOTL.MO": "FX Reserves / Import Cover",
    "GGXWDG_NGDP": "Government Gross Debt / GDP",
    "BN.CAB.XOKA.GD.ZS": "Current Account Balance / GDP",
}


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def validate_input(df):
    """Validate the structure and coverage of the input dataset."""

    required_columns = {
        "country",
        "year",
        "value",
        "indicator",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    if df["year"].isna().any():
        raise ValueError("Found invalid year values.")

    if df["value"].isna().any():
        raise ValueError("Found missing or non-numeric indicator values.")

    df["year"] = df["year"].astype(int)

    countries = set(df["country"].unique())
    years = set(df["year"].unique())
    indicators = set(df["indicator"].unique())

    unexpected_countries = countries - EXPECTED_COUNTRIES
    unexpected_years = years - EXPECTED_YEARS
    unexpected_indicators = indicators - EXPECTED_INDICATORS

    if unexpected_countries:
        raise ValueError(
            f"Unexpected countries found: {sorted(unexpected_countries)}"
        )

    if unexpected_years:
        raise ValueError(
            f"Unexpected years found: {sorted(unexpected_years)}"
        )

    if unexpected_indicators:
        raise ValueError(
            f"Unexpected indicators found: {sorted(unexpected_indicators)}"
        )

    expected_rows = (
        len(EXPECTED_COUNTRIES)
        * len(EXPECTED_YEARS)
        * len(EXPECTED_INDICATORS)
    )

    if len(df) != expected_rows:
        raise ValueError(
            f"Unexpected row count: {len(df)}. "
            f"Expected {expected_rows}."
        )

    duplicates = df.duplicated(
        subset=["country", "year", "indicator"]
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate country-year-indicator records found."
        )

    return df


def pooled_descriptive_statistics(df):
    """Calculate pooled descriptive statistics by indicator."""

    rows = []

    for indicator in sorted(EXPECTED_INDICATORS):
        subset = df[df["indicator"] == indicator]["value"]

        rows.append(
            {
                "indicator": indicator,
                "indicator_name": INDICATOR_NAMES[indicator],
                "count": int(subset.count()),
                "mean": subset.mean(),
                "std": subset.std(),
                "min": subset.min(),
                "p05": subset.quantile(0.05),
                "p10": subset.quantile(0.10),
                "p25": subset.quantile(0.25),
                "median": subset.median(),
                "p75": subset.quantile(0.75),
                "p90": subset.quantile(0.90),
                "p95": subset.quantile(0.95),
                "max": subset.max(),
            }
        )

    return pd.DataFrame(rows)


def country_statistics(df):
    """Calculate country-level statistics by indicator."""

    rows = []

    for country in sorted(EXPECTED_COUNTRIES):
        for indicator in sorted(EXPECTED_INDICATORS):

            subset = df[
                (df["country"] == country)
                & (df["indicator"] == indicator)
            ]["value"]

            rows.append(
                {
                    "country": country,
                    "indicator": indicator,
                    "indicator_name": INDICATOR_NAMES[indicator],
                    "count": int(subset.count()),
                    "mean": subset.mean(),
                    "std": subset.std(),
                    "min": subset.min(),
                    "median": subset.median(),
                    "max": subset.max(),
                }
            )

    return pd.DataFrame(rows)


def pooled_percentiles(df):
    """Calculate pooled empirical percentiles."""

    percentile_levels = [
        0.01,
        0.05,
        0.10,
        0.25,
        0.50,
        0.75,
        0.90,
        0.95,
        0.99,
    ]

    rows = []

    for indicator in sorted(EXPECTED_INDICATORS):

        subset = df[
            df["indicator"] == indicator
        ]["value"]

        for percentile in percentile_levels:
            rows.append(
                {
                    "indicator": indicator,
                    "indicator_name": INDICATOR_NAMES[indicator],
                    "percentile": percentile * 100,
                    "value": subset.quantile(percentile),
                }
            )

    return pd.DataFrame(rows)


def country_year_extremes(df):
    """Identify minimum and maximum observations by indicator."""

    rows = []

    for indicator in sorted(EXPECTED_INDICATORS):

        subset = df[df["indicator"] == indicator].copy()

        min_row = subset.loc[subset["value"].idxmin()]
        max_row = subset.loc[subset["value"].idxmax()]

        rows.append(
            {
                "indicator": indicator,
                "indicator_name": INDICATOR_NAMES[indicator],
                "extreme_type": "minimum",
                "country": min_row["country"],
                "year": int(min_row["year"]),
                "value": min_row["value"],
            }
        )

        rows.append(
            {
                "indicator": indicator,
                "indicator_name": INDICATOR_NAMES[indicator],
                "extreme_type": "maximum",
                "country": max_row["country"],
                "year": int(max_row["year"]),
                "value": max_row["value"],
            }
        )

    return pd.DataFrame(rows)


def candidate_reference_zones(df):
    """
    Produce descriptive candidate reference zones.

    These are NOT final scoring thresholds.
    They are empirical candidates for later methodological calibration.
    """

    rows = []

    for indicator in [
        "GGXWDG_NGDP",
        "BN.CAB.XOKA.GD.ZS",
    ]:

        subset = df[
            df["indicator"] == indicator
        ]["value"]

        p05 = subset.quantile(0.05)
        p10 = subset.quantile(0.10)
        p25 = subset.quantile(0.25)
        p75 = subset.quantile(0.75)
        p90 = subset.quantile(0.90)
        p95 = subset.quantile(0.95)

        zones = [
            ("P05-P95", p05, p95),
            ("P10-P90", p10, p90),
            ("P25-P75", p25, p75),
        ]

        for zone_name, lower, upper in zones:

            rows.append(
                {
                    "indicator": indicator,
                    "indicator_name": INDICATOR_NAMES[indicator],
                    "reference_zone": zone_name,
                    "lower_bound": lower,
                    "upper_bound": upper,
                    "interpretation": (
                        "Descriptive empirical candidate only; "
                        "not a final scoring threshold."
                    ),
                }
            )

    return pd.DataFrame(rows)


def nonlinear_indicator_notes():
    """Document conceptual treatment of nonlinear resilience indicators."""

    rows = [
        {
            "indicator": "GGXWDG_NGDP",
            "indicator_name": "Government Gross Debt / GDP",
            "baseline_direction": "Nonlinear",
            "proposed_treatment": "Target/penalty or reference-zone model",
            "reason": (
                "Lower debt is not automatically stronger. "
                "Debt sustainability depends on growth, interest rates, "
                "maturity, currency composition, and fiscal capacity."
            ),
        },
        {
            "indicator": "BN.CAB.XOKA.GD.ZS",
            "indicator_name": "Current Account Balance / GDP",
            "baseline_direction": "Target-optimal",
            "proposed_treatment": "Reference-zone / distance-from-zone model",
            "reason": (
                "Both persistent large deficits and unusually large "
                "surpluses may indicate structural imbalance."
            ),
        },
        {
            "indicator": "FI.RES.TOTL.MO",
            "indicator_name": "FX Reserves / Import Cover",
            "baseline_direction": "Higher is better",
            "proposed_treatment": "Positive normalization baseline",
            "reason": (
                "Higher reserve coverage generally improves external "
                "shock-absorption capacity, subject to robustness testing."
            ),
        },
    ]

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------

def main():
    print("=" * 72)
    print("JESI RESILIENCE DISTRIBUTION ANALYSIS")
    print("=" * 72)
    print()

    print("Input file:")
    print(INPUT_FILE)
    print()

    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        return 1

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print()

    try:
        df = validate_input(df)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Input validation: PASSED")
    print()

    print("=" * 72)
    print("POOLED DESCRIPTIVE STATISTICS")
    print("=" * 72)

    pooled_stats = pooled_descriptive_statistics(df)
    print(pooled_stats.to_string(index=False))
    print()

    print("=" * 72)
    print("COUNTRY-LEVEL STATISTICS")
    print("=" * 72)

    country_stats = country_statistics(df)
    print(country_stats.to_string(index=False))
    print()

    print("=" * 72)
    print("POOLED EMPIRICAL PERCENTILES")
    print("=" * 72)

    percentiles = pooled_percentiles(df)
    print(percentiles.to_string(index=False))
    print()

    print("=" * 72)
    print("COUNTRY-YEAR EXTREMES")
    print("=" * 72)

    extremes = country_year_extremes(df)
    print(extremes.to_string(index=False))
    print()

    print("=" * 72)
    print("CANDIDATE EMPIRICAL REFERENCE ZONES")
    print("=" * 72)

    zones = candidate_reference_zones(df)
    print(zones.to_string(index=False))
    print()

    print("=" * 72)
    print("NONLINEAR INDICATOR TREATMENT NOTES")
    print("=" * 72)

    notes = nonlinear_indicator_notes()
    print(notes.to_string(index=False))
    print()

    # -----------------------------------------------------------------
    # Save outputs
    # -----------------------------------------------------------------

    pooled_stats.to_csv(
        OUTPUT_DIR / "resilience_pooled_descriptive_statistics.csv",
        index=False,
    )

    country_stats.to_csv(
        OUTPUT_DIR / "resilience_country_statistics.csv",
        index=False,
    )

    percentiles.to_csv(
        OUTPUT_DIR / "resilience_pooled_percentiles.csv",
        index=False,
    )

    extremes.to_csv(
        OUTPUT_DIR / "resilience_country_year_extremes.csv",
        index=False,
    )

    zones.to_csv(
        OUTPUT_DIR / "resilience_candidate_reference_zones.csv",
        index=False,
    )

    notes.to_csv(
        OUTPUT_DIR / "resilience_nonlinear_indicator_notes.csv",
        index=False,
    )

    print("=" * 72)
    print("OUTPUT FILES")
    print("=" * 72)

    output_files = [
        "resilience_pooled_descriptive_statistics.csv",
        "resilience_country_statistics.csv",
        "resilience_pooled_percentiles.csv",
        "resilience_country_year_extremes.csv",
        "resilience_candidate_reference_zones.csv",
        "resilience_nonlinear_indicator_notes.csv",
    ]

    for filename in output_files:
        print(f"Saved: data/processed/{filename}")

    print()
    print("=" * 72)
    print("JESI resilience distribution analysis completed successfully.")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
