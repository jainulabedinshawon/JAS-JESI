"""
JESI Productivity P2
---------------------

Download Total Factor Productivity (TFP) data from the
Asian Productivity Organization (APO) Productivity Database 2025.

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
    BAN = Bangladesh
    IND = India
    VIE = Viet Nam
    IDN = Indonesia
    MAL = Malaysia

Period:
    TFP levels: 2015-2023
    TFP growth: 2016-2023

Output:
    data/raw/productivity_p2_tfp_growth_2015_2023.csv

Method:
    1. Download official APO workbook.
    2. Open each country sheet.
    3. Detect annual year columns.
    4. Locate the economy-wide TFP level/index row.
    5. Extract APO TFP levels for 2015-2023.
    6. Calculate annual TFP growth using:
           TFP_growth_t = (TFP_t / TFP_(t-1) - 1) * 100
    7. Preserve 2015 TFP growth as NaN.
    8. Validate the complete 5-country panel.
"""

from io import BytesIO
from pathlib import Path
import re

import numpy as np
import pandas as pd
import requests


# ============================================================
# Configuration
# ============================================================

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


# ============================================================
# Download APO workbook
# ============================================================

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

    if response.content[:2] != b"PK":
        raise ValueError(
            "Downloaded content is not a valid XLSX workbook."
        )

    return response.content


# ============================================================
# Text utilities
# ============================================================

def normalize_text(value):
    """Normalize spreadsheet text for reliable matching."""

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
    """Return True when a value looks like an annual year."""

    if pd.isna(value):
        return False

    try:
        year = int(float(value))
    except (TypeError, ValueError):
        return False

    return 1970 <= year <= 2035


# ============================================================
# Load country worksheet
# ============================================================

def load_country_sheet(
    content,
    sheet_name,
):
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


# ============================================================
# Detect year columns
# ============================================================

