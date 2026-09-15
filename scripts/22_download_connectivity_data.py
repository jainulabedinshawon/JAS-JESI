"""
JESI Connectivity Data Validation
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/raw/connectivity_indicators_2015_2024.csv"
)

EXPECTED_COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}

START_YEAR = 2015
END_YEAR = 2024

REQUIRED_COLUMNS = {
    "country_code",
    "country",
    "year",
    "trade_openness",
    "fdi_inflows",
    "internet_use",
}


def main():
    print("=" * 72)
    print("JESI CONNECTIVITY DATA VALIDATION")
    print("=" * 72)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    dataframe = pd.read_csv(INPUT_FILE)

    missing_columns = REQUIRED_COLUMNS.difference(
        dataframe.columns
    )

    if missing_columns:
        raise ValueError(
            f"Missing columns: {sorted(missing_columns)}"
        )

    expected_rows = 5 * (
        END_YEAR - START_YEAR + 1
    )

    if len(dataframe) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, "
            f"found {len(dataframe)}."
        )

    if set(dataframe["country_code"]) != set(
        EXPECTED_COUNTRIES
    ):
        raise ValueError(
            "Country coverage does not match expected JESI countries."
        )

    for code, country in EXPECTED_COUNTRIES.items():
        subset = dataframe[
            dataframe["country_code"] == code
        ]

        if set(subset["country"]) != {country}:
            raise ValueError(
                f"Country name mismatch for {code}."
            )

        years = set(subset["year"])

        expected_years = set(
            range(START_YEAR, END_YEAR + 1)
        )

        if years != expected_years:
            raise ValueError(
                f"Year coverage mismatch for {country}."
            )

    if dataframe.duplicated(
        subset=["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations detected."
        )

    indicator_columns = [
        "trade_openness",
        "fdi_inflows",
        "internet_use",
    ]

    for column in indicator_columns:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        if dataframe[column].isna().any():
            missing = int(
                dataframe[column].isna().sum()
            )
            raise ValueError(
                f"{column} contains {missing} missing values."
            )

        if not np.isfinite(
            dataframe[column]
        ).all():
            raise ValueError(
                f"{column} contains non-finite values."
            )

    if (
        dataframe["trade_openness"] < 0
    ).any():
        raise ValueError(
            "Trade openness contains negative values."
        )

    if (
        dataframe["internet_use"] < 0
    ).any() or (
        dataframe["internet_use"] > 100
    ).any():
        raise ValueError(
            "Internet use must be between 0 and 100."
        )

    print()
    print("VALIDATION RESULTS")
    print("=" * 72)
    print(f"Rows                  : {len(dataframe)}")
    print(f"Countries             : {dataframe['country'].nunique()}")
    print(f"Years                 : {dataframe['year'].nunique()}")
    print("Duplicate country-year: 0")
    print("Missing values        : 0")
    print("Non-finite values     : 0")

    print()
    print(
        "JESI Connectivity data validation completed successfully."
    )


if __name__ == "__main__":
    main()
