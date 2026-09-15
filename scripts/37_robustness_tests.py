"""
JAS Unified Economic Strength Index (JESI)
Robustness Testing Module

Tests the stability of country rankings under:

1. JAS Strategic weights
2. Equal weights
3. Arithmetic vs geometric aggregation
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/results/jesi_country_year_2016_2023.csv"
)

OUTPUT_DIR = Path("data/results")


PILLARS = ["G", "P", "C", "R", "A"]


JAS_WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}


EQUAL_WEIGHTS = {
    "G": 0.20,
    "P": 0.20,
    "C": 0.20,
    "R": 0.20,
    "A": 0.20,
}


def arithmetic_score(row, weights):
    values = np.array(
        [row[p] for p in PILLARS],
        dtype=float,
    )

    weight_values = np.array(
        [weights[p] for p in PILLARS],
        dtype=float,
    )

    return 100 * np.sum(
        values * weight_values
    )


def geometric_score(row, weights):
    values = np.array(
        [row[p] for p in PILLARS],
        dtype=float,
    )

    values = np.clip(
        values,
        1e-12,
        1.0,
    )

    weight_values = np.array(
        [weights[p] for p in PILLARS],
        dtype=float,
    )

    return 100 * np.exp(
        np.sum(
            weight_values * np.log(values)
        )
    )


def main():
    print("=" * 70)
    print("JESI Robustness Testing")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required = {
        "country_code",
        "country",
        "year",
        *PILLARS,
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if df[PILLARS].isna().any().any():
        raise ValueError(
            "Missing pillar values detected."
        )

    # ------------------------------------------------------------
    # JAS strategic weights
    # ------------------------------------------------------------

    df["JAS_arithmetic"] = df.apply(
        lambda row: arithmetic_score(
            row,
            JAS_WEIGHTS,
        ),
        axis=1,
    )

    df["JAS_geometric"] = df.apply(
        lambda row: geometric_score(
            row,
            JAS_WEIGHTS,
        ),
        axis=1,
    )

    # ------------------------------------------------------------
    # Equal weights
    # ------------------------------------------------------------

    df["Equal_arithmetic"] = df.apply(
        lambda row: arithmetic_score(
            row,
            EQUAL_WEIGHTS,
        ),
        axis=1,
    )

    df["Equal_geometric"] = df.apply(
        lambda row: geometric_score(
            row,
            EQUAL_WEIGHTS,
        ),
        axis=1,
    )

    # ------------------------------------------------------------
    # Country-level averages
    # ------------------------------------------------------------

    score_columns = [
        "JAS_arithmetic",
        "JAS_geometric",
        "Equal_arithmetic",
        "Equal_geometric",
    ]

    country_results = (
        df.groupby(
            ["country_code", "country"]
        )[score_columns]
        .mean()
        .reset_index()
    )

    # ------------------------------------------------------------
    # Rankings
    # ------------------------------------------------------------

    for column in score_columns:
        rank_column = f"{column}_rank"

        country_results[rank_column] = (
            country_results[column]
            .rank(
                ascending=False,
                method="min",
            )
            .astype(int)
        )

    # ------------------------------------------------------------
    # Rank differences
    # ------------------------------------------------------------

    country_results["rank_diff_JAS_vs_Equal"] = (
        country_results["JAS_arithmetic_rank"]
        - country_results["Equal_arithmetic_rank"]
    )

    country_results["rank_diff_Arithmetic_vs_Geometric"] = (
        country_results["JAS_arithmetic_rank"]
        - country_results["JAS_geometric_rank"]
    )

    # ------------------------------------------------------------
    # Ranking correlations
    # ------------------------------------------------------------

    correlations = pd.DataFrame(
        {
            "comparison": [
                "JAS vs Equal",
                "Arithmetic vs Geometric",
            ],
            "spearman_correlation": [
                country_results[
                    "JAS_arithmetic_rank"
                ].corr(
                    country_results[
                        "Equal_arithmetic_rank"
                    ],
                    method="spearman",
                ),
                country_results[
                    "JAS_arithmetic_rank"
                ].corr(
                    country_results[
                        "JAS_geometric_rank"
                    ],
                    method="spearman",
                ),
            ],
        }
    )

    # ------------------------------------------------------------
    # Save results
    # ------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    country_results = country_results.sort_values(
        "JAS_arithmetic_rank"
    )

    country_results.to_csv(
        OUTPUT_DIR
        / "jesi_robustness_country_results.csv",
        index=False,
    )

    correlations.to_csv(
        OUTPUT_DIR
        / "jesi_robustness_correlations.csv",
        index=False,
    )

    # ------------------------------------------------------------
    # Console output
    # ------------------------------------------------------------

    print()
    print("Country robustness results:")
    print(country_results)

    print()
    print("Ranking correlations:")
    print(correlations)

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print("JESI robustness testing completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
