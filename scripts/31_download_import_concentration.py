"""
JESI Strategic Autonomy
Official UNCTAD Import Product Concentration Download

Script 31:
Download the official UNCTAD merchandise import product
concentration index and integrate it into the JESI
Strategic Autonomy dataset.

Period:
    2015-2024

Countries:
    Bangladesh, India, Viet Nam, Indonesia, Malaysia
"""

from pathlib import Path
import csv
import io
import re
import tempfile
import zipfile

import pandas as pd
import requests

try:
    import py7zr
except ImportError:
    py7zr = None


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

START_YEAR = 2015
END_YEAR = 2024
EXPECTED_ROWS = 50


def normalize_text(value):
    """Normalize text for robust country matching."""

    if pd.isna(value):
        return ""

    text = str(value).strip().upper()

    text = re.sub(
        r"\[[^\]]*\]",
        " ",
        text,
    )

    text = re.sub(
        r"\([^)]*\)",
        " ",
        text,
    )

    text = re.sub(
        r"[^A-Z0-9]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def map_country_name(value):
    """
    Map UNCTAD Economy text to JESI ISO3 code.

    Handles variants such as:
    Bangladesh
    Bangladesh [050]
    050 Bangladesh
    Viet Nam
    Viet Nam [704]
    etc.
    """

    normalized = normalize_text(value)

    if not normalized:
        return None

    if "BANGLADESH" in normalized:
        return "BGD"

    if normalized == "INDIA":
        return "IND"

    if normalized.startswith("INDIA "):
        return "IND"

    if "VIET NAM" in normalized:
        return "VNM"

    if "VIETNAM" in normalized:
        return "VNM"

    if "INDONESIA" in normalized:
        return "IDN"

    if "MALAYSIA" in normalized:
        return "MYS"

    return None


def detect_delimiter(text):
    sample = text[:10000]

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",;\t|",
        )

        return dialect.delimiter

    except csv.Error:

        candidates = [
            ",",
            ";",
            "\t",
            "|",
        ]

        counts = {
            delimiter: sample.count(delimiter)
            for delimiter in candidates
        }

        delimiter = max(
            counts,
            key=counts.get,
        )

        if counts[delimiter] == 0:
            raise ValueError(
                "Could not detect the UNCTAD "
                "file delimiter."
            )

        return delimiter


def read_text_data(raw_bytes):
    """Read extracted UNCTAD text data."""

    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp1252",
        "latin-1",
    ]

    attempts = []

    for encoding in encodings:

        try:
            text = raw_bytes.decode(
                encoding
            )

        except UnicodeDecodeError as exc:

            attempts.append(
                f"{encoding}: {exc}"
            )

            continue

        try:

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

            dataframe = pd.read_csv(
                io.StringIO(text),
                sep=delimiter,
                engine="python",
            )

            if dataframe.empty:
                raise ValueError(
                    "Parsed UNCTAD dataframe "
                    "is empty."
                )

            return dataframe

        except Exception as exc:

            attempts.append(
                f"{encoding}: {exc}"
            )

    raise ValueError(
        "Could not parse extracted UNCTAD "
        f"data. Attempts: {attempts}"
    )


