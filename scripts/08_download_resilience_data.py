"""
JAS-JESI Resilience Data Pipeline

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

Resilience indicators:
    1. FX Reserves / Import Cover
       Source: World Bank

    2. General Government Gross Debt (% GDP)
       Source: IMF WEO April 2026

    3. Current Account Balance (% GDP)
       Source: World Bank

Period:
    2015–2024
"""

from pathlib import Path

import pandas as pd
import requests


WORLD_BANK_API = (
    "https://api.worldbank.org/v2/country"
)

COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}

WORLD_BANK_INDICATORS = [
    "FI.RES.TOTL.MO",
    "BN.CAB.XOKA.GD.ZS",
]

IMF_DEBT_INDICATOR = "GGXWDG_NGDP"

START_YEAR = 2015
END_YEAR = 2024

IMF_FILE = Path(
    "WEOApr2026all.xlsx"
)

OUTPUT_DIR = Path(
    "data/raw"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "resilience_indicators_2015_2024.csv"
)


def download_world_bank_indicator(
    country,
    indicator,
):
    """
    Download one World Bank indicator.
    """

    url = (
        f"{WORLD_BANK_API}/{country}/indicator/"
        f"{indicator}?format=json&per_page=100"
        f"&date={START_YEAR}:{END_YEAR}"
    )

    response = requests.get(
        url,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if len(data) < 2 or not data[1]:
        return []

    records = []

    for item in data[1]:

        records.append(
            {
                "country": COUNTRIES[country],
                "year": int(item["date"]),
                "value": item.get("value"),
                "indicator": indicator,
            }
        )

    return records


def find_imf_table():
    """
    Locate the WEO country table inside the IMF workbook.

    Supports both:

    1. Legacy IMF WEO schema
       - Country
       - WEO Subject Code
       - Subject Descriptor

    2. New IMF WEO April 2026 schema
       - COUNTRY
       - SERIES_CODE
       - COUNTRY.ID
       - INDICATOR

    The workbook can contain several sheets and
    metadata rows before the actual country table.
    """

    print()
    print(
        "Inspecting IMF workbook sheets..."
    )

    workbook = pd.ExcelFile(
        IMF_FILE
    )

    print(
        "Sheets found:"
    )

    for sheet in workbook.sheet_names:
        print(
            f"  - {sheet}"
        )

    # New IMF WEO April 2026 schema
    # is checked first because it is the
    # current schema.
    header_candidates = [
        (
            "country.id",
            "series_code",
        ),
        (
            "country",
            "series_code",
        ),

        # Legacy WEO schemas
        (
            "country",
            "subject descriptor",
        ),
        (
            "country",
            "weo subject code",
        ),
        (
            "country",
            "subject code",
        ),
    ]

    for sheet_name in workbook.sheet_names:

        print()
        print(
            f"Inspecting sheet: {sheet_name}"
        )

        preview = pd.read_excel(
            IMF_FILE,
            sheet_name=sheet_name,
            header=None,
            nrows=100,
        )

        for row_number in range(
            len(preview)
        ):

            values = (
                preview
                .iloc[row_number]
                .astype(str)
                .str.strip()
                .str.lower()
                .tolist()
            )

            for first, second in (
                header_candidates
            ):

                if (
                    first in values
                    and second in values
                ):

                    print()
                    print(
                        "IMF country table header detected:"
                    )

                    print(
                        f"  Sheet: {sheet_name}"
                    )

                    print(
                        f"  Row: {row_number}"
                    )

                    print(
                        f"  Schema fields: "
                        f"{first} + {second}"
                    )

                    return (
                        sheet_name,
                        row_number,
                    )

    print()
    print(
        "Could not automatically detect "
        "the IMF country table header."
    )

    print()
    print(
        "First rows from each sheet:"
    )

    for sheet_name in workbook.sheet_names:

        preview = pd.read_excel(
            IMF_FILE,
            sheet_name=sheet_name,
            header=None,
            nrows=12,
        )

        print()
        print(
            f"--- {sheet_name} ---"
        )

        print(
            preview.to_string(
                index=False,
                header=False,
            )
        )

    raise ValueError(
        "Could not locate the IMF WEO "
        "country table."
    )


def find_column(
    dataframe,
    possible_names,
):
    """
    Find a column using several possible names.

    Matching is case-insensitive and ignores
    newline differences.
    """

    normalized = {}

    for column in dataframe.columns:

        key = (
            str(column)
            .strip()
            .lower()
            .replace(
                "\n",
                " ",
            )
        )

        normalized[key] = column

    for name in possible_names:

        key = (
            name
            .strip()
            .lower()
            .replace(
                "\n",
                " ",
            )
        )

        if key in normalized:
            return normalized[key]

    return None


def find_year_column(
    dataframe,
    year,
):
    """
    Find an IMF year column.

    IMF Excel files can expose year headers as:

        2015
        2015.0
        2015.00
        2015.000

    This function supports all of these formats.
    """

    candidates = {
        str(year),
        f"{year}.0",
        f"{year}.00",
        f"{year}.000",
    }

    for column in dataframe.columns:

        if str(column).strip() in candidates:
            return column

    return None


def normalize_country_id(
    value,
):
    """
    Normalize country IDs such as:

        BGD
        bgd
        BGD.0

    into a clean three-letter code.
    """

    if pd.isna(value):
        return ""

    text = (
        str(value)
        .strip()
        .upper()
    )

    # Handle Excel-style numeric-looking
    # values defensively.
    if text.endswith(".0"):
        text = text[:-2]

    return text


def download_imf_debt_data():
    """
    Read General Government Gross Debt (% GDP)
    from the IMF April 2026 WEO Excel dataset.

    Supports both legacy and new IMF WEO schemas.
    """

    print()
    print(
        "Reading IMF WEO April 2026 dataset..."
    )

    if not IMF_FILE.exists():

        raise FileNotFoundError(
            "IMF WEO file not found: "
            f"{IMF_FILE}"
        )

    print(
        f"IMF file: {IMF_FILE}"
    )

    sheet_name, header_row = (
        find_imf_table()
    )

    data = pd.read_excel(
        IMF_FILE,
        sheet_name=sheet_name,
        header=header_row,
    )

    data.columns = [
        str(column).strip()
        for column in data.columns
    ]

    print()
    print(
        f"IMF sheet: {sheet_name}"
    )

    print(
        f"IMF header row: {header_row}"
    )

    print(
        f"IMF dataset rows: {len(data)}"
    )

    print()
    print(
        "Detected IMF columns:"
    )

    print(
        list(data.columns[:25])
    )

    # --------------------------------------------------
    # Detect country column
    # --------------------------------------------------

    country_column = find_column(
        data,
        [
            "Country",
            "Country Name",
            "COUNTRY",
        ],
    )

    # --------------------------------------------------
    # Detect IMF indicator / series code
    # --------------------------------------------------

    subject_code_column = find_column(
        data,
        [
            "WEO Subject Code",
            "Subject Code",
            "SERIES_CODE",
            "Series Code",
        ],
    )

    # --------------------------------------------------
    # Detect indicator description
    # --------------------------------------------------

    subject_descriptor_column = find_column(
        data,
        [
            "Subject Descriptor",
            "INDICATOR",
            "Indicator",
        ],
    )

    # --------------------------------------------------
    # Detect ISO / country ID
    # --------------------------------------------------

    iso_column = find_column(
        data,
        [
            "ISO",
            "ISO Code",
            "COUNTRY.ID",
            "Country ID",
        ],
    )

    # --------------------------------------------------
    # Validate required columns
    # --------------------------------------------------

    if (
        country_column is None
        or subject_code_column is None
        or subject_descriptor_column is None
    ):

        raise ValueError(
            "Could not identify required IMF "
            "WEO columns.\n\n"
            "Detected columns:\n"
            f"{list(data.columns)}"
        )

    print()
    print(
        "IMF columns detected:"
    )

    print(
        f"Country: {country_column}"
    )

    print(
        f"Subject Code: {subject_code_column}"
    )

    print(
        f"Subject Descriptor: "
        f"{subject_descriptor_column}"
    )

    print(
        f"ISO / Country ID: {iso_column}"
    )

    # --------------------------------------------------
    # Find General Government Gross Debt
    # --------------------------------------------------

    debt = data[
        data[subject_code_column]
        .astype(str)
        .str.strip()
        == IMF_DEBT_INDICATOR
    ].copy()

    # Fallback:
    # Search by indicator description if
    # SERIES_CODE / WEO Subject Code is not
    # populated as expected.
    if debt.empty:

        debt = data[
            data[subject_descriptor_column]
            .astype(str)
            .str.contains(
                "general government gross debt",
                case=False,
                na=False,
            )
        ].copy()

    if debt.empty:

        raise ValueError(
            "Could not find General Government "
            "Gross Debt in IMF WEO dataset.\n\n"
            "Expected indicator code: "
            f"{IMF_DEBT_INDICATOR}"
        )

    print()
    print(
        "IMF debt rows found: "
        f"{len(debt)}"
    )

    records = []

    # --------------------------------------------------
    # Process each country
    # --------------------------------------------------

    for country_code, country_name in (
        COUNTRIES.items()
    ):

        country_data = pd.DataFrame()

        # --------------------------------------------------
        # Preferred method:
        # ISO / COUNTRY.ID matching
        # --------------------------------------------------

        if iso_column is not None:

            normalized_ids = (
                debt[iso_column]
                .apply(
                    normalize_country_id
                )
            )

            country_data = debt[
                normalized_ids
                == country_code
            ].copy()

        # --------------------------------------------------
        # Fallback:
        # Country name matching
        # --------------------------------------------------

        if country_data.empty:

            possible_country_names = [
                country_name
            ]

            if country_code == "VNM":

                possible_country_names.extend(
                    [
                        "Vietnam",
                        "Viet Nam",
                    ]
                )

            country_names_normalized = [
                str(name)
                .strip()
                .lower()
                for name
                in possible_country_names
            ]

            country_data = debt[
                debt[country_column]
                .astype(str)
                .str.strip()
                .str.lower()
                .isin(
                    country_names_normalized
                )
            ].copy()

        # --------------------------------------------------
        # Validate country
        # --------------------------------------------------

        if country_data.empty:

            raise ValueError(
                "Country not found in IMF WEO: "
                f"{country_name} "
                f"({country_code})"
            )

        if len(country_data) > 1:

            print()
            print(
                "Warning: multiple IMF rows found "
                f"for {country_name} "
                f"({country_code})."
            )

            print(
                "Using the first matching row."
            )

        row = country_data.iloc[0]

        # --------------------------------------------------
        # Extract requested years
        # --------------------------------------------------

        for year in range(
            START_YEAR,
            END_YEAR + 1,
        ):

            year_column = find_year_column(
                data,
                year,
            )

            if year_column is None:

                raise ValueError(
                    "Year column not found "
                    f"in IMF WEO: {year}\n"
                    f"Available columns include: "
                    f"{list(data.columns[-25:])}"
                )

            value = row[
                year_column
            ]

            if pd.isna(value):
                value = None

            records.append(
                {
                    "country": country_name,
                    "year": year,
                    "value": value,
                    "indicator": IMF_DEBT_INDICATOR,
                }
            )

    return records


def main():

    print(
        "Downloading JESI Resilience pillar data..."
    )

    print(
        f"Countries: {list(COUNTRIES.keys())}"
    )

    print(
        f"Years: {START_YEAR}-{END_YEAR}"
    )

    records = []

    # --------------------------------------------------
    # World Bank
    # --------------------------------------------------

    print()
    print(
        "Downloading World Bank indicators..."
    )

    for country in COUNTRIES:

        for indicator in (
            WORLD_BANK_INDICATORS
        ):

            country_records = (
                download_world_bank_indicator(
                    country,
                    indicator,
                )
            )

            records.extend(
                country_records
            )

    print(
        f"World Bank rows: {len(records)}"
    )

    # --------------------------------------------------
    # IMF
    # --------------------------------------------------

    imf_debt = (
        download_imf_debt_data()
    )

    print(
        f"IMF debt rows: {len(imf_debt)}"
    )

    records.extend(
        imf_debt
    )

    # --------------------------------------------------
    # Create dataframe
    # --------------------------------------------------

    data = pd.DataFrame(
        records,
        columns=[
            "country",
            "year",
            "value",
            "indicator",
        ],
    )

    data = data.sort_values(
        [
            "country",
            "year",
            "indicator",
        ]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------
    # Save output
    # --------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------
    # Validation / reporting
    # --------------------------------------------------

    print()
    print(
        "========================================"
    )

    print(
        "Resilience data download completed."
    )

    print(
        f"Total rows: {len(data)}"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print(
        "========================================"
    )

    print()

    print(
        "Rows by indicator:"
    )

    print(
        data.groupby(
            "indicator"
        ).size()
    )

    print()

    print(
        "Missing values:"
    )

    print(
        data.groupby(
            "indicator"
        )["value"]
        .apply(
            lambda x: x.isna().sum()
        )
    )

    print()

    print(
        "Rows by country:"
    )

    print(
        data.groupby(
            "country"
        ).size()
    )

    print()

    print(
        "First rows:"
    )

    print(
        data.head(15)
    )


if __name__ == "__main__":
    main()
