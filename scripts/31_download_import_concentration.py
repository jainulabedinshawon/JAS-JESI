"""
JESI Strategic Autonomy
UNCTAD Import Product Concentration Integration

Downloads the official UNCTAD merchandise product
concentration dataset and integrates import product
concentration into:

data/raw/autonomy_indicators_2015_2024.csv

Target countries:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia

Target period:
    2015-2024
"""

from io import BytesIO
from pathlib import Path
import csv
import re
import tempfile
import zipfile

import pandas as pd
import py7zr
import requests


INPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024.csv"
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

YEAR_MIN = 2015
YEAR_MAX = 2024


def normalize_text(value):
    """Normalize text for robust country matching."""

    text = str(value)

    text = (
        text
        .replace("\ufeff", " ")
        .replace("\xa0", " ")
        .strip()
        .upper()
    )

    text = re.sub(
        r"[^A-Z0-9]+",
        " ",
        text,
    )

    return " ".join(
        text.split()
    )


def normalize_column_name(column):
    """Normalize column names."""

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
    """Find a column using candidate names."""

    normalized = {
        normalize_column_name(column): column
        for column in columns
    }

    for candidate in candidates:

        key = normalize_column_name(
            candidate
        )

        if key in normalized:
            return normalized[key]

    return None


def detect_delimiter(text):
    """Detect CSV delimiter."""

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
            delimiter: first_line.count(
                delimiter
            )
            for delimiter in candidates
        }

        delimiter = max(
            counts,
            key=counts.get,
        )

        if counts[delimiter] == 0:

            raise ValueError(
                "Could not detect CSV delimiter."
            )

        return delimiter


def read_text_data(content):
    """Read CSV/TXT/TSV content."""

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
            )

            if len(data.columns) <= 1:

                raise ValueError(
                    "Only one column was detected."
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
        "Could not parse UNCTAD data. "
        f"Attempts: {errors}"
    )


