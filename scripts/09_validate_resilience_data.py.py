"""
JAS-JESI Resilience Data Validation

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This script validates the Resilience pillar dataset.

Resilience indicators:
    1. Total Reserves in Months of Imports
       FI.RES.TOTL.MO

    2. Central Government Debt (% of GDP)
       GC.DOD.TOTL.GD.ZS

    3. Current Account Balance (% of GDP)
       BN.CAB.XOKA.GD.ZS

Countries:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia

Period:
    2015–2024
"""

from pathlib import Path

from src.data_cleaning import (
    validate_indicator_coverage,
    validate_required_columns,
    validate_missing_values,
)

import pandas as pd


INPUT_FILE = Path(
    "data/raw/resilience_indicators_2015_2024.csv"
)


COUNTRIES = [
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
]


RESILIENCE_INDICATORS = [
    "FI.RES.TOTL.MO",
    "GC.DOD.TOTL.GD.ZS",
    "BN.CAB.XOKA.GD.ZS",
]


START_YEAR = 2015
END_YEAR = 2024


def main():
    print("Validating JESI Resilience data...")
    print(
        f"Expected countries: {COUNTRIES}"
    )
    print(
        f"Expected period: {START_YEAR}-{END_YEAR}"
    )

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    data = pd.read_csv(INPUT_FILE)

    print()
    print(
        f"Actual rows: {len(data)}"
    )

    expected_records = (
        len(COUNTRIES)
        * (END_YEAR - START_YEAR + 1)
        * len(RESILIENCE_INDICATORS)
    )

    print(
        f"Expected rows: {expected_records}"
    )

    validate_required_columns(
        data,
        [
            "country",
            "year",
            "value",
            "indicator",
        ],
    )

    missing_records = (
        validate_indicator_coverage(
            data,
            COUNTRIES,
            RESILIENCE_INDICATORS,
            START_YEAR,
            END_YEAR,
        )
    )

    print()
    print(
        f"Missing records: {len(missing_records)}"
    )

    if not missing_records.empty:
        print()
        print("Missing records:")
        print(missing_records)

    missing_values = (
        validate_missing_values(
            data,
            column="value",
        )
    )

    print()
    print(
        f"Missing indicator values: {missing_values}"
    )

    if len(data) != expected_records:
        print()
        print(
            "WARNING: Actual row count does not "
            "match expected row count."
        )

    if not missing_records.empty:
        print()
        print(
            "WARNING: Some country-year-indicator "
            "records are missing."
        )

    if missing_values > 0:
        print()
        print(
            "WARNING: Some indicator values are missing."
        )

    if (
        len(data) == expected_records
        and missing_records.empty
        and missing_values == 0
    ):
        print()
        print(
            "RESILIENCE DATA VALIDATION PASSED."
        )


if __name__ == "__main__":
    main()
