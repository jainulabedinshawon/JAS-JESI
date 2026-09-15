"""
JESI Growth Pillar Construction
JAS Unified Economic Strength Index (JESI)

Script 28:
Construct the Growth (G) pillar from:

1. Real GDP Growth Rate
2. GNI per Capita Growth

Baseline:
    Arithmetic mean

Robustness:
    Geometric mean when both indicators are available.
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/processed/growth_indicator_scores_2015_2024.csv"
)

OUTPUT_FILE = Path(
    "data/processed/growth_pillar_scores_2015_2024.csv"
)


INDICATORS = [
    "real_gdp_growth",
    "gni_per_capita_growth",
]


def main():
    """Construct the Growth pillar."""

    data = pd.read_csv(INPUT_FILE)

    required_columns = [
        "country_code",
        "country",
        "year",
        "real_gdp_growth_score",
        "gni_per_capita_growth_score",
        "real_gdp_growth_score_robust",
        "gni_per_capita_growth_score_robust",
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
        "real_gdp_growth_score",
        "gni_per_capita_growth_score",
    ]

    robust_columns = [
        "real_gdp_growth_score_robust",
        "gni_per_capita_growth_score_robust",
    ]

    # At least one valid Growth indicator is required.
    if data[score_columns].notna().sum(axis=1).eq(0).any():
        raise ValueError(
            "At least one Growth indicator is required."
        )

    # Baseline: arithmetic mean of available indicators.
    data["growth_score"] = data[
        score_columns
    ].mean(axis=1, skipna=True)

    # Robustness:
    # geometric mean only when both indicators are available.
    data["growth_score_geometric"] = np.nan

    both_available = data[
        robust_columns
    ].notna().all(axis=1)

    data.loc[
        both_available,
        "growth_score_geometric",
    ] = np.sqrt(
        data.loc[
            both_available,
            robust_columns[0],
        ]
        * data.loc[
            both_available,
            robust_columns[1],
        ]
    )

    pillar_columns = [
        "growth_score",
        "growth_score_geometric",
    ]

    available = data[pillar_columns].dropna(
        subset=["growth_score"]
    )

    if not np.isfinite(
        available[["growth_score"]].to_numpy()
    ).all():
        raise ValueError(
            "Non-finite Growth pillar scores found."
        )

    if (
        available["growth_score"].min() < 0
        or available["growth_score"].max() > 1
    ):
        raise ValueError(
            "Growth pillar scores must be between 0 and 1."
        )

    if data["growth_score_geometric"].notna().any():
        geometric_values = data[
            "growth_score_geometric"
        ].dropna()

        if not np.isfinite(
            geometric_values.to_numpy()
        ).all():
            raise ValueError(
                "Non-finite geometric Growth scores found."
            )

        if (
            geometric_values.min() < 0
            or geometric_values.max() > 1
        ):
            raise ValueError(
                "Geometric Growth scores must be between 0 and 1."
            )

    output_columns = [
        "country_code",
        "country",
        "year",
        "real_gdp_growth",
        "gni_per_capita_growth",
        "real_gdp_growth_score",
        "gni_per_capita_growth_score",
        "real_gdp_growth_score_robust",
        "gni_per_capita_growth_score_robust",
        "growth_score",
        "growth_score_geometric",
    ]

    output = data[
        [
            column
            for column in output_columns
            if column in data.columns
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

    print("Growth pillar construction completed.")
    print(f"Rows: {len(output)}")
    print()
    print("Missing Growth indicators:")
    print(output[INDICATORS].isna().sum())
    print()
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
