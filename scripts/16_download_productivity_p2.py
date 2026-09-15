"""
Download JESI Productivity P2 data from the
Asian Productivity Organization (APO) Productivity Database 2025.

P2:
    Total Factor Productivity Growth (TFPG)

Primary source:
    APO Productivity Database 2025 Version 1

Official source:
    https://www.apo-tokyo.org/productivitydatabook/

Countries:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia

APO workbook structure:
    Country-specific worksheets such as:
        BAN = Bangladesh
        IND = India
        VIE = Viet Nam
        IDN = Indonesia
        MAL = Malaysia

Analysis period:
    2015-2023

TFP growth period:
    2016-2023

Output:
    data/raw/productivity_p2_tfp_growth_2015_2023.csv

Notes:
    The APO workbook provides country-sheet based productivity data.
    This script searches the relevant country sheet for the annual
    TFP growth series instead of assuming a flat TFP column.
"""

from io import BytesIO
from pathlib import Path
import re

import numpy as np
import pandas as pd
import requests


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

APO_URL = (
    "https://www.apo-tokyo.org/wp-content/uploads/2025/10/"
    "APO-Productivity-Database-2025v1-1.xlsx"
)

OUTPUT_FILE = Path(
    "data/raw/productivity_p2_tfp_growth_2015_2023.csv"
)

START_YEAR = 2015
END_YEAR = 2023

COUNTRIES = {
    "BAN": {
        "code": "BGD",
        "name": "Bangladesh",
    },
    "IND": {
        "code": "IND",
        "name": "India",
    },
    "VIE": {
        "code": "VNM",
        "name": "Viet Nam",
    },
    "IDN": {
        "code": "IDN",
        "name": "Indonesia",
    },
    "MAL": {
        "code": "MYS",
        "name": "Malaysia",
    },
}


# ---------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------

def download_apo_workbook():
    """Download the official APO Productivity Database workbook."""

    print("Downloading APO Productivity Database 2025...")

    response = requests.get(
        APO_URL,
        timeout=120,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        "",
    )

    print(f"HTTP status: {response.status_code}")
    print(f"Content-Type: {content_type}")
    print(
        f"Downloaded bytes: {len(response.content):,}"
    )

    if len(response.content) < 100_000:
        raise ValueError(
            "Downloaded APO workbook is unexpectedly small."
        )

    # XLSX files are ZIP containers and normally begin with PK.
    if response.content[:2] != b"PK":
        raise ValueError(
            "Downloaded content is not a valid XLSX workbook."
        )

    return response.content


# ---------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------

