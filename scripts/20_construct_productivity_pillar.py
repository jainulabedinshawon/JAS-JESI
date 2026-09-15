"""
JESI Productivity Pillar Construction

Combines:
    P1 - GDP per Person Employed
    P2 - Total Factor Productivity Growth

Common analysis period:
    2016-2023

Baseline aggregation:
    Arithmetic mean

Robustness alternative:
    Geometric mean
"""

from pathlib import Path

import numpy as np
import pandas as pd


P1_FILE = Path(
    "data/processed/productivity_p1_scores_2015_2024.csv"
)

P2_FILE = Path(
    "data/processed/productivity_p2_scores_2016_2023.csv"
)

OUTPUT_FILE = Path(
    "data/processed/productivity_pillar_scores_2016_2023.csv"
)

START_YEAR = 2016
END_YEAR = 2023

EXPECTED_COUNTRIES = {
    "BGD",
    "IND",
    "IDN",
    "MYS",
    "VNM",
}


def validate_score(
    dataframe: pd.DataFrame,
    column: str,
    label: str,
) -> None:
    """Validate that a score column contains valid [0,1] values."""
    if dataframe[column].isna().any():
        raise ValueError(
            f"{label} contains missing values."
        )

    if not dataframe[column].between(0, 1).all():
        raise ValueError(
            f"{label} must be between 0 and 1."
        )


def main() -> None:
    print("=" * 72)
    print("JESI PRODUCTIVITY PILLAR CONSTRUCTION")
    print("=" * 72)

    if not P1_FILE.exists():
        raise FileNotFoundError(
            f"P1 input file not found: {P1_FILE}"
        )

    if not P2_FILE.exists():
        raise FileNotFoundError(
            f"P2 input file not found: {P2_FILE}"
        )

    p1 = pd.read_csv(P1_FILE)
    p2 = pd.read_csv(P2_FILE)

    required_p1 = {
        "country_code",
        "country",
        "year",
        "p1_score",
    }

    required_p2 = {
        "country_code",
        "country",
        "year",
        "p2_score",
    }

    missing_p1 = required_p1.difference(p1.columns)
    missing_p2 = required_p2.difference(p2.columns)

    if missing_p1:
        raise ValueError(
            f"P1 file missing columns: {sorted(missing_p1)}"
        )

    if missing_p2:
        raise ValueError(
            f"P2 file missing columns: {sorted(missing_p2)}"
        )

    # Restrict both components to the common period.
    p1 = p1[
        (p1["year"] >= START_YEAR)
        & (p1["year"] <= END_YEAR)
    ].copy()

    p2 = p2[
        (p2["year"] >= START_YEAR)
        & (p2["year"] <= END_YEAR)
    ].copy()

    # Keep only the fields required for pillar construction.
    p1 = p1[
        [
            "country_code",
            "country",
            "year",
            "p1_score",
        ]
    ]

    p2 = p2[
        [
            "country_code",
            "country",
            "year",
            "p2_score",
        ]
    ]

    # Validate country coverage.
    if set(p1["country_code"]) != EXPECTED_COUNTRIES:
        raise ValueError(
            "P1 country coverage does not match expected JESI countries."
        )

    if set(p2["country_code"]) != EXPECTED_COUNTRIES:
        raise ValueError(
            "P2 country coverage does not match expected JESI countries."
        )

    # Validate uniqueness before merging.
    if p1.duplicated(
        subset=["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate P1 country-year observations detected."
        )

    if p2.duplicated(
        subset=["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate P2 country-year observations detected."
        )

    # Validate component scores.
    validate_score(
        p1,
        "p1_score",
        "P1 score",
    )

    validate_score(
        p2,
        "p2_score",
        "P2 score",
    )

    # Merge P1 and P2 on common country-year observations.
    merged = pd.merge(
        p1,
        p2,
        on=["country_code", "year"],
        how="inner",
        suffixes=("_p1", "_p2"),
    )

    expected_rows = 5 * (
        END_YEAR - START_YEAR + 1
    )

    if len(merged) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} common country-year observations, "
            f"found {len(merged)}."
        )

    if merged["p1_score"].isna().any():
        raise ValueError(
            "Missing P1 score after merge."
        )

    if merged["p2_score"].isna().any():
        raise ValueError(
            "Missing P2 score after merge."
        )

    # ---------------------------------------------------------------
    # Baseline: arithmetic aggregation
    # ---------------------------------------------------------------
    merged["productivity_score_arithmetic"] = (
        merged["p1_score"] + merged["p2_score"]
    ) / 2.0

    # ---------------------------------------------------------------
    # Robustness: geometric aggregation
    # ---------------------------------------------------------------
    merged["productivity_score_geometric"] = np.sqrt(
        merged["p1_score"] * merged["p2_score"]
    )

    # Baseline Productivity pillar.
    merged["productivity_score"] = merged[
        "productivity_score_arithmetic"
    ]

    # Final validation.
    validate_score(
        merged,
        "productivity_score",
        "Productivity pillar score",
    )

    validate_score(
        merged,
        "productivity_score_geometric",
        "Geometric Productivity score",
    )

    output = merged[
        [
            "country_code",
            "country_p1",
            "year",
            "p1_score",
            "p2_score",
            "productivity_score",
            "productivity_score_arithmetic",
            "productivity_score_geometric",
        ]
    ].rename(
        columns={
            "country_p1": "country",
        }
    )

    output = output.sort_values(
        ["country_code", "year"]
    ).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("COMMON PRODUCTIVITY PERIOD")
    print("=" * 72)
    print(f"{START_YEAR}-{END_YEAR}")

    print()
    print("COUNTRIES")
    print("=" * 72)
    print(", ".join(sorted(EXPECTED_COUNTRIES)))

    print()
    print("OBSERVATIONS")
    print("=" * 72)
    print(len(output))

    print()
    print("PRODUCTIVITY AGGREGATION")
    print("=" * 72)
    print("Baseline     : Arithmetic mean")
    print("Robustness   : Geometric mean")

    print()
    print("PRODUCTIVITY SCORE SUMMARY")
    print("=" * 72)
    print(
        output[
            [
                "productivity_score",
                "productivity_score_geometric",
            ]
        ].describe()
    )

    print()
    print("OUTPUT")
    print("=" * 72)
    print(f"Saved: {OUTPUT_FILE}")

    print()
    print(
        "JESI Productivity pillar construction completed successfully."
    )


if __name__ == "__main__":
    main()
