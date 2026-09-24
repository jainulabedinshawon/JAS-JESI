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
import time

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
)

INDICATORS = {
    "fdi_inflows": "BX.KLT.DINV.WD.GD.ZS",
    "internet_use": "IT.NET.USER.ZS",
}

REQUEST_TIMEOUT = (30, 120)
MAX_RETRIES = 4
BACKOFF_SECONDS = 3


def download_world_bank_indicator(
    country_code,
    indicator,
):
    """Download one World Bank indicator with retry handling."""

    url = WORLD_BANK_URL.format(
        country=country_code,
        indicator=indicator,
    )

    params = {
        "format": "json",
        "per_page": 100,
        "date": f"{START_YEAR}:{END_YEAR}",
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(
                f"  World Bank request: "
                f"{country_code} / {indicator} "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )

            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            payload = response.json()

            if not isinstance(payload, list) or len(payload) < 2:
                raise ValueError(
                    f"Invalid World Bank response for "
                    f"{country_code} / {indicator}."
                )

            rows = payload[1]

            if not isinstance(rows, list):
                raise ValueError(
                    f"Unexpected World Bank data structure for "
                    f"{country_code} / {indicator}."
                )

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

            dataframe = pd.DataFrame(records)

            if dataframe.empty:
                raise ValueError(
                    f"No World Bank observations returned for "
                    f"{country_code} / {indicator} "
                    f"for {START_YEAR}-{END_YEAR}."
                )

            return dataframe

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as exc:
            last_error = exc

            print(
                f"  Temporary World Bank connection error: "
                f"{type(exc).__name__}"
            )

            if attempt < MAX_RETRIES:
                wait_seconds = (
                    BACKOFF_SECONDS * (2 ** (attempt - 1))
                )

                print(
                    f"  Retrying in {wait_seconds} seconds..."
                )

                time.sleep(wait_seconds)

        except requests.exceptions.HTTPError as exc:
            status_code = (
                exc.response.status_code
                if exc.response is not None
                else None
            )

            last_error = exc

            if status_code in {
                429,
                500,
                502,
                503,
                504,
            } and attempt < MAX_RETRIES:
                wait_seconds = (
                    BACKOFF_SECONDS * (2 ** (attempt - 1))
                )

                print(
                    f"  World Bank HTTP {status_code}. "
                    f"Retrying in {wait_seconds} seconds..."
                )

                time.sleep(wait_seconds)
            else:
                raise

    raise RuntimeError(
        f"World Bank request failed after "
        f"{MAX_RETRIES} attempts: "
        f"{country_code} / {indicator}"
    ) from last_error


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

    print(
        f"World Bank period requested: "
        f"{START_YEAR}-{END_YEAR}"
    )

    print(
        f"Retry policy: "
        f"{MAX_RETRIES} attempts"
    )

    print(
        f"Request timeout: "
        f"{REQUEST_TIMEOUT}"
    )

    all_records = []

    for country_code in COUNTRIES:

        print()
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
    # Complete-data validation
    # ------------------------------------------------------------------

    indicator_columns = [
        "trade_openness",
        "fdi_inflows",
        "internet_use",
    ]

    for column in indicator_columns:

        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        missing_count = int(
            dataframe[column].isna().sum()
        )

        if missing_count > 0:
            raise ValueError(
                f"{column} contains "
                f"{missing_count} missing values."
            )

        if not dataframe[column].map(
            lambda value: pd.notna(value)
        ).all():
            raise ValueError(
                f"{column} contains invalid values."
            )

    if (
        dataframe["trade_openness"] < 0
    ).any():
        raise ValueError(
            "Trade openness contains negative values."
        )

    if (
        dataframe["internet_use"] < 0
    ).any() or (
        dataframe["internet_use"] > 100
    ).any():
        raise ValueError(
            "Internet use must be between 0 and 100."
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

    # ------------------------------------------------------------------
    # Final status
    # ------------------------------------------------------------------

    print()
    print("=" * 72)
    print("CONNECTIVITY DOWNLOAD STATUS")
    print("=" * 72)

    print(
        f"Rows              : {len(dataframe)}"
    )

    print(
        f"Countries         : "
        f"{dataframe['country_code'].nunique()}"
    )

    print(
        f"Years             : "
        f"{dataframe['year'].nunique()}"
    )

    print(
        f"Year range        : "
        f"{int(dataframe['year'].min())}-"
        f"{int(dataframe['year'].max())}"
    )

    print(
        "Missing values    : 0"
    )

    print(
        "Duplicate rows    : 0"
    )

    print(
        f"Saved             : {OUTPUT_FILE}"
    )

    print()
    print(
        "STATUS: GREEN"
    )

    print(
        "JESI Connectivity data download "
        "completed successfully."
    )


if __name__ == "__main__":
    main()
