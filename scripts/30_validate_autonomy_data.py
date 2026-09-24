"""
JESI Strategic Autonomy Data Validation
JAS Unified Economic Strength Index (JESI)

Script 30:
Integrate official UNCTAD import product concentration
data into the Strategic Autonomy dataset and validate
the completed 2015-2024 benchmark dataset.

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
    """Validate the ECI and high-tech base dataset."""

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

    if set(data["year"]) != YEARS:
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
        values = pd.to_numeric(
            data[column],
            errors="coerce",
        )

        finite_values = values.dropna()

        if not np.isfinite(
            finite_values.to_numpy()
        ).all():
            raise ValueError(
                f"Non-finite values found in {column}."
            )

        data[column] = values

    return data


def load_import_concentration():
    """Load and validate official UNCTAD concentration data."""

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
        missing = int(
            concentration[
                "import_product_concentration"
            ].isna().sum()
        )

        raise ValueError(
            "UNCTAD concentration data contains "
            f"{missing} missing observations."
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
    """Merge official UNCTAD data into autonomy data."""

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
            "Country-year integration changed the "
            "expected number of autonomy observations."
        )

    missing = int(
        merged[
            "import_product_concentration"
        ].isna().sum()
    )

    if missing:
        raise ValueError(
            "UNCTAD import concentration integration "
            f"left {missing} missing observations."
        )

    return merged


def validate_completed_data(data):
    """Validate the completed Strategic Autonomy dataset."""

    expected_rows = len(COUNTRIES) * len(YEARS)

    if len(data) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} completed rows, "
            f"found {len(data)}."
        )

    if set(data["country_code"]) != set(COUNTRIES):
        raise ValueError(
            "Completed dataset country set does not "
            "match JESI sample."
        )

    if set(data["year"]) != YEARS:
        raise ValueError(
            "Completed dataset year coverage must be "
            "exactly 2015-2024."
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

        values = data[column]

        if values.isna().any():
            missing = int(
                values.isna().sum()
            )

            raise ValueError(
                f"{column} contains "
                f"{missing} missing/non-numeric values."
            )

        if not np.isfinite(
            values.to_numpy()
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
    print(
        "JESI STRATEGIC AUTONOMY DATA VALIDATION"
    )
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

    print()
    print(
        "Base Strategic Autonomy rows:",
        len(data),
    )

    data = validate_base_data(
        data
    )

    print(
        "Base country-year validation: GREEN"
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
        "UNCTAD concentration observations:",
        len(concentration),
    )

    print(
        "UNCTAD country-year validation: GREEN"
    )

    print()
    print(
        "Integrating UNCTAD concentration "
        "into Strategic Autonomy dataset..."
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
        "Integrated Strategic Autonomy dataset: GREEN"
    )

    print(
        "Rows:",
        len(completed),
    )

    print(
        "Countries:",
        completed[
            "country_code"
        ].nunique(),
    )

    print(
        "Years:",
        completed[
            "year"
        ].nunique(),
    )

    print(
        "Period: 2015-2024"
    )

    print()
    print(
        "Missing observations:"
    )

    print(
        completed[
            [
                "eci",
                "high_tech_exports",
                "import_product_concentration",
            ]
        ].isna().sum()
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
        "Saved completed dataset:",
        OUTPUT_FILE,
    )

    print()
    print("=" * 72)
    print(
        "STATUS: GREEN"
    )
    print(
        "Strategic Autonomy data integration "
        "and validation completed successfully."
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
