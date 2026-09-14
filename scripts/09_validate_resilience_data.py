#!/usr/bin/env python3

"""
Validate JESI Resilience Pillar Data

Expected indicators:
1. FX Reserves / Import Cover
   World Bank: FI.RES.TOTL.MO

2. General Government Gross Debt (% GDP)
   IMF WEO April 2026: GGXWDG_NGDP

3. Current Account Balance (% GDP)
   World Bank: BN.CAB.XOKA.GD.ZS

Countries:
- Bangladesh
- India
- Viet Nam
- Indonesia
- Malaysia

Period:
2015-2024
"""

from pathlib import Path
import sys

import pandas as pd


# ============================================================
# Configuration
# ============================================================

DATA_FILE = Path(
    "data/raw/resilience_indicators_2015_2024.csv"
)

EXPECTED_COUNTRIES = [
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
]

EXPECTED_YEARS = list(range(2015, 2025))

# IMPORTANT:
# Government debt is now sourced from IMF WEO April 2026.
EXPECTED_INDICATORS = [
    "FI.RES.TOTL.MO",
    "GGXWDG_NGDP",
    "BN.CAB.XOKA.GD.ZS",
]

EXPECTED_ROWS = (
    len(EXPECTED_COUNTRIES)
    * len(EXPECTED_YEARS)
    * len(EXPECTED_INDICATORS)
)


# ============================================================
# Helper functions
# ============================================================

def normalize_country(value):
    """Normalize country names for reliable comparison."""

    if pd.isna(value):
        return ""

    value = str(value).strip()

    aliases = {
        "Viet Nam": "Viet Nam",
        "Vietnam": "Viet Nam",
        "Bangladesh": "Bangladesh",
        "India": "India",
        "Indonesia": "Indonesia",
        "Malaysia": "Malaysia",
    }

    return aliases.get(value, value)


def print_indicator_summary(df):
    """Print indicator counts for diagnostics."""

    print("\nIndicator counts:")

    counts = (
        df["indicator"]
        .value_counts()
        .sort_index()
    )

    for indicator, count in counts.items():
        print(f"  {indicator}: {count}")


# ============================================================
# Main validation
# ============================================================

