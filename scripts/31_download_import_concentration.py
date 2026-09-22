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
import zipfile

import pandas as pd
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
    """
    Detect the delimiter used by the UNCTAD text file.

    Prefer common delimiters and validate the result
    using the CSV sniffer.
    """

    sample = text[:100000]

    candidates = [
        ",",
        ";",
        "\t",
        "|",
    ]

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",;\t|",
        )

        detected = dialect.delimiter

        if detected in candidates:
            return detected

    except csv.Error:
        pass

    # Fallback based on header occurrence.
    first_line = text.splitlines()[0]

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
            "Could not detect the UNCTAD file delimiter."
        )

    return detected


def read_csv_with_fallbacks(content):
    """
    Read an UNCTAD CSV/text download robustly.

    Handles:
    - UTF-8
    - UTF-8 BOM
    - Windows-1252
    - Latin-1
    - comma
    - semicolon
    - tab
    - pipe delimiters
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
                f"Detected UNCTAD encoding: "
                f"{encoding}"
            )

            print(
                "Detected UNCTAD delimiter: "
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
                    "Detected only one column. "
                    "Delimiter detection may be incorrect."
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
        "Could not parse the UNCTAD download. "
        f"Attempts: {errors}"
    )


def read_unctad_download(content):
    """
    Read the UNCTAD bulk-download response.

    The endpoint may return a CSV/text file or a ZIP
    containing the official CSV file.
    """

    if content[:2] == b"PK":

        with zipfile.ZipFile(
            BytesIO(content)
        ) as archive:

            csv_files = [
                name
                for name in archive.namelist()
                if name.lower().endswith(
                    (".csv", ".txt")
                )
            ]

            if not csv_files:
                raise ValueError(
                    "UNCTAD download is a ZIP file, "
                    "but no CSV/TXT data file was found."
                )

            preferred = [
                name
                for name in csv_files
                if "concent" in name.lower()
            ]

            filename = (
                preferred[0]
                if preferred
                else csv_files[0]
            )

            print(
                f"Reading UNCTAD archive member: "
                f"{filename}"
            )

            with archive.open(filename) as file:
                file_content = file.read()

            return read_csv_with_fallbacks(
                file_content
            )

    return read_csv_with_fallbacks(
        content
    )


def identify_unctad_columns(data):
    """Identify country, year, indicator and value columns."""

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
        missing.append("country code")

    if country_column is None:
        missing.append("country")

    if year_column is None:
        missing.append("year")

    if value_column is None:
        missing.append("value")

    if missing:
        raise ValueError(
            "Could not identify required UNCTAD columns: "
            f"{missing}. Available columns: "
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
    concentration indicator.
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
            "Could not identify the official UNCTAD "
            "import product concentration series. "
            "Available indicators/series include: "
            f"{available[:50]}"
        )

    return selected


def main():
    """
    Download and integrate official UNCTAD
    import product concentration data.
    """

    print("=" * 70)
    print("JESI Strategic Autonomy")
    print("Official UNCTAD Import Product Concentration")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
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
            f"Missing columns in autonomy input: "
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
            "Expected 50 country-year rows in the "
            "autonomy dataset, found "
            f"{len(data)}."
        )

    print()
    print(
        "Downloading official UNCTAD dataset..."
    )
    print(UNCTAD_URL)

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

    print(
        f"UNCTAD rows downloaded: "
        f"{len(unctad):,}"
    )

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
