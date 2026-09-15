"""
JESI Strategic Autonomy Data Validation
JAS Unified Economic Strength Index (JESI)

Script 30:
Validate Strategic Autonomy raw data.

Indicators:
    - Economic Complexity Index (ECI)
    - High-tech exports
    - Import product concentration
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024.csv"
)

COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}

YEARS = set(range(2015, 2025))

REQUIRED_COLUMNS = [
    "country_code",
    "country",
    "year",
    "eci",
    "high_tech_exports",
    "import_product_concentration",
]


def main():
    """Validate Strategic Autonomy data."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    data = pd.read_csv(INPUT_FILE)

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    expected_rows = len(COUNTRIES) * len(YEARS)

    if len(data) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, "
            f"found {len(data)}."
        )

    if set(data["country_code"]) != set(COUNTRIES):
        raise ValueError(
            "Country set does not match JESI sample."
        )

    if set(data["year"]) != YEARS:
        raise ValueError(
            "Year coverage must be 2015-2024."
        )

    if data.duplicated(
        ["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations found."
        )

    # Validate ECI and high-tech data.
    numeric_columns = [
        "eci",
        "high_tech_exports",
    ]

    for column in numeric_columns:
        values = data[column].dropna()

        if not np.isfinite(
            values.to_numpy()
        ).all():
            raise ValueError(
                f"Non-finite values found in {column}."
            )

    # Import concentration is required before
    # Strategic Autonomy can be finalized.
    concentration_missing = (
        data["import_product_concentration"]
        .isna()
        .sum()
    )

    print(
        "Strategic Autonomy validation completed."
    )
    print(f"Rows: {len(data)}")
    print(f"Countries: {len(COUNTRIES)}")
    print("Period: 2015-2024")
    print()
    print("Missing observations:")
    print(
        data[
            [
                "eci",
                "high_tech_exports",
                "import_product_concentration",
            ]
        ].isna().sum()
    )
    print()

    if concentration_missing > 0:
        print(
            "STATUS: BLOCKED"
        )
        print(
            "UNCTAD import product concentration "
            "data must be integrated before scoring."
        )
        print(
            f"Missing concentration observations: "
            f"{concentration_missing}"
        )

        raise ValueError(
            "Strategic Autonomy cannot be scored "
            "until import concentration data is available."
        )

    print("STATUS: GREEN")
    print(
        "All Strategic Autonomy indicators "
        "are available."
    )


if __name__ == "__main__":
    main()
