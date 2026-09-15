"""
JESI Growth Indicator Scoring
JAS Unified Economic Strength Index (JESI)

Script 27:
Score Growth indicators using empirical reference zones.

Baseline:
    P10-P90

Robustness:
    P05-P95

Both Growth indicators are positive-direction indicators.
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/raw/growth_indicators_2015_2025.csv"
)

PERCENTILE_FILE = Path(
    "data/processed/growth_pooled_percentiles.csv"
)

OUTPUT_FILE = Path(
    "data/processed/growth_indicator_scores_2015_2024.csv"
)

INDICATORS = [
    "real_gdp_growth",
    "gni_per_capita_growth",
]


def normalize_positive(value, lower, upper):
    """Normalize a positive-direction indicator to 0-1."""

    if pd.isna(value):
        return np.nan

    if upper <= lower:
        raise ValueError(
            "Upper reference value must be greater than lower."
        )

    score = (value - lower) / (upper - lower)

    return max(0.0, min(1.0, score))


def main():
    """Run Growth indicator scoring."""

    data = pd.read_csv(INPUT_FILE)
    percentiles = pd.read_csv(PERCENTILE_FILE)

    data = data[
        data["year"].between(2015, 2024)
    ].copy()

    reference = percentiles.set_index("indicator")

    for indicator in INDICATORS:
        if indicator not in reference.index:
            raise ValueError(
                f"Missing percentile data for {indicator}."
            )

    output = data.copy()

    for indicator in INDICATORS:
        p10 = float(reference.loc[indicator, "P10"])
        p90 = float(reference.loc[indicator, "P90"])
        p05 = float(reference.loc[indicator, "P05"])
        p95 = float(reference.loc[indicator, "P95"])

        output[f"{indicator}_score"] = output[
            indicator
        ].apply(
            lambda value: normalize_positive(
                value,
                p10,
                p90,
            )
        )

        output[f"{indicator}_score_robust"] = output[
            indicator
        ].apply(
            lambda value: normalize_positive(
                value,
                p05,
                p95,
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

    # Arithmetic mean of available indicator scores.
    output["growth_indicator_mean"] = output[
        score_columns
    ].mean(axis=1, skipna=True)

    output["growth_indicator_mean_robust"] = output[
        robust_score_columns
    ].mean(axis=1, skipna=True)

    # Require at least one valid Growth indicator.
    if output[score_columns].notna().sum(axis=1).eq(0).any():
        raise ValueError(
            "At least one valid Growth indicator is required."
        )

    # Verify all available scores are within [0, 1].
    numeric_columns = (
        score_columns
        + robust_score_columns
        + [
            "growth_indicator_mean",
            "growth_indicator_mean_robust",
        ]
    )

    available_values = output[numeric_columns].dropna()

    if not np.isfinite(
        available_values.to_numpy()
    ).all():
        raise ValueError(
            "Non-finite Growth scores found."
        )

    if (
        available_values.min().min() < 0
        or available_values.max().max() > 1
    ):
        raise ValueError(
            "Growth scores must remain between 0 and 1."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("Growth indicator scoring completed.")
    print(f"Rows: {len(output)}")
    print("Missing values:")
    print(output[INDICATORS].isna().sum())
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
