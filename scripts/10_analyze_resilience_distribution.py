"""
JAS Unified Economic Strength Index (JESI)
Resilience Distribution Analysis — Version 1.0

Purpose
-------
Analyze the empirical distributions of the JESI Resilience indicators
before defining nonlinear scoring rules.

Indicators
----------
1. FI.RES.TOTL.MO  -> FX Reserves / Import Cover
2. GGXWDG_NGDP     -> General Government Gross Debt / GDP
3. BN.CAB.XOKA.GD.ZS -> Current Account Balance / GDP

Countries
---------
BGD - Bangladesh
IND - India
VNM - Viet Nam
IDN - Indonesia
MYS - Malaysia

Period
------
2015–2024

This script DOES NOT calculate final JESI scores.
It produces descriptive statistics and candidate empirical
reference information for later methodological calibration.
"""

from pathlib import Path
import sys

import pandas as pd


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "resilience_indicators_2015_2024.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}

INDICATORS = {
    "FI.RES.TOTL.MO": "FX Reserves / Import Cover",
    "GGXWDG_NGDP": "General Government Gross Debt / GDP",
    "BN.CAB.XOKA.GD.ZS": "Current Account Balance / GDP",
}

EXPECTED_YEARS = list(range(2015, 2025))


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def fail(message: str) -> None:
    """Print an error message and stop execution."""
    print(f"ERROR: {message}")
    sys.exit(1)


def load_data() -> pd.DataFrame:
    """Load and validate the resilience dataset."""
    print("=" * 72)
    print("JESI RESILIENCE DISTRIBUTION ANALYSIS")
    print("=" * 72)

    print("\nInput file:")
    print(INPUT_FILE)

    if not INPUT_FILE.exists():
        fail(f"Input file not found: {INPUT_FILE}")

    try:
        df = pd.read_csv(INPUT_FILE)
    except Exception as exc:
        fail(f"Could not read CSV file: {exc}")

    print(f"\nLoaded rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    required_columns = {"country_code", "year", "indicator", "value"}

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        fail(
            "Missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    # Standardize data types.
    df["country_code"] = df["country_code"].astype(str).str.strip().str.upper()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    )

    df["indicator"] = (
        df["indicator"]
        .astype(str)
        .str.strip()
    )

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce"
    )

    if df["year"].isna().any():
        fail("Found invalid or missing year values.")

    if df["value"].isna().any():
        fail("Found missing or non-numeric indicator values.")

    df["year"] = df["year"].astype(int)

    return df


def validate_dataset(df: pd.DataFrame) -> None:
    """Validate expected countries, years and indicators."""

    print("\n" + "-" * 72)
    print("DATASET VALIDATION")
    print("-" * 72)

    expected_country_codes = set(COUNTRIES.keys())
    expected_indicators = set(INDICATORS.keys())
    expected_years = set(EXPECTED_YEARS)

    actual_country_codes = set(df["country_code"].unique())
    actual_indicators = set(df["indicator"].unique())
    actual_years = set(df["year"].unique())

    unexpected_countries = actual_country_codes - expected_country_codes
    missing_countries = expected_country_codes - actual_country_codes

    unexpected_indicators = actual_indicators - expected_indicators
    missing_indicators = expected_indicators - actual_indicators

    unexpected_years = actual_years - expected_years
    missing_years = expected_years - actual_years

    if unexpected_countries:
        fail(
            "Unexpected country codes found: "
            + ", ".join(sorted(unexpected_countries))
        )

    if missing_countries:
        fail(
            "Missing country codes: "
            + ", ".join(sorted(missing_countries))
        )

    if unexpected_indicators:
        fail(
            "Unexpected indicators found: "
            + ", ".join(sorted(unexpected_indicators))
        )

    if missing_indicators:
        fail(
            "Missing indicators: "
            + ", ".join(sorted(missing_indicators))
        )

    if unexpected_years:
        fail(
            "Unexpected years found: "
            + ", ".join(map(str, sorted(unexpected_years)))
        )

    if missing_years:
        fail(
            "Missing years: "
            + ", ".join(map(str, sorted(missing_years)))
        )

    # Check duplicate country-year-indicator observations.
    duplicate_mask = df.duplicated(
        subset=["country_code", "year", "indicator"],
        keep=False,
    )

    if duplicate_mask.any():
        duplicates = df.loc[
            duplicate_mask,
            ["country_code", "year", "indicator"]
        ].drop_duplicates()

        print("\nDuplicate records detected:")
        print(duplicates.to_string(index=False))

        fail("Duplicate country-year-indicator records found.")

    expected_rows = (
        len(COUNTRIES)
        * len(EXPECTED_YEARS)
        * len(INDICATORS)
    )

    if len(df) != expected_rows:
        fail(
            f"Unexpected number of rows. "
            f"Expected {expected_rows}, found {len(df)}."
        )

    print("Countries: OK")
    print("Indicators: OK")
    print("Years: OK")
    print("Duplicate check: OK")
    print(f"Expected rows: {expected_rows}")
    print(f"Actual rows:   {len(df)}")


