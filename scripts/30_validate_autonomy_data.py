"""
JESI Strategic Autonomy Data Validation
Master Version 1.0

Script 30:
Integrate official UNCTAD import product concentration
data into the Strategic Autonomy dataset.

Important methodological rule:
Missing official high-tech export observations are NOT
imputed, interpolated, replaced, or converted to zero.

They remain explicit missing observations for subsequent
coverage and methodological diagnosis.
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024.csv"
)

IMPORT_CONCENTRATION_FILE = Path(
    "data/raw/import_product_concentration_2015_2024.csv"
)

OUTPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024_complete.csv"
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
]


def validate_base_data(data):
    """Validate the base Strategic Autonomy dataset."""

    expected_rows = len(COUNTRIES) * len(YEARS)

    if len(data) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} base rows, "
            f"found {len(data)}."
        )

    if set(data["country_code"]) != set(COUNTRIES):
        raise ValueError(
            "Country set does not match JESI sample."
        )

    if set(data["year"].astype(int)) != YEARS:
        raise ValueError(
            "Year coverage must be 2015-2024."
        )

    if data.duplicated(
        ["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations "
            "found in base autonomy data."
        )

    for column in [
        "eci",
        "high_tech_exports",
    ]:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

        finite = data[column].dropna()

        if not np.isfinite(
            finite.to_numpy()
        ).all():
            raise ValueError(
                f"Non-finite values found in {column}."
            )

    return data


def load_import_concentration():
    """Load official UNCTAD import concentration data."""

    if not IMPORT_CONCENTRATION_FILE.exists():
        raise FileNotFoundError(
            "Official UNCTAD import concentration file "
            f"not found: {IMPORT_CONCENTRATION_FILE}"
        )

    concentration = pd.read_csv(
        IMPORT_CONCENTRATION_FILE
    )

    required_columns = {
        "country",
        "country_code",
        "year",
        "import_product_concentration",
    }

    missing_columns = (
        required_columns
        - set(concentration.columns)
    )

    if missing_columns:
        raise ValueError(
            "UNCTAD concentration file is missing "
            f"required columns: {sorted(missing_columns)}"
        )

    concentration["year"] = pd.to_numeric(
        concentration["year"],
        errors="coerce",
    )

    concentration[
        "import_product_concentration"
    ] = pd.to_numeric(
        concentration[
            "import_product_concentration"
        ],
        errors="coerce",
    )

    if concentration[
        "import_product_concentration"
    ].isna().any():
        raise ValueError(
            "UNCTAD concentration data contains "
            "missing observations."
        )

    if concentration.duplicated(
        ["country_code", "year"]
    ).any():
        raise ValueError(
            "UNCTAD concentration data contains "
            "duplicate country-year observations."
        )

    expected_rows = len(COUNTRIES) * len(YEARS)

    if len(concentration) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} UNCTAD "
            f"country-year observations, "
            f"found {len(concentration)}."
        )

    if set(
        concentration["country_code"]
    ) != set(COUNTRIES):
        raise ValueError(
            "UNCTAD concentration country set "
            "does not match JESI sample."
        )

    if set(
        concentration["year"].astype(int)
    ) != YEARS:
        raise ValueError(
            "UNCTAD concentration year coverage "
            "must be exactly 2015-2024."
        )

    values = concentration[
        "import_product_concentration"
    ]

    if (
        (values < 0)
        | (values > 1)
    ).any():
        raise ValueError(
            "UNCTAD import product concentration "
            "contains values outside [0, 1]."
        )

    return concentration[
        [
            "country_code",
            "year",
            "import_product_concentration",
        ]
    ].copy()


def integrate_concentration(
    data,
    concentration,
):
    """Merge official UNCTAD data."""

    merged = data.drop(
        columns=[
            "import_product_concentration"
        ],
        errors="ignore",
    ).merge(
        concentration,
        on=[
            "country_code",
            "year",
        ],
        how="left",
        validate="one_to_one",
    )

    if len(merged) != len(data):
        raise ValueError(
            "Country-year integration changed "
            "the expected number of observations."
        )

    missing = int(
        merged[
            "import_product_concentration"
        ].isna().sum()
    )

    if missing:
        raise ValueError(
            "UNCTAD integration left "
            f"{missing} missing observations."
        )

    return merged


def report_high_tech_coverage(data):
    """Report high-tech coverage without modifying values."""

    data = data.copy()

    data["high_tech_exports"] = pd.to_numeric(
        data["high_tech_exports"],
        errors="coerce",
    )

    missing = data[
        data["high_tech_exports"].isna()
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

    print()
    print("=" * 72)
    print("HIGH-TECH EXPORTS COVERAGE DIAGNOSTIC")
    print("=" * 72)

    print(
        f"Total observations: {len(data)}"
    )

    print(
        "Available high-tech observations:",
        int(data["high_tech_exports"].notna().sum()),
    )

    print(
        "Missing high-tech observations:",
        len(missing),
    )

    if missing.empty:
        print(
            "High-tech coverage: COMPLETE"
        )
    else:
        print()
        print(
            "Missing official observations:"
        )

        for _, row in missing.iterrows():
            print(
                f"{row['country_code']} | "
                f"{row['country']} | "
                f"{int(row['year'])}"
            )

        print()
        print(
            "IMPORTANT:"
        )
        print(
            "These values remain missing."
        )
        print(
            "No zero, interpolation, mean, or proxy "
            "has been inserted."
        )

    print("=" * 72)

    return missing


def validate_completed_data(data):
    """
    Validate the integrated dataset.

    High-tech missing values are allowed at this stage
    because they are an explicit source-coverage issue.
    """

    expected_rows = len(COUNTRIES) * len(YEARS)

    if len(data) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} completed rows, "
            f"found {len(data)}."
        )

    if data.duplicated(
        ["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations "
            "found after integration."
        )

    numeric_columns = [
        "eci",
        "high_tech_exports",
        "import_product_concentration",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

        finite = data[column].dropna()

        if not np.isfinite(
            finite.to_numpy()
        ).all():
            raise ValueError(
                f"{column} contains non-finite values."
            )

    concentration = data[
        "import_product_concentration"
    ]

    if (
        (concentration < 0)
        | (concentration > 1)
    ).any():
        raise ValueError(
            "Import product concentration contains "
            "values outside [0, 1]."
        )

    return data.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(
        drop=True
    )


def main():
    """Integrate and validate Strategic Autonomy data."""

    print("=" * 72)
    print("JESI STRATEGIC AUTONOMY DATA VALIDATION")
    print("=" * 72)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    data = pd.read_csv(
        INPUT_FILE
    )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Base autonomy data is missing "
            f"required columns: {missing_columns}"
        )

    data = validate_base_data(
        data
    )

    print()
    print(
        "Base country-year validation: GREEN"
    )

    missing_high_tech = (
        report_high_tech_coverage(data)
    )

    print()
    print(
        "Loading official UNCTAD import "
        "concentration data..."
    )

    concentration = (
        load_import_concentration()
    )

    print(
        "UNCTAD validation: GREEN"
    )

    completed = integrate_concentration(
        data,
        concentration,
    )

    completed = validate_completed_data(
        completed
    )

    print()
    print(
        "Strategic Autonomy integration: GREEN"
    )

    print(
        f"Rows: {len(completed)}"
    )

    print(
        "High-tech missing:",
        len(missing_high_tech),
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    completed.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        "Saved:",
        OUTPUT_FILE,
    )

    print()
    print("=" * 72)
    print(
        "STATUS: GREEN"
    )
    print(
        "Integration completed without "
        "fabricating missing observations."
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
