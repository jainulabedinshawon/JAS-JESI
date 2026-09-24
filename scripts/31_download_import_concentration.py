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

import csv
import io
import json
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
    """Normalize text for safe matching."""
    if pd.isna(value):
        return ""

    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)

    return text


def normalize_column_name(value: object) -> str:
    """Normalize a column name for flexible matching."""
    text = normalize_text(value)
    text = re.sub(r"[^a-z0-9]+", "_", text)

    return text.strip("_")


def download_unctad() -> tuple[bytes, str]:
    """Download the official UNCTAD bulk response."""
    response = requests.get(
        UNCTAD_URL,
        timeout=120,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        "",
    )

    print(
        "UNCTAD HTTP status:",
        response.status_code,
    )

    print(
        "UNCTAD Content-Type:",
        content_type,
    )

    print(
        "UNCTAD download received:",
        f"{len(response.content):,}",
        "bytes",
    )

    print(
        "UNCTAD final URL:",
        response.url,
    )

    return response.content, content_type


def parse_unctad_text(raw: bytes) -> pd.DataFrame:
    """Parse a text-based UNCTAD table."""
    encodings = [
        "utf-8-sig",
        "utf-8",
        "latin1",
    ]

    last_error = None

    for encoding in encodings:
        try:
            text = raw.decode(encoding)

            print(
                "Detected encoding:",
                encoding,
            )

            break

        except UnicodeDecodeError as exc:
            last_error = exc

    else:
        raise ValueError(
            "Could not decode UNCTAD text response."
        ) from last_error

    stripped = text.lstrip()

    if stripped.startswith("<"):
        preview = text[:500]

        raise ValueError(
            "UNCTAD returned markup/HTML instead of a data table. "
            f"Response preview: {preview!r}"
        )

    try:
        sample = text[:10000]

        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",\t;|",
        )

        separator = dialect.delimiter

    except csv.Error:
        separator = ","

    print(
        "Detected UNCTAD delimiter:",
        repr(separator),
    )

    df = pd.read_csv(
        io.StringIO(text),
        sep=separator,
    )

    if len(df.columns) <= 1:
        raise ValueError(
            "UNCTAD response was treated as text, but no tabular "
            "delimiter could be identified."
        )

    print(
        "UNCTAD raw rows:",
        len(df),
    )

    print(
        "UNCTAD raw columns:",
        len(df.columns),
    )

    print("UNCTAD columns:")

    for column in df.columns:
        print(
            f"  - {column}"
        )

    return df


