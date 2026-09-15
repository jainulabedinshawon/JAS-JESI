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
        timeout=120,
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
    Locate the IMF WEO country table.

    Supports:
        - April 2026 IMF WEO schema
        - Legacy IMF WEO schema
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

    header_candidates = [
        # New April 2026 schema
        (
            "country.id",
            "series_code",
        ),
        (
            "country",
            "series_code",
        ),
        (
            "country.id",
            "indicator.id",
        ),
        (
            "country",
            "indicator.id",
        ),

        # Legacy schemas
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

    Supports:
        2015
        2015.0
        2015.00
        2015.000
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


def normalize_text(
    value,
):
    """
    Normalize text for robust IMF matching.
    """

    if pd.isna(value):
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace(
            "_",
            " ",
        )
        .replace(
            "-",
            " ",
        )
        .replace(
            "%",
            " percent ",
        )
    )


def normalize_country_id(
    value,
):
    """
    Normalize country IDs such as:

        BGD
        bgd
        BGD.0
    """

    if pd.isna(value):
        return ""

    text = (
        str(value)
        .strip()
        .upper()
    )

    if text.endswith(".0"):
        text = text[:-2]

    return text


def find_imf_debt_rows(
    data,
    subject_code_column,
    subject_descriptor_column,
):
    """
    Identify General Government Gross Debt rows.

    Strategy:

    1. Try GGXWDG_NGDP in every likely code column.
    2. Try indicator ID.
    3. Try exact / broad indicator description matching.
    """

    print()
    print(
        "Searching IMF dataset for "
        "General Government Gross Debt..."
    )

    debt = pd.DataFrame()

    # --------------------------------------------------
    # Possible code columns
    # --------------------------------------------------

    code_columns = []

    for possible_name in [
        "WEO Subject Code",
        "Subject Code",
        "SERIES_CODE",
        "Series Code",
        "INDICATOR.ID",
        "Indicator ID",
    ]:

        column = find_column(
            data,
            [possible_name],
        )

        if (
            column is not None
            and column not in code_columns
        ):

            code_columns.append(
                column
            )

    print()
    print(
        "IMF indicator/code columns checked:"
    )

    for column in code_columns:
        print(
            f"  - {column}"
        )

    # --------------------------------------------------
    # Strategy 1:
    # Search indicator code
    # --------------------------------------------------

    for column in code_columns:

        candidate = data[
            data[column]
            .astype(str)
            .str.strip()
            .str.upper()
            == IMF_DEBT_INDICATOR
        ].copy()

        if not candidate.empty:

            debt = candidate

            print()
            print(
                "Debt indicator found by code:"
            )

            print(
                f"  Column: {column}"
            )

            print(
                f"  Code: {IMF_DEBT_INDICATOR}"
            )

            return debt

    # --------------------------------------------------
    # Strategy 2:
    # Search indicator description
    # --------------------------------------------------

    description_columns = []

    for possible_name in [
        "Subject Descriptor",
        "INDICATOR",
        "Indicator",
        "INDICATOR.Description",
        "Indicator Description",
    ]:

        column = find_column(
            data,
            [possible_name],
        )

        if (
            column is not None
            and column not in description_columns
        ):

            description_columns.append(
                column
            )

    print()
    print(
        "IMF description columns checked:"
    )

    for column in description_columns:
        print(
            f"  - {column}"
        )

    # Exact-ish phrase first
    for column in description_columns:

        text = (
            data[column]
            .apply(normalize_text)
        )

        candidate = data[
            text.str.contains(
                "general government gross debt",
                case=False,
                na=False,
            )
        ].copy()

        if not candidate.empty:

            debt = candidate

            print()
            print(
                "Debt indicator found by description:"
            )

            print(
                f"  Column: {column}"
            )

            print(
                "  Match: general government "
                "gross debt"
            )

            return debt

    # --------------------------------------------------
    # Strategy 3:
    # More flexible description search
    # --------------------------------------------------

    for column in description_columns:

        text = (
            data[column]
            .apply(normalize_text)
        )

        candidate = data[
            text.str.contains(
                "gross debt",
                case=False,
                na=False,
            )
            &
            text.str.contains(
                "government",
                case=False,
                na=False,
            )
        ].copy()

        if not candidate.empty:

            debt = candidate

            print()
            print(
                "Debt indicator found by "
                "flexible description search:"
            )

            print(
                f"  Column: {column}"
            )

            return debt

    # --------------------------------------------------
    # Diagnostic output
    # --------------------------------------------------

    print()
    print(
        "DEBUG: Could not find debt indicator."
    )

    for column in code_columns:

        print()
        print(
            f"Unique values from {column}:"
        )

        print(
            data[column]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .head(50)
            .tolist()
        )

    for column in description_columns:

        print()
        print(
            f"Possible debt-related values from "
            f"{column}:"
        )

        text = (
            data[column]
            .astype(str)
        )

        mask = (
            text.str.contains(
                "debt",
                case=False,
                na=False,
            )
        )

        print(
            data.loc[
                mask,
                column,
            ]
            .drop_duplicates()
            .head(50)
            .tolist()
        )

    return pd.DataFrame()


