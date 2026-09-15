"""
JESI Strategic Autonomy
Import Product Concentration Download

Script 31:
Download UNCTAD import product concentration data.

Period:
    2015-2024

Countries:
    Bangladesh, India, Viet Nam, Indonesia, Malaysia
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024.csv"
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


def main():
    """
    Prepare the Strategic Autonomy dataset for
    official UNCTAD import-concentration integration.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    data = pd.read_csv(INPUT_FILE)

    required_columns = [
        "country_code",
        "country",
        "year",
        "eci",
        "high_tech_exports",
        "import_product_concentration",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    data = data[
        data["country_code"].isin(COUNTRIES)
        & data["year"].between(2015, 2024)
    ].copy()

    if len(data) != 50:
        raise ValueError(
            f"Expected 50 country-year rows, "
            f"found {len(data)}."
        )

    # Do not fabricate concentration values.
    # UNCTAD official values must be supplied here.
    if data[
        "import_product_concentration"
    ].isna().any():
        missing = data[
            "import_product_concentration"
        ].isna().sum()

        raise ValueError(
            "UNCTAD import product concentration "
            f"data are still missing: {missing} observations. "
            "Import the official UNCTAD series before continuing."
        )

    data.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "Strategic Autonomy dataset completed."
    )
    print(f"Rows: {len(data)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