def extract_archive(raw_bytes):
    """Extract UNCTAD ZIP or 7z archive."""

    signature = raw_bytes[:6]

    with tempfile.TemporaryDirectory() as temp_dir:

        temp_path = Path(temp_dir)

        archive_path = (
            temp_path / "unctad_download"
        )

        archive_path.write_bytes(
            raw_bytes
        )

        extracted_dir = (
            temp_path / "extracted"
        )

        extracted_dir.mkdir()

        if raw_bytes[:2] == b"PK":

            print(
                "Detected UNCTAD ZIP archive."
            )

            with zipfile.ZipFile(
                archive_path,
                "r",
            ) as archive:

                names = archive.namelist()

                print(
                    "Files inside UNCTAD archive:"
                )

                for name in names:
                    print(f"  - {name}")

                archive.extractall(
                    extracted_dir
                )

        elif signature == (
            b"7z\xbc\xaf'\x1c"
        ):

            if py7zr is None:
                raise ImportError(
                    "py7zr is required to "
                    "extract the UNCTAD 7z archive."
                )

            print(
                "Detected UNCTAD 7z archive."
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
                    print(f"  - {name}")

                archive.extractall(
                    path=extracted_dir
                )

        else:

            return raw_bytes

        files = []

        for path in extracted_dir.rglob("*"):

            if not path.is_file():
                continue

            if path.suffix.lower() in {
                ".csv",
                ".txt",
                ".tsv",
            }:

                files.append(path)

        if not files:
            raise ValueError(
                "No CSV, TXT, or TSV file was "
                "found inside the UNCTAD archive."
            )

        preferred = [
            path
            for path in files
            if (
                "concent" in path.name.lower()
                or "divers" in path.name.lower()
            )
        ]

        selected = (
            preferred[0]
            if preferred
            else files[0]
        )

        print(
            "Selected UNCTAD data file:"
        )

        print(
            f"  {selected.name}"
        )

        return selected.read_bytes()


def download_unctad():
    """Download official UNCTAD dataset."""

    print(
        "Downloading official UNCTAD dataset..."
    )

    print(UNCTAD_URL)

    response = requests.get(
        UNCTAD_URL,
        timeout=120,
    )

    response.raise_for_status()

    raw_bytes = response.content

    print(
        "UNCTAD download received: "
        f"{len(raw_bytes):,} bytes"
    )

    return raw_bytes


def find_column(
    dataframe,
    candidates,
):
    """Find a dataframe column robustly."""

    normalized = {
        str(column).strip().lower(): column
        for column in dataframe.columns
    }

    for candidate in candidates:

        key = candidate.lower()

        if key in normalized:
            return normalized[key]

    for column in dataframe.columns:

        column_text = (
            str(column)
            .strip()
            .lower()
        )

        for candidate in candidates:

            if candidate.lower() in column_text:
                return column

    return None


def identify_unctad_columns(
    dataframe,
):
    """Identify UNCTAD columns."""

    country_code_column = find_column(
        dataframe,
        [
            "Economy Code",
            "Country Code",
            "country_code",
            "ISO3",
            "ISO3 Code",
        ],
    )

    country_column = find_column(
        dataframe,
        [
            "Economy",
            "Country",
            "country",
            "Country or Area",
        ],
    )

    year_column = find_column(
        dataframe,
        [
            "Year",
            "year",
        ],
    )

    concentration_column = find_column(
        dataframe,
        [
            "Import product concentration",
            "Import product concentration index",
            "Product concentration",
            "Concentration Index",
            "Concentration",
        ],
    )

    print(
        "UNCTAD columns detected:"
    )

    print(
        f"  country_code: "
        f"{country_code_column}"
    )

    print(
        f"  country: "
        f"{country_column}"
    )

    print(
        f"  year: "
        f"{year_column}"
    )

    print(
        f"  concentration: "
        f"{concentration_column}"
    )

    if year_column is None:
        raise ValueError(
            "Could not identify UNCTAD "
            "year column."
        )

    if concentration_column is None:
        raise ValueError(
            "Could not identify the official "
            "UNCTAD concentration column."
        )

    if (
        country_code_column is None
        and country_column is None
    ):
        raise ValueError(
            "Could not identify UNCTAD country "
            "or country-code column."
        )

    return (
        country_code_column,
        country_column,
        year_column,
        concentration_column,
    )


def standardize_unctad(
    dataframe,
):
    """Standardize UNCTAD observations."""

    (
        country_code_column,
        country_column,
        year_column,
        concentration_column,
    ) = identify_unctad_columns(
        dataframe
    )

    data = dataframe.copy()

    # -------------------------------------------------
    # Country text
    # -------------------------------------------------

    if country_column is not None:

        data["country"] = (
            data[country_column]
            .astype(str)
            .str.strip()
        )

    else:

        data["country"] = ""

    # -------------------------------------------------
    # Country code
    # -------------------------------------------------

    if country_code_column is not None:

        data["country_code"] = (
            data[country_code_column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    else:

        data["country_code"] = ""

    # If UNCTAD does not provide ISO3,
    # derive it from Economy.

    mapped_codes = data[
        "country"
    ].apply(
        map_country_name
    )

    valid_existing_codes = (
        data["country_code"]
        .isin(COUNTRIES)
    )

    data.loc[
        ~valid_existing_codes,
        "country_code",
    ] = mapped_codes[
        ~valid_existing_codes
    ]

    # -------------------------------------------------
    # Year
    # -------------------------------------------------

    data["year"] = pd.to_numeric(
        data[year_column],
        errors="coerce",
    )

    # -------------------------------------------------
    # Concentration
    # -------------------------------------------------

    data[
        "import_product_concentration"
    ] = pd.to_numeric(
        data[concentration_column],
        errors="coerce",
    )

    # -------------------------------------------------
    # Diagnostics BEFORE filtering
    # -------------------------------------------------

    print(
        "Country mapping diagnostics:"
    )

    for code, name in COUNTRIES.items():

        count = (
            data["country_code"]
            == code
        ).sum()

        print(
            f"  {code} ({name}): "
            f"{count} rows"
        )

    # -------------------------------------------------
    # Filter required sample
    # -------------------------------------------------

    data = data[
        data["country_code"].isin(
            COUNTRIES
        )
        & data["year"].between(
            START_YEAR,
            END_YEAR,
        )
    ].copy()

    data["year"] = (
        data["year"]
        .astype(int)
    )

    data["country"] = (
        data["country_code"]
        .map(COUNTRIES)
    )

    data = data[
        [
            "country_code",
            "country",
            "year",
            "import_product_concentration",
        ]
    ].copy()

    data = data.dropna(
        subset=[
            "import_product_concentration"
        ]
    )

    return data


def validate_unctad(
    data,
):
    """Validate required UNCTAD observations."""

    if data.empty:

        raise ValueError(
            "No UNCTAD observations found "
            "for the required countries "
            "and years."
        )

    if data[
        "import_product_concentration"
    ].isna().any():

        raise ValueError(
            "UNCTAD concentration data "
            "contain missing observations."
        )

    if (
        data[
            "import_product_concentration"
        ] < 0
    ).any():

        raise ValueError(
            "UNCTAD concentration values "
            "cannot be negative."
        )

    if (
        data[
            "import_product_concentration"
        ] > 1
    ).any():

        raise ValueError(
            "UNCTAD normalized concentration "
            "values must be between 0 and 1."
        )

    duplicates = data.duplicated(
        subset=[
            "country_code",
            "year",
        ]
    )

    if duplicates.any():

        raise ValueError(
            "Duplicate UNCTAD country-year "
            "observations detected."
        )

    expected_pairs = {
        (code, year)
        for code in COUNTRIES
        for year in range(
            START_YEAR,
            END_YEAR + 1,
        )
    }

    actual_pairs = set(
        zip(
            data["country_code"],
            data["year"],
        )
    )

    missing_pairs = (
        expected_pairs - actual_pairs
    )

    if missing_pairs:

        raise ValueError(
            "Missing UNCTAD country-year "
            f"observations: "
            f"{sorted(missing_pairs)}"
        )

    if len(data) != EXPECTED_ROWS:

        raise ValueError(
            f"Expected {EXPECTED_ROWS} "
            f"UNCTAD observations, "
            f"found {len(data)}."
        )


def integrate_with_autonomy(
    autonomy,
    unctad,
):
    """Merge UNCTAD data with autonomy data."""

    autonomy = autonomy.copy()

    autonomy["country_code"] = (
        autonomy["country_code"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    autonomy["year"] = pd.to_numeric(
        autonomy["year"],
        errors="coerce",
    )

    if autonomy["year"].isna().any():

        raise ValueError(
            "Autonomy dataset contains "
            "invalid years."
        )

    autonomy["year"] = (
        autonomy["year"]
        .astype(int)
    )

    autonomy = autonomy[
        autonomy["country_code"].isin(
            COUNTRIES
        )
        & autonomy["year"].between(
            START_YEAR,
            END_YEAR,
        )
    ].copy()

    if len(autonomy) != EXPECTED_ROWS:

        raise ValueError(
            "Expected 50 autonomy "
            f"country-year rows, found "
            f"{len(autonomy)}."
        )

    concentration = unctad[
        [
            "country_code",
            "year",
            "import_product_concentration",
        ]
    ].copy()

    merged = autonomy.drop(
        columns=[
            "import_product_concentration"
        ],
        errors="ignore",
    ).merge(
        concentration,
        on=[
            "country_code",
            "year",
        ],
        how="left",
        validate="one_to_one",
    )

    if len(merged) != EXPECTED_ROWS:

        raise ValueError(
            "UNCTAD integration changed "
            "the expected row count."
        )

    if merged[
        "import_product_concentration"
    ].isna().any():

        missing = merged[
            "import_product_concentration"
        ].isna().sum()

        raise ValueError(
            "UNCTAD integration still has "
            f"{missing} missing concentration "
            "observations."
        )

    merged["country"] = (
        merged["country_code"]
        .map(COUNTRIES)
    )

    return merged


def main():
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

    autonomy = pd.read_csv(
        INPUT_FILE
    )

    required_columns = [
        "country_code",
        "country",
        "year",
        "eci",
        "high_tech_exports",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in autonomy.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in autonomy input: "
            f"{missing_columns}"
        )

    raw_download = download_unctad()

    extracted_bytes = extract_archive(
        raw_download
    )

    unctad_raw = read_text_data(
        extracted_bytes
    )

    print(
        f"UNCTAD raw rows: "
        f"{len(unctad_raw)}"
    )

    print(
        f"UNCTAD raw columns: "
        f"{len(unctad_raw.columns)}"
    )

    unctad = standardize_unctad(
        unctad_raw
    )

    print(
        "UNCTAD filtered rows: "
        f"{len(unctad)}"
    )

    validate_unctad(
        unctad
    )

    complete = integrate_with_autonomy(
        autonomy,
        unctad,
    )

    complete.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "Strategic Autonomy dataset completed."
    )

    print(
        f"Rows: {len(complete)}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print(
        "Official UNCTAD import product "
        "concentration successfully integrated."
    )


if __name__ == "__main__":
    main()