def main():

    print("Validating JESI Resilience data...")

    print(f"Expected countries: {EXPECTED_COUNTRIES}")
    print(
        f"Expected period: "
        f"{EXPECTED_YEARS[0]}-{EXPECTED_YEARS[-1]}"
    )

    print("\nExpected indicators:")
    for indicator in EXPECTED_INDICATORS:
        print(f"  - {indicator}")

    # --------------------------------------------------------
    # Check file exists
    # --------------------------------------------------------

    if not DATA_FILE.exists():
        print(
            f"\nERROR: Data file not found: {DATA_FILE}"
        )
        sys.exit(1)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    try:
        df = pd.read_csv(DATA_FILE)
    except Exception as exc:
        print(
            f"\nERROR: Could not read data file: {exc}"
        )
        sys.exit(1)

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "country",
        "year",
        "indicator",
        "value",
    ]

    missing_columns = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        print(
            "\nERROR: Missing required columns:"
        )

        for col in missing_columns:
            print(f"  - {col}")

        print(
            f"\nActual columns: {list(df.columns)}"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Normalize fields
    # --------------------------------------------------------

    df["country"] = (
        df["country"]
        .apply(normalize_country)
    )

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

    # --------------------------------------------------------
    # Basic row count
    # --------------------------------------------------------

    actual_rows = len(df)

    print(f"\nActual rows: {actual_rows}")
    print(f"Expected rows: {EXPECTED_ROWS}")

    # --------------------------------------------------------
    # Duplicate detection
    # --------------------------------------------------------

    key_columns = [
        "country",
        "year",
        "indicator",
    ]

    duplicates = df[
        df.duplicated(
            subset=key_columns,
            keep=False
        )
    ]

    if not duplicates.empty:

        print(
            f"\nERROR: Duplicate records found: "
            f"{len(duplicates)}"
        )

        print(
            duplicates[
                key_columns + ["value"]
            ].sort_values(key_columns).to_string(
                index=False
            )
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Build expected records
    # --------------------------------------------------------

    expected_records = pd.MultiIndex.from_product(
        [
            EXPECTED_COUNTRIES,
            EXPECTED_YEARS,
            EXPECTED_INDICATORS,
        ],
        names=[
            "country",
            "year",
            "indicator",
        ],
    ).to_frame(index=False)

    # --------------------------------------------------------
    # Actual record keys
    # --------------------------------------------------------

    actual_records = df[
        key_columns
    ].drop_duplicates()

    # --------------------------------------------------------
    # Find missing records
    # --------------------------------------------------------

    missing_records = expected_records.merge(
        actual_records,
        on=key_columns,
        how="left",
        indicator=True,
    )

    missing_records = missing_records[
        missing_records["_merge"] == "left_only"
    ].drop(columns=["_merge"])

    print(
        f"\nMissing records: "
        f"{len(missing_records)}"
    )

    if not missing_records.empty:

        print("\nMissing records:")

        print(
            missing_records.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # Find unexpected records
    # --------------------------------------------------------

    unexpected_records = actual_records.merge(
        expected_records,
        on=key_columns,
        how="left",
        indicator=True,
    )

    unexpected_records = unexpected_records[
        unexpected_records["_merge"]
        == "left_only"
    ].drop(columns=["_merge"])

    if not unexpected_records.empty:

        print(
            f"\nUnexpected records: "
            f"{len(unexpected_records)}"
        )

        print("\nUnexpected records:")

        print(
            unexpected_records.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # Missing indicator values
    # --------------------------------------------------------

    missing_values = df[
        df["value"].isna()
    ]

    print(
        f"\nMissing indicator values: "
        f"{len(missing_values)}"
    )

    if not missing_values.empty:

        print("\nRecords with missing values:")

        print(
            missing_values[
                key_columns + ["value"]
            ].to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # Indicator summary
    # --------------------------------------------------------

    print_indicator_summary(df)

    # --------------------------------------------------------
    # Country summary
    # --------------------------------------------------------

    print("\nCountry counts:")

    country_counts = (
        df["country"]
        .value_counts()
        .sort_index()
    )

    for country, count in country_counts.items():
        print(f"  {country}: {count}")

    # --------------------------------------------------------
    # Year summary
    # --------------------------------------------------------

    print("\nYear counts:")

    year_counts = (
        df["year"]
        .value_counts()
        .sort_index()
    )

    for year, count in year_counts.items():
        print(f"  {int(year)}: {count}")

    # --------------------------------------------------------
    # Validate countries
    # --------------------------------------------------------

    actual_countries = set(
        df["country"].dropna()
    )

    expected_countries = set(
        EXPECTED_COUNTRIES
    )

    missing_countries = (
        expected_countries
        - actual_countries
    )

    unexpected_countries = (
        actual_countries
        - expected_countries
    )

    if missing_countries:

        print(
            "\nERROR: Missing countries:"
        )

        for country in sorted(
            missing_countries
        ):
            print(f"  - {country}")

    if unexpected_countries:

        print(
            "\nERROR: Unexpected countries:"
        )

        for country in sorted(
            unexpected_countries
        ):
            print(f"  - {country}")

    # --------------------------------------------------------
    # Validate years
    # --------------------------------------------------------

    actual_years = set(
        int(year)
        for year in df["year"].dropna()
    )

    expected_years = set(
        EXPECTED_YEARS
    )

    missing_years = (
        expected_years
        - actual_years
    )

    unexpected_years = (
        actual_years
        - expected_years
    )

    if missing_years:

        print(
            "\nERROR: Missing years:"
        )

        for year in sorted(
            missing_years
        ):
            print(f"  - {year}")

    if unexpected_years:

        print(
            "\nERROR: Unexpected years:"
        )

        for year in sorted(
            unexpected_years
        ):
            print(f"  - {year}")

    # --------------------------------------------------------
    # Validate indicators
    # --------------------------------------------------------

    actual_indicators = set(
        df["indicator"].dropna()
    )

    expected_indicators = set(
        EXPECTED_INDICATORS
    )

    missing_indicators = (
        expected_indicators
        - actual_indicators
    )

    unexpected_indicators = (
        actual_indicators
        - expected_indicators
    )

    if missing_indicators:

        print(
            "\nERROR: Missing indicators:"
        )

        for indicator in sorted(
            missing_indicators
        ):
            print(f"  - {indicator}")

    if unexpected_indicators:

        print(
            "\nWARNING: Unexpected indicators:"
        )

        for indicator in sorted(
            unexpected_indicators
        ):
            print(f"  - {indicator}")

    # --------------------------------------------------------
    # Final validation decision
    # --------------------------------------------------------

    validation_failed = False

    if actual_rows != EXPECTED_ROWS:
        validation_failed = True

    if not missing_records.empty:
        validation_failed = True

    if not unexpected_records.empty:
        validation_failed = True

    if not missing_values.empty:
        validation_failed = True

    if missing_countries:
        validation_failed = True

    if unexpected_countries:
        validation_failed = True

    if missing_years:
        validation_failed = True

    if unexpected_years:
        validation_failed = True

    if missing_indicators:
        validation_failed = True

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    if validation_failed:

        print(
            "\nWARNING: "
            "Some country-year-indicator "
            "records are missing."
        )

        sys.exit(1)

    print(
        "\nValidation checks passed."
    )

    print(
        f"Total rows: {actual_rows}"
    )

    print(
        "\nJESI Resilience data validation "
        "completed successfully."
    )


if __name__ == "__main__":
    main()