def read_unctad_response(
    content: bytes,
    content_type: str,
) -> pd.DataFrame:
    """Read ZIP, CSV/TSV, or JSON UNCTAD responses."""
    if not content:
        raise ValueError(
            "UNCTAD returned an empty response."
        )

    print(
        "Inspecting UNCTAD response format..."
    )

    if zipfile.is_zipfile(
        io.BytesIO(content)
    ):
        print(
            "Detected UNCTAD format: ZIP archive"
        )

        archive = zipfile.ZipFile(
            io.BytesIO(content)
        )

        names = archive.namelist()

        print(
            "Files inside UNCTAD archive:"
        )

        for name in names:
            print(
                f"  - {name}"
            )

        csv_files = [
            name
            for name in names
            if name.lower().endswith(".csv")
        ]

        if not csv_files:
            raise ValueError(
                "UNCTAD returned a ZIP archive, "
                "but no CSV file was found."
            )

        csv_name = csv_files[0]

        print(
            "Selected UNCTAD data file:",
            csv_name,
        )

        raw = archive.read(
            csv_name
        )

        return parse_unctad_text(raw)

    print(
        "Response is not a ZIP archive."
    )

    sample = content[:500].lstrip()

    sample_lower = sample.lower()

    if (
        sample_lower.startswith(
            b"<!doctype html"
        )
        or sample_lower.startswith(
            b"<html"
        )
        or b"<html" in sample_lower[:200]
    ):
        preview = content[:500].decode(
            "utf-8",
            errors="replace",
        )

        raise ValueError(
            "UNCTAD returned HTML instead of a "
            "data file. "
            f"Response preview: {preview!r}"
        )

    if sample.startswith(
        (b"{", b"[")
    ):
        print(
            "Detected UNCTAD format: JSON"
        )

        try:
            payload = json.loads(
                content.decode(
                    "utf-8-sig"
                )
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ValueError(
                "UNCTAD response looks like JSON "
                "but could not be parsed."
            ) from exc

        if isinstance(payload, dict):
            list_candidates = [
                value
                for value in payload.values()
                if isinstance(value, list)
            ]

            if len(list_candidates) == 1:
                payload = list_candidates[0]

        if (
            isinstance(payload, list)
            and payload
            and all(
                isinstance(item, dict)
                for item in payload
            )
        ):
            df = pd.DataFrame(
                payload
            )

            print(
                "UNCTAD JSON records:",
                len(df),
            )

            print(
                "UNCTAD JSON columns:",
                len(df.columns),
            )

            print("UNCTAD columns:")

            for column in df.columns:
                print(
                    f"  - {column}"
                )

            return df

        raise ValueError(
            "UNCTAD returned JSON, but no "
            "tabular record structure was found."
        )

    print(
        "Detected UNCTAD format: text table"
    )

    return parse_unctad_text(
        content
    )


def find_economy_column(
    df: pd.DataFrame,
) -> str | None:
    """Find the economy-name column."""
    candidates = [
        "Economy",
        "Economy_Label",
        "Economy label",
        "economy",
        "economy_label",
        "Country",
        "Country_Label",
        "Country label",
        "country",
        "country_label",
    ]

    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    for candidate in [
        "economy",
        "economy_label",
        "country",
        "country_label",
    ]:
        if candidate in normalized_columns:
            return normalized_columns[candidate]

    return None


def find_country_code_column(
    df: pd.DataFrame,
) -> str | None:
    """Find an economy/country code column if available."""
    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    candidates = [
        "economy_code",
        "country_code",
        "iso3",
        "iso_3",
        "iso3_code",
    ]

    for candidate in candidates:
        if candidate in normalized_columns:
            return normalized_columns[candidate]

    return None


def find_concentration_columns(
    df: pd.DataFrame,
) -> dict[int, str]:
    """Find annual concentration-index columns."""
    result: dict[int, str] = {}

    patterns = [
        re.compile(
            r"^(\d{4})_Concentration_Index_Value$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^(\d{4}).*Concentration.*Value$",
            re.IGNORECASE,
        ),
    ]

    for column in df.columns:
        column_text = str(column)

        for pattern in patterns:
            match = pattern.match(
                column_text
            )

            if match:
                year = int(
                    match.group(1)
                )

                result[year] = column

                break

    return result


def find_year_column(
    df: pd.DataFrame,
) -> str | None:
    """Find a year/time column for long-format data."""
    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    candidates = [
        "year",
        "time",
        "time_period",
        "period",
        "reference_year",
    ]

    for candidate in candidates:
        if candidate in normalized_columns:
            return normalized_columns[candidate]

    return None


def find_long_value_column(
    df: pd.DataFrame,
) -> str | None:
    """Find the concentration value column in long-format data."""
    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    preferred = [
        "concentration_index_value",
        "concentration_value",
        "concentration_index",
    ]

    for candidate in preferred:
        if candidate in normalized_columns:
            return normalized_columns[candidate]

    concentration_candidates = []

    for normalized, original in normalized_columns.items():
        if (
            "concentration" in normalized
            and (
                normalized.endswith("value")
                or normalized.endswith("index")
            )
        ):
            concentration_candidates.append(
                original
            )

    if len(concentration_candidates) == 1:
        return concentration_candidates[0]

    return None


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
        temp[economy_column].map(
            normalize_text
        )
    )

    temp["country_code"] = (
        temp["_normalized_economy"].map(
            normalized_targets
        )
    )

    return temp[
        temp["country_code"].notna()
    ].copy()


