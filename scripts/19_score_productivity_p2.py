"""
JESI Productivity P2 Scoring

P2 indicator:
    Total Factor Productivity (TFP) Growth

Input:
    data/raw/productivity_p2_tfp_growth_2015_2023.csv

Expected input columns:
    country_code
    country
    year
    tfp
    tfp_growth

Final JESI sample:
    Bangladesh
    India
    Indonesia
    Malaysia
    Vietnam

Years:
    2016–2023

Output:
    data/processed/productivity_p2_scores_2016_2023.csv
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT
    / "data"
    / "raw"
    / "productivity_p2_tfp_growth_2015_2023.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "productivity_p2_scores_2016_2023.csv"
)

EXPECTED_COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
    "VNM": "Vietnam",
}

EXPECTED_YEARS = set(range(2016, 2024))


def main() -> None:
    print("=" * 72)
    print("JESI PRODUCTIVITY P2 SCORING")
    print("=" * 72)

    # ------------------------------------------------------------------
    # Load input
    # ------------------------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: "
            f"{INPUT_FILE.relative_to(ROOT)}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(
        f"Input: {INPUT_FILE.relative_to(ROOT)}"
    )
    print(f"Loaded rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # ------------------------------------------------------------------
    # Validate required columns
    # ------------------------------------------------------------------

    required_columns = {
        "country_code",
        "country",
        "year",
        "tfp_growth",
    }

    missing_columns = sorted(
        required_columns - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            "P2 input file missing columns: "
            f"{missing_columns}"
        )

    # ------------------------------------------------------------------
    # Standardize country codes
    # ------------------------------------------------------------------

    df["country_code"] = (
        df["country_code"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["country"] = (
        df["country"]
        .astype("string")
        .str.strip()
    )

    # Keep only expected countries.
    df = df[
        df["country_code"].isin(
            EXPECTED_COUNTRIES
        )
    ].copy()

    if df.empty:
        raise ValueError(
            "No expected JESI countries found in P2 input."
        )

    # ------------------------------------------------------------------
    # Standardize year
    # ------------------------------------------------------------------

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    if df["year"].isna().any():
        raise ValueError(
            "P2 input contains invalid year values."
        )

    df["year"] = df["year"].astype(int)

    # Keep final JESI sample.
    df = df[
        df["year"].isin(
            EXPECTED_YEARS
        )
    ].copy()

    if df.empty:
        raise ValueError(
            "No P2 observations remain for "
            "the 2016–2023 sample."
        )

    # ------------------------------------------------------------------
    # Standardize TFP growth
    # ------------------------------------------------------------------

    df["tfp_growth"] = pd.to_numeric(
        df["tfp_growth"],
        errors="coerce",
    )

    if df["tfp_growth"].isna().all():
        raise ValueError(
            "All TFP growth observations are missing."
        )

    # ------------------------------------------------------------------
    # Remove missing TFP growth observations
    # ------------------------------------------------------------------

    df = df.dropna(
        subset=["tfp_growth"]
    ).copy()

    if df.empty:
        raise ValueError(
            "No non-missing TFP growth observations remain."
        )

    # ------------------------------------------------------------------
    # Duplicate validation
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Standardize country names from country codes
    # ------------------------------------------------------------------

    df["country"] = df["country_code"].map(
        EXPECTED_COUNTRIES
    )

    # ------------------------------------------------------------------
    # Pooled percentile scoring
    #
    # Higher TFP growth = higher P2 score.
    #
    # Percentile rank is calculated across the complete
    # five-country sample for 2016–2023.
    # ------------------------------------------------------------------

    df["productivity_p2_score"] = (
        df["tfp_growth"]
        .rank(
            method="average",
            pct=True,
        )
    )

    # Avoid zero values because JESI uses a geometric
    # aggregation and therefore requires positive scores.
    df["productivity_p2_score"] = (
        df["productivity_p2_score"]
        .clip(
            lower=1e-6,
            upper=1.0,
        )
    )

    # ------------------------------------------------------------------
    # Expected completeness
    # ------------------------------------------------------------------

    expected_rows = (
        len(EXPECTED_COUNTRIES)
        * len(EXPECTED_YEARS)
    )

    actual_rows = len(df)

    if actual_rows != expected_rows:
        expected_pairs = {
            (country_code, year)
            for country_code in EXPECTED_COUNTRIES
            for year in EXPECTED_YEARS
        }

        actual_pairs = set(
            zip(
                df["country_code"],
                df["year"],
            )
        )

        missing_pairs = sorted(
            expected_pairs - actual_pairs
        )

        raise ValueError(
            "Incomplete Productivity P2 sample. "
            f"Expected {expected_rows} observations, "
            f"found {actual_rows}. "
            f"Missing country-year pairs: {missing_pairs}"
        )

    # ------------------------------------------------------------------
    # Final output schema
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Final validation
    # ------------------------------------------------------------------

    if output["productivity_p2_score"].isna().any():
        raise ValueError(
            "P2 score contains missing values."
        )

    if (
        output["productivity_p2_score"] <= 0
    ).any():
        raise ValueError(
            "P2 score contains non-positive values."
        )

    if (
        output["productivity_p2_score"] > 1
    ).any():
        raise ValueError(
            "P2 score contains values above 1."
        )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 72)
    print("PRODUCTIVITY P2 SCORING SUCCESSFUL")
    print("=" * 72)
    print(
        f"Output: {OUTPUT_FILE.relative_to(ROOT)}"
    )
    print(f"Observations: {len(output)}")
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
        output.to_string(index=False)
    )
    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
