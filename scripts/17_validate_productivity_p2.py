"""
JESI Productivity P2 Validation Module

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

P2 Indicator:
    Total Factor Productivity (TFP) Growth

Source:
    Penn World Table (PWT) 11.0

Expected period:
    2015-2023

Countries:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/raw/"
    "productivity_p2_tfp_growth_2015_2023.csv"
)

COUNTRIES = [
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
]

COUNTRY_CODES = [
    "BGD",
    "IND",
    "VNM",
    "IDN",
    "MYS",
]

START_YEAR = 2015
END_YEAR = 2023

EXPECTED_ROWS = 5 * 9
EXPECTED_GROWTH_ROWS = 5 * 8


def validate_columns(dataframe):
    """
    Validate the required dataset columns.
    """

    required_columns = {
        "country_code",
        "country",
        "year",
        "tfp",
        "tfp_growth",
    }

    missing_columns = (
        required_columns
        - set(dataframe.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing_columns)}"
        )


def validate_countries(dataframe):
    """
    Validate the country set and country codes.
    """

    actual_countries = sorted(
        dataframe["country"].unique()
    )

    expected_countries = sorted(
        COUNTRIES
    )

    if actual_countries != expected_countries:
        raise ValueError(
            "Unexpected country set. "
            f"Expected {expected_countries}, "
            f"found {actual_countries}."
        )

    actual_codes = sorted(
        dataframe["country_code"].unique()
    )

    expected_codes = sorted(
        COUNTRY_CODES
    )

    if actual_codes != expected_codes:
        raise ValueError(
            "Unexpected country-code set. "
            f"Expected {expected_codes}, "
            f"found {actual_codes}."
        )


def validate_years(dataframe):
    """
    Validate the year range and country-year coverage.
    """

    if dataframe["year"].min() != START_YEAR:
        raise ValueError(
            "Unexpected minimum year."
        )

    if dataframe["year"].max() != END_YEAR:
        raise ValueError(
            "Unexpected maximum year."
        )

    years = set(
        dataframe["year"].unique()
    )

    expected_years = set(
        range(
            START_YEAR,
            END_YEAR + 1,
        )
    )

    if years != expected_years:
        raise ValueError(
            "Unexpected year set. "
            f"Expected {sorted(expected_years)}, "
            f"found {sorted(years)}."
        )


def validate_row_count(dataframe):
    """
    Validate the expected number of observations.
    """

    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Unexpected row count. "
            f"Expected {EXPECTED_ROWS}, "
            f"found {len(dataframe)}."
        )


def validate_duplicates(dataframe):
    """
    Ensure there is exactly one observation
    per country-year.
    """

    duplicate_mask = dataframe[
        [
            "country_code",
            "country",
            "year",
        ]
    ].duplicated()

    if duplicate_mask.any():
        raise ValueError(
            "Duplicate country-year observations "
            "found."
        )


def validate_tfp(dataframe):
    """
    Validate TFP level observations.
    """

    if dataframe["tfp"].isna().any():
        raise ValueError(
            "Missing TFP level observations found."
        )

    if not np.isfinite(
        dataframe["tfp"]
    ).all():
        raise ValueError(
            "Non-finite TFP values found."
        )

    if (
        dataframe["tfp"] <= 0
    ).any():
        raise ValueError(
            "TFP values must be positive."
        )


def validate_tfp_growth(dataframe):
    """
    Validate TFP growth observations.

    The first year for each country must be
    missing because annual growth requires the
    previous year's TFP level.

    All subsequent years must contain finite
    TFP growth observations.
    """

    first_year = dataframe[
        dataframe["year"] == START_YEAR
    ]

    if len(first_year) != len(COUNTRIES):
        raise ValueError(
            "Unexpected number of first-year "
            "observations."
        )

    if not first_year[
        "tfp_growth"
    ].isna().all():
        raise ValueError(
            "TFP growth for the first year of each "
            "country should be missing."
        )

    growth_data = dataframe[
        dataframe["year"] > START_YEAR
    ]

    if len(growth_data) != EXPECTED_GROWTH_ROWS:
        raise ValueError(
            "Unexpected number of TFP growth "
            "observations."
        )

    if growth_data[
        "tfp_growth"
    ].isna().any():
        raise ValueError(
            "Missing TFP growth observations found "
            "after the first year."
        )

    if not np.isfinite(
        growth_data["tfp_growth"]
    ).all():
        raise ValueError(
            "Non-finite TFP growth observations "
            "found."
        )


def validate_country_year_coverage(
    dataframe,
):
    """
    Ensure every country has a complete
    2015-2023 observation window.
    """

    expected_years = set(
        range(
            START_YEAR,
            END_YEAR + 1,
        )
    )

    for country in COUNTRIES:
        country_years = set(
            dataframe.loc[
                dataframe["country"] == country,
                "year",
            ]
        )

        if country_years != expected_years:
            raise ValueError(
                f"Incomplete year coverage for "
                f"{country}. "
                f"Expected {sorted(expected_years)}, "
                f"found {sorted(country_years)}."
            )


def main():
    """
    Run all P2 validation checks.
    """

    print("=" * 72)
    print("JESI PRODUCTIVITY P2 VALIDATION")
    print("=" * 72)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    dataframe = pd.read_csv(
        INPUT_FILE
    )

    validate_columns(
        dataframe
    )

    validate_countries(
        dataframe
    )

    validate_years(
        dataframe
    )

    validate_row_count(
        dataframe
    )

    validate_duplicates(
        dataframe
    )

    validate_tfp(
        dataframe
    )

    validate_tfp_growth(
        dataframe
    )

    validate_country_year_coverage(
        dataframe
    )

    print()
    print("VALIDATION SUMMARY")
    print("=" * 72)

    print()
    print(
        f"Rows validated: {len(dataframe)}"
    )

    print(
        f"Countries validated: {len(COUNTRIES)}"
    )

    print(
        f"Years validated: "
        f"{START_YEAR}-{END_YEAR}"
    )

    print(
        f"TFP level observations: "
        f"{dataframe['tfp'].notna().sum()}"
    )

    print(
        f"TFP growth observations: "
        f"{dataframe['tfp_growth'].notna().sum()}"
    )

    print(
        f"Expected TFP growth observations: "
        f"{EXPECTED_GROWTH_ROWS}"
    )

    print()
    print("Country coverage:")
    print(
        dataframe.groupby(
            "country"
        )["year"].agg(
            [
                "min",
                "max",
                "count",
            ]
        ).to_string()
    )

    print()
    print("TFP growth summary:")
    print(
        dataframe[
            "tfp_growth"
        ].describe().to_string()
    )

    print()
    print("=" * 72)
    print(
        "ALL P2 VALIDATION CHECKS PASSED."
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
