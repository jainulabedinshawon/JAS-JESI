"""
JESI Strategic Autonomy Data Download
JAS Unified Economic Strength Index (JESI)

Script 29:
Download Strategic Autonomy indicators.

Indicators:
    1. Economic Complexity Index (ECI)
    2. High-technology exports (% of manufactured exports)
    3. Import product concentration index

Period:
    2015-2024

Countries:
    Bangladesh, India, Viet Nam, Indonesia, Malaysia
"""

from pathlib import Path

import pandas as pd
import requests


OUTPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024.csv"
)

COUNTRIES = {
    "BGD": {"name": "Bangladesh", "atlas_id": 50},
    "IND": {"name": "India", "atlas_id": 356},
    "VNM": {"name": "Viet Nam", "atlas_id": 704},
    "IDN": {"name": "Indonesia", "atlas_id": 360},
    "MYS": {"name": "Malaysia", "atlas_id": 458},
}

START_YEAR = 2015
END_YEAR = 2024

ATLAS_URL = (
    "https://atlas.hks.harvard.edu/api/graphql"
)

WORLD_BANK_URL = (
    "https://api.worldbank.org/v2/country/"
    "{country}/indicator/TX.VAL.TECH.MF.ZS"
    "?format=json&per_page=100"
)


def download_eci():
    """Download ECI from Harvard Atlas GraphQL API."""

    query = """
    query {
      countryYear(
        countryId: 50
        yearMin: 2015
        yearMax: 2024
      ) {
        year
        eci
      }
    }
    """

    records = []

    for code, info in COUNTRIES.items():
        country_query = query.replace(
            "countryId: 50",
            f"countryId: {info['atlas_id']}",
        )

        response = requests.post(
            ATLAS_URL,
            json={"query": country_query},
            timeout=60,
        )

        response.raise_for_status()

        payload = response.json()

        if "errors" in payload:
            raise RuntimeError(
                f"Atlas API error for {info['name']}: "
                f"{payload['errors']}"
            )

        rows = payload["data"]["countryYear"]

        for row in rows:
            records.append(
                {
                    "country_code": code,
                    "country": info["name"],
                    "year": row["year"],
                    "eci": row["eci"],
                }
            )

    return pd.DataFrame(records)


def download_high_tech():
    """Download high-tech exports from World Bank WDI."""

    records = []

    for code, info in COUNTRIES.items():
        url = WORLD_BANK_URL.format(
            country=code
        )

        response = requests.get(
            url,
            timeout=60,
        )

        response.raise_for_status()

        payload = response.json()

        if len(payload) < 2 or payload[1] is None:
            continue

        for row in payload[1]:
            year = int(row["date"])

            if START_YEAR <= year <= END_YEAR:
                records.append(
                    {
                        "country_code": code,
                        "country": info["name"],
                        "year": year,
                        "high_tech_exports": row[
                            "value"
                        ],
                    }
                )

    return pd.DataFrame(records)


def main():
    """Download Strategic Autonomy data."""

    eci = download_eci()

    high_tech = download_high_tech()

    data = eci.merge(
        high_tech,
        on=[
            "country_code",
            "country",
            "year",
        ],
        how="outer",
    )

    # Import concentration is intentionally kept as a
    # separate field for the UNCTAD official dataset.
    #
    # It is not fabricated or replaced by an arbitrary proxy.
    data["import_product_concentration"] = pd.NA

    data = data.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "Strategic Autonomy data download completed "
        "for ECI and high-tech exports."
    )

    print(
        "UNCTAD import concentration field is reserved "
        "for official dataset integration in the next step."
    )

    print(f"Rows: {len(data)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
