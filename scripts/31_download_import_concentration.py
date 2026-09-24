"""
Download and extract UNCTAD merchandise import product
concentration data for the JESI target countries.

JESI target countries:
    BGD - Bangladesh
    IND - India
    VNM - Viet Nam
    IDN - Indonesia
    MYS - Malaysia

Benchmark period:
    2015-2024

The script:
    1. Downloads the official UNCTAD bulk dataset.
    2. Detects 7Z, ZIP, JSON, or text responses.
    3. Extracts the actual UNCTAD data table.
    4. Uses Economy Label for country identification.
    5. Uses Flow Label for Import observations.
    6. Uses Year and Concentration Index for long-format data.
    7. Validates exactly 50 country-year observations.
    8. Does not fabricate missing observations.
"""

from __future__ import annotations

import csv
import io
import json
import re
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import py7zr
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

TARGET_CODE_TO_NAME = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}

TARGET_YEARS = set(range(2015, 2025))

SEVEN_Z_SIGNATURE = b"\x37\x7a\xbc\xaf\x27\x1c"


def normalize_text(value: object) -> str:
    """Normalize text for matching."""
    if pd.isna(value):
        return ""

    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)

    return text


def normalize_column_name(value: object) -> str:
    """Normalize column names for flexible schema detection."""
    text = normalize_text(value)
    text = re.sub(r"[^a-z0-9]+", "_", text)

    return text.strip("_")


def decode_unctad_text(raw: bytes) -> str:
    """Decode UNCTAD text using common encodings."""
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

            return text

        except UnicodeDecodeError as exc:
            last_error = exc

    raise ValueError(
        "Could not decode UNCTAD text response."
    ) from last_error


