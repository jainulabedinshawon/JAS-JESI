"""
JAS-JESI Real Data Pipeline
Step 1: Download Connectivity Pillar Data

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

Connectivity indicators:

1. Trade Openness
   World Bank: NE.TRD.GNFS.ZS

2. FDI Net Inflows (% of GDP)
   World Bank: BX.KLT.DINV.WD.GD.ZS

3. Individuals Using Internet (% of population)
   World Bank: IT.NET.USER.ZS

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

from src.data_download import download_country_indicators


COUNTRIES = [
    "BGD",
    "IND",
    "VNM",
    "IDN",
    "MYS",
]


CONNECTIVITY_INDICATORS = [
    "NE.TRD.GNFS.ZS",
    "BX.KLT.DINV.WD.GD.ZS",
    "IT.NET.USER.ZS",
]


START_YEAR = 2015
END_YEAR = 2024


OUTPUT_DIR = Path("data/raw")

OUTPUT_FILE = (
    OUTPUT_DIR
    / "connectivity_indicators_2015_2024.csv"
)


def main():
    """
    Download real World Bank Connectivity data.
    """

    print(
        "Downloading JESI Connectivity pillar data..."
    )

    print(
        f"Countries: {COUNTRIES}"
    )

    print(
        f"Years: {START_YEAR}-{END_YEAR}"
    )

    data = download_country_indicators(
        countries=COUNTRIES,
        indicators=CONNECTIVITY_INDICATORS,
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
        "Connectivity download completed."
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
