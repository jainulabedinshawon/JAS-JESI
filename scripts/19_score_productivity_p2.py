"""
JESI Productivity P2 Scoring

P2 indicator:
    Total Factor Productivity (TFP) Growth

This script:
1. Reads Productivity P2 raw data.
2. Identifies country, year, and TFP growth.
3. Restricts the sample to:
       Bangladesh
       India
       Indonesia
       Malaysia
       Vietnam
       2016–2023
4. Computes pooled percentile scores.
5. Writes a standardized P2 score file.

Output:
    data/processed/productivity_p2_scores_2016_2023.csv

Output score column:
    productivity_p2_score
"""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT_CANDIDATES = [
    ROOT / "data" / "raw" / "productivity_p2_2016_2023.csv",
    ROOT / "data" / "raw" / "productivity_p2.csv",
    ROOT / "data" / "raw" / "productivity_p2_data_2016_2023.csv",
]

OUTPUT = (
    ROOT
    / "data"
    / "processed"
    / "productivity_p2_scores_2016_2023.csv"
)

COUNTRY_MAP = {
    "bangladesh": ("Bangladesh", "BGD"),
    "india": ("India", "IND"),
    "indonesia": ("Indonesia", "IDN"),
    "malaysia": ("Malaysia", "MYS"),
    "vietnam": ("Vietnam", "VNM"),
    "viet nam": ("Vietnam", "VNM"),
}

EXPECTED_COUNTRIES = {
    "BGD",
    "IND",
    "IDN",
    "MYS",
    "VNM",
}

EXPECTED_YEARS = set(range(2016, 2024))


def find_input_file() -> Path:
    for path in INPUT_CANDIDATES:
        if path.exists():
            return path

    raw_dir = ROOT / "data" / "raw"

    candidates = sorted(raw_dir.glob("*.csv"))

    for path in candidates:
        name = path.name.lower()

        if "productivity" in name and "p2" in name:
            return path

    raise FileNotFoundError(
        "No Productivity P2 input CSV found in data/raw."
    )


def detect_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    normalized = {
        str(column)
        .strip()
        .lower()
        .replace(" ", "_"): column
        for column in df.columns
    }

    for candidate in candidates:
        key = (
            candidate
            .lower()
            .replace(" ", "_")
        )

        if key in normalized:
            return normalized[key]

    return None


def normalize_country(
    value: object,
) -> tuple[str, str] | tuple[None, None]:

    if pd.isna(value):
        return None, None

    text = str(value).strip()
    key = text.lower()

    if key in COUNTRY_MAP:
        return COUNTRY_MAP[key]

    return None, None


