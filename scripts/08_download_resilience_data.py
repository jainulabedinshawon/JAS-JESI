"""
JAS-JESI Resilience Data Pipeline

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

Resilience indicators:

1. Total Reserves in Months of Imports
   World Bank: FI.RES.TOTL.MO

2. General Government Gross Debt (% of GDP)
   IMF WEO: GGXWDG_NGDP

3. Current Account Balance (% of GDP)
   World Bank: BN.CAB.XOKA.GD.ZS

Countries:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia

Period:
    2015–2024

Debt methodology:
    IMF WEO General Government Gross Debt (% GDP)
    is used as a debt sustainability proxy.
"""

from pathlib import Path

import pandas as pd
import requests

from src.data_download import (
    download_country_indicators,
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


OUTPUT_DIR = Path("data/raw")


OUTPUT_FILE = (
    OUTPUT_DIR
    / "resilience_indicators_2015_2024.csv"
)


IMF_WEO_URL = (
    "https://www.imf.org/-/media/Websites/IMF/imported-datasets"
    "/external/2026/1/WEOApr2026all.ashx"
)


WORLD_BANK_INDICATORS = [
    "FI.RES.TOTL.MO",
    "BN.CAB.XOKA.GD.ZS",
]


COUNTRY_NAME_MAP = {
    "Bangladesh": "Bangladesh",
    "India": "India",
    "Vietnam": "Viet Nam",
    "Viet Nam": "Viet Nam",
    "Indonesia": "Indonesia",
    "Malaysia": "Malaysia",
}


def download_world_bank_data():
    """
    Download Reserves and Current Account data
    from the World Bank.
    """

    data = download_country_indicators(
        countries=COUNTRIES,
        indicators=WORLD_BANK_INDICATORS,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    return data


def download_imf_weo_debt():
    """
    Download IMF WEO General Government Gross Debt
    (% of GDP).

    IMF WEO indicator:
        GGXWDG_NGDP
    """

    response = requests.get(
        IMF_WEO_URL,
        timeout=60,
    )

    response.raise_for_status()

    output_file = (
        OUTPUT_DIR
        / "imf_weo_april_2026_raw.xls"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_bytes(
        response.content
    )

    try:
        data = pd.read_csv(
            output_file,
            sep="\t",
            encoding="utf-8-sig",
        )
    except Exception:
        data = pd.read_csv(
            output_file,
            sep="\t",
            encoding="latin1",
        )

    return data


def extract_imf_debt(data):
    """
    Extract IMF WEO General Government Gross Debt
    (% of GDP) for the five JESI countries.
    """

    country_column = "Country"
    subject_column = "Subject Descriptor"

    debt_subject = (
        "General government gross debt"
    )

    debt = data[
        data[subject_column]
        == debt_subject
    ].copy()

    selected_countries = [
        "Bangladesh",
        "India",
        "Viet Nam",
        "Vietnam",
        "Indonesia",
        "Malaysia",
    ]

    debt = debt[
        debt[country_column]
        .isin(selected_countries)
    ].copy()

    year_columns = [
        str(year)
        for year in range(
            START_YEAR,
            END_YEAR + 1,
        )
    ]

    available_years = [
        year
        for year in year_columns
        if year in debt.columns
    ]

    debt = debt[
        [
            country_column,
            *available_years,
        ]
    ]

    debt = debt.rename(
        columns={
            country_column: "country",
        }
    )

    debt = debt.melt(
        id_vars=["country"],
        var_name="year",
        value_name="value",
    )

    debt["year"] = pd.to_numeric(
        debt["year"],
        errors="coerce",
    )

    debt["value"] = pd.to_numeric(
        debt["value"],
        errors="coerce",
    )

    debt = debt.dropna(
        subset=["year"]
    )

    debt["year"] = debt[
        "year"
    ].astype(int)

    debt["indicator"] = (
        "GGXWDG_NGDP"
    )

    debt["country"] = debt[
        "country"
    ].map(
        COUNTRY_NAME_MAP
    )

    return debt[
        [
            "country",
            "year",
            "value",
            "indicator",
        ]
    ]


def main():
    print(
        "Downloading JESI Resilience pillar data..."
    )

    print(
        f"Countries: {COUNTRIES}"
    )

    print(
        f"Years: {START_YEAR}-{END_YEAR}"
    )

    print()
    print(
        "Downloading World Bank indicators..."
    )

    world_bank_data = (
        download_world_bank_data()
    )

    print(
        f"World Bank rows: "
        f"{len(world_bank_data)}"
    )

    print()
    print(
        "Downloading IMF WEO debt data..."
    )

    imf_data = (
        download_imf_weo_debt()
    )

    debt_data = (
        extract_imf_debt(
            imf_data
        )
    )

    print(
        f"IMF debt rows: "
        f"{len(debt_data)}"
    )

    combined = pd.concat(
        [
            world_bank_data,
            debt_data,
        ],
        ignore_index=True,
    )

    combined = combined[
        [
            "country",
            "year",
            "value",
            "indicator",
        ]
    ]

    combined["year"] = pd.to_numeric(
        combined["year"],
        errors="coerce",
    )

    combined = combined[
        combined["year"].between(
            START_YEAR,
            END_YEAR,
        )
    ]

    combined = combined.sort_values(
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

    combined.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        "Resilience download completed."
    )

    print(
        f"Rows: {len(combined)}"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print()
    print(
        combined.head(15)
    )


if __name__ == "__main__":
    main()