def percentile_table(series: pd.Series) -> pd.DataFrame:
    """Return selected empirical percentiles."""
    percentiles = [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100]

    values = series.quantile(
        [p / 100 for p in percentiles]
    )

    result = pd.DataFrame(
        {
            "percentile": percentiles,
            "value": values.values,
        }
    )

    return result


def describe_indicator(df: pd.DataFrame, indicator: str) -> pd.DataFrame:
    """Create pooled descriptive statistics for one indicator."""

    subset = df.loc[
        df["indicator"] == indicator,
        "value"
    ]

    description = {
        "indicator": indicator,
        "indicator_name": INDICATORS[indicator],
        "n": int(subset.count()),
        "min": subset.min(),
        "p01": subset.quantile(0.01),
        "p05": subset.quantile(0.05),
        "p10": subset.quantile(0.10),
        "p25": subset.quantile(0.25),
        "median": subset.median(),
        "p75": subset.quantile(0.75),
        "p90": subset.quantile(0.90),
        "p95": subset.quantile(0.95),
        "p99": subset.quantile(0.99),
        "max": subset.max(),
        "mean": subset.mean(),
        "std": subset.std(),
    }

    return pd.DataFrame([description])


def country_statistics(
    df: pd.DataFrame,
    indicator: str,
) -> pd.DataFrame:
    """Create country-level descriptive statistics."""

    subset = df.loc[
        df["indicator"] == indicator
    ].copy()

    result = (
        subset.groupby("country_code")["value"]
        .agg(
            n="count",
            min="min",
            mean="mean",
            median="median",
            max="max",
            std="std",
        )
        .reset_index()
    )

    result["country"] = result["country_code"].map(COUNTRIES)

    result = result[
        [
            "country_code",
            "country",
            "n",
            "min",
            "mean",
            "median",
            "max",
            "std",
        ]
    ]

    return result.sort_values("country_code")


def pooled_percentiles(
    df: pd.DataFrame,
    indicator: str,
) -> pd.DataFrame:
    """Create pooled percentile table."""

    subset = df.loc[
        df["indicator"] == indicator,
        "value"
    ]

    result = percentile_table(subset)

    result.insert(
        0,
        "indicator",
        indicator,
    )

    result.insert(
        1,
        "indicator_name",
        INDICATORS[indicator],
    )

    return result


def country_year_extremes(
    df: pd.DataFrame,
    indicator: str,
) -> pd.DataFrame:
    """
    Identify minimum and maximum observations by country,
    including their corresponding years.
    """

    subset = df.loc[
        df["indicator"] == indicator
    ].copy()

    rows = []

    for country_code, group in subset.groupby("country_code"):

        min_row = group.loc[group["value"].idxmin()]
        max_row = group.loc[group["value"].idxmax()]

        rows.append(
            {
                "country_code": country_code,
                "country": COUNTRIES[country_code],
                "min_value": min_row["value"],
                "min_year": int(min_row["year"]),
                "max_value": max_row["value"],
                "max_year": int(max_row["year"]),
            }
        )

    return pd.DataFrame(rows).sort_values("country_code")


def reference_zone_candidates(
    df: pd.DataFrame,
    indicator: str,
) -> pd.DataFrame:
    """
    Produce candidate empirical central ranges.

    These are descriptive candidates only.
    They are NOT automatically adopted as final
    methodological reference zones.
    """

    subset = df.loc[
        df["indicator"] == indicator,
        "value"
    ]

    candidates = [
        {
            "indicator": indicator,
            "indicator_name": INDICATORS[indicator],
            "candidate": "P10-P90",
            "lower": subset.quantile(0.10),
            "upper": subset.quantile(0.90),
            "interpretation": "Broad central empirical range",
        },
        {
            "indicator": indicator,
            "indicator_name": INDICATORS[indicator],
            "candidate": "P25-P75",
            "lower": subset.quantile(0.25),
            "upper": subset.quantile(0.75),
            "interpretation": "Interquartile central range",
        },
        {
            "indicator": indicator,
            "indicator_name": INDICATORS[indicator],
            "candidate": "P05-P95",
            "lower": subset.quantile(0.05),
            "upper": subset.quantile(0.95),
            "interpretation": "Wide robust central range",
        },
    ]

    return pd.DataFrame(candidates)


