"""
JESI Productivity P2 Scoring

Scores Total Factor Productivity Growth (TFP growth)
using empirically calibrated pooled reference zones.

Baseline:
    P10-P90

Robustness:
    P05-P95
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/raw/productivity_p2_tfp_growth_2015_2023.csv"
)

OUTPUT_FILE = Path(
    "data/processed/productivity_p2_scores_2016_2023.csv"
)


# Empirical pooled reference zones from the
# JESI five-country P2 distribution analysis.
P10_LOWER = -2.464743
P90_UPPER = 5.149487

P05_LOWER = -5.805382
P95_UPPER = 5.892609


START_YEAR = 2016
END_YEAR = 2023


def min_max_score(
    value: float,
    lower: float,
    upper: float,
) -> float:
    """Normalize a value to [0, 1] using a reference zone."""
    if upper <= lower:
        raise ValueError("Upper reference bound must exceed lower bound.")

    score = (value - lower) / (upper - lower)
    return float(np.clip(score, 0.0, 1.0))


def main() -> None:
    print("=" * 72)
    print("JESI PRODUCTIVITY P2 SCORING")
    print("=" * 72)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    dataframe = pd.read_csv(INPUT_FILE)

    required_columns = {
        "country_code",
        "country",
        "year",
        "tfp",
        "tfp_growth",
    }

    missing_columns = required_columns.difference(dataframe.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    dataframe = dataframe[
        (dataframe["year"] >= START_YEAR)
        & (dataframe["year"] <= END_YEAR)
    ].copy()

    dataframe["tfp_growth"] = pd.to_numeric(
        dataframe["tfp_growth"],
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=["tfp_growth"]
    ).copy()

    expected_rows = 40

    if len(dataframe) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} valid TFP growth observations, "
            f"found {len(dataframe)}."
        )

    # Baseline P10-P90 score.
    dataframe["p2_score_p10_p90"] = dataframe[
        "tfp_growth"
    ].apply(
        lambda value: min_max_score(
            value,
            P10_LOWER,
            P90_UPPER,
        )
    )

    # Robustness alternative: P05-P95.
    dataframe["p2_score_p05_p95"] = dataframe[
        "tfp_growth"
    ].apply(
        lambda value: min_max_score(
            value,
            P05_LOWER,
            P95_UPPER,
        )
    )

    # Final baseline P2 score.
    dataframe["p2_score"] = dataframe[
        "p2_score_p10_p90"
    ]

    output_columns = [
        "country_code",
        "country",
        "year",
        "tfp_growth",
        "p2_score",
        "p2_score_p10_p90",
        "p2_score_p05_p95",
    ]

    output = dataframe[output_columns].sort_values(
        ["country_code", "year"]
    )

    # Validation.
    if output["p2_score"].isna().any():
        raise ValueError("P2 score contains missing values.")

    if not output["p2_score"].between(0, 1).all():
        raise ValueError("P2 score must be between 0 and 1.")

    if not output["p2_score_p05_p95"].between(0, 1).all():
        raise ValueError(
            "P05-P95 robustness score must be between 0 and 1."
        )

    if output.duplicated(
        subset=["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations detected."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("SCORING REFERENCE ZONES")
    print("=" * 72)
    print(f"P10-P90 lower bound : {P10_LOWER:.6f}")
    print(f"P10-P90 upper bound : {P90_UPPER:.6f}")
    print(f"P05-P95 lower bound : {P05_LOWER:.6f}")
    print(f"P05-P95 upper bound : {P95_UPPER:.6f}")

    print()
    print("SCORE SUMMARY")
    print("=" * 72)
    print(
        output[
            [
                "p2_score",
                "p2_score_p05_p95",
            ]
        ].describe()
    )

    print()
    print("OUTPUT")
    print("=" * 72)
    print(f"Saved: {OUTPUT_FILE}")

    print()
    print(
        "JESI Productivity P2 scoring completed successfully."
    )


if __name__ == "__main__":
    main()
