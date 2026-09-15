"""
JESI Strategic Autonomy Data Validation
Master Version 1.0

Validates the completed Strategic Autonomy dataset
for the 2015–2024 benchmark period.
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
    print("JESI Strategic Autonomy Data Validation")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(f"Rows found: {len(df)}")
    print(f"Columns found: {list(df.columns)}")

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    expected_rows = len(EXPECTED_COUNTRIES) * len(EXPECTED_YEARS)

    if len(df) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, found {len(df)}."
        )

    actual_countries = set(df["country"])
    unexpected_countries = actual_countries - EXPECTED_COUNTRIES
    missing_countries = EXPECTED_COUNTRIES - actual_countries

    if unexpected_countries:
        raise ValueError(
            f"Unexpected countries: {sorted(unexpected_countries)}"
        )

    if missing_countries:
        raise ValueError(
            f"Missing countries: {sorted(missing_countries)}"
        )

    actual_years = set(df["year"].astype(int))

    if actual_years != EXPECTED_YEARS:
        raise ValueError(
            "Year coverage is not exactly 2015–2024."
        )

    duplicates = df.duplicated(
        subset=["country_code", "year"]
    )

    if duplicates.any():
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
            errors="coerce"
        )

        if df[column].isna().any():
            missing = int(df[column].isna().sum())

            raise ValueError(
                f"{column} contains {missing} missing/non-numeric values."
            )

        if not df[column].apply(
            lambda x: pd.notna(x) and pd.api.types.is_number(x)
        ).all():
            raise ValueError(
                f"{column} contains invalid numeric values."
            )

    # Import product concentration should normally lie between 0 and 1.
    concentration = df["import_product_concentration"]

    if ((concentration < 0) | (concentration > 1)).any():
        raise ValueError(
            "Import product concentration contains values outside [0, 1]."
        )

    print()
    print("Country coverage:")
    print(df["country"].value_counts().sort_index())

    print()
    print("Year coverage:")
    print(df["year"].value_counts().sort_index())

    print()
    print("Missing values:")
    print(df[numeric_columns].isna().sum())

    print()
    print("Descriptive statistics:")
    print(df[numeric_columns].describe())

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print("Strategic Autonomy dataset validation passed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
