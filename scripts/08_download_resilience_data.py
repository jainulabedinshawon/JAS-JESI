"""
JAS-JESI Real Data Pipeline
Step 1: Download Resilience Pillar Data

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

Resilience indicators:

1. Total Reserves in Months of Imports
   World Bank: FI.RES.TOTL.MO

2. Central Government Debt (% of GDP)
   World Bank: GC.DOD.TOTL.GD.ZS

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


RESILIENCE_INDICATORS = [
    "FI.RES.TOTL.MO",
    "GC.DOD.TOTL.GD.ZS",
    "BN.CAB.XOKA.GD.ZS",
]


START_YEAR = 2015
END_YEAR = 2024


OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = (
    OUTPUT_DIR / "resilience_indicators_2015_2024.csv"
)


def main():
    print("Downloading JESI Resilience pillar data...")
    print(f"Countries: {COUNTRIES}")
    print(f"Years: {START_YEAR}-{END_YEAR}")

    data = download_country_indicators(
        countries=COUNTRIES,
        indicators=RESILIENCE_INDICATORS,
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
    print("Resilience download completed.")
    print(f"Rows: {len(data)}")
    print(f"Saved to: {OUTPUT_FILE}")
    print()
    print(data.head(10))


if __name__ == "__main__":
    main()
