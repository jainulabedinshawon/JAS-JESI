"""
JESI Growth Pillar Distribution Analysis
JAS Unified Economic Strength Index (JESI)

Script 26:
Analyze the empirical distribution of Growth indicators.

Indicators:
    - Real GDP Growth Rate
    - GNI per Capita Growth

Reference zones:
    - P05-P95
    - P10-P90
    - P25-P75
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/raw/growth_indicators_2015_2025.csv"
)

OUTPUT_DIR = Path("data/processed")

INDICATORS = [
    "real_gdp_growth",
    "gni_per_capita_growth",
]


def main():
    """Run Growth distribution analysis."""

    data = pd.read_csv(INPUT_FILE)

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

    # Growth pillar common analysis period.
    # The real-data pipeline uses 2015-2024.
    data = data[
        data["year"].between(2015, 2024)
    ].copy()

    if data.empty:
        raise ValueError(
            "No Growth observations found for 2015-2024."
        )

    # Analyze each indicator using available observations.
    descriptive = data[INDICATORS].describe().T

    descriptive = descriptive.rename(
        columns={
            "count": "n",
            "mean": "mean",
            "std": "std",
            "min": "min",
            "25%": "p25",
            "50%": "p50",
            "75%": "p75",
            "max": "max",
        }
    )

    descriptive = descriptive[
        [
            "n",
            "mean",
            "std",
            "min",
            "p25",
            "p50",
            "p75",
            "max",
        ]
    ]

    descriptive.index.name = "indicator"

    # Pooled empirical percentiles.
    percentile_rows = []

    for indicator in INDICATORS:
        values = data[indicator].dropna()

        percentile_rows.append(
            {
                "indicator": indicator,
                "P01": np.percentile(values, 1),
                "P05": np.percentile(values, 5),
                "P10": np.percentile(values, 10),
                "P25": np.percentile(values, 25),
                "P50": np.percentile(values, 50),
                "P75": np.percentile(values, 75),
                "P90": np.percentile(values, 90),
                "P95": np.percentile(values, 95),
                "P99": np.percentile(values, 99),
            }
        )

    percentiles = pd.DataFrame(percentile_rows)

    # Candidate reference zones.
    reference_rows = []

    for _, row in percentiles.iterrows():
        reference_rows.append(
            {
                "indicator": row["indicator"],
                "P05_P95_lower": row["P05"],
                "P05_P95_upper": row["P95"],
                "P10_P90_lower": row["P10"],
                "P10_P90_upper": row["P90"],
                "P25_P75_lower": row["P25"],
                "P25_P75_upper": row["P75"],
            }
        )

    reference_zones = pd.DataFrame(reference_rows)

    # Country-level statistics.
    country_statistics = (
        data.groupby(["country_code", "country"])[INDICATORS]
        .agg(["count", "mean", "min", "max"])
        .reset_index()
    )

    # Country-year extremes.
    extreme_rows = []

    for indicator in INDICATORS:
        valid = data.dropna(
            subset=[indicator]
        )

        minimum = valid.loc[
            valid[indicator].idxmin()
        ]

        maximum = valid.loc[
            valid[indicator].idxmax()
        ]

        extreme_rows.append(
            {
                "indicator": indicator,
                "minimum_value": minimum[indicator],
                "minimum_country": minimum["country"],
                "minimum_year": minimum["year"],
                "maximum_value": maximum[indicator],
                "maximum_country": maximum["country"],
                "maximum_year": maximum["year"],
            }
        )

    extremes = pd.DataFrame(extreme_rows)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptive.to_csv(
        OUTPUT_DIR
        / "growth_pooled_descriptive_statistics.csv"
    )

    country_statistics.to_csv(
        OUTPUT_DIR
        / "growth_country_statistics.csv",
        index=False,
    )

    percentiles.to_csv(
        OUTPUT_DIR
        / "growth_pooled_percentiles.csv",
        index=False,
    )

    reference_zones.to_csv(
        OUTPUT_DIR
        / "growth_candidate_reference_zones.csv",
        index=False,
    )

    extremes.to_csv(
        OUTPUT_DIR
        / "growth_country_year_extremes.csv",
        index=False,
    )

    print("Growth distribution analysis completed.")
    print(f"Analysis period: 2015-2024")
    print(f"Rows: {len(data)}")
    print()
    print("Missing observations:")
    print(data[INDICATORS].isna().sum())
    print()
    print("Pooled percentiles:")
    print(percentiles.to_string(index=False))
    print()
    print("Output directory:")
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()
