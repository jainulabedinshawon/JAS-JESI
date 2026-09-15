"""
JESI Productivity P2 Data Download Module

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

P2 Indicator:
    Total Factor Productivity (TFP) Growth

Primary Source:
    Penn World Table (PWT) 11.0

PWT Variable:
    rtfpna

Period:
    2015-2023

Countries:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia
"""

from io import BytesIO
from pathlib import Path

import pandas as pd
import requests


PWT_DATASET_DOI = "doi:10.34894/FABVLR"

PWT_DATASET_API = (
    "https://dataverse.nl/api/datasets/:persistentId"
)

PWT_FILE_NAME = "pwt110.xlsx"

OUTPUT_FILE = Path(
    "data/raw/"
    "productivity_p2_tfp_growth_2015_2023.csv"
)

COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}

START_YEAR = 2015
END_YEAR = 2023


def download_pwt_excel():
    """
    Locate and download the official PWT 11.0 Excel file
    through the Dataverse persistent dataset API.

    The downloaded response is validated to ensure that
    Dataverse returned an actual Excel workbook.
    """

    response = requests.get(
        PWT_DATASET_API,
        params={
            "persistentId": PWT_DATASET_DOI,
        },
        timeout=120,
    )

    response.raise_for_status()

    dataset = response.json()

    files = (
        dataset
        .get("data", {})
        .get("latestVersion", {})
        .get("files", [])
    )

    target_file = None

    for file_info in files:
        data_file = file_info.get("dataFile", {})

        if data_file.get("filename") == PWT_FILE_NAME:
            target_file = data_file
            break

    if target_file is None:
        raise FileNotFoundError(
            f"Could not find {PWT_FILE_NAME} "
            "in the PWT 11.0 dataset."
        )

    file_id = target_file.get("id")

    if file_id is None:
        raise ValueError(
            "PWT file ID was not found."
        )

    download_url = (
        "https://dataverse.nl/api/access/datafile/"
        f"{file_id}"
    )

    file_response = requests.get(
        download_url,
        timeout=120,
        allow_redirects=True,
    )

    file_response.raise_for_status()

    content_type = (
        file_response.headers
        .get("Content-Type", "")
        .lower()
    )

    content = file_response.content

    print()
    print("PWT DOWNLOAD RESPONSE")
    print("=" * 72)

    print(
        f"HTTP status: {file_response.status_code}"
    )

    print(
        f"Content-Type: {content_type}"
    )

    print(
        f"Downloaded bytes: {len(content)}"
    )

    print(
        f"Final URL: {file_response.url}"
    )

    if not content:
        raise ValueError(
            "PWT download returned an empty file."
        )

    # XLSX files are ZIP containers and normally begin
    # with the ZIP magic bytes PK.
    if not content.startswith(b"PK"):
        preview = content[:200].decode(
            "utf-8",
            errors="replace",
        )

        raise ValueError(
            "The downloaded PWT file does not appear "
            "to be a valid XLSX file. "
            f"Response preview: {preview}"
        )

    return BytesIO(content)


def load_pwt_data(excel_file):
    """
    Locate the PWT data table automatically.

    PWT Excel files may contain metadata sheets or
    header rows before the actual data table.

    This function searches all worksheets and multiple
    header rows for the required PWT columns.
    """

    required_columns = {
        "countrycode",
        "country",
        "year",
        "rtfpna",
    }

    workbook = pd.ExcelFile(
        excel_file,
        engine="openpyxl",
    )

    print()
    print("PWT WORKBOOK SHEETS")
    print("=" * 72)

    print(
        workbook.sheet_names
    )

    for sheet_name in workbook.sheet_names:

        for header_row in range(0, 20):

            try:
                dataframe = pd.read_excel(
                    excel_file,
                    sheet_name=sheet_name,
                    header=header_row,
                    engine="openpyxl",
                )
            except Exception:
                continue

            dataframe.columns = [
                str(column)
                .strip()
                .lower()
                for column in dataframe.columns
            ]

            available_columns = set(
                dataframe.columns
            )

            if required_columns.issubset(
                available_columns
            ):

                print()
                print(
                    "PWT DATA TABLE FOUND"
                )
                print("=" * 72)

                print(
                    f"Sheet: {sheet_name}"
                )

                print(
                    f"Header row: {header_row}"
                )

                print(
                    "Required columns detected:"
                )

                print(
                    sorted(required_columns)
                )

                return dataframe

    raise ValueError(
        "Could not locate the required PWT columns "
        "in any worksheet/header combination. "
        f"Required columns: "
        f"{sorted(required_columns)}"
    )