def find_year_columns(dataframe):
    """
    Detect the columns containing annual years.

    The APO workbook contains metadata before the actual
    data area, so the function scans the worksheet.
    """

    year_columns = {}

    # Search the first 40 rows for year headers.
    for row_index in range(
        min(40, dataframe.shape[0])
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

            # We need the first occurrence of each year.
            if year not in year_columns:
                year_columns[year] = column_index

    required_years = set(
        range(
            START_YEAR,
            END_YEAR + 1,
        )
    )

    missing_years = sorted(
        required_years
        - set(year_columns)
    )

    if missing_years:
        raise ValueError(
            "Could not identify all required years "
            f"in APO sheet. Missing: {missing_years}"
        )

    return year_columns


# ============================================================
# Row utilities
# ============================================================

def get_row_text(
    dataframe,
    row_index,
):
    """Return normalized text from an entire worksheet row."""

    values = []

    for value in dataframe.iloc[
        row_index
    ].tolist():

        text = normalize_text(value)

        if text:
            values.append(text)

    return " ".join(values)


def count_numeric_values(
    dataframe,
    row_index,
    year_columns,
):
    """Count valid numeric observations across required years."""

    count = 0

    for year in range(
        START_YEAR,
        END_YEAR + 1,
    ):

        column_index = year_columns[year]

        value = pd.to_numeric(
            dataframe.iat[
                row_index,
                column_index
            ],
            errors="coerce",
        )

        if pd.notna(value):
            count += 1

    return count


# ============================================================
# Locate TFP level/index row
# ============================================================

def find_tfp_level_row(
    dataframe,
    year_columns,
):
    """
    Locate the economy-wide TFP level/index row.

    APO country sheets may contain several productivity-related
    rows. We therefore score candidates rather than assuming a
    fixed row number.

    The selected row must:
        - mention TFP / total factor productivity
        - contain numeric observations for the requested years
        - not be a contribution/share row
        - not be a labor/capital productivity row
    """

    candidates = []

    for row_index in range(
        dataframe.shape[0]
    ):

        text = get_row_text(
            dataframe,
            row_index,
        )

        if not text:
            continue

        # ----------------------------------------------------
        # Must contain TFP terminology.
        # ----------------------------------------------------

        has_tfp = (
            "total factor productivity" in text
            or re.search(
                r"\btfp\b",
                text,
            ) is not None
        )

        if not has_tfp:
            continue

        # ----------------------------------------------------
        # Exclude rows that are not the TFP level/index.
        # ----------------------------------------------------

        excluded_terms = [
            "contribution",
            "contributions",
            "share",
            "contribution share",
            "growth contribution",
            "capital contribution",
            "labor contribution",
            "labour contribution",
            "tfp contribution",
            "tfp growth",
            "growth rate",
        ]

        if any(
            term in text
            for term in excluded_terms
        ):
            continue

        numeric_count = count_numeric_values(
            dataframe,
            row_index,
            year_columns,
        )

        if numeric_count < 7:
            continue

        # ----------------------------------------------------
        # Score the candidate.
        # ----------------------------------------------------

        score = 0

        # Strongest match: explicit total factor productivity.
        if "total factor productivity" in text:
            score += 30

        # Explicit TFP label.
        if re.search(
            r"\btfp\b",
            text,
        ):
            score += 20

        # Index wording is desirable because APO reports TFP
        # as an index series.
        if "index" in text:
            score += 10

        if "1970=1" in text:
            score += 15

        if "1970 = 1" in text:
            score += 15

        if "1970" in text and "1.0" in text:
            score += 5

        # More complete observations are preferable.
        score += numeric_count

        candidates.append(
            {
                "score": score,
                "row": row_index,
                "text": text,
                "numeric_count": numeric_count,
            }
        )

    if not candidates:
        return None

    candidates = sorted(
        candidates,
        key=lambda item: (
            item["score"],
            item["numeric_count"],
        ),
        reverse=True,
    )

    print(
        "\nTFP level/index row candidates:"
    )

    for candidate in candidates[:10]:

        print(
            f"  row={candidate['row']} "
            f"score={candidate['score']} "
            f"numeric={candidate['numeric_count']} "
            f"label={candidate['text'][:250]}"
        )

    selected = candidates[0]

    print(
        "\nSelected APO TFP level/index row:"
    )

    print(
        f"  row={selected['row']}"
    )

    print(
        f"  label={selected['text'][:300]}"
    )

    print(
        f"  numeric observations="
        f"{selected['numeric_count']}"
    )

    return selected["row"]


# ============================================================
# Extract TFP levels
# ============================================================

def extract_tfp_levels(
    dataframe,
    year_columns,
    tfp_row,
):
    """Extract APO TFP level/index observations."""

    records = []

    for year in range(
        START_YEAR,
        END_YEAR + 1,
    ):

        column_index = year_columns[
            year
        ]

        raw_value = dataframe.iat[
            tfp_row,
            column_index,
        ]

        value = pd.to_numeric(
            pd.Series([raw_value]),
            errors="coerce",
        ).iloc[0]

        records.append(
            {
                "year": year,
                "tfp": value,
            }
        )

    result = pd.DataFrame(
        records
    )

    return result


# ============================================================
# Calculate annual TFP growth
# ============================================================

def calculate_tfp_growth(
    dataframe,
):
    """
    Calculate annual TFP growth from APO TFP levels.

    Formula:

        TFPG_t =
            (TFP_t / TFP_(t-1) - 1) * 100

    2015 growth remains NaN because the JESI P2 panel
    begins at 2015 and does not use 2014 as an input year.
    """

    dataframe = dataframe.copy()

    dataframe = dataframe.sort_values(
        "year"
    ).reset_index(
        drop=True
    )

    dataframe["tfp_growth"] = (
        dataframe["tfp"]
        .pct_change()
        * 100.0
    )

    # Explicitly preserve 2015 as missing growth.
    dataframe.loc[
        dataframe["year"] == START_YEAR,
        "tfp_growth",
    ] = np.nan

    return dataframe


# ============================================================
# Process one country
# ============================================================

def process_country(
    content,
    sheet_name,
    country_code,
    country_name,
):
    """Extract and calculate TFP for one country."""

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"Processing {country_name} "
        f"({sheet_name} -> {country_code})"
    )

    print(
        "=" * 70
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

    tfp_row = find_tfp_level_row(
        dataframe,
        year_columns,
    )

    if tfp_row is None:
        raise ValueError(
            "Could not locate an economy-wide "
            f"TFP level/index row in APO sheet "
            f"{sheet_name}."
        )

    result = extract_tfp_levels(
        dataframe,
        year_columns,
        tfp_row,
    )

    result = calculate_tfp_growth(
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


# ============================================================
# Validate complete panel
# ============================================================

def validate_panel(
    dataframe,
):
    """Validate the complete five-country P2 panel."""

    expected_rows = (
        len(COUNTRIES)
        * (
            END_YEAR
            - START_YEAR
            + 1
        )
    )

    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    if len(dataframe) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, "
            f"found {len(dataframe)}."
        )

    # --------------------------------------------------------
    # Country coverage
    # --------------------------------------------------------

    expected_codes = {
        information["code"]
        for information in COUNTRIES.values()
    }

    actual_codes = set(
        dataframe[
            "country_code"
        ].unique()
    )

    if actual_codes != expected_codes:
        raise ValueError(
            "Country coverage mismatch. "
            f"Expected={expected_codes}, "
            f"Found={actual_codes}"
        )

    # --------------------------------------------------------
    # Year coverage
    # --------------------------------------------------------

    expected_years = set(
        range(
            START_YEAR,
            END_YEAR + 1,
        )
    )

    actual_years = set(
        dataframe[
            "year"
        ].astype(int)
        .unique()
    )

    if actual_years != expected_years:
        raise ValueError(
            "Year coverage mismatch. "
            f"Expected={expected_years}, "
            f"Found={actual_years}"
        )

    # --------------------------------------------------------
    # Duplicate country-year observations
    # --------------------------------------------------------

    if dataframe.duplicated(
        subset=[
            "country_code",
            "year",
        ]
    ).any():

        raise ValueError(
            "Duplicate country-year observations found."
        )

    # --------------------------------------------------------
    # Missing TFP levels
    # --------------------------------------------------------

    missing_tfp = dataframe[
        dataframe["tfp"].isna()
    ]

    if not missing_tfp.empty:

        print(
            "\nMissing TFP level observations:"
        )

        print(
            missing_tfp.to_string(
                index=False
            )
        )

        raise ValueError(
            "Missing TFP level observations found."
        )

    # --------------------------------------------------------
    # TFP levels must be positive
    # --------------------------------------------------------

    if (
        dataframe["tfp"] <= 0
    ).any():

        print(
            "\nNon-positive TFP observations:"
        )

        print(
            dataframe[
                dataframe["tfp"] <= 0
            ].to_string(
                index=False
            )
        )

        raise ValueError(
            "TFP levels/index values must be positive."
        )

    # --------------------------------------------------------
    # Growth observations
    # --------------------------------------------------------

    growth_panel = dataframe[
        dataframe["year"]
        >= START_YEAR + 1
    ].copy()

    expected_growth_rows = (
        len(COUNTRIES)
        * (
            END_YEAR
            - START_YEAR
        )
    )

    if len(growth_panel) != (
        expected_growth_rows
    ):

        raise ValueError(
            f"Expected {expected_growth_rows} "
            f"growth rows, found "
            f"{len(growth_panel)}."
        )

    missing_growth = growth_panel[
        growth_panel[
            "tfp_growth"
        ].isna()
    ]

    if not missing_growth.empty:

        print(
            "\nMissing TFP growth observations:"
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

    # --------------------------------------------------------
    # Finite growth observations
    # --------------------------------------------------------

    if not np.isfinite(
        growth_panel[
            "tfp_growth"
        ]
    ).all():

        raise ValueError(
            "Non-finite TFP growth values found."
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "P2 validation summary"
    )

    print(
        "=" * 70
    )

    print(
        f"Validated TFP level observations: "
        f"{len(dataframe)}"
    )

    print(
        f"Validated TFP growth observations: "
        f"{len(growth_panel)}"
    )

    print(
        "Expected TFP level observations: 45"
    )

    print(
        "Expected TFP growth observations: 40"
    )

    print(
        "Missing TFP levels: 0"
    )

    print(
        "Missing TFP growth observations: 0"
    )


# ============================================================
# Main
# ============================================================

def main():
    """Run the complete APO Productivity P2 pipeline."""

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

    # --------------------------------------------------------
    # Verify required country sheets.
    # --------------------------------------------------------

    available_sheets = set(
        workbook.sheet_names
    )

    required_sheets = set(
        COUNTRIES.keys()
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

    # --------------------------------------------------------
    # Process all five countries.
    # --------------------------------------------------------

    country_frames = []

    for sheet_name, information in (
        COUNTRIES.items()
    ):

        country_frame = process_country(
            content=content,
            sheet_name=sheet_name,
            country_code=information["code"],
            country_name=information["name"],
        )

        country_frames.append(
            country_frame
        )

    # --------------------------------------------------------
    # Combine panel.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Print coverage.
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "Country/year coverage"
    )

    print(
        "=" * 70
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

    # --------------------------------------------------------
    # Print TFP growth coverage.
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "TFP growth coverage (2016-2023)"
    )

    print(
        "=" * 70
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

    # --------------------------------------------------------
    # Validate.
    # --------------------------------------------------------

    validate_panel(
        dataframe
    )

    # --------------------------------------------------------
    # Save.
    # --------------------------------------------------------

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
