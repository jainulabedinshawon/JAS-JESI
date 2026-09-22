"""
JESI Productivity Pillar Construction

Constructs the Productivity pillar from:

P1:
    GDP per Person Employed

P2:
    Total Factor Productivity Growth

Baseline aggregation:
    Arithmetic mean

Alternative aggregation:
    Geometric mean

Final sample:
    Bangladesh, India, Indonesia, Malaysia, Vietnam
    2016–2023

Required P1 columns:
    country
    country_code
    year
    productivity_p1_score

Required P2 columns:
    country
    country_code
    year
    productivity_p2_score
"""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

P1_FILE = (
    ROOT
    / "data"
    / "processed"
    / "productivity_p1_scores_2016_2023.csv"
)

P2_FILE = (
    ROOT
    / "data"
    / "processed"
    / "productivity_p2_scores_2016_2023.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "productivity_pillar_scores_2016_2023.csv"
)

EXPECTED_COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
    "VNM": "Vietnam",
}

EXPECTED_YEARS = set(range(2016, 2024))


def validate_input(
    df: pd.DataFrame,
    name: str,
    score_column: str,
) -> None:
    required = {
        "country",
        "country_code",
        "year",
        score_column,
    }

    missing = sorted(required - set(df.columns))

    if missing:
        raise ValueError(
            f"{name} file missing columns: {missing}"
        )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    if df["year"].isna().any():
        raise ValueError(
            f"{name} contains invalid year values."
        )

    invalid_countries = set(df["country_code"]) - set(
        EXPECTED_COUNTRIES
    )

    if invalid_countries:
        raise ValueError(
            f"{name} contains unexpected country codes: "
            f"{sorted(invalid_countries)}"
        )

    invalid_years = set(df["year"].astype(int)) - EXPECTED_YEARS

    if invalid_years:
        raise ValueError(
            f"{name} contains unexpected years: "
            f"{sorted(invalid_years)}"
        )

    duplicates = df.duplicated(
        subset=["country_code", "year"],
        keep=False,
    )

    if duplicates.any():
        raise ValueError(
            f"{name} contains duplicate country-year "
            "observations."
        )

    df[score_column] = pd.to_numeric(
        df[score_column],
        errors="coerce",
    )

    if df[score_column].isna().any():
        raise ValueError(
            f"{name} contains missing values in "
            f"{score_column}."
        )

    if (
        (df[score_column] <= 0)
        | (df[score_column] > 1)
    ).any():
        raise ValueError(
            f"{name} contains scores outside (0, 1]."
        )


def main() -> None:
    print("=" * 72)
    print("JESI PRODUCTIVITY PILLAR CONSTRUCTION")
    print("=" * 72)

    # ---------------------------------------------------------------
    # Load P1
    # ---------------------------------------------------------------

    if not P1_FILE.exists():
        raise FileNotFoundError(
            f"P1 input file not found: "
            f"{P1_FILE.relative_to(ROOT)}"
        )

    if not P2_FILE.exists():
        raise FileNotFoundError(
            f"P2 input file not found: "
            f"{P2_FILE.relative_to(ROOT)}"
        )

    p1 = pd.read_csv(P1_FILE)
    p2 = pd.read_csv(P2_FILE)

    print(
        f"P1 input: {P1_FILE.relative_to(ROOT)}"
    )
    print(
        f"P2 input: {P2_FILE.relative_to(ROOT)}"
    )

    print(f"P1 rows: {len(p1)}")
    print(f"P2 rows: {len(p2)}")

    # ---------------------------------------------------------------
    # Validate inputs
    # ---------------------------------------------------------------

    validate_input(
        p1,
        "P1",
        "productivity_p1_score",
    )

    validate_input(
        p2,
        "P2",
        "productivity_p2_score",
    )

    p1["year"] = p1["year"].astype(int)
    p2["year"] = p2["year"].astype(int)

    # ---------------------------------------------------------------
    # Restrict to expected sample
    # ---------------------------------------------------------------

    p1 = p1[
        p1["country_code"].isin(EXPECTED_COUNTRIES)
        & p1["year"].isin(EXPECTED_YEARS)
    ].copy()

    p2 = p2[
        p2["country_code"].isin(EXPECTED_COUNTRIES)
        & p2["year"].isin(EXPECTED_YEARS)
    ].copy()

    # ---------------------------------------------------------------
    # Merge P1 and P2
    # ---------------------------------------------------------------

    merged = pd.merge(
        p1[
            [
                "country",
                "country_code",
                "year",
                "productivity_p1_score",
            ]
        ],
        p2[
            [
                "country_code",
                "year",
                "productivity_p2_score",
            ]
        ],
        on=["country_code", "year"],
        how="inner",
        validate="one_to_one",
    )

    if merged.empty:
        raise ValueError(
            "No overlapping P1/P2 country-year observations."
        )

    # Use standardized country names from the expected mapping.
    merged["country"] = merged["country_code"].map(
        EXPECTED_COUNTRIES
    )

    # ---------------------------------------------------------------
    # Completeness check
    # ---------------------------------------------------------------

    expected_observations = (
        len(EXPECTED_COUNTRIES)
        * len(EXPECTED_YEARS)
    )

    if len(merged) != expected_observations:
        missing = []

        for country_code in EXPECTED_COUNTRIES:
            for year in sorted(EXPECTED_YEARS):
                mask = (
                    (merged["country_code"] == country_code)
                    & (merged["year"] == year)
                )

                if not mask.any():
                    missing.append(
                        f"{country_code}-{year}"
                    )

        raise ValueError(
            "Productivity pillar does not contain the "
            f"expected {expected_observations} observations. "
            f"Found {len(merged)}. Missing: {missing}"
        )

    # ---------------------------------------------------------------
    # Baseline arithmetic aggregation
    # ---------------------------------------------------------------

    merged["productivity_score"] = (
        merged["productivity_p1_score"]
        + merged["productivity_p2_score"]
    ) / 2.0

    # ---------------------------------------------------------------
    # Alternative geometric aggregation
    # ---------------------------------------------------------------

    merged["productivity_geometric"] = np.sqrt(
        merged["productivity_p1_score"]
        * merged["productivity_p2_score"]
    )

    # ---------------------------------------------------------------
    # Final validation
    # ---------------------------------------------------------------

    for column in [
        "productivity_score",
        "productivity_geometric",
    ]:
        if (
            merged[column].isna().any()
            or (merged[column] <= 0).any()
            or (merged[column] > 1).any()
        ):
            raise ValueError(
                f"Invalid values detected in {column}."
            )

    merged = merged.sort_values(
        ["country_code", "year"]
    ).reset_index(drop=True)

    # ---------------------------------------------------------------
    # Final output
    # ---------------------------------------------------------------

    output = merged[
        [
            "country",
            "country_code",
            "year",
            "productivity_p1_score",
            "productivity_p2_score",
            "productivity_score",
            "productivity_geometric",
        ]
    ].copy()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("PRODUCTIVITY PILLAR CONSTRUCTION SUCCESSFUL")
    print("-" * 72)
    print(
        f"Output: {OUTPUT_FILE.relative_to(ROOT)}"
    )
    print(f"Observations: {len(output)}")
    print(
        f"Countries: {sorted(output['country_code'].unique())}"
    )
    print(
        f"Years: {output['year'].min()}–"
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