def calculate_tfp_growth(dataframe):
    """
    Calculate annual TFP growth from PWT TFP levels.

    Formula:

        ((TFP_t / TFP_(t-1)) - 1) * 100

    The first year of each country is therefore used
    only as the base year for calculating the following
    year's growth.
    """

    dataframe = dataframe.copy()

    dataframe = dataframe.sort_values(
        [
            "country",
            "year",
        ]
    )

    dataframe["tfp_growth"] = (
        dataframe
        .groupby("country")["tfp"]
        .pct_change()
        * 100
    )

    return dataframe


def main():
    """
    Download PWT 11.0 data and construct the JESI P2
    TFP growth dataset.
    """

    print("=" * 72)
    print("JESI PRODUCTIVITY P2 DATA DOWNLOAD")
    print("=" * 72)

    print()
    print("Source:")
    print("Penn World Table 11.0")

    print()
    print("PWT variable:")
    print("rtfpna")

    print()
    print("Period:")
    print(
        f"{START_YEAR}-{END_YEAR}"
    )

    print()
    print("Countries:")
    print(
        ", ".join(COUNTRIES.values())
    )

    print()
    print(
        "Downloading official PWT 11.0 Excel file..."
    )

    excel_file = download_pwt_excel()

    dataframe = load_pwt_data(
        excel_file
    )

    dataframe = dataframe[
        dataframe["countrycode"].isin(
            COUNTRIES.keys()
        )
    ].copy()

    dataframe = dataframe[
        dataframe["year"].between(
            START_YEAR,
            END_YEAR,
        )
    ].copy()

    dataframe = dataframe[
        [
            "countrycode",
            "country",
            "year",
            "rtfpna",
        ]
    ].rename(
        columns={
            "countrycode": "country_code",
            "rtfpna": "tfp",
        }
    )

    dataframe["country"] = dataframe[
        "country_code"
    ].map(COUNTRIES)

    if dataframe["country"].isna().any():
        raise ValueError(
            "Unexpected country code found."
        )

    dataframe["year"] = pd.to_numeric(
        dataframe["year"],
        errors="coerce",
    )

    dataframe["tfp"] = pd.to_numeric(
        dataframe["tfp"],
        errors="coerce",
    )

    if dataframe["year"].isna().any():
        raise ValueError(
            "Invalid year values found."
        )

    if dataframe["tfp"].isna().any():
        raise ValueError(
            "Missing TFP observations found."
        )

    if (dataframe["tfp"] <= 0).any():
        raise ValueError(
            "TFP values must be positive."
        )

    expected_rows = (
        len(COUNTRIES)
        * (END_YEAR - START_YEAR + 1)
    )

    if len(dataframe) != expected_rows:
        raise ValueError(
            "Unexpected number of PWT observations. "
            f"Expected {expected_rows}, "
            f"found {len(dataframe)}."
        )

    duplicates = dataframe.duplicated(
        subset=[
            "country_code",
            "year",
        ]
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate country-year observations found."
        )

    dataframe = calculate_tfp_growth(
        dataframe
    )

    dataframe = dataframe[
        [
            "country_code",
            "country",
            "year",
            "tfp",
            "tfp_growth",
        ]
    ]

    dataframe = dataframe.sort_values(
        [
            "country",
            "year",
        ]
    ).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("P2 DATA SUMMARY")
    print("=" * 72)

    print(
        dataframe.to_string(
            index=False
        )
    )

    print()
    print("OUTPUT")
    print("=" * 72)

    print(
        f"Saved: {OUTPUT_FILE}"
    )

    print()
    print(
        f"Rows: {len(dataframe)}"
    )

    print()
    print(
        "JESI Productivity P2 data "
        "download completed successfully."
    )


if __name__ == "__main__":
    main()
