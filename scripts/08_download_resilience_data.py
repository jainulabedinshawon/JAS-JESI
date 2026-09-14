"""
JAS-JESI Resilience Data Pipeline

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

Resilience indicators:
    1. FX Reserves / Import Cover
       Source: World Bank
    2. General Government Gross Debt (% GDP)
       Source: IMF World Economic Outlook (WEO)
    3. Current Account Balance (% GDP)
       Source: World Bank

Period:
    2015–2024

IMF WEO vintage:
    April 2026
"""

from pathlib import Path

import pandas as pd

from src.data_download import download_country_indicators


COUNTRIES = [
    "BGD",
    "IND",
    "VNM",
    "IDN",
    "MYS",
]


WORLD_BANK_INDICATORS = [
    "FI.RES.TOTL.MO",
    "BN.CAB.XOKA.GD.ZS",
]


START_YEAR = 2015
END_YEAR = 2024


OUTPUT_DIR = Path("data/raw")

OUTPUT_FILE = (
    OUTPUT_DIR
    / "resilience_indicators_2015_2024.csv"
)


# Official IMF April 2026 WEO Excel dataset.
IMF_WEO_URL = (
    "https://data.imf.org/-/media/iData/"
    "External-Storage/Documents/"
    "2F78EE59F79143A7921E5E203D3AAA80/"
    "en/WEOApr2026all.xlsx"
)


IMF_DEBT_INDICATOR = (
    "GGXWDG_NGDP"
)


COUNTRY_NAMES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}


def download_world_bank_data():
    """Download World Bank resilience indicators."""

    print("Downloading World Bank indicators...")

    data = download_country_indicators(
        countries=COUNTRIES,
        indicators=WORLD_BANK_INDICATORS,
        start_year=START_YEAR,
        end_year=END_YEAR,
    )

    return data


def download_imf_debt_data():
    """
    Download General Government Gross Debt (% GDP)
    from the official IMF April 2026 WEO Excel dataset.
    """

    print("Downloading IMF WEO debt data...")
    print("IMF vintage: April 2026")

    data = pd.read_excel(
        IMF_WEO_URL,
        sheet_name="Countries",
    )

    required_columns = [
        "Country",
        "ISO",
        "Subject Descriptor",
        "Units",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing IMF columns: "
            f"{missing_columns}"
        )

    debt = data[
        data["ISO"].isin(COUNTRIES)
    ].copy()

    debt = debt[
        debt["Subject Descriptor"].str.contains(
            "Gross debt",
            case=False,
            na=False,
        )
    ]

    debt = debt[
        debt["Units"].str.contains(
            "Percent of GDP",
            case=False,
            na=False,
        )
    ]

    if debt.empty:
        raise ValueError(
            "IMF gross-debt series could not be found."
        )

    year_columns = [
        str(year)
        for year in range(
            START_YEAR,
            END_YEAR + 1,
        )
        if str(year) in debt.columns
    ]

    if not year_columns:
        raise ValueError(
            "No requested IMF year columns found."
        )

    debt = debt[
        [
            "ISO",
            "Country",
            *year_columns,
        ]
    ]

    debt = debt.melt(
        id_vars=[
            "ISO",
            "Country",
        ],
        value_vars=year_columns,
        var_name="year",
        value_name="value",
    )

    debt["year"] = debt["year"].astype(int)

    debt["country"] = debt["ISO"].map(
        COUNTRY_NAMES
    )

    debt["indicator"] = IMF_DEBT_INDICATOR

    debt = debt[
        [
            "country",
            "year",
            "value",
            "indicator",
        ]
    ]

    debt["value"] = pd.to_numeric(
        debt["value"],
        errors="coerce",
    )

    return debt


def main():
    print(
        "Downloading JESI Resilience pillar data..."
    )
    print(f"Countries: {COUNTRIES}")
    print(
        f"Years: {START_YEAR}-{END_YEAR}"
    )
    print()

    world_bank = download_world_bank_data()

    print(
        f"World Bank rows: {len(world_bank)}"
    )
    print()

    imf_debt = download_imf_debt_data()

    print(
        f"IMF debt rows: {len(imf_debt)}"
    )
    print()

    data = pd.concat(
        [
            world_bank,
            imf_debt,
        ],
        ignore_index=True,
    )

    data = data.sort_values(
        [
            "country",
            "year",
            "indicator",
        ]
    ).reset_index(drop=True)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        OUTPUT_FILE,
        index=False,
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
    print()
    print(data.head(15))


if __name__ == "__main__":
    main()