def normalize_text(value):
    """Normalize spreadsheet text for robust matching."""

    if pd.isna(value):
        return ""

    text = str(value)

    text = (
        text.replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip().lower()


def is_year(value):
    """Return True when value represents a year in the APO range."""

    if pd.isna(value):
        return False

    try:
        year = int(float(value))
    except (TypeError, ValueError):
        return False

    return 1970 <= year <= 2035


# ---------------------------------------------------------------------
# Workbook inspection
# ---------------------------------------------------------------------

def load_country_sheet(content, sheet_name):
    """Load an APO country worksheet without assuming headers."""

    dataframe = pd.read_excel(
        BytesIO(content),
        sheet_name=sheet_name,
        header=None,
        engine="openpyxl",
    )

    print(
        f"Loaded sheet {sheet_name}: "
        f"{dataframe.shape[0]} rows x "
        f"{dataframe.shape[1]} columns"
    )

    return dataframe


def find_year_columns(dataframe):
    """
    Search the worksheet for year labels.

    APO country sheets are not assumed to have a fixed header row.
    The function scans all cells and identifies columns containing
    annual year labels.
    """

    year_columns = {}

    for row_index in range(
        min(dataframe.shape[0], 30)
    ):
        for column_index in range(
            dataframe.shape[1]
        ):
            value = dataframe.iat[
                row_index,
                column_index,
            ]

            if not is_year(value):
                continue

            year = int(float(value))

            # Prefer the first consistent year header.
            if year not in year_columns:
                year_columns[year] = column_index

    required_years = set(
        range(
            START_YEAR,
            END_YEAR + 1,
        )
    )

    missing_years = sorted(
        required_years - set(year_columns)
    )

    if missing_years:
        raise ValueError(
            f"Could not identify all required years "
            f"in APO sheet. Missing: {missing_years}"
        )

    return year_columns


# ---------------------------------------------------------------------
# TFP row detection
# ---------------------------------------------------------------------

def row_text(dataframe, row_index):
    """Return normalized text from a worksheet row."""

    values = []

    for value in dataframe.iloc[row_index].tolist():
        text = normalize_text(value)

        if text:
            values.append(text)

    return " ".join(values)


def find_tfp_growth_row(dataframe):
    """
    Locate the annual Total Factor Productivity Growth row.

    The APO workbook can contain several productivity measures.
    We specifically search for a row whose label refers to
    TFP / total factor productivity and growth.
    """

    candidates = []

    for row_index in range(dataframe.shape[0]):

        text = row_text(
            dataframe,
            row_index,
        )

        if not text:
            continue

        has_tfp = (
            "total factor productivity" in text
            or re.search(
                r"\btfp\b",
                text,
            ) is not None
        )

        has_growth = (
            "growth" in text
            or "growth rate" in text
            or "annual growth" in text
        )

        if has_tfp and has_growth:
            candidates.append(
                (
                    row_index,
                    text,
                )
            )

    if not candidates:
        return None

    print("TFP growth row candidates:")

    for row_index, text in candidates:
        print(
            f"  row {row_index}: {text[:250]}"
        )

    # Prefer the most explicit wording.
    preferred = []

    for row_index, text in candidates:

        score = 0

        if "total factor productivity growth" in text:
            score += 10

        if "tfp growth" in text:
            score += 8

        if "annual growth" in text:
            score += 3

        preferred.append(
            (
                score,
                row_index,
                text,
            )
        )

    preferred.sort(
        reverse=True
    )

    selected = preferred[0]

    print(
        "Selected TFP growth row: "
        f"{selected[1]}"
    )

    print(
        f"Label: {selected[2][:250]}"
    )

    return selected[1]


# ---------------------------------------------------------------------
# Numeric extraction
# ---------------------------------------------------------------------

def extract_tfp_growth(
    dataframe,
    year_columns,
    tfp_growth_row,
):
    """Extract annual TFP growth values from the selected row."""

    records = []

    for year in range(
        START_YEAR,
        END_YEAR + 1,
    ):

        column_index = year_columns.get(year)

        if column_index is None:
            raise ValueError(
                f"Year column not found: {year}"
            )

        value = dataframe.iat[
            tfp_growth_row,
            column_index,
        ]

        numeric = pd.to_numeric(
            pd.Series([value]),
            errors="coerce",
        ).iloc[0]

        records.append(
            {
                "year": year,
                "tfp_growth": numeric,
            }
        )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------
# TFP index reconstruction
# ---------------------------------------------------------------------

def construct_tfp_index(growth_dataframe):
    """
    Construct a technical TFP index from APO annual TFP growth.

    The JESI pipeline historically expects a 'tfp' column and uses
    'tfp_growth' as the analytical P2 variable.

    Because the APO country workbook provides the growth series in
    country-sheet form, this creates a normalized index with:

        TFP_2015 = 100

    and compounds the APO annual growth rates forward.

    This does NOT alter the APO growth observations.
    """

    dataframe = growth_dataframe.copy()

    dataframe = dataframe.sort_values(
        "year"
    ).reset_index(drop=True)

    dataframe["tfp"] = np.nan

    dataframe.loc[
        dataframe["year"] == START_YEAR,
        "tfp",
    ] = 100.0

    for index in range(
        1,
        len(dataframe),
    ):

        previous_tfp = dataframe.loc[
            index - 1,
            "tfp",
        ]

        growth = dataframe.loc[
            index,
            "tfp_growth",
        ]

        if pd.isna(previous_tfp):
            raise ValueError(
                "Cannot construct TFP index because "
                "the previous TFP index is missing."
            )

        if pd.isna(growth):
            dataframe.loc[
                index,
                "tfp",
            ] = np.nan
        else:
            dataframe.loc[
                index,
                "tfp",
            ] = previous_tfp * (
                1.0 + growth / 100.0
            )

    return dataframe


# ---------------------------------------------------------------------
# Country extraction
# ---------------------------------------------------------------------

def extract_country(
    content,
    sheet_name,
    country_code,
    country_name,
):
    """Extract one country's APO TFP growth series."""

    print(
        f"\nProcessing {country_name} "
        f"({sheet_name} -> {country_code})"
    )

    dataframe = load_country_sheet(
        content,
        sheet_name,
    )

    year_columns = find_year_columns(
        dataframe
    )

    print(
        "Detected required year columns:"
    )

    print(
        {
            year: year_columns[year]
            for year in range(
                START_YEAR,
                END_YEAR + 1,
            )
        }
    )

    tfp_growth_row = find_tfp_growth_row(
        dataframe
    )

    if tfp_growth_row is None:
        raise ValueError(
            f"Could not locate TFP growth row "
            f"in APO sheet {sheet_name}."
        )

    result = extract_tfp_growth(
        dataframe,
        year_columns,
        tfp_growth_row,
    )

    result = construct_tfp_index(
        result
    )

    result.insert(
        0,
        "country_code",
        country_code,
    )

    result.insert(
        1,
        "country",
        country_name,
    )

    return result


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def validate_panel(dataframe):
    """Validate the complete five-country P2 panel."""

    expected_rows = (
        len(COUNTRIES)
        * (
            END_YEAR
            - START_YEAR
            + 1
        )
    )

    if len(dataframe) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, "
            f"found {len(dataframe)}."
        )

    expected_codes = {
        information["code"]
        for information in COUNTRIES.values()
    }

    actual_codes = set(
        dataframe["country_code"].unique()
    )

    if actual_codes != expected_codes:
        raise ValueError(
            "Country coverage mismatch. "
            f"Expected={expected_codes}, "
            f"Found={actual_codes}"
        )

    expected_years = set(
        range(
            START_YEAR,
            END_YEAR + 1,
        )
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
        subset=[
            "country_code",
            "year",
        ]
    ).any():

        raise ValueError(
            "Duplicate country-year observations found."
        )

    # TFP level/index must exist for every year.
    if dataframe["tfp"].isna().any():

        print(
            "Missing TFP index observations:"
        )

        print(
            dataframe[
                dataframe["tfp"].isna()
            ].to_string(
                index=False
            )
        )

        raise ValueError(
            "Missing TFP index observations."
        )

    # Growth is expected to be missing only in 2015.
    growth_period = dataframe[
        dataframe["year"] >= START_YEAR + 1
    ]

    missing_growth = growth_period[
        growth_period["tfp_growth"].isna()
    ]

    if not missing_growth.empty:

        print(
            "Missing TFP growth observations:"
        )

        print(
            missing_growth.to_string(
                index=False
            )
        )

        raise ValueError(
            "Missing TFP growth observations "
            "for 2016-2023."
        )

    if not np.isfinite(
        growth_period["tfp_growth"]
    ).all():

        raise ValueError(
            "Non-finite TFP growth observations found."
        )

    growth_rows = len(
        growth_period
    )

    expected_growth_rows = (
        len(COUNTRIES)
        * (
            END_YEAR
            - START_YEAR
        )
    )

    if growth_rows != expected_growth_rows:
        raise ValueError(
            f"Expected {expected_growth_rows} "
            f"growth observations, "
            f"found {growth_rows}."
        )

    print(
        f"\nValidated {len(dataframe)} "
        "TFP panel observations."
    )

    print(
        f"Validated {growth_rows} "
        "TFP growth observations."
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    """Run the complete APO P2 download pipeline."""

    content = download_apo_workbook()

    workbook = pd.ExcelFile(
        BytesIO(content),
        engine="openpyxl",
    )

    print(
        "\nWorkbook sheets:"
    )

    print(
        workbook.sheet_names
    )

    required_sheets = set(
        COUNTRIES.keys()
    )

    available_sheets = set(
        workbook.sheet_names
    )

    missing_sheets = sorted(
        required_sheets
        - available_sheets
    )

    if missing_sheets:
        raise ValueError(
            "Required APO country sheets are missing: "
            f"{missing_sheets}"
        )

    country_frames = []

    for sheet_name, information in COUNTRIES.items():

        country_frame = extract_country(
            content=content,
            sheet_name=sheet_name,
            country_code=information["code"],
            country_name=information["name"],
        )

        country_frames.append(
            country_frame
        )

    dataframe = pd.concat(
        country_frames,
        ignore_index=True,
    )

    dataframe = dataframe[
        [
            "country_code",
            "country",
            "year",
            "tfp",
            "tfp_growth",
        ]
    ].copy()

    dataframe["year"] = (
        dataframe["year"]
        .astype(int)
    )

    dataframe = dataframe.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(
        drop=True
    )

    print(
        "\nCountry/year coverage:"
    )

    print(
        dataframe.groupby(
            "country_code"
        )["year"]
        .agg(
            [
                "min",
                "max",
                "count",
            ]
        )
        .to_string()
    )

    print(
        "\nTFP growth observations "
        "(2016-2023):"
    )

    print(
        dataframe[
            dataframe["year"] >= 2016
        ]
        .groupby(
            "country_code"
        )["tfp_growth"]
        .count()
        .to_string()
    )

    validate_panel(
        dataframe
    )

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
        "\nJESI Productivity P2 APO "
        "download completed successfully."
    )


if __name__ == "__main__":
    main()
