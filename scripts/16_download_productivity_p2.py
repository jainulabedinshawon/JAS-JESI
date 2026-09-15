"""
Download JESI Productivity P2 data from the
Asian Productivity Organization (APO) Productivity Database 2025.

P2:
    Total Factor Productivity Growth (TFPG)

Source:
    APO Productivity Database 2025 Version 1

Official source:
    https://www.apo-tokyo.org/productivitydatabook/

Coverage:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia

Level period:
    2015-2023

Growth period:
    2016-2023

Output:
    data/raw/productivity_p2_tfp_growth_2015_2023.csv
"""

from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests


SOURCE_URL = (
    "https://www.apo-tokyo.org/wp-content/uploads/2025/10/"
    "APO-Productivity-Database-2025v1-1.xlsx"
)

OUTPUT_FILE = Path(
    "data/raw/productivity_p2_tfp_growth_2015_2023.csv"
)

START_YEAR = 2015
END_YEAR = 2023

COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}


def download_apo_excel():
    """Download the official APO Productivity Database workbook."""

    print("Downloading APO Productivity Database 2025...")

    response = requests.get(
        SOURCE_URL,
        timeout=120,
    )

    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")

    print(f"HTTP status: {response.status_code}")
    print(f"Content-Type: {content_type}")
    print(f"Downloaded bytes: {len(response.content):,}")

    if len(response.content) < 100_000:
        raise ValueError(
            "Downloaded APO file is unexpectedly small. "
            "The official XLSX file may not have been retrieved."
        )

    if not response.content[:2] == b"PK":
        raise ValueError(
            "Downloaded file does not appear to be a valid XLSX workbook."
        )

    return response.content


def normalize_column_name(value):
    """Normalize column names for matching."""

    return (
        str(value)
        .strip()
        .lower()
        .replace("\n", " ")
        .replace("_", " ")
        .replace("-", " ")
    )


def find_header_row(raw_df):
    """
    Find a header row containing country/year information.
    """

    for row_number in range(min(30, len(raw_df))):
        values = [
            normalize_column_name(value)
            for value in raw_df.iloc[row_number].tolist()
        ]

        has_country = any(
            "country" in value or "economy" in value
            for value in values
        )

        has_year = any(
            value == "year" or "year" in value
            for value in values
        )

        if has_country and has_year:
            return row_number

    return None


def load_apo_data(content):
    """
    Load the APO workbook.

    The APO workbook may contain multiple sheets or metadata rows,
    so the script searches the workbook rather than assuming a
    fixed sheet/header location.
    """

    workbook = pd.ExcelFile(BytesIO(content), engine="openpyxl")

    print("Workbook sheets:")
    print(workbook.sheet_names)

    candidates = []

    for sheet_name in workbook.sheet_names:
        raw = pd.read_excel(
            BytesIO(content),
            sheet_name=sheet_name,
            header=None,
            engine="openpyxl",
        )

        header_row = find_header_row(raw)

        if header_row is None:
            continue

        candidate = raw.iloc[header_row + 1:].copy()
        candidate.columns = raw.iloc[header_row].tolist()

        candidate = candidate.dropna(
            axis=1,
            how="all",
        )

        normalized = {
            normalize_column_name(column): column
            for column in candidate.columns
        }

        tfp_columns = [
            original
            for normalized_name, original in normalized.items()
            if "tfp" in normalized_name
        ]

        if tfp_columns:
            candidates.append(
                (
                    sheet_name,
                    header_row,
                    candidate,
                    tfp_columns,
                )
            )

    if not candidates:
        raise ValueError(
            "Could not find an APO worksheet containing a TFP column."
        )

    print("TFP worksheet candidates:")

    for sheet_name, header_row, _, tfp_columns in candidates:
        print(
            f"  Sheet={sheet_name}, "
            f"header_row={header_row}, "
            f"TFP columns={tfp_columns}"
        )

    # Prefer a candidate with an explicit economy-wide TFP field.
    selected = None

    for candidate in candidates:
        sheet_name, header_row, dataframe, tfp_columns = candidate

        preferred_columns = []

        for column in tfp_columns:
            name = normalize_column_name(column)

            if (
                "total factor productivity" in name
                or name.strip() == "tfp"
                or "tfp index" in name
            ):
                preferred_columns.append(column)

        if preferred_columns:
            selected = (
                sheet_name,
                header_row,
                dataframe,
                preferred_columns,
            )
            break

    if selected is None:
        selected = candidates[0]

    sheet_name, header_row, dataframe, tfp_columns = selected

    print(f"Selected sheet: {sheet_name}")
    print(f"Selected header row: {header_row}")
    print(f"Candidate TFP columns: {tfp_columns}")

    return dataframe


