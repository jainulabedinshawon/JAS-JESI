"""
JAS Unified Economic Strength Index (JESI)
Robustness Testing Module

Tests JESI stability under:

1. JAS strategic weights
2. Equal weights
3. Arithmetic aggregation
4. Geometric aggregation
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/results/jesi_country_year_2016_2023.csv"
)

OUTPUT_DIR = Path("data/results")

PILLARS = [
    "G",
    "P",
    "C",
    "R",
    "A",
]

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


def validate_weights(weights):
    """Validate JESI weighting scheme."""

    if set(weights.keys()) != set(PILLARS):
        raise ValueError(
            "Weight dictionary must contain exactly "
            "G, P, C, R, and A."
        )

    values = np.array(
        [weights[pillar] for pillar in PILLARS],
        dtype=float,
    )

    if np.any(values < 0):
        raise ValueError(
            "JESI weights cannot be negative."
        )

    if not np.isclose(values.sum(), 1.0):
        raise ValueError(
            "JESI weights must sum to 1."
        )


def arithmetic_score(row, weights):
    """Calculate weighted arithmetic JESI score."""

    values = np.array(
        [row[pillar] for pillar in PILLARS],
        dtype=float,
    )

    weight_values = np.array(
        [weights[pillar] for pillar in PILLARS],
        dtype=float,
    )

    if np.any(~np.isfinite(values)):
        raise ValueError(
            "Pillar values contain non-finite observations."
        )

    if np.any(values < 0) or np.any(values > 1):
        raise ValueError(
            "Pillar values must be between 0 and 1."
        )

    return float(
        100 * np.sum(
            values * weight_values
        )
    )


def geometric_score(row, weights):
    """Calculate weighted geometric JESI score."""

    values = np.array(
        [row[pillar] for pillar in PILLARS],
        dtype=float,
    )

    weight_values = np.array(
        [weights[pillar] for pillar in PILLARS],
        dtype=float,
    )

    if np.any(~np.isfinite(values)):
        raise ValueError(
            "Pillar values contain non-finite observations."
        )

    if np.any(values < 0) or np.any(values > 1):
        raise ValueError(
            "Pillar values must be between 0 and 1."
        )

    # Numerical protection for zero pillar scores.
    values = np.clip(
        values,
        1e-12,
        1.0,
    )

    return float(
        100
        * np.exp(
            np.sum(
                weight_values
                * np.log(values)
            )
        )
    )


def validate_input(df):
    """Validate the JESI country-year input dataset."""

    required = {
        "country_code",
        "country",
        "year",
        "JESI",
        *PILLARS,
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            "Input JESI dataset is missing columns: "
            f"{sorted(missing)}"
        )

    if df.empty:
        raise ValueError(
            "Input JESI dataset is empty."
        )

    duplicates = df[
        df.duplicated(
            subset=[
                "country_code",
                "year",
            ],
            keep=False,
        )
    ]

    if not duplicates.empty:
        raise ValueError(
            "Duplicate country-year observations "
            "found in JESI input."
        )

    for pillar in PILLARS:
        if df[pillar].isna().any():
            raise ValueError(
                f"Missing values found in pillar {pillar}."
            )

        if (
            (df[pillar] < 0).any()
            or (df[pillar] > 1).any()
        ):
            raise ValueError(
                f"Pillar {pillar} contains values "
                "outside [0, 1]."
            )

    if df["JESI"].isna().any():
        raise ValueError(
            "Missing JESI values found."
        )

    if (
        (df["JESI"] < 0).any()
        or (df["JESI"] > 100).any()
    ):
        raise ValueError(
            "JESI values must be between 0 and 100."
        )


def calculate_rank_series(series):
    """Calculate descending rank."""

    return (
        series.rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )


def main():
    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Robustness Testing Module")
    print("=" * 70)

    # ---------------------------------------------------------------
    # Validate weighting schemes
    # ---------------------------------------------------------------

    validate_weights(JAS_WEIGHTS)
    validate_weights(EQUAL_WEIGHTS)

    # ---------------------------------------------------------------
    # Load final JESI country-year dataset
    # ---------------------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing JESI input file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    validate_input(df)

    # ---------------------------------------------------------------
    # Calculate alternative aggregation methods
    # ---------------------------------------------------------------

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

    score_columns = [
        "JAS_arithmetic",
        "JAS_geometric",
        "Equal_arithmetic",
        "Equal_geometric",
    ]

    # ---------------------------------------------------------------
    # Validate alternative scores
    # ---------------------------------------------------------------

    for column in score_columns:
        if df[column].isna().any():
            raise ValueError(
                f"{column} contains missing values."
            )

        if (
            (df[column] < 0).any()
            or (df[column] > 100).any()
        ):
            raise ValueError(
                f"{column} contains values outside [0, 100]."
            )

    # ---------------------------------------------------------------
    # Country-level robustness results
    # ---------------------------------------------------------------

    country_results = (
        df.groupby(
            [
                "country_code",
                "country",
            ]
        )[score_columns]
        .mean()
        .reset_index()
    )

    # ---------------------------------------------------------------
    # Country-level rankings
    # ---------------------------------------------------------------

    for column in score_columns:
        country_results[
            f"{column}_rank"
        ] = calculate_rank_series(
            country_results[column]
        )

    # ---------------------------------------------------------------
    # Ranking differences
    # ---------------------------------------------------------------

    country_results[
        "rank_diff_JAS_vs_Equal"
    ] = (
        country_results["JAS_arithmetic_rank"]
        - country_results["Equal_arithmetic_rank"]
    )

    country_results[
        "rank_diff_Arithmetic_vs_Geometric"
    ] = (
        country_results["JAS_arithmetic_rank"]
        - country_results["JAS_geometric_rank"]
    )

    country_results[
        "score_diff_JAS_arithmetic_vs_geometric"
    ] = (
        country_results["JAS_arithmetic"]
        - country_results["JAS_geometric"]
    )

    country_results[
        "score_diff_JAS_vs_Equal"
    ] = (
        country_results["JAS_arithmetic"]
        - country_results["Equal_arithmetic"]
    )

    # ---------------------------------------------------------------
    # Rank correlations
    # ---------------------------------------------------------------

    jas_vs_equal = country_results[
        "JAS_arithmetic_rank"
    ].corr(
        country_results[
            "Equal_arithmetic_rank"
        ],
        method="spearman",
    )

    arithmetic_vs_geometric = country_results[
        "JAS_arithmetic_rank"
    ].corr(
        country_results[
            "JAS_geometric_rank"
        ],
        method="spearman",
    )

    jas_vs_equal_geometric = country_results[
        "JAS_arithmetic_rank"
    ].corr(
        country_results[
            "Equal_geometric_rank"
        ],
        method="spearman",
    )

    correlations = pd.DataFrame(
        {
            "comparison": [
                "JAS vs Equal",
                "Arithmetic vs Geometric",
                "JAS Arithmetic vs Equal Geometric",
            ],
            "spearman_correlation": [
                jas_vs_equal,
                arithmetic_vs_geometric,
                jas_vs_equal_geometric,
            ],
        }
    )

    # ---------------------------------------------------------------
    # Ranking stability summary
    # ---------------------------------------------------------------

    ranking_summary = pd.DataFrame(
        {
            "metric": [
                "Spearman: JAS vs Equal",
                "Spearman: Arithmetic vs Geometric",
                "Maximum absolute rank difference: JAS vs Equal",
                "Maximum absolute rank difference: Arithmetic vs Geometric",
                "Maximum absolute score difference: JAS vs Equal",
                "Maximum absolute score difference: Arithmetic vs Geometric",
            ],
            "value": [
                jas_vs_equal,
                arithmetic_vs_geometric,
                country_results[
                    "rank_diff_JAS_vs_Equal"
                ]
                .abs()
                .max(),
                country_results[
                    "rank_diff_Arithmetic_vs_Geometric"
                ]
                .abs()
                .max(),
                country_results[
                    "score_diff_JAS_vs_Equal"
                ]
                .abs()
                .max(),
                country_results[
                    "score_diff_JAS_arithmetic_vs_geometric"
                ]
                .abs()
                .max(),
            ],
        }
    )

    # ---------------------------------------------------------------
    # Save outputs
    # ---------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    country_results_file = (
        OUTPUT_DIR
        / "jesi_robustness_country_results.csv"
    )

    correlations_file = (
        OUTPUT_DIR
        / "jesi_robustness_correlations.csv"
    )

    summary_file = (
        OUTPUT_DIR
        / "jesi_robustness_summary.csv"
    )

    country_results.to_csv(
        country_results_file,
        index=False,
    )

    correlations.to_csv(
        correlations_file,
        index=False,
    )

    ranking_summary.to_csv(
        summary_file,
        index=False,
    )

    # ---------------------------------------------------------------
    # Console output
    # ---------------------------------------------------------------

    print()
    print("Country-level robustness results:")
    print(
        country_results.to_string(
            index=False
        )
    )

    print()
    print("Rank correlations:")
    print(
        correlations.to_string(
            index=False
        )
    )

    print()
    print("Robustness summary:")
    print(
        ranking_summary.to_string(
            index=False
        )
    )

    print()
    print(
        f"Saved: {country_results_file}"
    )

    print(
        f"Saved: {correlations_file}"
    )

    print(
        f"Saved: {summary_file}"
    )

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print(
        "JESI robustness testing completed successfully."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