def find_target_rows_by_code(
    df: pd.DataFrame,
    country_code_column: str,
) -> pd.DataFrame:
    """Find target economies using official country codes."""
    target_codes = set(
        TARGET_COUNTRIES.values()
    )

    temp = df.copy()

    temp["_normalized_country_code"] = (
        temp[country_code_column]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    temp["country_code"] = (
        temp["_normalized_country_code"]
        .where(
            temp["_normalized_country_code"].isin(
                target_codes
            )
        )
    )

    return temp[
        temp["country_code"].notna()
    ].copy()


def build_wide_output(
    target_rows: pd.DataFrame,
    concentration_columns: dict[int, str],
    economy_column: str,
) -> pd.DataFrame:
    """Build the JESI country-year output from wide data."""
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

        for year in sorted(
            TARGET_YEARS
        ):
            value_column = (
                concentration_columns[year]
            )

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

    return pd.DataFrame(rows)


def build_long_output(
    target_rows: pd.DataFrame,
    year_column: str,
    value_column: str,
) -> pd.DataFrame:
    """Build the JESI output from long-format data."""
    temp = target_rows.copy()

    temp["year"] = pd.to_numeric(
        temp[year_column],
        errors="coerce",
    )

    temp[
        "import_product_concentration"
    ] = pd.to_numeric(
        temp[value_column],
        errors="coerce",
    )

    temp = temp[
        temp["year"].isin(
            TARGET_YEARS
        )
    ].copy()

    output = temp[
        [
            "country_code",
            "year",
            "import_product_concentration",
        ]
    ].copy()

    output["country"] = output[
        "country_code"
    ].map(
        {
            "BGD": "Bangladesh",
            "IND": "India",
            "VNM": "Viet Nam",
            "IDN": "Indonesia",
            "MYS": "Malaysia",
        }
    )

    return output[
        [
            "country",
            "country_code",
            "year",
            "import_product_concentration",
        ]
    ]


def validate_output(
    output: pd.DataFrame,
) -> pd.DataFrame:
    """Validate the final country-year dataset."""
    expected_rows = 5 * 10

    output = output.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(
        drop=True
    )

    duplicate_mask = output.duplicated(
        [
            "country_code",
            "year",
        ],
        keep=False,
    )

    if duplicate_mask.any():
        duplicates = output[
            duplicate_mask
        ]

        raise ValueError(
            "Duplicate country-year observations "
            "were found in UNCTAD data:\n"
            f"{duplicates.to_string(index=False)}"
        )

    if len(output) != expected_rows:
        raise ValueError(
            "Unexpected number of country-year "
            f"observations: {len(output)}; "
            f"expected {expected_rows}."
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
            "UNCTAD concentration data contains "
            f"missing observations: {missing}"
        )

    return output


def main() -> None:
    print(
        "Downloading official UNCTAD "
        "concentration dataset..."
    )

    content, content_type = (
        download_unctad()
    )

    print(
        "UNCTAD response content type:",
        content_type,
    )

    df = read_unctad_response(
        content,
        content_type,
    )

    economy_column = find_economy_column(
        df
    )

    country_code_column = (
        find_country_code_column(df)
    )

    print(
        "Detected economy column:",
        economy_column,
    )

    print(
        "Detected country-code column:",
        country_code_column,
    )

    concentration_columns = (
        find_concentration_columns(df)
    )

    print(
        "Detected concentration years:",
        sorted(concentration_columns),
    )

    if concentration_columns:
        missing_years = [
            year
            for year in sorted(
                TARGET_YEARS
            )
            if year not in concentration_columns
        ]

        if missing_years:
            raise ValueError(
                "Missing required UNCTAD years: "
                f"{missing_years}"
            )

    if (
        economy_column is None
        and country_code_column is None
    ):
        raise ValueError(
            "Could not identify an economy/country "
            "column or country-code column in "
            "the UNCTAD dataset."
        )

    if country_code_column is not None:
        target_rows = (
            find_target_rows_by_code(
                df,
                country_code_column,
            )
        )

    else:
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
        print(
            "STATUS: BLOCKED"
        )

        print()
        print(
            "The downloaded UNCTAD table contains "
            "no individual rows for:"
        )

        for country, code in TARGET_COUNTRIES.items():
            print(
                f"  {code}: {country}"
            )

        print()
        print(
            "No fabricated country values will be created."
        )

        raise ValueError(
            "UNCTAD individual-economy "
            "concentration data is not present "
            "in the downloaded table."
        )

    if concentration_columns:
        if economy_column is None:
            raise ValueError(
                "Wide-format UNCTAD data was detected, "
                "but no economy column was found."
            )

        output = build_wide_output(
            target_rows,
            concentration_columns,
            economy_column,
        )

    else:
        year_column = find_year_column(
            df
        )

        value_column = (
            find_long_value_column(df)
        )

        print(
            "Detected year column:",
            year_column,
        )

        print(
            "Detected concentration value column:",
            value_column,
        )

        if year_column is None:
            raise ValueError(
                "UNCTAD data is not in the expected "
                "wide format and no year column "
                "could be identified."
            )

        if value_column is None:
            raise ValueError(
                "UNCTAD data is not in the expected "
                "wide format and no concentration "
                "value column could be identified."
            )

        output = build_long_output(
            target_rows,
            year_column,
            value_column,
        )

    output = validate_output(
        output
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
    print(
        f"Saved: {OUTPUT}"
    )

    print(
        f"Rows: {len(output)}"
    )

    print(
        "STATUS: SUCCESS"
    )


if __name__ == "__main__":
    main()