def main() -> None:
    print("=" * 72)
    print("JESI PRODUCTIVITY P2 SCORING")
    print("=" * 72)

    input_file = find_input_file()

    print(f"Input: {input_file}")

    df = pd.read_csv(input_file)

    print(f"Loaded rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # ---------------------------------------------------------------
    # Detect columns
    # ---------------------------------------------------------------

    country_col = detect_column(
        df,
        [
            "country",
            "country_name",
            "economy",
            "location",
        ],
    )

    code_col = detect_column(
        df,
        [
            "country_code",
            "iso3",
            "iso3_code",
            "code",
        ],
    )

    year_col = detect_column(
        df,
        [
            "year",
            "time",
        ],
    )

    value_col = detect_column(
        df,
        [
            "tfp_growth",
            "tfp_growth_rate",
            "total_factor_productivity_growth",
            "total_factor_productivity_growth_rate",
            "productivity_p2",
            "p2",
            "value",
        ],
    )

    if year_col is None:
        raise ValueError(
            "Could not identify year column."
        )

    if value_col is None:
        raise ValueError(
            "Could not identify TFP growth value column."
        )

    if country_col is None and code_col is None:
        raise ValueError(
            "Could not identify country or country_code column."
        )

    # ---------------------------------------------------------------
    # Country normalization
    # ---------------------------------------------------------------

    df["country"] = np.nan
    df["country_code"] = np.nan

    if country_col is not None:
        normalized = df[country_col].apply(
            normalize_country
        )

        df["country"] = normalized.apply(
            lambda x: (
                x[0]
                if x[0] is not None
                else np.nan
            )
        )

        df["country_code"] = normalized.apply(
            lambda x: (
                x[1]
                if x[1] is not None
                else np.nan
            )
        )

    if code_col is not None:
        code_values = (
            df[code_col]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        code_to_country = {
            "BGD": "Bangladesh",
            "IND": "India",
            "IDN": "Indonesia",
            "MYS": "Malaysia",
            "VNM": "Vietnam",
        }

        for code, country in code_to_country.items():
            mask = (
                df["country_code"].isna()
                & (code_values == code)
            )

            df.loc[
                mask,
                "country_code",
            ] = code

            df.loc[
                mask,
                "country",
            ] = country

    # ---------------------------------------------------------------
    # Year and value
    # ---------------------------------------------------------------

    df["year"] = pd.to_numeric(
        df[year_col],
        errors="coerce",
    )

    df["tfp_growth"] = pd.to_numeric(
        df[value_col],
        errors="coerce",
    )

    df = df[
        df["country_code"].isin(
            EXPECTED_COUNTRIES
        )
        & df["year"].isin(
            EXPECTED_YEARS
        )
    ].copy()

    if df.empty:
        raise ValueError(
            "No valid Productivity P2 observations "
            "remain for the expected countries and years."
        )

    df["year"] = df["year"].astype(int)

    # ---------------------------------------------------------------
    # Duplicate validation
    # ---------------------------------------------------------------

    duplicates = df.duplicated(
        subset=[
            "country_code",
            "year",
        ],
        keep=False,
    )

    if duplicates.any():
        duplicate_rows = df.loc[
            duplicates,
            [
                "country_code",
                "year",
            ],
        ]

        raise ValueError(
            "Duplicate country-year observations found:\n"
            f"{duplicate_rows.to_string(index=False)}"
        )

    # ---------------------------------------------------------------
    # Missing values
    # ---------------------------------------------------------------

    df = df.dropna(
        subset=["tfp_growth"]
    ).copy()

    if df.empty:
        raise ValueError(
            "No non-missing TFP growth values remain."
        )

    # ---------------------------------------------------------------
    # Pooled percentile scoring
    #
    # Higher TFP growth = higher productivity score.
    # ---------------------------------------------------------------

    df["productivity_p2_score"] = (
        df["tfp_growth"]
        .rank(
            method="average",
            pct=True,
        )
    )

    df["productivity_p2_score"] = (
        df["productivity_p2_score"]
        .clip(
            lower=1e-6,
            upper=1.0,
        )
    )

    # ---------------------------------------------------------------
    # Final schema
    # ---------------------------------------------------------------

    output = df[
        [
            "country",
            "country_code",
            "year",
            "tfp_growth",
            "productivity_p2_score",
        ]
    ].copy()

    output = output.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)

    # ---------------------------------------------------------------
    # Completeness check
    # ---------------------------------------------------------------

    expected_rows = (
        len(EXPECTED_COUNTRIES)
        * len(EXPECTED_YEARS)
    )

    if len(output) != expected_rows:
        raise ValueError(
            "Unexpected number of P2 observations. "
            f"Expected {expected_rows}, found {len(output)}."
        )

    # ---------------------------------------------------------------
    # Save
    # ---------------------------------------------------------------

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
        "P2 scoring completed successfully."
    )
    print(
        f"Output: {OUTPUT}"
    )
    print(
        f"Rows: {len(output)}"
    )
    print(
        "Countries: "
        f"{sorted(output['country_code'].unique())}"
    )
    print(
        f"Years: "
        f"{output['year'].min()}–"
        f"{output['year'].max()}"
    )

    print()
    print(
        output.head(10).to_string(
            index=False
        )
    )

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
