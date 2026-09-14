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

Countries:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia

Period:
    2015–2024
"""

from pathlib import Path

import pandas as pd
import requests


# ============================================================
# Configuration
# ============================================================

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


# IMF WEO indicator:
# General Government Gross Debt (% GDP)
IMF_DEBT_INDICATOR = "GGXWDG_NGDP"


START_YEAR = 2015
END_YEAR = 2024


# IMF Excel file is located in repository root.
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


# ============================================================
# World Bank
# ============================================================

def download_world_bank_indicator(
    country,
    indicator,
):
    """
    Download one World Bank indicator
    for one country.
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


# ============================================================
# IMF WEO
# ============================================================

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

    data = pd.read_excel(
        IMF_FILE,
        sheet_name="Countries",
    )

    print(
        f"IMF dataset rows: {len(data)}"
    )

    required_columns = [
        "ISO",
        "Country",
        "WEO Subject Code",
        "Subject Descriptor",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing IMF WEO columns: "
            f"{missing_columns}"
        )

    debt = data[
        data["WEO Subject Code"]
        == IMF_DEBT_INDICATOR
    ].copy()

    if debt.empty:

        raise ValueError(
            "IMF WEO indicator not found: "
            f"{IMF_DEBT_INDICATOR}"
        )

    print(
        "IMF debt indicator found:"
    )

    print(
        debt[
            [
                "ISO",
                "Country",
                "WEO Subject Code",
                "Subject Descriptor",
            ]
        ].head()
    )

    records = []

    for country_code in COUNTRIES:

        country_data = debt[
            debt["ISO"]
            == country_code
        ]

        if country_data.empty:

            raise ValueError(
                "Country not found in IMF WEO: "
                f"{country_code}"
            )

        row = country_data.iloc[0]

        for year in range(
            START_YEAR,
            END_YEAR + 1,
        ):

            year_column = str(year)

            if year_column not in debt.columns:

                raise ValueError(
                    "Year column not found "
                    f"in IMF WEO: {year_column}"
                )

            value = row[year_column]

            if pd.isna(value):
                value = None

            records.append(
                {
                    "country": COUNTRIES[
                        country_code
                    ],
                    "year": year,
                    "value": value,
                    "indicator": IMF_DEBT_INDICATOR,
                }
            )

    return records


# ============================================================
# Main pipeline
# ============================================================

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

    # --------------------------------------------------------
    # World Bank
    # --------------------------------------------------------

    print()
    print(
        "Downloading World Bank indicators..."
    )

    records = []

    for country in COUNTRIES:

        for indicator in WORLD_BANK_INDICATORS:

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

    # --------------------------------------------------------
    # IMF
    # --------------------------------------------------------

    print()

    imf_debt = (
        download_imf_debt_data()
    )

    print(
        f"IMF debt rows: {len(imf_debt)}"
    )

    records.extend(
        imf_debt
    )

    # --------------------------------------------------------
    # Build dataframe
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

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
