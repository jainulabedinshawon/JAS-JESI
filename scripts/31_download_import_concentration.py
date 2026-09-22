"""
JESI Strategic Autonomy
Import Product Concentration Download

Script 31:
Download the official UNCTAD merchandise product
concentration and diversification dataset and integrate
the import product concentration index.

Official source:
UNCTADstat Data Hub

Dataset:
Merchandise: Standard product concentration and
diversification indices - Annual (analytical)

Official bulk-download endpoint:
https://unctadstat-api.unctad.org/bulkdownload/US.ConcentDiversIndices/US_ConcentDiversIndices

Period:
    2015-2024

Countries:
    Bangladesh, India, Viet Nam, Indonesia, Malaysia
"""

from io import BytesIO
from pathlib import Path
import csv
import tempfile
import zipfile

import pandas as pd
import py7zr
import requests


INPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024.csv"
)

OUTPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024_complete.csv"
)

UNCTAD_URL = (
    "https://unctadstat-api.unctad.org/"
    "bulkdownload/US.ConcentDiversIndices/"
    "US_ConcentDiversIndices"
)

COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}


def normalize_column_name(column):
    """Normalize a column name for flexible matching."""
    return (
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )


def find_column(columns, candidates):
    """Find a column using normalized candidate names."""
    normalized = {
        normalize_column_name(column): column
        for column in columns
    }

    for candidate in candidates:
        key = normalize_column_name(candidate)

        if key in normalized:
            return normalized[key]

    return None


def detect_delimiter(text):
    """Detect common CSV delimiters."""

    sample = text[:100000]

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",;\t|",
        )

        return dialect.delimiter

    except csv.Error:
        first_line = text.splitlines()[0]

        candidates = [
            ",",
            ";",
            "\t",
            "|",
        ]

        counts = {
            delimiter: first_line.count(delimiter)
            for delimiter in candidates
        }

        detected = max(
            counts,
            key=counts.get,
        )

        if counts[detected] == 0:
            raise ValueError(
                "Could not detect the data delimiter."
            )

        return detected


def read_text_data(content):
    """
    Read extracted UNCTAD text data using multiple
    encodings and delimiter detection.
    """

    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp1252",
        "latin-1",
    ]

    errors = []

    for encoding in encodings:
        try:
            text = content.decode(
                encoding
            )

            delimiter = detect_delimiter(
                text
            )

            print(
                f"Detected encoding: {encoding}"
            )

            print(
                "Detected delimiter: "
                f"{repr(delimiter)}"
            )

            data = pd.read_csv(
                BytesIO(
                    text.encode(encoding)
                ),
                encoding=encoding,
                sep=delimiter,
                engine="python",
                low_memory=False,
            )

            if len(data.columns) <= 1:
                raise ValueError(
                    "Only one column detected."
                )

            return data

        except (
            UnicodeDecodeError,
            csv.Error,
            ValueError,
            pd.errors.ParserError,
        ) as error:

            errors.append(
                f"{encoding}: {error}"
            )

    raise ValueError(
        "Could not parse extracted UNCTAD "
        f"data. Attempts: {errors}"
    )


def read_unctad_download(content):
    """
    Read the official UNCTAD bulk download.

    The UNCTAD endpoint currently returns a 7z archive.
    This function detects the 7z signature and extracts
    the contained data file.
    """

    # 7z signature:
    # 37 7A BC AF 27 1C
    if content[:6] == b"7z\xbc\xaf'\x1c":

        print(
            "Detected UNCTAD 7z archive."
        )

        with tempfile.TemporaryDirectory() as temp_dir:

            archive_path = Path(
                temp_dir
            ) / "unctad_download.7z"

            archive_path.write_bytes(
                content
            )

            extract_dir = Path(
                temp_dir
            ) / "extracted"

            extract_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            with py7zr.SevenZipFile(
                archive_path,
                mode="r",
            ) as archive:

                names = archive.getnames()

                print(
                    "Files inside UNCTAD archive:"
                )

                for name in names:
                    print(
                        f"  - {name}"
                    )

                archive.extractall(
                    path=extract_dir
                )

            data_files = [
                path
                for path in extract_dir.rglob("*")
                if path.is_file()
                and path.suffix.lower()
                in {
                    ".csv",
                    ".txt",
                    ".tsv",
                }
            ]

            if not data_files:
                raise ValueError(
                    "UNCTAD 7z archive was opened, "
                    "but no CSV/TXT/TSV data file "
                    "was found."
                )

            preferred = [
                path
                for path in data_files
                if "concent" in path.name.lower()
                or "divers" in path.name.lower()
            ]

            data_file = (
                preferred[0]
                if preferred
                else data_files[0]
            )

            print(
                "Selected UNCTAD data file:"
            )
            print(
                f"  {data_file.name}"
            )

            return read_text_data(
                data_file.read_bytes()
            )

    # ZIP support
    if content[:2] == b"PK":

        print(
            "Detected UNCTAD ZIP archive."
        )

        with zipfile.ZipFile(
            BytesIO(content)
        ) as archive:

            files = [
                name
                for name in archive.namelist()
                if name.lower().endswith(
                    (
                        ".csv",
                        ".txt",
                        ".tsv",
                    )
                )
            ]

            if not files:
                raise ValueError(
                    "UNCTAD ZIP archive contains "
                    "no CSV/TXT/TSV data file."
                )

            preferred = [
                name
                for name in files
                if "concent" in name.lower()
                or "divers" in name.lower()
            ]

            filename = (
                preferred[0]
                if preferred
                else files[0]
            )

            print(
                "Selected UNCTAD data file:"
            )
            print(
                f"  {filename}"
            )

            with archive.open(
                filename
            ) as file:

                return read_text_data(
                    file.read()
                )

    # Direct text/CSV fallback
    print(
        "UNCTAD response is not a detected "
        "7z or ZIP archive."
    )

    return read_text_data(
        content
    )


