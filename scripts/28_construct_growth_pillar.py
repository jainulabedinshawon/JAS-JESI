"""
JAS Unified Economic Strength Index
Growth Pillar Construction

Purpose
-------
Construct the final Growth pillar score from the two validated
Growth indicator percentile scores.

Input
-----
data/processed/growth_pillar_scores_2015_2024.csv

Required columns
----------------
country_code
country
year
real_gdp_growth
gni_per_capita_growth
real_gdp_growth_percentile
gni_per_capita_growth_percentile
growth_score

Output
------
data/processed/growth_pillar_scores_2015_2024.csv

Notes
-----
The Growth indicator scoring is performed in script 27.

This script validates the resulting Growth pillar and preserves
the validated growth_score for downstream JESI calculation.
"""

from pathlib import Path
import sys

import pandas as pd


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/growth_pillar_scores_2015_2024.csv"
)

OUTPUT_FILE = Path(
    "data/processed/growth_pillar_scores_2015_2024.csv"
)

EXPECTED_COUNTRIES = {
    "BGD",
    "IND",
    "IDN",
    "MYS",
    "VNM",
}

EXPECTED_YEARS = set(range(2015, 2025))

REQUIRED_COLUMNS = {
    "country_code",
    "country",
    "year",
    "real_gdp_growth",
    "gni_per_capita_growth",
    "real_gdp_growth_percentile",
    "gni_per_capita_growth_percentile",
    "growth_score",
}


# ---------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------

def fail(message: str) -> None:
    """Stop execution with a clear validation error."""
    raise RuntimeError(message)


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def validate_schema(data: pd.DataFrame) -> None:
    """Validate the Growth pillar schema."""

    missing = REQUIRED_COLUMNS.difference(
        data.columns
    )

    if missing:
        fail(
            "Growth pillar output is missing required columns: "
            f"{sorted(missing)}"
        )


def validate_country_year(data: pd.DataFrame) -> None:
    """Validate country and year coverage."""

    countries = set(
        data["country_code"]
        .dropna()
        .astype(str)
    )

    unexpected = countries.difference(
        EXPECTED_COUNTRIES
    )

    if unexpected:
        fail(
            "Unexpected country codes found in Growth pillar: "
            f"{sorted(unexpected)}"
        )

    years = set(
        pd.to_numeric(
            data["year"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
    )

    unexpected_years = years.difference(
        EXPECTED_YEARS
    )

    if unexpected_years:
        fail(
            "Unexpected years found in Growth pillar: "
            f"{sorted(unexpected_years)}"
        )


def validate_duplicates(data: pd.DataFrame) -> None:
    """Ensure one observation per country-year."""

    duplicates = data[
        data.duplicated(
            subset=[
                "country_code",
                "year",
            ],
            keep=False,
        )
    ]

    if not duplicates.empty:
        fail(
            "Duplicate Growth country-year observations detected:\n"
            + duplicates[
                [
                    "country_code",
                    "year",
                ]
            ]
            .drop_duplicates()
            .to_string(index=False)
        )


def validate_scores(data: pd.DataFrame) -> None:
    """Validate percentile and pillar score ranges."""

    score_columns = [
        "real_gdp_growth_percentile",
        "gni_per_capita_growth_percentile",
        "growth_score",
    ]

    for column in score_columns:
        values = pd.to_numeric(
            data[column],
            errors="coerce",
        )

        if values.isna().any():
            fail(
                f"Missing or non-numeric values found in {column}."
            )

        if not values.between(
            0.001,
            1.0,
        ).all():
            fail(
                f"Values outside the valid 0.001-1.0 range "
                f"found in {column}."
            )


def validate_indicator_values(data: pd.DataFrame) -> None:
    """Validate raw Growth indicator values."""

    for column in [
        "real_gdp_growth",
        "gni_per_capita_growth",
    ]:
        values = pd.to_numeric(
            data[column],
            errors="coerce",
        )

        if values.isna().any():
            fail(
                f"Missing or non-numeric values found in {column}."
            )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:
    """Validate and finalize the Growth pillar."""

    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Growth Pillar Construction")
    print("=" * 70)

    if not INPUT_FILE.exists():
        fail(
            f"Missing Growth scoring output: {INPUT_FILE}"
        )

    data = pd.read_csv(INPUT_FILE)

    print(
        f"Loaded {len(data)} Growth pillar observations."
    )

    # Schema validation.
    validate_schema(data)

    # Normalize year.
    data["year"] = pd.to_numeric(
        data["year"],
        errors="coerce",
    )

    if data["year"].isna().any():
        fail(
            "Growth pillar contains invalid year values."
        )

    data["year"] = data["year"].astype(int)

    # Validation.
    validate_country_year(data)
    validate_duplicates(data)
    validate_indicator_values(data)
    validate_scores(data)

    # -------------------------------------------------------------
    # Reconstruct / verify Growth pillar score
    # -------------------------------------------------------------
    #
    # Baseline Growth pillar:
    #
    # G = arithmetic mean of:
    #     Real GDP Growth percentile
    #     GNI per Capita Growth percentile
    #
    # This is consistent with the JESI pillar-construction
    # methodology and avoids silently changing the score.
    #

    calculated_growth_score = (
        data["real_gdp_growth_percentile"]
        + data["gni_per_capita_growth_percentile"]
    ) / 2.0

    score_difference = (
        calculated_growth_score
        - data["growth_score"]
    ).abs()

    if not (
        score_difference <= 1e-10
    ).all():
        failed_rows = data.loc[
            score_difference > 1e-10,
            [
                "country_code",
                "year",
                "growth_score",
            ],
        ].copy()

        failed_rows["calculated_growth_score"] = (
            calculated_growth_score[
                score_difference > 1e-10
            ]
        )

        fail(
            "Growth pillar score does not match the arithmetic "
            "mean of its two indicator percentile scores.\n"
            + failed_rows.to_string(index=False)
        )

    # Use the explicitly reconstructed baseline score.
    data["growth_score"] = calculated_growth_score.clip(
        lower=0.001,
        upper=1.0,
    )

    # -------------------------------------------------------------
    # Final ordering
    # -------------------------------------------------------------

    data = data.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)

    # -------------------------------------------------------------
    # Final validation
    # -------------------------------------------------------------

    if data.empty:
        fail(
            "Growth pillar output is empty."
        )

    if data["growth_score"].isna().any():
        fail(
            "Growth pillar contains missing growth_score values."
        )

    if not data["growth_score"].between(
        0.001,
        1.0,
    ).all():
        fail(
            "Growth pillar scores are outside the valid range."
        )

    # Ensure all five countries are represented.
    actual_countries = set(
        data["country_code"]
    )

    if actual_countries != EXPECTED_COUNTRIES:
        fail(
            "Growth pillar country coverage mismatch.\n"
            f"Expected: {sorted(EXPECTED_COUNTRIES)}\n"
            f"Found: {sorted(actual_countries)}"
        )

    # -------------------------------------------------------------
    # Save
    # -------------------------------------------------------------

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
        f"Growth pillar output written to: {OUTPUT_FILE}"
    )

    print(
        f"Final observations: {len(data)}"
    )

    print(
        "Country coverage:"
    )

    for country_code in sorted(
        data["country_code"].unique()
    ):
        count = int(
            (
                data["country_code"]
                == country_code
            ).sum()
        )

        print(
            f"  - {country_code}: {count} observations"
        )

    print()
    print(
        "Growth Pillar Construction completed successfully."
    )

    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        raise
