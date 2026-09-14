"""
JAS-JESI Resilience Data Pipeline

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

Resilience indicators:
    1. FX Reserves / Import Cover
       Source: World Bank

    2. General Government Gross Debt (% GDP)
       Source: IMF WEO / DataMapper API

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

IMF_DATAMAPPER_API = (
    "https://www.imf.org/external/datamapper/api/v2"
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


OUTPUT_DIR = Path("data/raw")

OUTPUT_FILE = (
    OUTPUT_DIR
    / "resilience_indicators_2015_2024.csv"
)


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


def download_imf_debt_data():
    """
    Download General Government Gross Debt
    (% GDP) from the IMF DataMapper API.

    IMF WEO indicator:
        GGXWDG_NGDP
    """

    print(
        "IMF source: DataMapper API"
    )

    print(
        f"IMF indicator: {IMF_DEBT_INDICATOR}"
    )

    periods = ",".join(
        str(year)
        for year in range(
            START_YEAR,
            END_YEAR + 1,
        )
    )

    records = []

    for country_code in COUNTRIES:

        url = (
            f"{IMF_DATAMAPPER_API}/"
            f"{IMF_DEBT_INDICATOR}/"
            f"{country_code}"
        )

        params = {
            "periods": periods,
        }

        response = requests.get(
            url,
            params=params,
            timeout=30,
            headers={
                "User-Agent": (
                    "JAS-JESI/1.0 "
                    "(research data pipeline)"
                )
            },
        )

        response.raise_for_status()

        data = response.json()

        values = (
            data
            .get("values", {})
            .get(IMF_DEBT_INDICATOR, {})
            .get(country_code, {})
        )

        for year in range(
            START_YEAR,
            END_YEAR + 1,
        ):
            value = values.get(
                str(year)
            )

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

    print()
    print(
        "Downloading IMF WEO debt data..."
    )

    imf_debt = (
        download_imf_debt_data()
    )

    print(
        f"IMF debt rows: {len(imf_debt)}"
    )

    records.extend(imf_debt)

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
    ).reset_index(drop=True)

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
