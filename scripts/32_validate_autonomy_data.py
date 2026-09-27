"""
JESI Strategic Autonomy Coverage Validation
Master Version 1.0

Validates structural integrity and reports source coverage.

Important:
Missing high-tech export observations are reported,
not imputed.
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024_complete.csv"
)

EXPECTED_COUNTRIES = {
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
}

EXPECTED_YEARS = set(range(2015, 2025))

REQUIRED_COLUMNS = {
    "country_code",
    "country",
    "year",
    "eci",
    "high_tech_exports",
    "import_product_concentration",
}


def main():
    print("=" * 70)
    print("JESI Strategic Autonomy Coverage Validation")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    missing_columns = (
        REQUIRED_COLUMNS - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    expected_rows = (
        len(EXPECTED_COUNTRIES)
        * len(EXPECTED_YEARS)
    )

    if len(df) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, "
            f"found {len(df)}."
        )

    if set(df["country"]) != EXPECTED_COUNTRIES:
        raise ValueError(
            "Country coverage does not match JESI sample."
        )

    actual_years = set(
        df["year"].astype(int)
    )

    if actual_years != EXPECTED_YEARS:
        raise ValueError(
            "Year coverage is not exactly 2015-2024."
        )

    if df.duplicated(
        ["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations detected."
        )

    numeric_columns = [
        "eci",
        "high_tech_exports",
        "import_product_concentration",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    print()
    print("Rows:", len(df))
    print(
        "Countries:",
        df["country_code"].nunique(),
    )
    print(
        "Years:",
        df["year"].nunique(),
    )

    print()
    print("Missing-value coverage:")

    missing_summary = (
        df[numeric_columns]
        .isna()
        .sum()
    )

    print(missing_summary)

    print()
    print("High-tech missing observations:")

    missing_high_tech = df[
        df["high_tech_exports"].isna()
    ][
        [
            "country_code",
            "country",
            "year",
        ]
    ].sort_values(
        [
            "country_code",
            "year",
        ]
    )

    if missing_high_tech.empty:
        print("NONE")
    else:
        print(
            missing_high_tech.to_string(
                index=False
            )
        )

    print()
    print(
        "Final JESI sample coverage check:"
    )

    final_sample = df[
        df["year"].between(
            2016,
            2023,
        )
    ].copy()

    expected_final_rows = 40

    print(
        "Expected final observations:",
        expected_final_rows,
    )

    print(
        "Final sample rows:",
        len(final_sample),
    )

    final_missing = (
        final_sample[numeric_columns]
        .isna()
        .sum()
    )

    print(
        "Missing values inside final sample:"
    )

    print(final_missing)

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print(
        "Strategic Autonomy coverage validation completed."
    )
    print(
        "Missing source observations were not fabricated."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
