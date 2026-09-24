"""
Download and inspect UNCTAD merchandise product concentration data.

This script intentionally stops if the downloaded UNCTAD table does not
contain individual-economy observations for the JESI target countries.

JESI target countries:
BGD, IND, VNM, IDN, MYS

Required years:
2015-2024
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pandas as pd
import requests


UNCTAD_URL = (
    "https://unctadstat-api.unctad.org/"
    "bulkdownload/US.ConcentDiversIndices/"
    "US_ConcentDiversIndices"
)

OUTPUT = Path(
    "data/raw/import_product_concentration_2015_2024.csv"
)

TARGET_COUNTRIES = {
    "Bangladesh": "BGD",
    "India": "IND",
    "Viet Nam": "VNM",
    "Vietnam": "VNM",
    "Indonesia": "IDN",
    "Malaysia": "MYS",
}

TARGET_YEARS = set(range(2015, 2025))


def normalize_text(value: object) -> str:
    """Normalize text for safe country-name matching."""
    if pd.isna(value):
        return ""

    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def download_unctad() -> bytes:
    """Download the official UNCTAD bulk file."""
    response = requests.get(
        UNCTAD_URL,
        timeout=120,
    )
    response.raise_for_status()

    print(f"UNCTAD download received: {len(response.content):,} bytes")

    return response.content


def read_unctad_archive(content: bytes) -> pd.DataFrame:
    """Read the CSV contained in the UNCTAD archive."""
    archive = zipfile.ZipFile(io.BytesIO(content))

    names = archive.namelist()

    print("Files inside UNCTAD archive:")
    for name in names:
        print(f"  - {name}")

    csv_files = [
        name for name in names
        if name.lower().endswith(".csv")
    ]

    if not csv_files:
        raise ValueError(
            "No CSV file was found inside the UNCTAD archive."
        )

    csv_name = csv_files[0]

    print(f"Selected UNCTAD data file: {csv_name}")

    raw = archive.read(csv_name)

    encodings = [
        "utf-8-sig",
        "utf-8",
        "latin1",
    ]

    last_error = None

    for encoding in encodings:
        try:
            text = raw.decode(encoding)
            print(f"Detected encoding: {encoding}")
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:
        raise ValueError(
            "Could not decode UNCTAD CSV."
        ) from last_error

    df = pd.read_csv(
        io.StringIO(text),
        sep=",",
    )

    print(f"UNCTAD raw rows: {len(df)}")
    print(f"UNCTAD raw columns: {len(df.columns)}")

    print("UNCTAD columns:")
    for column in df.columns:
        print(f"  - {column}")

    return df


def find_economy_column(df: pd.DataFrame) -> str | None:
    """Find the economy-name column."""
    candidates = [
        "Economy",
        "Economy_Label",
        "Economy label",
        "economy",
        "economy_label",
    ]

    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    for column in df.columns:
        normalized = normalize_text(column)

        if normalized in {
            "economy",
            "economy label",
            "economy_label",
        }:
            return column

    return None


def find_concentration_columns(
    df: pd.DataFrame,
) -> dict[int, str]:
    """Find annual concentration-index columns."""
    result: dict[int, str] = {}

    pattern = re.compile(
        r"^(\d{4})_Concentration_Index_Value$",
        re.IGNORECASE,
    )

    for column in df.columns:
        match = pattern.match(str(column))

        if match:
            year = int(match.group(1))
            result[year] = column

    return result


def find_target_rows(
    df: pd.DataFrame,
    economy_column: str,
) -> pd.DataFrame:
    """Find individual target-country rows."""
    normalized_targets = {
        normalize_text(country): code
        for country, code in TARGET_COUNTRIES.items()
    }

    temp = df.copy()

    temp["_normalized_economy"] = (
        temp[economy_column].map(normalize_text)
    )

    temp["country_code"] = (
        temp["_normalized_economy"].map(normalized_targets)
    )

    return temp[temp["country_code"].notna()].copy()


def main() -> None:
    print("Downloading official UNCTAD concentration dataset...")
    content = download_unctad()

    df = read_unctad_archive(content)

    economy_column = find_economy_column(df)

    if economy_column is None:
        raise ValueError(
            "Could not identify the UNCTAD economy column."
        )

    print(f"Detected economy column: {economy_column}")

    concentration_columns = find_concentration_columns(df)

    print(
        "Detected concentration years:",
        sorted(concentration_columns),
    )

    target_rows = find_target_rows(
        df,
        economy_column,
    )

    print(
        "Target-country rows found:",
        len(target_rows),
    )

    if len(target_rows) == 0:
        print()
        print("STATUS: BLOCKED")
        print()
        print(
            "The downloaded UNCTAD bulk table contains no "
            "individual rows for:"
        )

        for country, code in TARGET_COUNTRIES.items():
            print(f"  {code}: {country}")

        print()
        print(
            "This means the current UNCTAD bulk file is an "
            "aggregate/group table, not the individual-economy "
            "extract required by JESI."
        )

        print()
        print(
            "No fabricated country values will be created."
        )

        raise ValueError(
            "UNCTAD individual-economy concentration data "
            "is not present in the downloaded table."
        )

    missing_years = [
        year
        for year in sorted(TARGET_YEARS)
        if year not in concentration_columns
    ]

    if missing_years:
        raise ValueError(
            "Missing required UNCTAD years: "
            f"{missing_years}"
        )

    rows = []

    for _, row in target_rows.iterrows():
        country_code = row["country_code"]

        country_name = next(
            (
                country
                for country, code in TARGET_COUNTRIES.items()
                if code == country_code
            ),
            str(row[economy_column]),
        )

        for year in sorted(TARGET_YEARS):
            value_column = concentration_columns[year]

            value = pd.to_numeric(
                row[value_column],
                errors="coerce",
            )

            rows.append(
                {
                    "country": country_name,
                    "country_code": country_code,
                    "year": year,
                    "import_product_concentration": value,
                }
            )

    output = pd.DataFrame(rows)

    output = output.sort_values(
        ["country_code", "year"]
    ).reset_index(drop=True)

    expected_rows = 5 * 10

    if len(output) != expected_rows:
        raise ValueError(
            "Unexpected number of country-year observations: "
            f"{len(output)}; expected {expected_rows}."
        )

    missing = output[
        "import_product_concentration"
    ].isna().sum()

    print()
    print(
        "Missing concentration observations:",
        int(missing),
    )

    if missing:
        raise ValueError(
            "UNCTAD concentration data contains missing "
            f"observations: {missing}"
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT,
        index=False,
    )

    print()
    print(f"Saved: {OUTPUT}")
    print(f"Rows: {len(output)}")
    print("STATUS: SUCCESS")


if __name__ == "__main__":
    main()
