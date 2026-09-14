"""
JAS-JESI Real Data Pipeline
Step 1: Download Productivity Pillar Data

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

Productivity indicators:

1. GDP per Person Employed
   Source: World Bank
   Indicator: SL.GDP.PCAP.EM.KD

2. Total Factor Productivity
   Source: Penn World Table 11.0
   Variable: ctfp

Countries:
    Bangladesh
    India
    Vietnam
    Indonesia
    Malaysia

Period:
    2015–2023

Note:
    PWT 11.0 currently covers data through 2023.
"""

from pathlib import Path

import pandas as pd

from src.data_download import download_productivity_data


COUNTRIES = [
    "BGD",
    "IND",
    "VNM",
    "IDN",
    "MYS",
]


START_YEAR = 2015
END_YEAR = 2023


OUTPUT_DIR = Path("data/raw")

OUTPUT_FILE = (
    OUTPUT_DIR
    / "productivity_world_bank_2015_2023.csv"
)


def main():
    """
    Download World Bank GDP per person employed data.
    """

    print(
        "Downloading JESI Productivity data..."
    )

    print(
        f"Countries: {COUNTRIES}"
    )

    print(
        f"Years: {START_YEAR}-{END_YEAR}"
    )

    data = download_productivity_data(
        countries=COUNTRIES,
        start_year=START_YEAR,
        end_year=END_YEAR,
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
        "World Bank Productivity download completed."
    )

    print(
        f"Rows: {len(data)}"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print()
    print(
        data.head(10)
    )


if __name__ == "__main__":
    main()
