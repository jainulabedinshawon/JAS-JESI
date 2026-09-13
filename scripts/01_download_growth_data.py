"""
JAS-JESI Real Data Pipeline
Step 1: Download Growth Pillar Data

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This script downloads real World Bank data for the
Growth (G) pillar.

Growth indicators:
    1. Real GDP Growth Rate
    2. GNI per Capita Growth

Countries:
    Bangladesh
    India
    Vietnam
    Indonesia
    Malaysia

Period:
    2015–2025
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


GROWTH_INDICATORS = [
    "NY.GDP.MKTP.KD.ZG",
    "NY.GNP.PCAP.KD.ZG",
]


START_YEAR = 2015
END_YEAR = 2025


OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "growth_indicators_2015_2025.csv"


def main():
    """
    Download and save real World Bank Growth pillar data.
    """

    print("Downloading JESI Growth pillar data...")
    print(f"Countries: {COUNTRIES}")
    print(f"Years: {START_YEAR}-{END_YEAR}")

    data = download_country_indicators(
        countries=COUNTRIES,
        indicators=GROWTH_INDICATORS,
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
    print("Download completed.")
    print(f"Rows: {len(data)}")
    print(f"Saved to: {OUTPUT_FILE}")
    print()
    print(data.head(10))


if __name__ == "__main__":
    main()
