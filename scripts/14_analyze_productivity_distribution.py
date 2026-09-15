"""
JESI Productivity P1 Distribution Analysis

Purpose:
    Analyze the empirical distribution of GDP per Person
    Employed before defining the normalization protocol.

Indicator:
    SL.GDP.PCAP.EM.KD

Period:
    2015-2024

Countries:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia
"""

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = BASE_DIR / "data" / "raw" / (
    "productivity_p1_gdp_per_person_employed_2015_2024.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "processed"

POOLED_STATS_FILE = OUTPUT_DIR / (
    "productivity_p1_pooled_descriptive_statistics.csv"
)

COUNTRY_STATS_FILE = OUTPUT_DIR / (
    "productivity_p1_country_statistics.csv"
)

PERCENTILES_FILE = OUTPUT_DIR / (
    "productivity_p1_pooled_percentiles.csv"
)

EXTREMES_FILE = OUTPUT_DIR / (
    "productivity_p1_country_year_extremes.csv"
)

REFERENCE_ZONES_FILE = OUTPUT_DIR / (
    "productivity_p1_candidate_reference_zones.csv"
)

EXPECTED_COUNTRIES = {
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
}

EXPECTED_YEARS = set(range(2015, 2025))

EXPECTED_INDICATOR = "SL.GDP.PCAP.EM.KD"


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def validate_input(df):
    """Validate the P1 input dataset."""

    required_columns = {
        "country",
        "year",
        "value",
        "indicator",
    }

    missing_columns = (
        required_columns - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    df = df.copy()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce",
    )

    if df["year"].isna().any():
        raise ValueError(
            "Found invalid year values."
        )

    if df["value"].isna().any():
        raise ValueError(
            "Found missing or non-numeric values."
        )

    df["year"] = df["year"].astype(int)

    if set(df["country"].unique()) != EXPECTED_COUNTRIES:
        raise ValueError(
            "Country coverage does not match the "
            "expected five-country sample."
        )

    if set(df["year"].unique()) != EXPECTED_YEARS:
        raise ValueError(
            "Year coverage does not match 2015-2024."
        )

    if set(df["indicator"].unique()) != {
        EXPECTED_INDICATOR
    }:
        raise ValueError(
            "Indicator coverage does not match "
            "SL.GDP.PCAP.EM.KD."
        )

    expected_rows = (
        len(EXPECTED_COUNTRIES)
        * len(EXPECTED_YEARS)
    )

    if len(df) != expected_rows:
        raise ValueError(
            f"Unexpected row count: {len(df)}. "
            f"Expected {expected_rows}."
        )

    if df.duplicated(
        subset=["country", "year", "indicator"]
    ).any():
        raise ValueError(
            "Duplicate country-year-indicator "
            "records found."
        )

    if (df["value"] <= 0).any():
        raise ValueError(
            "GDP per Person Employed values must "
            "be strictly positive."
        )

    return df


# ---------------------------------------------------------------------
# Pooled descriptive statistics
# ---------------------------------------------------------------------

def calculate_pooled_statistics(df):
    """Calculate descriptive statistics for the pooled sample."""

    values = df["value"]

    statistics = {
        "indicator": EXPECTED_INDICATOR,
        "observations": len(values),
        "minimum": values.min(),
        "maximum": values.max(),
        "mean": values.mean(),
        "median": values.median(),
        "standard_deviation": values.std(),
        "variance": values.var(),
        "coefficient_of_variation": (
            values.std() / values.mean()
        ),
    }

    return pd.DataFrame([statistics])


# ---------------------------------------------------------------------
# Country statistics
# ---------------------------------------------------------------------

def calculate_country_statistics(df):
    """Calculate descriptive statistics by country."""

    country_stats = (
        df.groupby("country")["value"]
        .agg(
            observations="count",
            minimum="min",
            maximum="max",
            mean="mean",
            median="median",
            standard_deviation="std",
        )
        .reset_index()
    )

    country_stats["coefficient_of_variation"] = (
        country_stats["standard_deviation"]
        / country_stats["mean"]
    )

    return country_stats.sort_values(
        "country"
    ).reset_index(drop=True)


# ---------------------------------------------------------------------
# Pooled percentiles
# ---------------------------------------------------------------------

def calculate_percentiles(df):
    """Calculate empirical percentiles for the pooled sample."""

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

    values = df["value"]

    records = []

    for percentile in percentile_levels:
        records.append(
            {
                "indicator": EXPECTED_INDICATOR,
                "percentile": (
                    f"P{int(percentile * 100):02d}"
                ),
                "value": values.quantile(
                    percentile
                ),
            }
        )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------
# Country-year extremes
# ---------------------------------------------------------------------

def calculate_extremes(df):
    """Identify minimum and maximum country-year observations."""

    minimum_row = df.loc[
        df["value"].idxmin()
    ]

    maximum_row = df.loc[
        df["value"].idxmax()
    ]

    records = [
        {
            "extreme_type": "minimum",
            "country": minimum_row["country"],
            "year": int(minimum_row["year"]),
            "value": minimum_row["value"],
        },
        {
            "extreme_type": "maximum",
            "country": maximum_row["country"],
            "year": int(maximum_row["year"]),
            "value": maximum_row["value"],
        },
    ]

    return pd.DataFrame(records)


# ---------------------------------------------------------------------
# Candidate empirical reference zones
# ---------------------------------------------------------------------

def calculate_reference_zones(percentiles):
    """
    Construct candidate empirical reference zones.

    These are descriptive sample-based zones only.
    They are not universal economic thresholds.
    """

    percentile_values = dict(
        zip(
            percentiles["percentile"],
            percentiles["value"],
        )
    )

    records = [
        {
            "indicator": EXPECTED_INDICATOR,
            "reference_zone": "P05-P95",
            "lower": percentile_values["P05"],
            "upper": percentile_values["P95"],
        },
        {
            "indicator": EXPECTED_INDICATOR,
            "reference_zone": "P10-P90",
            "lower": percentile_values["P10"],
            "upper": percentile_values["P90"],
        },
        {
            "indicator": EXPECTED_INDICATOR,
            "reference_zone": "P25-P75",
            "lower": percentile_values["P25"],
            "upper": percentile_values["P75"],
        },
    ]

    return pd.DataFrame(records)


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    print("=" * 72)
    print("JESI PRODUCTIVITY — P1 DISTRIBUTION ANALYSIS")
    print("=" * 72)
    print()

    print("Input:")
    print(INPUT_FILE)
    print()

    if not INPUT_FILE.exists():
        print(
            "ERROR: P1 productivity input file "
            "was not found."
        )
        return 1

    df = pd.read_csv(INPUT_FILE)

    print(
        f"Loaded rows: {len(df)}"
    )
    print()

    try:
        df = validate_input(df)
    except ValueError as exc:
        print(
            f"ERROR: {exc}"
        )
        return 1

    print("Input validation: PASSED")
    print()

    pooled_stats = calculate_pooled_statistics(df)

    country_stats = calculate_country_statistics(df)

    percentiles = calculate_percentiles(df)

    extremes = calculate_extremes(df)

    reference_zones = calculate_reference_zones(
        percentiles
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pooled_stats.to_csv(
        POOLED_STATS_FILE,
        index=False,
    )

    country_stats.to_csv(
        COUNTRY_STATS_FILE,
        index=False,
    )

    percentiles.to_csv(
        PERCENTILES_FILE,
        index=False,
    )

    extremes.to_csv(
        EXTREMES_FILE,
        index=False,
    )

    reference_zones.to_csv(
        REFERENCE_ZONES_FILE,
        index=False,
    )

    print("=" * 72)
    print("POOLED DESCRIPTIVE STATISTICS")
    print("=" * 72)

    print(
        pooled_stats.to_string(index=False)
    )
    print()

    print("=" * 72)
    print("POOLED PERCENTILES")
    print("=" * 72)

    print(
        percentiles.to_string(index=False)
    )
    print()

    print("=" * 72)
    print("COUNTRY STATISTICS")
    print("=" * 72)

    print(
        country_stats.to_string(index=False)
    )
    print()

    print("=" * 72)
    print("COUNTRY-YEAR EXTREMES")
    print("=" * 72)

    print(
        extremes.to_string(index=False)
    )
    print()

    print("=" * 72)
    print("CANDIDATE EMPIRICAL REFERENCE ZONES")
    print("=" * 72)

    print(
        reference_zones.to_string(index=False)
    )
    print()

    print(
        "Note: Candidate reference zones are "
        "sample-based descriptive ranges, not "
        "universal economic thresholds."
    )
    print()

    print("=" * 72)
    print("OUTPUTS")
    print("=" * 72)

    print(f"Saved: {POOLED_STATS_FILE}")
    print(f"Saved: {COUNTRY_STATS_FILE}")
    print(f"Saved: {PERCENTILES_FILE}")
    print(f"Saved: {EXTREMES_FILE}")
    print(f"Saved: {REFERENCE_ZONES_FILE}")
    print()

    print(
        "JESI Productivity P1 distribution "
        "analysis completed successfully."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