def read_unctad_archive(content):
    """Read the UNCTAD bulk-download archive."""

    # -------------------------------------------------
    # 7z
    # -------------------------------------------------

    if content[:6] == b"7z\xbc\xaf'\x1c":

        print(
            "Detected UNCTAD 7z archive."
        )

        with tempfile.TemporaryDirectory() as temp_dir:

            archive_path = (
                Path(temp_dir)
                / "unctad_download.7z"
            )

            archive_path.write_bytes(
                content
            )

            extract_dir = (
                Path(temp_dir)
                / "extracted"
            )

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
                if (
                    path.is_file()
                    and path.suffix.lower()
                    in {
                        ".csv",
                        ".txt",
                        ".tsv",
                    }
                )
            ]

            if not data_files:

                raise ValueError(
                    "No CSV/TXT/TSV file found "
                    "inside UNCTAD 7z archive."
                )

            preferred = [
                path
                for path in data_files
                if (
                    "concent"
                    in path.name.lower()
                    or "divers"
                    in path.name.lower()
                )
            ]

            selected_file = (
                preferred[0]
                if preferred
                else data_files[0]
            )

            print(
                "Selected UNCTAD data file:"
            )

            print(
                f"  {selected_file.name}"
            )

            return read_text_data(
                selected_file.read_bytes()
            )

    # -------------------------------------------------
    # ZIP
    # -------------------------------------------------

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
                    "No CSV/TXT/TSV file found "
                    "inside UNCTAD ZIP archive."
                )

            preferred = [
                name
                for name in files
                if (
                    "concent"
                    in name.lower()
                    or "divers"
                    in name.lower()
                )
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

    # -------------------------------------------------
    # Plain CSV
    # -------------------------------------------------

    print(
        "UNCTAD response is not an archive."
    )

    return read_text_data(
        content
    )


def identify_columns(data):
    """Identify UNCTAD columns."""

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
            "Concentration Index",
        ],
    )

    if value_column is None:

        candidates = [
            column
            for column in data.columns
            if (
                "concentration"
                in str(column).lower()
            )
        ]

        if candidates:

            value_column = candidates[0]

    missing = []

    if country_column is None:
        missing.append("country")

    if year_column is None:
        missing.append("year")

    if value_column is None:
        missing.append("value")

    if missing:

        raise ValueError(
            "Could not identify required "
            f"UNCTAD columns: {missing}. "
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


def select_concentration_series(
    data,
    indicator_column,
):
    """
    Select the import product concentration
    series when a series/indicator column exists.
    """

    if indicator_column is None:

        return data.copy()

    series = (
        data[indicator_column]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    import_mask = series.str.contains(
        "IMPORT",
        na=False,
    )

    concentration_mask = (
        series.str.contains(
            "CONCENTRATION",
            na=False,
        )
    )

    product_mask = series.str.contains(
        "PRODUCT",
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

        print(
            "WARNING: Could not isolate "
            "import concentration series."
        )

        print(
            "Available UNCTAD indicators:"
        )

        values = (
            data[indicator_column]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .tolist()
        )

        for value in values[:100]:

            print(
                f"  [{value}]"
            )

        raise ValueError(
            "UNCTAD import concentration "
            "series could not be identified."
        )

    return selected


def country_from_label(label):
    """
    Convert an UNCTAD Economy label into
    the JESI country code.

    Matching uses both names and ISO3 codes.
    """

    normalized = normalize_text(
        label
    )

    # Bangladesh
    if (
        "BANGLADESH" in normalized
        or re.search(
            r"\bBGD\b",
            normalized,
        )
    ):
        return "BGD"

    # India
    if (
        "INDIA" in normalized
        or re.search(
            r"\bIND\b",
            normalized,
        )
    ):
        return "IND"

    # Viet Nam / Vietnam
    if (
        "VIET NAM" in normalized
        or "VIETNAM" in normalized
        or re.search(
            r"\bVNM\b",
            normalized,
        )
    ):
        return "VNM"

    # Indonesia
    if (
        "INDONESIA" in normalized
        or re.search(
            r"\bIDN\b",
            normalized,
        )
    ):
        return "IDN"

    # Malaysia
    if (
        "MALAYSIA" in normalized
        or re.search(
            r"\bMYS\b",
            normalized,
        )
    ):
        return "MYS"

    return None


def build_unctad_dataset(data):
    """Standardize and filter UNCTAD data."""

    (
        country_code_column,
        country_column,
        year_column,
        indicator_column,
        value_column,
    ) = identify_columns(
        data
    )

    print()
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
        f"  indicator: "
        f"{indicator_column}"
    )

    print(
        f"  value: "
        f"{value_column}"
    )

    data = select_concentration_series(
        data,
        indicator_column,
    )

    data = data.copy()

    data["unctad_country"] = (
        data[country_column]
        .astype(str)
        .str.strip()
    )

    data["country_code"] = (
        data["unctad_country"]
        .map(country_from_label)
    )

    # If an official ISO3 column exists,
    # use it as a fallback.
    if country_code_column is not None:

        official_codes = (
            data[country_code_column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        for code in COUNTRIES:

            mask = (
                data["country_code"].isna()
                & official_codes.eq(code)
            )

            data.loc[
                mask,
                "country_code",
            ] = code

    data["year"] = pd.to_numeric(
        data[year_column],
        errors="coerce",
    )

    data[
        "import_product_concentration"
    ] = pd.to_numeric(
        data[value_column],
        errors="coerce",
    )

    # -------------------------------------------------
    # Economy diagnostics
    # -------------------------------------------------

    print()
    print(
        "UNCTAD Economy sample values:"
    )

    economy_values = (
        data["unctad_country"]
        .drop_duplicates()
        .head(50)
        .tolist()
    )

    for value in economy_values:

        print(
            f"  [{value}]"
        )

    print()
    print(
        "UNCTAD target-country mapping:"
    )

    for code, name in COUNTRIES.items():

        matches = data[
            data["country_code"].eq(code)
        ]

        print(
            f"  {code} ({name}): "
            f"{len(matches)} rows"
        )

    filtered = data[
        data["country_code"].isin(
            COUNTRIES
        )
        & data["year"].between(
            YEAR_MIN,
            YEAR_MAX,
        )
        & data[
            "import_product_concentration"
        ].notna()
    ].copy()

    print()
    print(
        "UNCTAD filtered rows: "
        f"{len(filtered)}"
    )

    return filtered


def validate_unctad_dataset(data):
    """Validate 50 country-year observations."""

    expected_rows = 50

    if len(data) != expected_rows:

        counts = (
            data.groupby(
                "country_code"
            )["year"]
            .nunique()
            .to_dict()
        )

        print()
        print(
            "UNCTAD country-year counts:"
        )

        for code in COUNTRIES:

            print(
                f"  {code}: "
                f"{counts.get(code, 0)} years"
            )

        raise ValueError(
            "UNCTAD import concentration "
            f"must contain exactly {expected_rows} "
            f"country-year observations. "
            f"Found {len(data)}."
        )

    duplicates = data.duplicated(
        subset=[
            "country_code",
            "year",
        ],
        keep=False,
    )

    if duplicates.any():

        duplicate_rows = data.loc[
            duplicates,
            [
                "country_code",
                "year",
                "unctad_country",
                "import_product_concentration",
            ],
        ]

        print(
            "Duplicate UNCTAD observations:"
        )

        print(
            duplicate_rows.to_string(
                index=False
            )
        )

        raise ValueError(
            "Duplicate UNCTAD "
            "country-year observations found."
        )

    expected_pairs = {
        (
            code,
            year,
        )
        for code in COUNTRIES
        for year in range(
            YEAR_MIN,
            YEAR_MAX + 1,
        )
    }

    actual_pairs = set(
        zip(
            data["country_code"],
            data["year"].astype(int),
        )
    )

    missing_pairs = sorted(
        expected_pairs - actual_pairs
    )

    if missing_pairs:

        raise ValueError(
            "Missing UNCTAD country-year "
            f"observations: {missing_pairs}"
        )

    if (
        data[
            "import_product_concentration"
        ] < 0
    ).any():

        raise ValueError(
            "Negative UNCTAD concentration "
            "values detected."
        )

    if (
        data[
            "import_product_concentration"
        ] > 1
    ).any():

        print(
            "WARNING: Some UNCTAD concentration "
            "values are above 1."
        )

    print()
    print(
        "UNCTAD validation:"
    )

    print(
        "  Observations: 50"
    )

    print(
        "  Countries: 5"
    )

    print(
        "  Period: 2015-2024"
    )

    print(
        "  Duplicate country-years: 0"
    )

    print(
        "  Missing concentration values: 0"
    )


def integrate_into_autonomy(
    unctad_data
):
    """Integrate UNCTAD values into autonomy data."""

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
        "import_product_concentration",
    ]

    missing = [
        column
        for column in required_columns
        if column not in autonomy.columns
    ]

    if missing:

        raise ValueError(
            "Autonomy input is missing "
            f"required columns: {missing}"
        )

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

    concentration_lookup = (
        unctad_data[
            [
                "country_code",
                "year",
                "import_product_concentration",
            ]
        ]
        .drop_duplicates(
            subset=[
                "country_code",
                "year",
            ]
        )
    )

    autonomy = autonomy.drop(
        columns=[
            "import_product_concentration"
        ],
        errors="ignore",
    )

    autonomy = autonomy.merge(
        concentration_lookup,
        on=[
            "country_code",
            "year",
        ],
        how="left",
        validate="one_to_one",
    )

    autonomy.to_csv(
        INPUT_FILE,
        index=False,
    )

    print()
    print(
        "UNCTAD integration completed."
    )

    print(
        f"Updated file: {INPUT_FILE}"
    )

    print()
    print(
        "Import product concentration "
        "missing observations after integration:"
    )

    missing_count = int(
        autonomy[
            "import_product_concentration"
        ].isna().sum()
    )

    print(
        f"  {missing_count}"
    )

    if missing_count != 0:

        raise ValueError(
            "UNCTAD integration completed, "
            "but missing concentration "
            f"observations remain: "
            f"{missing_count}"
        )

    print()
    print(
        "Strategic Autonomy concentration "
        "data is now complete."
    )


def main():
    """Main execution."""

    print("=" * 70)

    print(
        "JESI Strategic Autonomy"
    )

    print(
        "Official UNCTAD Import Product "
        "Concentration Integration"
    )

    print("=" * 70)

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
                "JAS-JESI research pipeline"
            )
        },
    )

    response.raise_for_status()

    print(
        "UNCTAD download received: "
        f"{len(response.content):,} bytes"
    )

    raw_data = read_unctad_archive(
        response.content
    )

    print()
    print(
        "UNCTAD raw rows: "
        f"{len(raw_data):,}"
    )

    print(
        "UNCTAD raw columns: "
        f"{len(raw_data.columns)}"
    )

    unctad_data = build_unctad_dataset(
        raw_data
    )

    validate_unctad_dataset(
        unctad_data
    )

    integrate_into_autonomy(
        unctad_data
    )

    print()
    print(
        "STATUS: SUCCESS"
    )

    print(
        "UNCTAD import product concentration "
        "data successfully integrated."
    )


if __name__ == "__main__":
    main()