def download_imf_debt_data():
    """
    Read General Government Gross Debt (% GDP)
    from IMF WEO April 2026.

    Supports the new April 2026 IMF Data Portal
    workbook schema and legacy WEO schemas.
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
        list(data.columns[:30])
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
    # Detect subject / series code
    # --------------------------------------------------

    subject_code_column = find_column(
        data,
        [
            "WEO Subject Code",
            "Subject Code",
            "SERIES_CODE",
            "Series Code",
            "INDICATOR.ID",
            "Indicator ID",
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
            "INDICATOR.Description",
            "Indicator Description",
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

    if country_column is None:

        raise ValueError(
            "Could not identify IMF country column."
        )

    if (
        subject_code_column is None
        and subject_descriptor_column is None
    ):

        raise ValueError(
            "Could not identify IMF indicator "
            "columns.\n\n"
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
        f"Subject / Series Code: "
        f"{subject_code_column}"
    )

    print(
        f"Indicator Description: "
        f"{subject_descriptor_column}"
    )

    print(
        f"ISO / Country ID: {iso_column}"
    )

    # --------------------------------------------------
    # Find debt rows
    # --------------------------------------------------

    debt = find_imf_debt_rows(
        data,
        subject_code_column,
        subject_descriptor_column,
    )

    if debt.empty:

        raise ValueError(
            "Could not find General Government "
            "Gross Debt in IMF WEO dataset.\n\n"
            f"Expected indicator code: "
            f"{IMF_DEBT_INDICATOR}\n\n"
            "The diagnostic output above shows "
            "the available IMF indicator values."
        )

    print()
    print(
        "IMF debt rows found: "
        f"{len(debt)}"
    )

    records = []

    # --------------------------------------------------
    # Process countries
    # --------------------------------------------------

    for country_code, country_name in (
        COUNTRIES.items()
    ):

        country_data = pd.DataFrame()

        # --------------------------------------------------
        # Preferred:
        # ISO / COUNTRY.ID
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
        # Country name
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
                normalize_text(name)
                for name
                in possible_country_names
            ]

            country_data = debt[
                debt[country_column]
                .apply(normalize_text)
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
                "Warning: multiple IMF debt rows "
                f"found for {country_name} "
                f"({country_code})."
            )

            print(
                "Using the first matching row."
            )

        row = country_data.iloc[0]

        # --------------------------------------------------
        # Extract years
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
                    f"Available columns: "
                    f"{list(data.columns[-30:])}"
                )

            value = row[
                year_column
            ]

            # IMF can use strings such as
            # "n/a" or blank values.
            if pd.isna(value):

                value = None

            elif isinstance(value, str):

                cleaned_value = (
                    value
                    .strip()
                    .lower()
                )

                if cleaned_value in {
                    "",
                    "n/a",
                    "na",
                    "nan",
                    "--",
                }:

                    value = None

                else:

                    try:
                        value = float(
                            value.replace(
                                ",",
                                "",
                            )
                        )

                    except ValueError:
                        pass

            records.append(
                {
                    "country": country_name,
                    "year": year,
                    "value": value,
                    "indicator": IMF_DEBT_INDICATOR,
                }
            )

    return records


def validate_output(
    data,
):
    """
    Validate the final resilience dataset.
    """

    expected_countries = set(
        COUNTRIES.values()
    )

    actual_countries = set(
        data["country"]
        .dropna()
        .unique()
    )

    missing_countries = (
        expected_countries
        - actual_countries
    )

    if missing_countries:

        raise ValueError(
            "Missing countries in final dataset: "
            f"{sorted(missing_countries)}"
        )

    expected_years = set(
        range(
            START_YEAR,
            END_YEAR + 1,
        )
    )

    actual_years = set(
        data["year"]
        .dropna()
        .astype(int)
        .unique()
    )

    missing_years = (
        expected_years
        - actual_years
    )

    if missing_years:

        raise ValueError(
            "Missing years in final dataset: "
            f"{sorted(missing_years)}"
        )

    expected_indicators = set(
        WORLD_BANK_INDICATORS
        + [
            IMF_DEBT_INDICATOR
        ]
    )

    actual_indicators = set(
        data["indicator"]
        .dropna()
        .unique()
    )

    missing_indicators = (
        expected_indicators
        - actual_indicators
    )

    if missing_indicators:

        raise ValueError(
            "Missing indicators in final dataset: "
            f"{sorted(missing_indicators)}"
        )

    print()
    print(
        "Validation checks passed."
    )

    print(
        f"Countries validated: "
        f"{len(actual_countries)}"
    )

    print(
        f"Years validated: "
        f"{START_YEAR}-{END_YEAR}"
    )

    print(
        f"Indicators validated: "
        f"{len(actual_indicators)}"
    )


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
    # Validate
    # --------------------------------------------------

    validate_output(
        data
    )

    # --------------------------------------------------
    # Save
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
    # Final report
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
