"""
Download and inspect UNCTAD merchandise product concentration data.

This script downloads the official UNCTAD bulk dataset and extracts
import product concentration observations for the five JESI target
countries for 2015-2024.

JESI target countries:
BGD - Bangladesh
IND - India
VNM - Viet Nam
IDN - Indonesia
MYS - Malaysia

Required years:
2015-2024

The script does not fabricate missing observations.
It stops with an error if the required country-year observations
cannot be identified and validated.
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

TARGET_YEARS = set(range(2015, 2025))

TARGET_CODE_TO_NAME = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}

SEVEN_Z_SIGNATURE = b"\x37\x7a\xbc\xaf\x27\x1c"


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


def decode_unctad_text(raw: bytes) -> str:
    """Decode a UNCTAD text response using common encodings."""
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
    """Download the official UNCTAD bulk response."""
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
    """Return True if the response appears to be HTML."""
    sample = content[:1000].lstrip().lower()

    return (
        sample.startswith(b"<!doctype html")
        or sample.startswith(b"<html")
        or b"<html" in sample[:500]
    )


def is_7z_archive(content: bytes) -> bool:
    """Return True when content starts with the official 7z signature."""
    return content.startswith(
        SEVEN_Z_SIGNATURE
    )


def find_data_file(
    names: list[str],
) -> str | None:
    """
    Select the first likely tabular data file from an archive.

    UNCTAD bulk archives can contain metadata files as well as the
    actual data table. Prefer CSV/TSV/TXT files and ignore obvious
    documentation files when possible.
    """
    data_extensions = (
        ".csv",
        ".tsv",
        ".txt",
    )

    candidates = [
        name
        for name in names
        if name.lower().endswith(
            data_extensions
        )
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
    """
    Extract the primary tabular data file from a 7z archive.

    The archive is written to a temporary file because py7zr supports
    reliable archive extraction from a filesystem path across Python
    environments used by GitHub Actions.
    """
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
    """
    Locate the actual UNCTAD table header.

    UNCTAD bulk files can contain metadata before the actual
    tabular data. The first line of the response must therefore
    not automatically be treated as the CSV header.
    """

    candidates: list[int] = []

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

    # Broader fallback.
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
    """Detect the delimiter using the actual table area."""
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
    """
    Parse a text-based UNCTAD response.

    The parser first identifies the actual data-table header and
    only then passes the table portion to pandas. This prevents
    metadata lines before the table from being interpreted as CSV
    records.
    """

    text = decode_unctad_text(
        raw
    )

    if text.lstrip().startswith("<"):
        preview = text[:500]

        raise ValueError(
            "UNCTAD returned markup/HTML instead of a data table. "
            f"Response preview: {preview!r}"
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
            "Could not identify the UNCTAD data-table header.\n"
            "First 50 response lines:\n"
            f"{preview}"
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

    # First attempt: strict parsing.
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

        # Retry using the most likely alternative delimiter.
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
                "Could not parse the UNCTAD data table after "
                "locating the real header. "
                f"Primary error: {exc}. "
                f"Last alternative error: {alternative_error}"
            ) from exc

    if len(df.columns) <= 1:
        raise ValueError(
            "UNCTAD response was parsed, but only one column "
            "was detected. The table delimiter may be incorrect."
        )

    # Remove completely empty columns.
    df = df.dropna(
        axis=1,
        how="all",
    )

    # Remove completely empty rows.
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
    """
    Read 7Z, ZIP, text/CSV, or JSON UNCTAD responses.

    Format detection is based primarily on the actual response
    bytes rather than the HTTP Content-Type because the UNCTAD
    bulk endpoint may return an archive as application/octet-stream.
    """

    if not content:
        raise ValueError(
            "UNCTAD returned an empty response."
        )

    print(
        "Inspecting UNCTAD response format..."
    )

    # ---------------------------------------------------------
    # 7Z
    # ---------------------------------------------------------

    if is_7z_archive(
        content
    ):
        raw = extract_7z_data(
            content
        )

        return parse_unctad_text(
            raw
        )

    # ---------------------------------------------------------
    # ZIP
    # ---------------------------------------------------------

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
                    "UNCTAD returned a ZIP archive, "
                    "but no CSV/TXT/TSV data file was found."
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

    # ---------------------------------------------------------
    # HTML
    # ---------------------------------------------------------

    if looks_like_html(
        content
    ):
        preview = content[:500].decode(
            "utf-8",
            errors="replace",
        )

        raise ValueError(
            "UNCTAD returned HTML instead of a data file. "
            f"Response preview: {preview!r}"
        )

    # ---------------------------------------------------------
    # JSON
    # ---------------------------------------------------------

    stripped = content.lstrip()

    if stripped.startswith(
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

        if isinstance(
            payload,
            dict,
        ):
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

            print(
                "UNCTAD columns:"
            )

            for column in df.columns:
                print(
                    f"  - {column}"
                )

            return df

        raise ValueError(
            "UNCTAD returned JSON, but no "
            "tabular record structure was found."
        )

    # ---------------------------------------------------------
    # Text / CSV / TSV
    # ---------------------------------------------------------

    print(
        "Detected UNCTAD format: text table"
    )

    return parse_unctad_text(
        content
    )


def find_economy_column(
    df: pd.DataFrame,
) -> str | None:
    """Find the economy/country name column."""
    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    candidates = [
        "economy",
        "economy_label",
        "economy_name",
        "country",
        "country_label",
        "country_name",
    ]

    for candidate in candidates:
        if candidate in normalized_columns:
            return normalized_columns[candidate]

    # Fallback: find a column containing economy/country.
    for normalized, original in normalized_columns.items():
        if (
            "economy" in normalized
            or "country" in normalized
        ):
            return original

    return None


def find_country_code_column(
    df: pd.DataFrame,
) -> str | None:
    """Find an economy/country code column."""
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
        "iso_3_code",
    ]

    for candidate in candidates:
        if candidate in normalized_columns:
            return normalized_columns[candidate]

    for normalized, original in normalized_columns.items():
        if (
            normalized.endswith(
                "_code"
            )
            and (
                "economy" in normalized
                or "country" in normalized
                or "iso" in normalized
            )
        ):
            return original

    return None


def find_concentration_columns(
    df: pd.DataFrame,
) -> dict[int, str]:
    """
    Find annual concentration-index columns in wide-format data.
    """
    result: dict[int, str] = {}

    for column in df.columns:
        normalized = normalize_column_name(
            column
        )

        year_match = re.match(
            r"^(\d{4})_",
            normalized,
        )

        if not year_match:
            continue

        year = int(
            year_match.group(1)
        )

        if year not in TARGET_YEARS:
            continue

        if (
            "concentration" in normalized
            and (
                "value" in normalized
                or "index" in normalized
            )
        ):
            result[year] = column

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

    for normalized, original in normalized_columns.items():
        if (
            normalized == "year"
            or normalized.endswith("_year")
            or normalized.startswith("year_")
        ):
            return original

    return None


def find_long_value_column(
    df: pd.DataFrame,
) -> str | None:
    """Find the concentration value column."""
    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    preferred = [
        "concentration_index_value",
        "concentration_value",
        "concentration_index",
        "concentration",
    ]

    for candidate in preferred:
        if candidate in normalized_columns:
            return normalized_columns[candidate]

    candidates = []

    for normalized, original in normalized_columns.items():
        if "concentration" not in normalized:
            continue

        if (
            "value" in normalized
            or "index" in normalized
        ):
            candidates.append(
                original
            )

    if len(candidates) == 1:
        return candidates[0]

    return None


def find_target_rows(
    df: pd.DataFrame,
    economy_column: str,
) -> pd.DataFrame:
    """Find target countries by economy name."""
    target_lookup = {}

    for country, code in TARGET_COUNTRIES.items():
        target_lookup[
            normalize_text(country)
        ] = code

    temp = df.copy()

    temp["_normalized_economy"] = (
        temp[economy_column].map(
            normalize_text
        )
    )

    temp["country_code"] = (
        temp["_normalized_economy"].map(
            target_lookup
        )
    )

    return temp[
        temp["country_code"].notna()
    ].copy()


def find_target_rows_by_code(
    df: pd.DataFrame,
    country_code_column: str,
) -> pd.DataFrame:
    """Find target countries by official country/economy code."""
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


def identify_import_dimension(
    df: pd.DataFrame,
) -> str | None:
    """
    Identify a dimension column containing Import/Export information.

    This is used only when the downloaded UNCTAD table contains
    multiple trade-flow observations.
    """
    normalized_columns = {
        normalize_column_name(column): column
        for column in df.columns
    }

    preferred_terms = [
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

    for normalized, original in normalized_columns.items():
        if any(
            term in normalized
            for term in preferred_terms
        ):
            candidates.append(
                original
            )

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
            r"\bimport\b",
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
    """
    Filter to import observations when a trade-flow dimension exists.

    If no import/export dimension exists, the original data is
    returned unchanged. The script will later validate whether
    country-year observations are unique.
    """
    dimension = identify_import_dimension(
        df
    )

    if dimension is None:
        print(
            "No explicit import/export dimension detected."
        )

        return df

    values = (
        df[dimension]
        .astype(str)
        .map(normalize_text)
    )

    import_mask = values.str.contains(
        r"\bimport\b",
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
            "An import/export dimension was detected, "
            "but no Import observations were found."
        )

    return filtered


def build_wide_output(
    target_rows: pd.DataFrame,
    concentration_columns: dict[int, str],
    economy_column: str,
) -> pd.DataFrame:
    """Build JESI output from wide-format UNCTAD data."""
    rows = []

    for _, row in target_rows.iterrows():
        country_code = row["country_code"]

        country_name = TARGET_CODE_TO_NAME.get(
            country_code,
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

    return pd.DataFrame(
        rows
    )


def build_long_output(
    target_rows: pd.DataFrame,
    year_column: str,
    value_column: str,
) -> pd.DataFrame:
    """Build JESI output from long-format UNCTAD data."""
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
        output["country_code"].map(
            TARGET_CODE_TO_NAME
        )
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
    """
    Validate exactly 50 unique country-year observations.
    """
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

    # ---------------------------------------------------------
    # Basic schema validation
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Country validation
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Year validation
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Duplicate validation
    # ---------------------------------------------------------

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
        ].sort_values(
            [
                "country_code",
                "year",
            ]
        )

        print(
            "Duplicate country-year observations:"
        )

        print(
            duplicates.to_string(
                index=False
            )
        )

        raise ValueError(
            "Duplicate country-year observations "
            "were found in UNCTAD data."
        )

    # ---------------------------------------------------------
    # Row-count validation
    # ---------------------------------------------------------

    if len(output) != expected_rows:
        print()
        print(
            "Country-year counts:"
        )

        counts = (
            output.groupby(
                "country_code"
            )["year"]
            .nunique()
        )

        print(
            counts.to_string()
        )

        raise ValueError(
            "Unexpected number of country-year "
            f"observations: {len(output)}; "
            f"expected {expected_rows}."
        )

    # ---------------------------------------------------------
    # Missing-value validation
    # ---------------------------------------------------------

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
        missing_rows = output[
            missing_values
        ]

        print(
            missing_rows.to_string(
                index=False
            )
        )

        raise ValueError(
            "UNCTAD concentration data contains "
            f"{missing_count} missing observations."
        )

    # ---------------------------------------------------------
    # Numeric range validation
    #
    # UNCTAD concentration index is bounded between 0 and 1.
    # ---------------------------------------------------------

    invalid_range = (
        (
            output[
                "import_product_concentration"
            ]
            < 0
        )
        | (
            output[
                "import_product_concentration"
            ]
            > 1
        )
    )

    if invalid_range.any():
        invalid_rows = output[
            invalid_range
        ]

        print(
            "Out-of-range concentration values:"
        )

        print(
            invalid_rows.to_string(
                index=False
            )
        )

        raise ValueError(
            "UNCTAD concentration index contains "
            "values outside the expected 0-1 range."
        )

    # ---------------------------------------------------------
    # Final ordering
    # ---------------------------------------------------------

    output = output.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(
        drop=True
    )

    return output


def print_target_summary(
    output: pd.DataFrame,
) -> None:
    """Print a compact validation summary."""
    print()
    print(
        "Validated country-year observations:"
    )

    summary = (
        output.groupby(
            "country_code"
        )["year"]
        .agg(
            [
                "count",
                "min",
                "max",
            ]
        )
    )

    print(
        summary.to_string()
    )


def main() -> None:
    """Run the UNCTAD import concentration pipeline."""
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

    # ---------------------------------------------------------
    # Identify country/economy columns
    # ---------------------------------------------------------

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

    if (
        economy_column is None
        and country_code_column is None
    ):
        raise ValueError(
            "Could not identify an economy/country "
            "column or country-code column in "
            "the UNCTAD dataset."
        )

    # ---------------------------------------------------------
    # Detect wide-format annual concentration columns
    # ---------------------------------------------------------

    concentration_columns = (
        find_concentration_columns(
            df
        )
    )

    print(
        "Detected concentration years:",
        sorted(
            concentration_columns
        ),
    )

    # ---------------------------------------------------------
    # Filter to import observations when the source contains
    # multiple trade-flow dimensions.
    # ---------------------------------------------------------

    df = filter_import_rows(
        df
    )

    # ---------------------------------------------------------
    # Re-detect columns after filtering.
    # ---------------------------------------------------------

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
            "no individual rows for the JESI target countries:"
        )

        for code, country in (
            TARGET_CODE_TO_NAME.items()
        ):
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

    # ---------------------------------------------------------
    # Build output.
    # ---------------------------------------------------------

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
                "Wide-format UNCTAD data is missing "
                f"required years: {missing_years}"
            )

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
            find_long_value_column(
                df
            )
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

    # ---------------------------------------------------------
    # Validate final dataset.
    # ---------------------------------------------------------

    output = validate_output(
        output
    )

    print_target_summary(
        output
    )

    # ---------------------------------------------------------
    # Save final raw-derived dataset.
    # ---------------------------------------------------------

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

    print()
    print(
        "STATUS: SUCCESS"
    )


if __name__ == "__main__":
    main()
