"""
JESI Connectivity Pillar Construction
JAS Unified Economic Strength Index (JESI)

Script 25:
Construct the Connectivity (C) pillar from three
normalized indicator scores.

Baseline:
    Arithmetic mean

Robustness:
    Geometric mean
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/processed/connectivity_indicator_scores_2015_2024.csv"
)

OUTPUT_FILE = Path(
    "data/processed/connectivity_pillar_scores_2015_2024.csv"
)


INDICATORS = [
    "trade_openness",
    "fdi_inflows",
    "internet_use",
]


def main():
    """Construct the Connectivity pillar."""

    data = pd.read_csv(INPUT_FILE)

    required_columns = [
        "country_code",
        "country",
        "year",
        "trade_openness_score",
        "fdi_inflows_score",
        "internet_use_score",
        "trade_openness_score_robust",
        "fdi_inflows_score_robust",
        "internet_use_score_robust",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    score_columns = [
        f"{indicator}_score"
        for indicator in INDICATORS
    ]

    robust_score_columns = [
        f"{indicator}_score_robust"
        for indicator in INDICATORS
    ]

    if data[score_columns].isna().any().any():
        raise ValueError(
            "Missing baseline Connectivity scores."
        )

    if data[robust_score_columns].isna().any().any():
        raise ValueError(
            "Missing robustness Connectivity scores."
        )

    if (
        data[score_columns].min().min() < 0
        or data[score_columns].max().max() > 1
    ):
        raise ValueError(
            "Baseline Connectivity scores must be between 0 and 1."
        )

    if (
        data[robust_score_columns].min().min() < 0
        or data[robust_score_columns].max().max() > 1
    ):
        raise ValueError(
            "Robustness Connectivity scores must be between 0 and 1."
        )

    # Baseline Connectivity pillar:
    # arithmetic mean of the three indicator scores.
    data["connectivity_score"] = data[
        score_columns
    ].mean(axis=1)

    # Robustness Connectivity pillar:
    # geometric mean of the three indicator scores.
    data["connectivity_score_geometric"] = np.prod(
        data[robust_score_columns],
        axis=1,
    ) ** (1 / len(robust_score_columns))

    pillar_columns = [
        "connectivity_score",
        "connectivity_score_geometric",
    ]

    if not np.isfinite(
        data[pillar_columns].to_numpy()
    ).all():
        raise ValueError(
            "Non-finite Connectivity pillar scores found."
        )

    if (
        data[pillar_columns].min().min() < 0
        or data[pillar_columns].max().max() > 1
    ):
        raise ValueError(
            "Connectivity pillar scores must be between 0 and 1."
        )

    output_columns = [
        "country_code",
        "country",
        "year",
        "trade_openness",
        "fdi_inflows",
        "internet_use",
        "trade_openness_score",
        "fdi_inflows_score",
        "internet_use_score",
        "trade_openness_score_robust",
        "fdi_inflows_score_robust",
        "internet_use_score_robust",
        "connectivity_score",
        "connectivity_score_geometric",
    ]

    output_columns = [
        column
        for column in output_columns
        if column in data.columns
    ]

    output = data[output_columns].copy()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("Connectivity pillar construction completed.")
    print(f"Rows: {len(output)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
