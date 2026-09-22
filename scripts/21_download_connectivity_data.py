"""
JESI Connectivity Pillar
Real-data download pipeline.

Indicators:
1. Trade Openness
2. FDI Inflows (% of GDP)
3. Internet Use (% of population)

Countries:
Bangladesh, India, Viet Nam, Indonesia, Malaysia

Period:
2015-2024
"""

from pathlib import Path

import pandas as pd
import requests


COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}

START_YEAR = 2015
END_YEAR = 2024

OUTPUT_FILE = Path(
    "data/raw/connectivity_indicators_2015_2024.csv"
)

WORLD_BANK_URL = (
    "https://api.worldbank.org/v2/country/"
    "{country}/indicator/{indicator}"
    "?format=json&per_page=100"
)

INDICATORS = {
    "fdi_inflows": "BX.KLT.DINV.WD.GD.ZS",
    "internet_use": "IT.NET.USER.ZS",
}


def download_world_bank_indicator(
    country_code,
    indicator,
):
    """Download one World Bank indicator."""

    url = WORLD_BANK_URL.format(
        country=country_code,
        indicator=indicator,
    )

    response = requests.get(
        url,
        timeout=120,
    )

    response.raise_for_status()

    payload = response.json()

    if len(payload) < 2:
        raise ValueError(
            f"No World Bank data returned for "
            f"{country_code} / {indicator}."
        )

    rows = payload[1]

    records = []

    for row in rows:
        year = int(row["date"])

        if START_YEAR <= year <= END_YEAR:
            records.append(
                {
                    "country_code": country_code,
                    "country": COUNTRIES[country_code],
                    "year": year,
                    "value": row["value"],
                }
            )

    return pd.DataFrame(records)


def download_trade_openness(country_code):
    """Download exports and imports and calculate trade openness."""

    exports = download_world_bank_indicator(
        country_code,
        "NE.EXP.GNFS.ZS",
    )

    imports = download_world_bank_indicator(
        country_code,
        "NE.IMP.GNFS.ZS",
    )

    exports = exports.rename(
        columns={
            "value": "exports_pct_gdp"
        }
    )

    imports = imports.rename(
        columns={
            "value": "imports_pct_gdp"
        }
    )

    # Merge using the stable identifiers only.
    # Country name is restored from the fixed country mapping.
    merged = pd.merge(
        exports[
            [
                "country_code",
                "year",
                "exports_pct_gdp",
            ]
        ],
        imports[
            [
                "country_code",
                "year",
                "imports_pct_gdp",
            ]
        ],
        on=[
            "country_code",
            "year",
        ],
        how="outer",
        validate="one_to_one",
    )

    merged["country"] = merged[
        "country_code"
    ].map(COUNTRIES)

    merged["trade_openness"] = (
        merged["exports_pct_gdp"]
        + merged["imports_pct_gdp"]
    )

    return merged[
        [
            "country_code",
            "country",
            "year",
            "trade_openness",
        ]
    ]


def main():
    print("=" * 72)
    print("JESI CONNECTIVITY DATA DOWNLOAD")
    print("=" * 72)

    all_records = []

    for country_code in COUNTRIES:

        print(
            f"Downloading Connectivity data: "
            f"{COUNTRIES[country_code]}"
        )

        # ----------------------------------------------------------
        # Trade openness
        # ----------------------------------------------------------

        trade = download_trade_openness(
            country_code
        )

        # ----------------------------------------------------------
        # FDI
        # ----------------------------------------------------------

        fdi = download_world_bank_indicator(
            country_code,
            INDICATORS["fdi_inflows"],
        )

        fdi = fdi[
            [
                "country_code",
                "year",
                "value",
            ]
        ].rename(
            columns={
                "value": "fdi_inflows"
            }
        )

        # ----------------------------------------------------------
        # Internet use
        # ----------------------------------------------------------

        internet = download_world_bank_indicator(
            country_code,
            INDICATORS["internet_use"],
        )

        internet = internet[
            [
                "country_code",
                "year",
                "value",
            ]
        ].rename(
            columns={
                "value": "internet_use"
            }
        )

        # ----------------------------------------------------------
        # Merge Connectivity indicators
        # ----------------------------------------------------------

        country_data = trade.merge(
            fdi,
            on=[
                "country_code",
                "year",
            ],
            how="outer",
            validate="one_to_one",
        )

        country_data = country_data.merge(
            internet,
            on=[
                "country_code",
                "year",
            ],
            how="outer",
            validate="one_to_one",
        )

        country_data["country"] = (
            country_data["country_code"]
            .map(COUNTRIES)
        )

        all_records.append(
            country_data
        )

    # ------------------------------------------------------------------
    # Combine all countries
    # ------------------------------------------------------------------

    dataframe = pd.concat(
        all_records,
        ignore_index=True,
    )

    dataframe = dataframe[
        [
            "country_code",
            "country",
            "year",
            "trade_openness",
            "fdi_inflows",
            "internet_use",
        ]
    ]

    dataframe = dataframe.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)

    # ------------------------------------------------------------------
    # Structural validation
    # ------------------------------------------------------------------

    expected_rows = (
        len(COUNTRIES)
        * (END_YEAR - START_YEAR + 1)
    )

    if len(dataframe) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, "
            f"found {len(dataframe)}."
        )

    expected_codes = set(COUNTRIES.keys())

    actual_codes = set(
        dataframe["country_code"].unique()
    )

    if actual_codes != expected_codes:
        raise ValueError(
            "Unexpected country codes. "
            f"Expected {sorted(expected_codes)}, "
            f"found {sorted(actual_codes)}."
        )

    duplicates = dataframe.duplicated(
        subset=[
            "country_code",
            "year",
        ],
        keep=False,
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate country-year observations found."
        )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        f"Rows: {len(dataframe)}"
    )

    print(
        f"Saved: {OUTPUT_FILE}"
    )

    print()
    print(
        "JESI Connectivity data download "
        "completed successfully."
    )


if __name__ == "__main__":
    main()