def identify_columns(dataframe):
    """Identify country, country code, year and TFP columns."""

    column_map = {
        normalize_column_name(column): column
        for column in dataframe.columns
    }

    country_code_column = None
    country_column = None
    year_column = None

    for normalized, original in column_map.items():

        if country_code_column is None and (
            "country code" in normalized
            or normalized in {"code", "iso3", "iso3 code"}
        ):
            country_code_column = original

        if country_column is None and (
            normalized == "country"
            or "country name" in normalized
            or normalized == "economy"
            or "economy name" in normalized
        ):
            country_column = original

        if year_column is None and normalized == "year":
            year_column = original

    if year_column is None:
        for normalized, original in column_map.items():
            if "year" == normalized.strip():
                year_column = original
                break

    if country_code_column is None:
        # Some APO files may provide country names but not ISO3 codes.
        # Country names are handled below.
        print(
            "No explicit country-code column found; "
            "country names will be used."
        )

    if country_column is None:
        raise ValueError(
            "Could not identify the APO country/economy column."
        )

    if year_column is None:
        raise ValueError(
            "Could not identify the APO year column."
        )

    # Identify economy-wide TFP.
    tfp_candidates = []

    for normalized, original in column_map.items():

        if "tfp" not in normalized:
            continue

        # Avoid selecting contribution/decomposition columns.
        excluded_terms = [
            "contribution",
            "share",
            "growth contribution",
            "capital contribution",
            "labor contribution",
            "labour contribution",
        ]

        if any(term in normalized for term in excluded_terms):
            continue

        tfp_candidates.append(original)

    if not tfp_candidates:
        raise ValueError(
            "Could not identify an economy-wide TFP column."
        )

    print(f"Country code column: {country_code_column}")
    print(f"Country column: {country_column}")
    print(f"Year column: {year_column}")
    print(f"TFP candidates: {tfp_candidates}")

    # Prefer an explicit TFP index/level column.
    preferred_tfp = None

    for column in tfp_candidates:
        name = normalize_column_name(column)

        if (
            "total factor productivity" in name
            or "tfp index" in name
            or name.strip() == "tfp"
        ):
            preferred_tfp = column
            break

    if preferred_tfp is None:
        if len(tfp_candidates) > 1:
            raise ValueError(
                "Multiple TFP columns were found and none could be "
                "identified unambiguously as the economy-wide TFP level. "
                f"Candidates: {tfp_candidates}"
            )

        preferred_tfp = tfp_candidates[0]

    print(f"Selected TFP column: {preferred_tfp}")

    return (
        country_code_column,
        country_column,
        year_column,
        preferred_tfp,
    )


