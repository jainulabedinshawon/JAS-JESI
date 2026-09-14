"""
JAS-JESI Real Data Validation Pipeline
Step 2: Validate Growth Pillar Data

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This script validates the expected coverage and
missing values in the Growth pillar dataset.
"""

from pathlib import Path

import pandas as pd

from src.data_cleaning import (
    validate_required_columns,
    validate_indicator_coverage,
    validate_missing_values,
)


COUNTRIES = [
    "Bangladesh",
    "India",
    "Vietnam",
    "Indonesia",
    "Malaysia",
]


INDICATORS = [
    "NY.GDP.MKTP.KD.ZG",
    "NY.GNP.PCAP.KD.ZG",
]


START_YEAR = 2015
END_YEAR = 2025


INPUT_FILE = Path(
    "data/raw/growth_indicators_2015_2025.csv"
)


def main():
    """
    Validate the real JESI Growth dataset.
    """

    print("Validating JESI Growth pillar data...")
    print()

    dataframe = pd.read_csv(
        INPUT_FILE
    )

    print(f"Rows loaded: {len(dataframe)}")
    print()

    validate_required_columns(
        dataframe,
        [
            "country",
            "year",
            "value",
            "indicator",
        ],
    )

    print("Required columns: OK")
    print()

    missing_records = validate_indicator_coverage(
        dataframe=dataframe,
        countries=COUNTRIES,
        indicators=INDICATORS,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    print(
        f"Expected observations: "
        f"{len(COUNTRIES) * (END_YEAR - START_YEAR + 1) * len(INDICATORS)}"
    )

    print(
        f"Actual observations: "
        f"{len(dataframe)}"
    )

    print(
        f"Missing records: "
        f"{len(missing_records)}"
    )

    print()

    if missing_records.empty:
        print("Coverage validation: PASS")
    else:
        print("Coverage validation: MISSING RECORDS")
        print()
        print(missing_records)

    print()

    missing_values = validate_missing_values(
        dataframe,
        "value",
    )

    print(
        f"Missing indicator values: "
        f"{missing_values}"
    )

    print()

    if missing_values == 0:
        print("Missing-value validation: PASS")
    else:
        print(
            "Missing-value validation: "
            "MISSING VALUES DETECTED"
        )

    print()
    print("Validation completed.")


if __name__ == "__main__":
    main()