def download_unctad() -> tuple[bytes, str]:
    """Download the official UNCTAD bulk dataset."""
    headers = {
        "User-Agent": (
            "JAS-JESI/1.0 "
            "(research data pipeline)"
        ),
        "Accept": (
            "text/csv, text/plain, "
            "application/zip, "
            "application/x-7z-compressed, "
            "application/octet-stream, */*"
        ),
    }

    response = requests.get(
        UNCTAD_URL,
        headers=headers,
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


def looks_like_html(content: bytes) -> bool:
    """Return True when the response appears to be HTML."""
    sample = content[:1000].lstrip().lower()

    return (
        sample.startswith(b"<!doctype html")
        or sample.startswith(b"<html")
        or b"<html" in sample[:500]
    )


def is_7z_archive(content: bytes) -> bool:
    """Return True when content starts with the 7z signature."""
    return content.startswith(
        SEVEN_Z_SIGNATURE
    )


def find_data_file(
    names: list[str],
) -> str | None:
    """Select the primary tabular file from an archive."""

    extensions = (
        ".csv",
        ".tsv",
        ".txt",
    )

    candidates = [
        name
        for name in names
        if name.lower().endswith(extensions)
    ]

    if not candidates:
        return None

    preferred = [
        name
        for name in candidates
        if any(
            term in Path(name).name.lower()
            for term in (
                "concent",
                "divers",
                "data",
                "bulk",
            )
        )
    ]

    if preferred:
        return preferred[0]

    return candidates[0]


def extract_7z_data(
    content: bytes,
) -> bytes:
    """Extract the primary data file from a 7z archive."""

    print(
        "Detected UNCTAD format: 7Z archive"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        archive_path = (
            temp_path / "unctad_response.7z"
        )

        archive_path.write_bytes(
            content
        )

        try:
            with py7zr.SevenZipFile(
                archive_path,
                mode="r",
            ) as archive:

                names = archive.getnames()

                print(
                    "Files inside UNCTAD 7Z archive:"
                )

                for name in names:
                    print(
                        f"  - {name}"
                    )

                data_name = find_data_file(
                    names
                )

                if data_name is None:
                    raise ValueError(
                        "UNCTAD returned a 7Z archive, "
                        "but no CSV/TXT/TSV data file was found."
                    )

                print(
                    "Selected UNCTAD 7Z data file:",
                    data_name,
                )

                archive.extractall(
                    path=temp_path
                )

        except (
            py7zr.Bad7zFile,
            py7zr.exceptions.Bad7zFile,
            py7zr.exceptions.UnsupportedCompressionMethodError,
        ) as exc:
            raise ValueError(
                "UNCTAD returned a 7Z archive, "
                "but the archive could not be extracted."
            ) from exc

        extracted_path = (
            temp_path / data_name
        )

        if not extracted_path.exists():
            matches = list(
                temp_path.rglob(
                    Path(data_name).name
                )
            )

            if not matches:
                raise ValueError(
                    "UNCTAD 7Z archive was extracted, "
                    "but the selected data file "
                    "could not be located."
                )

            extracted_path = matches[0]

        raw = extracted_path.read_bytes()

        print(
            "Extracted UNCTAD data size:",
            f"{len(raw):,}",
            "bytes",
        )

        return raw


def find_table_header(
    lines: list[str],
) -> int | None:
    """Find the actual UNCTAD table header."""

    candidates = []

    for index, line in enumerate(lines):
        normalized = normalize_text(line)

        if not normalized:
            continue

        has_economy = (
            "economy" in normalized
            or "country" in normalized
        )

        has_year = (
            "year" in normalized
            or "time" in normalized
            or "period" in normalized
        )

        has_concentration = (
            "concentration" in normalized
        )

        has_indicator = (
            "indicator" in normalized
            or "series" in normalized
            or "measure" in normalized
        )

        if (
            has_economy
            and (
                has_year
                or has_concentration
                or has_indicator
            )
        ):
            candidates.append(index)

    if candidates:
        return candidates[0]

    for index, line in enumerate(lines):
        normalized = normalize_text(line)

        if (
            "economy" in normalized
            or "country" in normalized
        ):
            return index

    return None


def detect_delimiter(
    lines: list[str],
    header_index: int,
) -> str:
    """Detect the delimiter in the actual data table."""

    sample_lines = lines[
        header_index:
        min(
            header_index + 30,
            len(lines),
        )
    ]

    sample = "\n".join(sample_lines)

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",\t;|",
        )

        delimiter = dialect.delimiter

    except csv.Error:
        header = lines[header_index]

        if "\t" in header:
            delimiter = "\t"
        elif ";" in header:
            delimiter = ";"
        elif "|" in header:
            delimiter = "|"
        else:
            delimiter = ","

    print(
        "Detected UNCTAD delimiter:",
        repr(delimiter),
    )

    return delimiter


def parse_unctad_text(
    raw: bytes,
) -> pd.DataFrame:
    """Parse the actual UNCTAD tabular data."""

    text = decode_unctad_text(
        raw
    )

    if text.lstrip().startswith("<"):
        raise ValueError(
            "UNCTAD returned markup/HTML instead of data."
        )

    lines = text.splitlines()

    print(
        "UNCTAD text lines:",
        len(lines),
    )

    header_index = find_table_header(
        lines
    )

    if header_index is None:
        preview = "\n".join(
            lines[:50]
        )

        raise ValueError(
            "Could not identify the UNCTAD "
            "data-table header.\n"
            f"First 50 response lines:\n{preview}"
        )

    print(
        "Detected UNCTAD table header line:",
        header_index + 1,
    )

    print(
        "UNCTAD table header:",
        lines[header_index],
    )

    delimiter = detect_delimiter(
        lines,
        header_index,
    )

    table_text = "\n".join(
        lines[header_index:]
    )

    try:
        df = pd.read_csv(
            io.StringIO(table_text),
            sep=delimiter,
            engine="python",
        )

    except pd.errors.ParserError as exc:
        print(
            "Primary UNCTAD table parser failed:"
        )

        print(
            str(exc)
        )

        alternatives = [
            "\t",
            ",",
            ";",
            "|",
        ]

        alternatives = [
            value
            for value in alternatives
            if value != delimiter
        ]

        df = None
        alternative_error = None

        for alternative in alternatives:
            try:
                print(
                    "Trying alternative delimiter:",
                    repr(alternative),
                )

                candidate = pd.read_csv(
                    io.StringIO(table_text),
                    sep=alternative,
                    engine="python",
                )

                if len(candidate.columns) > 1:
                    df = candidate
                    delimiter = alternative
                    break

            except pd.errors.ParserError as retry_exc:
                alternative_error = retry_exc

        if df is None:
            raise ValueError(
                "Could not parse UNCTAD data table. "
                f"Primary error: {exc}. "
                f"Last alternative error: "
                f"{alternative_error}"
            ) from exc

    if len(df.columns) <= 1:
        raise ValueError(
            "UNCTAD data was parsed into only one column."
        )

    df = df.dropna(
        axis=1,
        how="all",
    )

    df = df.dropna(
        axis=0,
        how="all",
    ).reset_index(
        drop=True
    )

    print(
        "UNCTAD raw rows:",
        len(df),
    )

    print(
        "UNCTAD raw columns:",
        len(df.columns),
    )

    print(
        "UNCTAD columns:"
    )

    for column in df.columns:
        print(
            f"  - {column}"
        )

    return df


def read_unctad_response(
    content: bytes,
    content_type: str,
) -> pd.DataFrame:
    """Read 7Z, ZIP, JSON, or text UNCTAD responses."""

    if not content:
        raise ValueError(
            "UNCTAD returned an empty response."
        )

    print(
        "Inspecting UNCTAD response format..."
    )

    if is_7z_archive(content):
        raw = extract_7z_data(
            content
        )

        return parse_unctad_text(
            raw
        )

    if zipfile.is_zipfile(
        io.BytesIO(content)
    ):
        print(
            "Detected UNCTAD format: ZIP archive"
        )

        with zipfile.ZipFile(
            io.BytesIO(content)
        ) as archive:

            names = archive.namelist()

            print(
                "Files inside UNCTAD archive:"
            )

            for name in names:
                print(
                    f"  - {name}"
                )

            data_name = find_data_file(
                names
            )

            if data_name is None:
                raise ValueError(
                    "UNCTAD ZIP archive contains "
                    "no CSV/TXT/TSV data file."
                )

            print(
                "Selected UNCTAD data file:",
                data_name,
            )

            raw = archive.read(
                data_name
            )

        return parse_unctad_text(
            raw
        )

    print(
        "Response is not a 7Z or ZIP archive."
    )

    if looks_like_html(content):
        raise ValueError(
            "UNCTAD returned HTML instead of data."
        )

    stripped = content.lstrip()

    if stripped.startswith(
        (b"{", b"[")
    ):
        print(
            "Detected UNCTAD format: JSON"
        )

        try:
            payload = json.loads(
                stripped.decode(
                    "utf-8"
                )
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ValueError(
                "UNCTAD response looked like JSON "
                "but could not be parsed."
            ) from exc

        if isinstance(payload, list):
            return pd.DataFrame(
                payload
            )

        if isinstance(payload, dict):
            for key in (
                "data",
                "results",
                "records",
                "rows",
            ):
                value = payload.get(key)

                if isinstance(
                    value,
                    list,
                ):
                    return pd.DataFrame(
                        value
                    )

            return pd.json_normalize(
                payload
            )

        raise ValueError(
            "Unsupported UNCTAD JSON structure."
        )

    print(
        "Detected UNCTAD format: text/CSV"
    )

    return parse_unctad_text(
        content
    )


def find_column(
    df: pd.DataFrame,
    preferred_names: list[str],
    required_terms: list[str] | None = None,
) -> str | None:
    """Find a dataframe column using normalized names."""

    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    for name in preferred_names:
        normalized = normalize_column_name(
            name
        )

        if normalized in normalized_columns:
            return normalized_columns[
                normalized
            ]

    if required_terms:
        for normalized, original in (
            normalized_columns.items()
        ):
            if all(
                term in normalized
                for term in required_terms
            ):
                return original

    return None


def find_economy_column(
    df: pd.DataFrame,
) -> str | None:
    """Find the human-readable economy column."""

    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    preferred = [
        "economy_label",
        "economy_name",
        "country_label",
        "country_name",
        "economy",
        "country",
    ]

    for candidate in preferred:
        if candidate in normalized_columns:
            return normalized_columns[
                candidate
            ]

    return None


def find_country_code_column(
    df: pd.DataFrame,
) -> str | None:
    """Find an ISO-style country-code column."""

    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    preferred = [
        "iso3",
        "iso3_code",
        "country_code",
        "economy_code",
        "iso_code",
    ]

    for candidate in preferred:
        if candidate in normalized_columns:
            return normalized_columns[
                candidate
            ]

    return None


def find_year_column(
    df: pd.DataFrame,
) -> str | None:
    """Find the year column."""

    return find_column(
        df,
        [
            "year",
            "time",
            "period",
        ],
    )


def find_concentration_column(
    df: pd.DataFrame,
) -> str | None:
    """Find the concentration index column."""

    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    preferred = [
        "concentration_index",
        "concentration",
        "concentration_index_value",
    ]

    for candidate in preferred:
        if candidate in normalized_columns:
            return normalized_columns[
                candidate
            ]

    matches = []

    for normalized, original in normalized_columns.items():
        if "concentration" not in normalized:
            continue

        if (
            "value" in normalized
            or "index" in normalized
        ):
            matches.append(original)

    if len(matches) == 1:
        return matches[0]

    return None


def identify_import_dimension(
    df: pd.DataFrame,
) -> str | None:
    """
    Identify the Import/Export dimension.

    UNCTAD currently provides:
        Flow
        Flow Label

    Flow is coded.
    Flow Label contains human-readable text such as
    Import or Imports.

    Therefore Flow Label is deliberately preferred.
    """

    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    preferred = [
        "flow_label",
        "trade_flow_label",
        "direction_label",
        "trade_direction_label",
        "flow",
        "trade_flow",
        "direction",
        "trade_direction",
        "indicator",
        "series",
        "measure",
        "concept",
        "type",
    ]

    candidates = []

    for candidate in preferred:
        if candidate in normalized_columns:
            candidates.append(
                normalized_columns[candidate]
            )

    for normalized, original in (
        normalized_columns.items()
    ):
        if (
            "flow" in normalized
            or "direction" in normalized
        ) and original not in candidates:
            candidates.append(original)

    for column in candidates:
        values = (
            df[column]
            .dropna()
            .astype(str)
            .map(normalize_text)
        )

        if values.empty:
            continue

        import_count = values.str.contains(
            r"\bimports?\b",
            regex=True,
            na=False,
        ).sum()

        if import_count > 0:
            print(
                "Detected import/export dimension:",
                column,
            )

            return column

    return None


def filter_import_rows(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Filter the dataset to Import observations."""

    dimension = identify_import_dimension(
        df
    )

    if dimension is None:
        raise ValueError(
            "Could not identify the UNCTAD "
            "Import/Export flow dimension. "
            "Refusing to continue because selecting "
            "between Import and Export observations "
            "without an explicit flow dimension would "
            "risk using the wrong data."
        )

    values = (
        df[dimension]
        .astype(str)
        .map(normalize_text)
    )

    import_mask = values.str.contains(
        r"\bimports?\b",
        regex=True,
        na=False,
    )

    filtered = df[
        import_mask
    ].copy()

    print(
        "Rows before import filter:",
        len(df),
    )

    print(
        "Rows after import filter:",
        len(filtered),
    )

    if filtered.empty:
        raise ValueError(
            "Import/export dimension was detected, "
            "but no Import observations were found."
        )

    return filtered


def find_target_rows(
    df: pd.DataFrame,
    economy_column: str,
) -> pd.DataFrame:
    """Find JESI target countries by economy label."""

    target_lookup = {}

    for country, code in TARGET_COUNTRIES.items():
        target_lookup[
            normalize_text(country)
        ] = code

    temp = df.copy()

    temp["_normalized_economy"] = (
        temp[economy_column]
        .map(normalize_text)
    )

    temp["country_code"] = (
        temp["_normalized_economy"]
        .map(target_lookup)
    )

    return temp[
        temp["country_code"].notna()
    ].copy()


def find_target_rows_by_code(
    df: pd.DataFrame,
    country_code_column: str,
) -> pd.DataFrame:
    """Find target countries by ISO-style code."""

    target_codes = set(
        TARGET_CODE_TO_NAME.keys()
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
    """Build output from wide-format data."""

    rows = []

    for _, row in target_rows.iterrows():
        country_code = row["country_code"]

        country_name = TARGET_CODE_TO_NAME.get(
            country_code,
            str(row[economy_column]),
        )

        for year in sorted(TARGET_YEARS):
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
    """Build output from long-format data."""

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

    output["country"] = (
        output["country_code"]
        .map(TARGET_CODE_TO_NAME)
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
    """Validate exactly 50 country-year observations."""

    expected_rows = (
        len(TARGET_CODE_TO_NAME)
        * len(TARGET_YEARS)
    )

    required_codes = set(
        TARGET_CODE_TO_NAME.keys()
    )

    output = output.copy()

    output["year"] = pd.to_numeric(
        output["year"],
        errors="coerce",
    )

    output[
        "import_product_concentration"
    ] = pd.to_numeric(
        output[
            "import_product_concentration"
        ],
        errors="coerce",
    )

    required_columns = {
        "country",
        "country_code",
        "year",
        "import_product_concentration",
    }

    missing_columns = (
        required_columns
        - set(output.columns)
    )

    if missing_columns:
        raise ValueError(
            "Output is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    actual_codes = set(
        output["country_code"]
        .dropna()
        .astype(str)
        .str.upper()
    )

    missing_codes = (
        required_codes
        - actual_codes
    )

    if missing_codes:
        raise ValueError(
            "Required JESI countries are missing: "
            f"{sorted(missing_codes)}"
        )

    unexpected_codes = (
        actual_codes
        - required_codes
    )

    if unexpected_codes:
        raise ValueError(
            "Unexpected country codes found: "
            f"{sorted(unexpected_codes)}"
        )

    actual_years = set(
        output["year"]
        .dropna()
        .astype(int)
    )

    missing_years = (
        TARGET_YEARS
        - actual_years
    )

    if missing_years:
        raise ValueError(
            "Required years are missing: "
            f"{sorted(missing_years)}"
        )

    duplicate_mask = output.duplicated(
        [
            "country_code",
            "year",
        ],
        keep=False,
    )

    if duplicate_mask.any():
        print(
            "Duplicate country-year observations:"
        )

        print(
            output[
                duplicate_mask
            ]
            .sort_values(
                [
                    "country_code",
                    "year",
                ]
            )
            .to_string(index=False)
        )

        raise ValueError(
            "Duplicate country-year observations "
            "were found."
        )

    if len(output) != expected_rows:
        counts = (
            output.groupby(
                "country_code"
            )["year"]
            .nunique()
        )

        print(
            "Country-year counts:"
        )

        print(
            counts.to_string()
        )

        raise ValueError(
            "Unexpected number of country-year "
            f"observations: {len(output)}; "
            f"expected {expected_rows}."
        )

    missing_values = (
        output[
            "import_product_concentration"
        ].isna()
    )

    missing_count = int(
        missing_values.sum()
    )

    print()
    print(
        "Missing concentration observations:",
        missing_count,
    )

    if missing_count:
        print(
            output[
                missing_values
            ].to_string(index=False)
        )

        raise ValueError(
            "UNCTAD concentration data contains "
            f"{missing_count} missing observations."
        )

    if (
        output[
            "import_product_concentration"
        ] < 0
    ).any():
        raise ValueError(
            "Import product concentration contains "
            "negative values."
        )

    print()
    print(
        "Validated country-year observations:",
        len(output),
    )

    print(
        "Validated countries:",
        output[
            "country_code"
        ].nunique(),
    )

    print(
        "Validated years:",
        output[
            "year"
        ].nunique(),
    )

    print(
        "Year range:",
        f"{int(output['year'].min())}-"
        f"{int(output['year'].max())}",
    )

    return output.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(
        drop=True
    )


def prepare_output(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Detect schema, filter imports, and build output."""

    economy_column = find_economy_column(
        df
    )

    country_code_column = (
        find_country_code_column(
            df
        )
    )

    print(
        "Detected economy column:",
        economy_column,
    )

    print(
        "Detected country-code column:",
        country_code_column,
    )

    df = filter_import_rows(
        df
    )

    if economy_column is not None:
        target_rows = find_target_rows(
            df,
            economy_column,
        )
    elif country_code_column is not None:
        target_rows = find_target_rows_by_code(
            df,
            country_code_column,
        )
    else:
        raise ValueError(
            "Could not identify an economy or "
            "country-code column in UNCTAD data."
        )

    print(
        "Target-country rows found:",
        len(target_rows),
    )

    if target_rows.empty:
        raise ValueError(
            "No JESI target-country rows found "
            "in UNCTAD data."
        )

    year_column = find_year_column(
        target_rows
    )

    concentration_column = (
        find_concentration_column(
            target_rows
        )
    )

    print(
        "Detected year column:",
        year_column,
    )

    print(
        "Detected concentration value column:",
        concentration_column,
    )

    if (
        year_column is not None
        and concentration_column is not None
    ):
        output = build_long_output(
            target_rows,
            year_column,
            concentration_column,
        )

    else:
        normalized_columns = {
            normalize_column_name(column): column
            for column in target_rows.columns
        }

        concentration_columns = {}

        for year in TARGET_YEARS:
            candidates = [
                f"concentration_index_{year}",
                f"concentration_{year}",
                f"{year}_concentration_index",
                f"{year}_concentration",
            ]

            selected = None

            for candidate in candidates:
                if candidate in normalized_columns:
                    selected = normalized_columns[
                        candidate
                    ]
                    break

            if selected is not None:
                concentration_columns[
                    year
                ] = selected

        if len(
            concentration_columns
        ) != len(TARGET_YEARS):
            raise ValueError(
                "Could not identify a complete long- or "
                "wide-format UNCTAD concentration dataset."
            )

        if economy_column is None:
            economy_column = country_code_column

        output = build_wide_output(
            target_rows,
            concentration_columns,
            economy_column,
        )

    return validate_output(
        output
    )


def main() -> None:
    """Run the UNCTAD import concentration pipeline."""

    print("=" * 72)
    print(
        "JESI STRATEGIC AUTONOMY "
        "IMPORT CONCENTRATION DOWNLOAD"
    )
    print("=" * 72)

    print(
        "Target period:",
        "2015-2024",
    )

    print(
        "Target countries:",
        ", ".join(
            TARGET_CODE_TO_NAME.values()
        ),
    )

    content, content_type = (
        download_unctad()
    )

    dataframe = read_unctad_response(
        content,
        content_type,
    )

    output = prepare_output(
        dataframe
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
    print("=" * 72)
    print(
        "IMPORT CONCENTRATION DOWNLOAD STATUS"
    )
    print("=" * 72)

    print(
        "Rows              :",
        len(output),
    )

    print(
        "Countries         :",
        output[
            "country_code"
        ].nunique(),
    )

    print(
        "Years             :",
        output[
            "year"
        ].nunique(),
    )

    print(
        "Year range        :",
        f"{int(output['year'].min())}-"
        f"{int(output['year'].max())}",
    )

    print(
        "Missing values    :",
        int(
            output[
                "import_product_concentration"
            ].isna().sum()
        ),
    )

    print(
        "Duplicate rows    :",
        int(
            output.duplicated(
                [
                    "country_code",
                    "year",
                ]
            ).sum()
        ),
    )

    print(
        "Saved             :",
        OUTPUT,
    )

    print()
    print(
        "STATUS: GREEN"
    )

    print(
        "JESI Strategic Autonomy "
        "import concentration data "
        "download completed successfully."
    )


if __name__ == "__main__":
    main()