def identify_unctad_columns(data):
    """Identify UNCTAD data columns."""

    country_code_column = find_column(
        data.columns,
        [
            "Economy Code",
            "Economy code",
            "Country Code",
            "Country code",
            "ISO3",
            "ISO3 Code",
        ],
    )

    country_column = find_column(
        data.columns,
        [
            "Economy",
            "Country",
            "Country or Area",
        ],
    )

    year_column = find_column(
        data.columns,
        [
            "Year",
            "Time",
            "Period",
        ],
    )

    indicator_column = find_column(
        data.columns,
        [
            "Indicator",
            "Indicator Name",
            "Series",
            "Series Name",
        ],
    )

    value_column = find_column(
        data.columns,
        [
            "Value",
            "Observation Value",
            "Obs Value",
        ],
    )

    missing = []

    if country_code_column is None:
        missing.append(
            "country code"
        )

    if country_column is None:
        missing.append(
            "country"
        )

    if year_column is None:
        missing.append(
            "year"
        )

    if value_column is None:
        missing.append(
            "value"
        )

    if missing:
        raise ValueError(
            "Could not identify required UNCTAD "
            f"columns: {missing}. "
            f"Available columns: "
            f"{list(data.columns)}"
        )

    return (
        country_code_column,
        country_column,
        year_column,
        indicator_column,
        value_column,
    )


