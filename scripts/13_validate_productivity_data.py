"""
JESI Productivity P1 Data Validation

Purpose:
    Validate the downloaded GDP per Person Employed
    dataset before distribution analysis.

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

def validate_data(df):
    """Validate the complete P1 dataset."""

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
            "Found missing or non-numeric "
            "productivity values."
        )

    df["year"] = df["year"].astype(int)

    countries = set(df["country"].unique())
    years = set(df["year"].unique())
    indicators = set(df["indicator"].unique())

    if countries != EXPECTED_COUNTRIES:
        raise ValueError(
            "Country coverage does not match "
            "the expected five-country sample."
        )

    if years != EXPECTED_YEARS:
        raise ValueError(
            "Year coverage does not match "
            "2015-2024."
        )

    if indicators != {EXPECTED_INDICATOR}:
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

    duplicates = df.duplicated(
        subset=[
            "country",
            "year",
            "indicator",
        ]
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate country-year-indicator "
            "records found."
        )

    if (df["value"] <= 0).any():
        raise ValueError(
            "GDP per Person Employed must be "
            "strictly positive."
        )

    return df


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    print("=" * 72)
    print("JESI PRODUCTIVITY — P1 DATA VALIDATION")
    print("=" * 72)
    print()

    print("Input:")
    print(INPUT_FILE)
    print()

    if not INPUT_FILE.exists():
        print(
            "ERROR: Productivity P1 input file "
            "was not found."
        )
        return 1

    df = pd.read_csv(INPUT_FILE)

    print(
        f"Loaded rows: {len(df)}"
    )
    print()

    try:
        df = validate_data(df)
    except ValueError as exc:
        print(
            f"ERROR: {exc}"
        )
        return 1

    print("=" * 72)
    print("VALIDATION RESULTS")
    print("=" * 72)

    print("Status: PASSED")
    print(
        f"Countries: {len(EXPECTED_COUNTRIES)}"
    )
    print(
        f"Years: {min(EXPECTED_YEARS)}-"
        f"{max(EXPECTED_YEARS)}"
    )
    print(
        f"Indicator: {EXPECTED_INDICATOR}"
    )
    print(
        f"Observations: {len(df)}"
    )
    print(
        f"Missing values: {df['value'].isna().sum()}"
    )
    print(
        f"Duplicate records: "
        f"{df.duplicated().sum()}"
    )
    print()

    print("=" * 72)
    print("COUNTRY COVERAGE")
    print("=" * 72)

    for country in sorted(EXPECTED_COUNTRIES):
        count = (
            df[df["country"] == country]
            .shape[0]
        )

        print(
            f"{country}: {count} observations"
        )

    print()

    print(
        "JESI Productivity P1 validation "
        "completed successfully."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
