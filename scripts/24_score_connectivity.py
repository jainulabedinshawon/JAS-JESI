"""
JESI Connectivity Indicator Scoring
JAS Unified Economic Strength Index (JESI)

Script 24:
Score Connectivity indicators using empirical reference zones.

Baseline:
    P10-P90

Robustness:
    P05-P95

All Connectivity indicators are positive-direction indicators.
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/raw/connectivity_indicators_2015_2024.csv"
)

PERCENTILE_FILE = Path(
    "data/processed/connectivity_pooled_percentiles.csv"
)

OUTPUT_FILE = Path(
    "data/processed/connectivity_indicator_scores_2015_2024.csv"
)


INDICATORS = [
    "trade_openness",
    "fdi_inflows",
    "internet_use",
]


def normalize_positive(value, lower, upper):
    """Normalize a positive-direction indicator to 0-1."""

    if upper <= lower:
        raise ValueError(
            "Upper reference value must be greater than lower."
        )

    score = (value - lower) / (upper - lower)

    return max(0.0, min(1.0, score))


def main():
    """Run Connectivity indicator scoring."""

    data = pd.read_csv(INPUT_FILE)
    percentiles = pd.read_csv(PERCENTILE_FILE)

    required_columns = [
        "country_code",
        "country",
        "year",
        *INDICATORS,
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

    percentile_columns = [
        "indicator",
        "P05",
        "P10",
        "P90",
        "P95",
    ]

    missing_percentiles = [
        column
        for column in percentile_columns
        if column not in percentiles.columns
    ]

    if missing_percentiles:
        raise ValueError(
            f"Missing percentile columns: {missing_percentiles}"
        )

    reference = percentiles.set_index("indicator")

    for indicator in INDICATORS:
        if indicator not in reference.index:
            raise ValueError(
                f"Missing percentile data for {indicator}."
            )

    output = data.copy()

    for indicator in INDICATORS:
        lower_baseline = float(
            reference.loc[indicator, "P10"]
        )
        upper_baseline = float(
            reference.loc[indicator, "P90"]
        )

        lower_robustness = float(
            reference.loc[indicator, "P05"]
        )
        upper_robustness = float(
            reference.loc[indicator, "P95"]
        )

        output[f"{indicator}_score"] = output[
            indicator
        ].apply(
            lambda value: normalize_positive(
                value,
                lower_baseline,
                upper_baseline,
            )
        )

        output[f"{indicator}_score_robust"] = output[
            indicator
        ].apply(
            lambda value: normalize_positive(
                value,
                lower_robustness,
                upper_robustness,
            )
        )

    score_columns = [
        f"{indicator}_score"
        for indicator in INDICATORS
    ]

    robust_score_columns = [
        f"{indicator}_score_robust"
        for indicator in INDICATORS
    ]

    output["connectivity_indicator_mean"] = output[
        score_columns
    ].mean(axis=1)

    output["connectivity_indicator_mean_robust"] = output[
        robust_score_columns
    ].mean(axis=1)

    numeric_columns = (
        score_columns
        + robust_score_columns
        + [
            "connectivity_indicator_mean",
            "connectivity_indicator_mean_robust",
        ]
    )

    if not np.isfinite(
        output[numeric_columns].to_numpy()
    ).all():
        raise ValueError(
            "Non-finite values found in Connectivity scores."
        )

    if (
        output[numeric_columns].min().min() < 0
        or output[numeric_columns].max().max() > 1
    ):
        raise ValueError(
            "Connectivity scores must remain between 0 and 1."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("Connectivity scoring completed.")
    print(f"Rows: {len(output)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