def standardize_country_codes(
    dataframe,
    country_code_column,
    country_column,
):
    """Create a standardized ISO3 country code."""

    dataframe = dataframe.copy()

    if country_code_column is not None:

        dataframe["country_code"] = (
            dataframe[country_code_column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    else:

        country_name_to_code = {
            "BANGLADESH": "BGD",
            "INDIA": "IND",
            "VIETNAM": "VNM",
            "VIET NAM": "VNM",
            "INDONESIA": "IDN",
            "MALAYSIA": "MYS",
        }

        dataframe["country_code"] = (
            dataframe[country_column]
            .astype(str)
            .str.strip()
            .str.upper()
            .map(country_name_to_code)
        )

    dataframe = dataframe[
        dataframe["country_code"].isin(COUNTRIES)
    ].copy()

    dataframe["country"] = dataframe["country_code"].map(COUNTRIES)

    return dataframe


def calculate_tfp_growth(dataframe, year_column, tfp_column):
    """Calculate annual TFP growth from APO TFP levels."""

    dataframe = dataframe.copy()

    dataframe["year"] = pd.to_numeric(
        dataframe[year_column],
        errors="coerce",
    )

    dataframe["tfp"] = pd.to_numeric(
        dataframe[tfp_column],
        errors="coerce",
    )

    dataframe = dataframe[
        dataframe["year"].between(
            START_YEAR,
            END_YEAR,
        )
    ].copy()

    dataframe = dataframe.sort_values(
        ["country_code", "year"]
    )

    dataframe["tfp_growth"] = (
        dataframe.groupby("country_code")["tfp"]
        .pct_change()
        * 100
    )

    return dataframe


def validate_output(dataframe):
    """Validate the expected JESI P2 panel."""

    expected_rows = len(COUNTRIES) * (
        END_YEAR - START_YEAR + 1
    )

    if len(dataframe) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, "
            f"found {len(dataframe)}."
        )

    expected_country_codes = set(COUNTRIES)

    actual_country_codes = set(
        dataframe["country_code"].unique()
    )

    if actual_country_codes != expected_country_codes:
        raise ValueError(
            "Country coverage mismatch. "
            f"Expected={expected_country_codes}, "
            f"Found={actual_country_codes}"
        )

    expected_years = set(
        range(START_YEAR, END_YEAR + 1)
    )

    actual_years = set(
        dataframe["year"].astype(int).unique()
    )

    if actual_years != expected_years:
        raise ValueError(
            "Year coverage mismatch. "
            f"Expected={expected_years}, "
            f"Found={actual_years}"
        )

    if dataframe.duplicated(
        subset=["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations found."
        )

    level_missing = dataframe["tfp"].isna()

    if level_missing.any():
        print(
            "Missing TFP levels detected:"
        )
        print(
            dataframe.loc[
                level_missing,
                [
                    "country_code",
                    "country",
                    "year",
                    "tfp",
                ],
            ].to_string(index=False)
        )

        raise ValueError(
            "APO TFP levels contain missing observations."
        )

    growth_panel = dataframe[
        dataframe["year"] >= START_YEAR + 1
    ]

    if growth_panel["tfp_growth"].isna().any():
        raise ValueError(
            "Missing TFP growth observations for "
            "2016-2023."
        )

    if not np.isfinite(
        growth_panel["tfp_growth"]
    ).all():
        raise ValueError(
            "Non-finite TFP growth values found."
        )

    print(
        f"Validated {len(dataframe)} TFP level observations."
    )

    print(
        f"Validated {len(growth_panel)} TFP growth observations."
    )


def main():
    content = download_apo_excel()

    dataframe = load_apo_data(content)

    (
        country_code_column,
        country_column,
        year_column,
        tfp_column,
    ) = identify_columns(dataframe)

    dataframe = standardize_country_codes(
        dataframe,
        country_code_column,
        country_column,
    )

    dataframe = calculate_tfp_growth(
        dataframe,
        year_column,
        tfp_column,
    )

    output_columns = [
        "country_code",
        "country",
        "year",
        "tfp",
        "tfp_growth",
    ]

    dataframe = dataframe[
        output_columns
    ].copy()

    dataframe["year"] = dataframe["year"].astype(int)

    dataframe = dataframe.sort_values(
        ["country_code", "year"]
    ).reset_index(drop=True)

    print("\nAPO TFP coverage:")
    print(
        dataframe.groupby(
            "country_code"
        )["year"]
        .agg(["min", "max", "count"])
        .to_string()
    )

    print("\nMissing observations:")
    missing = dataframe[
        dataframe["tfp"].isna()
    ]

    if missing.empty:
        print("None")
    else:
        print(
            missing.to_string(index=False)
        )

    validate_output(dataframe)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nSaved: {OUTPUT_FILE}"
    )

    print(
        "\nJESI Productivity P2 APO download "
        "completed successfully."
    )


if __name__ == "__main__":
    main()
