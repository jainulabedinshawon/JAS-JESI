"""
JESI Strategic Autonomy Pillar Construction
Master Version 1.0

Constructs the Strategic Autonomy (A) pillar from
three normalized indicator scores:

1. Economic Complexity Index (ECI)
2. High-Tech Exports
3. Import Product Concentration

Baseline aggregation:
    Arithmetic mean

Robustness aggregation:
    Geometric mean
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/processed/autonomy_indicator_scores_2015_2024.csv"
)

OUTPUT_FILE = Path(
    "data/processed/strategic_autonomy_pillar_2015_2024.csv"
)

SCORE_COLUMNS = [
    "eci_score",
    "high_tech_exports_score",
    "import_product_concentration_score",
]


def main():
    print("=" * 70)
    print("JESI Strategic Autonomy Pillar Construction")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    missing_columns = [
        column
        for column in SCORE_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing score columns: {missing_columns}"
        )

    if df[SCORE_COLUMNS].isna().any().any():
        raise ValueError(
            "Missing Strategic Autonomy scores detected."
        )

    # ------------------------------------------------------------
    # Validate score range
    # ------------------------------------------------------------

    for column in SCORE_COLUMNS:
        if (
            (df[column] < 0).any()
            or (df[column] > 1).any()
        ):
            raise ValueError(
                f"{column} contains values outside [0, 1]."
            )

    # ------------------------------------------------------------
    # Baseline: arithmetic mean
    # ------------------------------------------------------------

    df["strategic_autonomy_arithmetic"] = (
        df[SCORE_COLUMNS].mean(axis=1)
    )

    # ------------------------------------------------------------
    # Robustness: geometric mean
    # ------------------------------------------------------------

    # Scores are clipped very slightly away from zero
    # to avoid numerical issues in the logarithm.
    geometric_values = np.clip(
        df[SCORE_COLUMNS].to_numpy(dtype=float),
        1e-12,
        1.0,
    )

    df["strategic_autonomy_geometric"] = np.exp(
        np.log(geometric_values).mean(axis=1)
    )

    # ------------------------------------------------------------
    # Country-year output
    # ------------------------------------------------------------

    output_columns = [
        "country_code",
        "country",
        "year",
        "eci_score",
        "high_tech_exports_score",
        "import_product_concentration_score",
        "strategic_autonomy_arithmetic",
        "strategic_autonomy_geometric",
    ]

    df[output_columns].to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # ------------------------------------------------------------
    # Country-level summary
    # ------------------------------------------------------------

    country_summary = (
        df.groupby("country")[
            [
                "strategic_autonomy_arithmetic",
                "strategic_autonomy_geometric",
            ]
        ]
        .mean()
        .sort_values(
            "strategic_autonomy_arithmetic",
            ascending=False,
        )
    )

    summary_file = Path(
        "data/processed/"
        "strategic_autonomy_country_summary_2015_2024.csv"
    )

    country_summary.to_csv(summary_file)

    # ------------------------------------------------------------
    # Console output
    # ------------------------------------------------------------

    print()
    print("Strategic Autonomy pillar — country averages:")
    print(country_summary)

    print()
    print("Overall arithmetic mean:")
    print(
        df["strategic_autonomy_arithmetic"].mean()
    )

    print()
    print("Overall geometric mean:")
    print(
        df["strategic_autonomy_geometric"].mean()
    )

    print()
    print(f"Output: {OUTPUT_FILE}")
    print(f"Summary: {summary_file}")

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print("Strategic Autonomy pillar construction completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
