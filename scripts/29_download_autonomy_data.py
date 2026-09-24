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

Important:
    Missing World Bank observations are NOT replaced with zero,
    interpolation, or fabricated values.
"""

from pathlib import Path
import time

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

YEARS = set(range(START_YEAR, END_YEAR + 1))

ATLAS_URL = (
    "https://atlas.hks.harvard.edu/api/graphql"
)

WORLD_BANK_URL = (
    "https://api.worldbank.org/v2/country/"
    "{country}/indicator/TX.VAL.TECH.MF.ZS"
    "?format=json&per_page=100"
)

REQUEST_TIMEOUT = (30, 120)
MAX_RETRIES = 4
BACKOFF_SECONDS = 3

EXPECTED_ROWS = len(COUNTRIES) * len(YEARS)


def request_with_retry(
    method,
    url,
    **kwargs,
):
    """
    Execute an HTTP request with retry handling.

    Retries:
        - timeouts
        - connection errors
        - HTTP 429
        - HTTP 500/502/503/504
    """

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.request(
                method,
                url,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )

            if response.status_code in {
                429,
                500,
                502,
                503,
                504,
            }:
                raise requests.HTTPError(
                    "Retryable HTTP status "
                    f"{response.status_code}",
                    response=response,
                )

            response.raise_for_status()

            return response

        except (
            requests.Timeout,
            requests.ConnectionError,
            requests.HTTPError,
        ) as error:
            last_error = error

            if attempt == MAX_RETRIES:
                break

            wait_seconds = (
                BACKOFF_SECONDS * (2 ** (attempt - 1))
            )

            print(
                f"Request attempt {attempt}/"
                f"{MAX_RETRIES} failed."
            )

            print(
                f"Retrying in {wait_seconds} seconds..."
            )

            time.sleep(wait_seconds)

    raise RuntimeError(
        "HTTP request failed after "
        f"{MAX_RETRIES} attempts: {url}"
    ) from last_error


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
        print(
            f"Downloading ECI: "
            f"{info['name']}"
        )

        country_query = query.replace(
            "countryId: 50",
            f"countryId: {info['atlas_id']}",
        )

        response = request_with_retry(
            "POST",
            ATLAS_URL,
            json={"query": country_query},
        )

        payload = response.json()

        if "errors" in payload:
            raise RuntimeError(
                f"Atlas API error for "
                f"{info['name']}: "
                f"{payload['errors']}"
            )

        data_block = payload.get("data")

        if not data_block:
            raise RuntimeError(
                f"Atlas API returned no data for "
                f"{info['name']}."
            )

        rows = data_block.get(
            "countryYear"
        )

        if rows is None:
            raise RuntimeError(
                f"Atlas API returned no "
                f"countryYear data for "
                f"{info['name']}."
            )

        for row in rows:
            year = int(row["year"])

            if START_YEAR <= year <= END_YEAR:
                records.append(
                    {
                        "country_code": code,
                        "country": info["name"],
                        "year": year,
                        "eci": row["eci"],
                    }
                )

    data = pd.DataFrame(records)

    if data.empty:
        raise ValueError(
            "No ECI observations were downloaded."
        )

    return data


def download_high_tech():
    """
    Download high-tech exports from World Bank WDI.

    Missing World Bank values remain missing.
    They are never converted to zero.
    """

    records = []

    for code, info in COUNTRIES.items():
        print(
            f"Downloading high-tech exports: "
            f"{info['name']}"
        )

        url = WORLD_BANK_URL.format(
            country=code
        )

        response = request_with_retry(
            "GET",
            url,
        )

        payload = response.json()

        if not isinstance(payload, list):
            raise ValueError(
                "Unexpected World Bank API "
                f"response for {code}."
            )

        if len(payload) < 2:
            raise ValueError(
                "World Bank API returned no "
                f"data block for {code}."
            )

        rows = payload[1]

        if rows is None:
            print(
                f"WARNING: World Bank returned "
                f"no observations for {code}."
            )
            rows = []

        for row in rows:
            if row.get("date") is None:
                continue

            year = int(row["date"])

            if START_YEAR <= year <= END_YEAR:
                records.append(
                    {
                        "country_code": code,
                        "country": info["name"],
                        "year": year,
                        "high_tech_exports": row.get(
                            "value"
                        ),
                    }
                )

    data = pd.DataFrame(records)

    if data.empty:
        raise ValueError(
            "No high-tech export observations "
            "were downloaded from World Bank."
        )

    return data


def build_complete_country_year_grid():
    """Create the complete JESI country-year grid."""

    rows = []

    for code, info in COUNTRIES.items():
        for year in sorted(YEARS):
            rows.append(
                {
                    "country_code": code,
                    "country": info["name"],
                    "year": year,
                }
            )

    return pd.DataFrame(rows)


def validate_eci(data):
    """Validate ECI coverage."""

    expected_keys = {
        (code, year)
        for code in COUNTRIES
        for year in YEARS
    }

    actual_keys = set(
        zip(
            data["country_code"],
            data["year"],
        )
    )

    missing_keys = sorted(
        expected_keys - actual_keys
    )

    if missing_keys:
        print()
        print(
            "WARNING: Missing ECI observations:"
        )

        for code, year in missing_keys:
            print(
                f"  {code} {year}"
            )

        raise ValueError(
            "ECI data is incomplete. "
            f"Missing {len(missing_keys)} "
            "country-year observations."
        )

    if data.duplicated(
        ["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate ECI country-year "
            "observations detected."
        )

    print(
        "ECI coverage validation: GREEN"
    )


def report_high_tech_missing(data):
    """
    Report missing high-tech observations.

    Missing observations are retained as NA.
    """

    expected_grid = (
        build_complete_country_year_grid()
    )

    merged = expected_grid.merge(
        data,
        on=[
            "country_code",
            "country",
            "year",
        ],
        how="left",
    )

    merged["high_tech_exports"] = pd.to_numeric(
        merged["high_tech_exports"],
        errors="coerce",
    )

    missing = merged[
        merged["high_tech_exports"].isna()
    ].copy()

    print()
    print(
        "High-tech export coverage:"
    )

    print(
        f"Expected observations: "
        f"{EXPECTED_ROWS}"
    )

    print(
        f"Available observations: "
        f"{EXPECTED_ROWS - len(missing)}"
    )

    print(
        f"Missing observations: "
        f"{len(missing)}"
    )

    if not missing.empty:
        print()
        print(
            "Missing World Bank "
            "high-tech observations:"
        )

        for _, row in missing.iterrows():
            print(
                f"  {row['country_code']} "
                f"{int(row['year'])} "
                f"({row['country']})"
            )

        print()
        print(
            "IMPORTANT: Missing values are "
            "retained as NA."
        )

        print(
            "No zero, interpolation, or "
            "proxy value has been inserted."
        )

    return merged


def validate_high_tech_duplicates(data):
    """Check for duplicate World Bank observations."""

    if data.duplicated(
        ["country_code", "year"]
    ).any():
        duplicates = data[
            data.duplicated(
                ["country_code", "year"],
                keep=False,
            )
        ]

        print()
        print(
            "Duplicate high-tech observations:"
        )

        print(
            duplicates[
                [
                    "country_code",
                    "year",
                    "high_tech_exports",
                ]
            ].to_string(index=False)
        )

        raise ValueError(
            "Duplicate high-tech "
            "country-year observations "
            "detected."
        )


def main():
    """Download and prepare Strategic Autonomy data."""

    print("=" * 72)
    print(
        "JESI STRATEGIC AUTONOMY DATA DOWNLOAD"
    )
    print("=" * 72)

    print()
    print(
        "Period:",
        f"{START_YEAR}-{END_YEAR}",
    )

    print(
        "Countries:",
        len(COUNTRIES),
    )

    print(
        "Expected country-year rows:",
        EXPECTED_ROWS,
    )

    print()
    print(
        "Downloading Economic Complexity "
        "Index (ECI)..."
    )

    eci = download_eci()

    print()
    print(
        f"ECI rows downloaded: {len(eci)}"
    )

    validate_eci(eci)

    print()
    print(
        "Downloading high-technology "
        "exports from World Bank..."
    )

    high_tech = download_high_tech()

    print()
    print(
        f"World Bank rows downloaded: "
        f"{len(high_tech)}"
    )

    validate_high_tech_duplicates(
        high_tech
    )

    high_tech = report_high_tech_missing(
        high_tech
    )

    print()
    print(
        "Building complete country-year "
        "autonomy grid..."
    )

    grid = build_complete_country_year_grid()

    data = grid.merge(
        eci,
        on=[
            "country_code",
            "country",
            "year",
        ],
        how="left",
        validate="one_to_one",
    )

    data = data.merge(
        high_tech[
            [
                "country_code",
                "country",
                "year",
                "high_tech_exports",
            ]
        ],
        on=[
            "country_code",
            "country",
            "year",
        ],
        how="left",
        validate="one_to_one",
    )

    # Import concentration is intentionally kept
    # as a separate field for official UNCTAD
    # dataset integration in Script 30.
    #
    # It is not fabricated or replaced by
    # an arbitrary proxy.
    data[
        "import_product_concentration"
    ] = pd.NA

    data["year"] = data["year"].astype(int)

    data = data.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(
        drop=True
    )

    if len(data) != EXPECTED_ROWS:
        raise ValueError(
            "Final autonomy dataset has "
            f"{len(data)} rows; expected "
            f"{EXPECTED_ROWS}."
        )

    if data.duplicated(
        ["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations "
            "found in final autonomy dataset."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    missing_high_tech = int(
        data[
            "high_tech_exports"
        ].isna().sum()
    )

    print()
    print(
        "Strategic Autonomy data download "
        "completed."
    )

    print(
        f"Rows: {len(data)}"
    )

    print(
        f"Countries: "
        f"{data['country_code'].nunique()}"
    )

    print(
        f"Years: "
        f"{data['year'].nunique()}"
    )

    print(
        f"High-tech missing observations: "
        f"{missing_high_tech}"
    )

    print(
        "UNCTAD import concentration "
        "field: reserved for Script 30."
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print()
    print("=" * 72)
    print(
        "STATUS: DOWNLOAD COMPLETED"
    )
    print(
        "Official source values were preserved."
    )
    print(
        "Missing observations were not fabricated."
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
