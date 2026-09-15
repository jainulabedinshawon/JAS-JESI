"""
JESI Productivity Data Download

Purpose:
    Download GDP per Person Employed data
    for the JESI five-country sample.

Indicator:
    SL.GDP.PCAP.EM.KD

Unit:
    Constant 2021 PPP dollars

Period:
    2015-2024

Countries:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia
"""

from pathlib import Path

import pandas as pd

from src.data_download import download_productivity_data


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = BASE_DIR / "data" / "raw"

OUTPUT_FILE = OUTPUT_DIR / (
    "productivity_p1_gdp_per_person_employed_2015_2024.csv"
)

COUNTRIES = [
    "BGD",
    "IND",
    "VNM",
    "IDN",
    "MYS",
]

START_YEAR = 2015
END_YEAR = 2024

EXPECTED_COUNTRIES = {
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
}

EXPECTED_INDICATOR = "SL.GDP.PCAP.EM.KD"


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def validate_productivity_data(df):
    """Validate downloaded P1 productivity data."""

    required_columns = {
        "country",
        "year",
        "value",
        "indicator",
    }

    missing_columns = (
        required_columns - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    df = df.copy()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce",
    )

    if df["year"].isna().any():
        raise ValueError(
            "Found invalid year values."
        )

    if df["value"].isna().any():
        raise ValueError(
            "Found missing or non-numeric "
            "productivity values."
        )

    df["year"] = df["year"].astype(int)

    countries = set(df["country"].unique())
    years = set(df["year"].unique())
    indicators = set(df["indicator"].unique())

    if countries != EXPECTED_COUNTRIES:
        raise ValueError(
            "Country coverage does not match "
            "the expected five-country sample."
        )

    expected_years = set(
        range(
            START_YEAR,
            END_YEAR + 1,
        )
    )

    if years != expected_years:
        raise ValueError(
            "Year coverage does not match "
            "2015-2024."
        )

    if indicators != {EXPECTED_INDICATOR}:
        raise ValueError(
            "Indicator coverage does not match "
            "SL.GDP.PCAP.EM.KD."
        )

    expected_rows = (
        len(EXPECTED_COUNTRIES)
        * len(expected_years)
    )

    if len(df) != expected_rows:
        raise ValueError(
            f"Unexpected row count: {len(df)}. "
            f"Expected {expected_rows}."
        )

    duplicates = df.duplicated(
        subset=[
            "country",
            "year",
            "indicator",
        ]
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate country-year-indicator "
            "records found."
        )

    return df


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    print("=" * 72)
    print("JESI PRODUCTIVITY — P1 DATA DOWNLOAD")
    print("=" * 72)
    print()

    print("Indicator:")
    print("SL.GDP.PCAP.EM.KD")
    print()

    print("Period:")
    print(f"{START_YEAR}-{END_YEAR}")
    print()

    print("Countries:")
    print(", ".join(COUNTRIES))
    print()

    try:
        df = download_productivity_data(
            countries=COUNTRIES,
            start_year=START_YEAR,
            end_year=END_YEAR,
        )
    except Exception as exc:
        print(
            "ERROR: Productivity data download failed."
        )
        print(exc)
        return 1

    print(
        f"Downloaded rows: {len(df)}"
    )
    print()

    try:
        df = validate_productivity_data(df)
    except ValueError as exc:
        print(
            f"ERROR: {exc}"
        )
        return 1

    df = df.sort_values(
        [
            "country",
            "year",
        ]
    ).reset_index(drop=True)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("=" * 72)
    print("VALIDATION")
    print("=" * 72)
    print("Status: PASSED")
    print()

    print(
        f"Countries: {len(EXPECTED_COUNTRIES)}"
    )
    print(
        f"Years: {START_YEAR}-{END_YEAR}"
    )
    print(
        f"Observations: {len(df)}"
    )
    print()

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)

    print(
        df[
            [
                "country",
                "year",
                "value",
            ]
        ].to_string(index=False)
    )

    print()

    print("=" * 72)
    print("OUTPUT")
    print("=" * 72)

    print(
        f"Saved: {OUTPUT_FILE}"
    )
    print()

    print(
        "JESI Productivity P1 data download "
        "completed successfully."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