def select_import_concentration(
    data,
    indicator_column,
):
    """
    Select the official UNCTAD import product
    concentration series.
    """

    if indicator_column is None:
        return data.copy()

    text = (
        data[indicator_column]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    import_mask = text.str.contains(
        "import",
        na=False,
    )

    concentration_mask = text.str.contains(
        "concentration",
        na=False,
    )

    product_mask = text.str.contains(
        "product",
        na=False,
    )

    selected = data[
        import_mask
        & concentration_mask
        & product_mask
    ].copy()

    if selected.empty:

        selected = data[
            import_mask
            & concentration_mask
        ].copy()

    if selected.empty:

        available = (
            data[indicator_column]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            "Could not identify the official "
            "UNCTAD import product concentration "
            "series. Available indicators/series: "
            f"{available[:100]}"
        )

    return selected


def main():
    """Download and integrate UNCTAD data."""

    print("=" * 70)
    print(
        "JESI Strategic Autonomy"
    )
    print(
        "Official UNCTAD Import Product Concentration"
    )
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: "
            f"{INPUT_FILE}"
        )

    data = pd.read_csv(
        INPUT_FILE
    )

    required_columns = [
        "country_code",
        "country",
        "year",
        "eci",
        "high_tech_exports",
        "import_product_concentration",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns in autonomy input: "
            f"{missing_columns}"
        )

    data = data[
        data["country_code"].isin(
            COUNTRIES
        )
        & data["year"].between(
            2015,
            2024,
        )
    ].copy()

    if len(data) != 50:
        raise ValueError(
            "Expected 50 country-year rows "
            "in autonomy dataset, found "
            f"{len(data)}."
        )

    print()
    print(
        "Downloading official UNCTAD dataset..."
    )
    print(
        UNCTAD_URL
    )

    response = requests.get(
        UNCTAD_URL,
        timeout=120,
        headers={
            "User-Agent": (
                "JAS-JESI research pipeline "
                "official UNCTAD data download"
            )
        },
    )

    response.raise_for_status()

    print(
        f"UNCTAD download received: "
        f"{len(response.content):,} bytes"
    )

    unctad = read_unctad_download(
        response.content
    )

    print()
    print(
        f"UNCTAD rows downloaded: "
        f"{len(unctad):,}"
    )

    print()
    print(
        "UNCTAD columns detected:"
    )

    for column in unctad.columns:
        print(
            f"  - {column}"
        )

    (
        country_code_column,
        country_column,
        year_column,
        indicator_column,
        value_column,
    ) = identify_unctad_columns(
        unctad
    )

    print()
    print(
        "Identified UNCTAD columns:"
    )
    print(
        f"Country code : "
        f"{country_code_column}"
    )
    print(
        f"Country      : "
        f"{country_column}"
    )
    print(
        f"Year         : "
        f"{year_column}"
    )
    print(
        f"Indicator    : "
        f"{indicator_column}"
    )
    print(
        f"Value        : "
        f"{value_column}"
    )

    unctad = select_import_concentration(
        unctad,
        indicator_column,
    )

    unctad["country_code"] = (
        unctad[country_code_column]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    unctad["country"] = (
        unctad[country_column]
        .astype(str)
        .str.strip()
    )

    unctad["year"] = pd.to_numeric(
        unctad[year_column],
        errors="coerce",
    )

    unctad[
        "import_product_concentration"
    ] = pd.to_numeric(
        unctad[value_column],
        errors="coerce",
    )

    unctad = unctad[
        unctad["country_code"].isin(
            COUNTRIES
        )
        & unctad["year"].between(
            2015,
            2024,
        )
    ].copy()

    unctad["country"] = unctad[
        "country_code"
    ].map(COUNTRIES)

    unctad = unctad[
        [
            "country_code",
            "country",
            "year",
            "import_product_concentration",
        ]
    ].copy()

    unctad["year"] = (
        unctad["year"].astype(int)
    )

    unctad = unctad.dropna(
        subset=[
            "country_code",
            "year",
            "import_product_concentration",
        ]
    )

    if (
        (
            unctad[
                "import_product_concentration"
            ] < 0
        )
        | (
            unctad[
                "import_product_concentration"
            ] > 1
        )
    ).any():

        raise ValueError(
            "UNCTAD import product concentration "
            "values outside the expected 0-1 range "
            "were detected."
        )

    unctad = (
        unctad
        .drop_duplicates(
            subset=[
                "country_code",
                "year",
            ],
            keep="last",
        )
        .copy()
    )

    expected_keys = pd.MultiIndex.from_product(
        [
            list(COUNTRIES.keys()),
            list(range(2015, 2025)),
        ],
        names=[
            "country_code",
            "year",
        ],
    )

    actual_keys = pd.MultiIndex.from_frame(
        unctad[
            [
                "country_code",
                "year",
            ]
        ]
    )

    missing_keys = expected_keys.difference(
        actual_keys
    )

    if len(missing_keys) > 0:

        missing_display = [
            f"{country_code}-{year}"
            for country_code, year
            in missing_keys
        ]

        raise ValueError(
            "Official UNCTAD data are incomplete. "
            f"Missing {len(missing_display)} "
            "country-year observations: "
            f"{missing_display}"
        )

    if len(unctad) != 50:
        raise ValueError(
            "Expected exactly 50 official UNCTAD "
            "country-year observations, found "
            f"{len(unctad)}."
        )

    concentration = unctad[
        [
            "country_code",
            "year",
            "import_product_concentration",
        ]
    ].copy()

    data = data.drop(
        columns=[
            "import_product_concentration"
        ]
    )

    data = data.merge(
        concentration,
        on=[
            "country_code",
            "year",
        ],
        how="left",
        validate="one_to_one",
    )

    data["country"] = data[
        "country_code"
    ].map(COUNTRIES)

    if data[
        "import_product_concentration"
    ].isna().any():

        missing = data[
            "import_product_concentration"
        ].isna().sum()

        raise ValueError(
            "Official UNCTAD integration failed: "
            f"{missing} concentration observations "
            "remain missing."
        )

    data = data.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(
        drop=True
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        "Official UNCTAD import product "
        "concentration successfully integrated."
    )
    print(
        f"Rows: {len(data)}"
    )
    print(
        "Countries: "
        f"{data['country_code'].nunique()}"
    )
    print(
        "Period: "
        f"{data['year'].min()}-"
        f"{data['year'].max()}"
    )
    print(
        "Concentration range: "
        f"{data['import_product_concentration'].min():.6f} - "
        f"{data['import_product_concentration'].max():.6f}"
    )
    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
