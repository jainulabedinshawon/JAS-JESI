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


def find_imf_header_row(file_path):
    """
    Find the actual header row in the IMF WEO Excel file.

    The April 2026 WEO workbook may contain title/
    metadata rows before the actual table header.
    """

    preview = pd.read_excel(
        file_path,
        sheet_name=0,
        header=None,
        nrows=30,
    )

    for row_number in range(
        len(preview)
    ):

        row = preview.iloc[
            row_number
        ].astype(str)

        row_text = " | ".join(
            row.tolist()
        ).lower()

        if (
            "subject descriptor" in row_text
            and "country" in row_text
        ):
            return row_number

    raise ValueError(
        "Could not locate the IMF WEO "
        "table header row."
    )


def find_column(
    dataframe,
    possible_names,
):
    """
    Find a column using several possible names.
    """

    normalized = {
        str(column)
        .strip()
        .lower()
        .replace(
            "\n",
            " ",
        ): column
        for column in dataframe.columns
    }

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


def download_imf_debt_data():
    """
    Read General Government Gross Debt (% GDP)
    from the IMF April 2026 WEO Excel dataset.
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

    header_row = find_imf_header_row(
        IMF_FILE
    )

    print(
        f"Detected IMF header row: "
        f"{header_row}"
    )

    data = pd.read_excel(
        IMF_FILE,
        sheet_name=0,
        header=header_row,
    )

    data.columns = [
        str(column).strip()
        for column in data.columns
    ]

    print(
        f"IMF dataset rows: {len(data)}"
    )

    print(
        "Detected columns:"
    )

    print(
        list(data.columns[:12])
    )

    country_column = find_column(
        data,
        [
            "Country",
            "Country Name",
        ],
    )

    subject_code_column = find_column(
        data,
        [
            "WEO Subject Code",
            "Subject Code",
        ],
    )

    subject_descriptor_column = find_column(
        data,
        [
            "Subject Descriptor",
        ],
    )

    iso_column = find_column(
        data,
        [
            "ISO",
            "ISO Code",
        ],
    )

    if (
        country_column is None
        or subject_code_column is None
        or subject_descriptor_column is None
    ):

        raise ValueError(
            "Could not identify required IMF WEO "
            "columns. Detected columns: "
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
        f"ISO: {iso_column}"
    )

    debt = data[
        data[subject_code_column]
        .astype(str)
        .str.strip()
        == IMF_DEBT_INDICATOR
    ].copy()

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
            "Gross Debt in IMF WEO dataset."
        )

    print()
    print(
        "IMF debt rows found: "
        f"{len(debt)}"
    )

    records = []

    for country_code, country_name in (
        COUNTRIES.items()
    ):

        if iso_column is not None:

            country_data = debt[
                debt[iso_column]
                .astype(str)
                .str.strip()
                .str.upper()
                == country_code
            ]

        else:

            country_data = debt[
                debt[country_column]
                .astype(str)
                .str.strip()
                .isin(
                    [
                        country_name,
                        "Vietnam"
                        if country_code == "VNM"
                        else country_name,
                    ]
                )
            ]

        if country_data.empty:

            raise ValueError(
                "Country not found in IMF WEO: "
                f"{country_name} "
                f"({country_code})"
            )

        row = country_data.iloc[0]

        for year in range(
            START_YEAR,
            END_YEAR + 1,
        ):

            year_column = str(year)

            if (
                year_column
                not in data.columns
            ):

                raise ValueError(
                    "Year column not found "
                    f"in IMF WEO: {year_column}"
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

    imf_debt = (
        download_imf_debt_data()
    )

    print(
        f"IMF debt rows: {len(imf_debt)}"
    )

    records.extend(
        imf_debt
    )

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

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        OUTPUT_FILE,
        index=False,
    )

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
        "First rows:"
    )

    print(
        data.head(15)
    )


if __name__ == "__main__":
    main()