def print_section(title: str) -> None:
    """Print a formatted section heading."""
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def save_output(
    dataframe: pd.DataFrame,
    filename: str,
) -> None:
    """Save dataframe to processed-data directory."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = OUTPUT_DIR / filename

    dataframe.to_csv(
        output_path,
        index=False,
    )

    print(f"Saved: {output_path}")


# ---------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------

def main() -> None:

    df = load_data()

    validate_dataset(df)

    # -------------------------------------------------------------
    # 1. Pooled descriptive statistics
    # -------------------------------------------------------------

    pooled_descriptive = pd.concat(
        [
            describe_indicator(df, indicator)
            for indicator in INDICATORS
        ],
        ignore_index=True,
    )

    print_section("POOLED DESCRIPTIVE STATISTICS")

    print(
        pooled_descriptive.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    save_output(
        pooled_descriptive,
        "resilience_pooled_descriptive_statistics.csv",
    )

    # -------------------------------------------------------------
    # 2. Country-level statistics
    # -------------------------------------------------------------

    country_stats_all = []

    for indicator in INDICATORS:

        stats = country_statistics(
            df,
            indicator,
        )

        country_stats_all.append(stats)

    country_stats_combined = pd.concat(
        country_stats_all,
        ignore_index=True,
    )

    print_section("COUNTRY-LEVEL DESCRIPTIVE STATISTICS")

    print(
        country_stats_combined.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    save_output(
        country_stats_combined,
        "resilience_country_statistics.csv",
    )

    # -------------------------------------------------------------
    # 3. Pooled percentiles
    # -------------------------------------------------------------

    percentile_tables = []

    for indicator in INDICATORS:

        table = pooled_percentiles(
            df,
            indicator,
        )

        percentile_tables.append(table)

    percentiles_combined = pd.concat(
        percentile_tables,
        ignore_index=True,
    )

    print_section("POOLED EMPIRICAL PERCENTILES")

    print(
        percentiles_combined.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    save_output(
        percentiles_combined,
        "resilience_pooled_percentiles.csv",
    )

    # -------------------------------------------------------------
    # 4. Country/year extremes
    # -------------------------------------------------------------

    extremes_tables = []

    for indicator in INDICATORS:

        table = country_year_extremes(
            df,
            indicator,
        )

        table.insert(
            0,
            "indicator",
            indicator,
        )

        table.insert(
            1,
            "indicator_name",
            INDICATORS[indicator],
        )

        extremes_tables.append(table)

    extremes_combined = pd.concat(
        extremes_tables,
        ignore_index=True,
    )

    print_section("COUNTRY/YEAR EXTREMES")

    print(
        extremes_combined.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    save_output(
        extremes_combined,
        "resilience_country_year_extremes.csv",
    )

    # -------------------------------------------------------------
    # 5. Candidate reference zones
    # -------------------------------------------------------------

    zone_tables = []

    # Focus especially on nonlinear indicators.
    nonlinear_indicators = [
        "GGXWDG_NGDP",
        "BN.CAB.XOKA.GD.ZS",
    ]

    for indicator in nonlinear_indicators:

        table = reference_zone_candidates(
            df,
            indicator,
        )

        zone_tables.append(table)

    zones_combined = pd.concat(
        zone_tables,
        ignore_index=True,
    )

    print_section("CANDIDATE EMPIRICAL REFERENCE ZONES")

    print(
        zones_combined.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print(
        "\nNOTE:"
        "\nThese ranges are descriptive candidates only."
        "\nThey are NOT final JESI scoring thresholds."
        "\nFinal reference zones require methodological justification "
        "and robustness testing."
    )

    save_output(
        zones_combined,
        "resilience_candidate_reference_zones.csv",
    )

    # -------------------------------------------------------------
    # 6. Indicator-specific interpretation summary
    # -------------------------------------------------------------

    interpretation = pd.DataFrame(
        [
            {
                "indicator": "GGXWDG_NGDP",
                "indicator_name": INDICATORS["GGXWDG_NGDP"],
                "baseline_concept":
                    "Nonlinear / target or penalty based",
                "reason":
                    "Debt sustainability depends on broader "
                    "macroeconomic and fiscal conditions.",
            },
            {
                "indicator": "BN.CAB.XOKA.GD.ZS",
                "indicator_name":
                    INDICATORS["BN.CAB.XOKA.GD.ZS"],
                "baseline_concept":
                    "Target-zone / distance based",
                "reason":
                    "Persistent extreme deficits or surpluses "
                    "may indicate structural imbalance.",
            },
        ]
    )

    print_section("NONLINEAR INDICATOR INTERPRETATION")

    print(
        interpretation.to_string(
            index=False,
        )
    )

    save_output(
        interpretation,
        "resilience_nonlinear_indicator_notes.csv",
    )

    # -------------------------------------------------------------
    # Final status
    # -------------------------------------------------------------

    print("\n" + "=" * 72)
    print("RESILIENCE DISTRIBUTION ANALYSIS COMPLETED SUCCESSFULLY")
    print("=" * 72)

    print(f"Countries: {len(COUNTRIES)}")
    print(f"Years: {EXPECTED_YEARS[0]}–{EXPECTED_YEARS[-1]}")
    print(f"Indicators: {len(INDICATORS)}")
    print(f"Observations analyzed: {len(df)}")

    print("\nOutput directory:")
    print(OUTPUT_DIR)

    print("\nNo final normalization or JESI score was calculated.")
    print(
        "The outputs are intended for empirical calibration of "
        "nonlinear resilience scoring."
    )


if __name__ == "__main__":
    main()
