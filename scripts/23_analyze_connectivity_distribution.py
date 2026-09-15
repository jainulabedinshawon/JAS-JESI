"""
JESI Connectivity Distribution Analysis
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/raw/connectivity_indicators_2015_2024.csv"
)

OUTPUT_DIR = Path("data/processed")

START_YEAR = 2015
END_YEAR = 2024

INDICATORS = [
    "trade_openness",
    "fdi_inflows",
    "internet_use",
]

PERCENTILES = [
    1, 5, 10, 25, 50, 75, 90, 95, 99
]


def main():
    print("=" * 72)
    print("JESI CONNECTIVITY DISTRIBUTION ANALYSIS")
    print("=" * 72)

    dataframe = pd.read_csv(INPUT_FILE)

    dataframe = dataframe[
        (dataframe["year"] >= START_YEAR)
        & (dataframe["year"] <= END_YEAR)
    ].copy()

    expected_rows = 50

    if len(dataframe) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, "
            f"found {len(dataframe)}."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Pooled descriptive statistics
    # ---------------------------------------------------------------
    descriptive_records = []

    for indicator in INDICATORS:
        series = dataframe[indicator].dropna()

        descriptive_records.append(
            {
                "indicator": indicator,
                "count": series.count(),
                "mean": series.mean(),
                "std": series.std(),
                "minimum": series.min(),
                "p25": series.quantile(0.25),
                "median": series.median(),
                "p75": series.quantile(0.75),
                "maximum": series.max(),
            }
        )

    descriptive = pd.DataFrame(
        descriptive_records
    )

    descriptive_file = (
        OUTPUT_DIR
        / "connectivity_pooled_descriptive_statistics.csv"
    )

    descriptive.to_csv(
        descriptive_file,
        index=False,
    )

    # ---------------------------------------------------------------
    # Country statistics
    # ---------------------------------------------------------------
    country_records = []

    for country, group in dataframe.groupby("country"):
        for indicator in INDICATORS:
            series = group[indicator].dropna()

            country_records.append(
                {
                    "country": country,
                    "indicator": indicator,
                    "count": series.count(),
                    "mean": series.mean(),
                    "std": series.std(),
                    "minimum": series.min(),
                    "median": series.median(),
                    "maximum": series.max(),
                }
            )

    country_statistics = pd.DataFrame(
        country_records
    )

    country_file = (
        OUTPUT_DIR
        / "connectivity_country_statistics.csv"
    )

    country_statistics.to_csv(
        country_file,
        index=False,
    )

    # ---------------------------------------------------------------
    # Pooled percentiles
    # ---------------------------------------------------------------
    percentile_records = []

    for indicator in INDICATORS:
        series = dataframe[indicator].dropna()

        for percentile in PERCENTILES:
            percentile_records.append(
                {
                    "indicator": indicator,
                    "percentile": percentile,
                    "value": series.quantile(
                        percentile / 100
                    ),
                }
            )

    percentiles = pd.DataFrame(
        percentile_records
    )

    percentile_file = (
        OUTPUT_DIR
        / "connectivity_pooled_percentiles.csv"
    )

    percentiles.to_csv(
        percentile_file,
        index=False,
    )

    # ---------------------------------------------------------------
    # Country-year extremes
    # ---------------------------------------------------------------
    extreme_records = []

    for indicator in INDICATORS:
        minimum_row = dataframe.loc[
            dataframe[indicator].idxmin()
        ]

        maximum_row = dataframe.loc[
            dataframe[indicator].idxmax()
        ]

        extreme_records.extend(
            [
                {
                    "indicator": indicator,
                    "extreme_type": "minimum",
                    "country": minimum_row["country"],
                    "year": int(minimum_row["year"]),
                    "value": minimum_row[indicator],
                },
                {
                    "indicator": indicator,
                    "extreme_type": "maximum",
                    "country": maximum_row["country"],
                    "year": int(maximum_row["year"]),
                    "value": maximum_row[indicator],
                },
            ]
        )

    extremes = pd.DataFrame(
        extreme_records
    )

    extremes_file = (
        OUTPUT_DIR
        / "connectivity_country_year_extremes.csv"
    )

    extremes.to_csv(
        extremes_file,
        index=False,
    )

    # ---------------------------------------------------------------
    # Candidate empirical reference zones
    # ---------------------------------------------------------------
    reference_records = []

    for indicator in INDICATORS:
        series = dataframe[indicator].dropna()

        p05 = series.quantile(0.05)
        p10 = series.quantile(0.10)
        p25 = series.quantile(0.25)
        p75 = series.quantile(0.75)
        p90 = series.quantile(0.90)
        p95 = series.quantile(0.95)

        reference_records.extend(
            [
                {
                    "indicator": indicator,
                    "reference_zone": "P05-P95",
                    "lower_bound": p05,
                    "upper_bound": p95,
                    "interpretation":
                        "Descriptive empirical candidate only; "
                        "not a final scoring threshold.",
                },
                {
                    "indicator": indicator,
                    "reference_zone": "P10-P90",
                    "lower_bound": p10,
                    "upper_bound": p90,
                    "interpretation":
                        "Descriptive empirical candidate only; "
                        "not a final scoring threshold.",
                },
                {
                    "indicator": indicator,
                    "reference_zone": "P25-P75",
                    "lower_bound": p25,
                    "upper_bound": p75,
                    "interpretation":
                        "Descriptive empirical candidate only; "
                        "not a final scoring threshold.",
                },
            ]
        )

    reference_zones = pd.DataFrame(
        reference_records
    )

    reference_file = (
        OUTPUT_DIR
        / "connectivity_candidate_reference_zones.csv"
    )

    reference_zones.to_csv(
        reference_file,
        index=False,
    )

    print()
    print("POOLED DISTRIBUTION")
    print("=" * 72)
    print(descriptive.to_string(index=False))

    print()
    print("CANDIDATE REFERENCE ZONES")
    print("=" * 72)
    print(reference_zones.to_string(index=False))

    print()
    print("OUTPUT FILES")
    print("=" * 72)
    print(f"Saved: {descriptive_file}")
    print(f"Saved: {country_file}")
    print(f"Saved: {percentile_file}")
    print(f"Saved: {extremes_file}")
    print(f"Saved: {reference_file}")

    print()
    print(
        "JESI Connectivity distribution analysis "
        "completed successfully."
    )


if __name__ == "__main__":
    main()
