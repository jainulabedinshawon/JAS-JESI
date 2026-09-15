"""
JESI Strategic Autonomy Distribution Analysis
Master Version 1.0

Analyzes the empirical distributions of the three
Strategic Autonomy indicators for 2015–2024.
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024_complete.csv"
)

OUTPUT_DIR = Path("data/processed")


INDICATORS = [
    "eci",
    "high_tech_exports",
    "import_product_concentration",
]


def main():
    print("=" * 70)
    print("JESI Strategic Autonomy Distribution Analysis")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_csv(INPUT_FILE)

    for column in INDICATORS:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # ------------------------------------------------------------
    # 1. Pooled descriptive statistics
    # ------------------------------------------------------------

    pooled_stats = df[INDICATORS].describe().T

    pooled_stats.to_csv(
        OUTPUT_DIR
        / "autonomy_pooled_descriptive_statistics.csv"
    )

    # ------------------------------------------------------------
    # 2. Country-level statistics
    # ------------------------------------------------------------

    country_stats = (
        df.groupby("country")[INDICATORS]
        .agg(["count", "mean", "std", "min", "median", "max"])
    )

    country_stats.to_csv(
        OUTPUT_DIR
        / "autonomy_country_statistics.csv"
    )

    # ------------------------------------------------------------
    # 3. Pooled percentiles
    # ------------------------------------------------------------

    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]

    pooled_percentiles = df[INDICATORS].quantile(
        [p / 100 for p in percentiles]
    )

    pooled_percentiles.index = [
        f"P{p}" for p in percentiles
    ]

    pooled_percentiles.to_csv(
        OUTPUT_DIR
        / "autonomy_pooled_percentiles.csv"
    )

    # ------------------------------------------------------------
    # 4. Candidate reference zones
    # ------------------------------------------------------------

    reference_zones = pd.DataFrame(
        {
            "zone": [
                "P05-P95",
                "P10-P90",
                "P25-P75",
            ],
            "lower_percentile": [
                0.05,
                0.10,
                0.25,
            ],
            "upper_percentile": [
                0.95,
                0.90,
                0.75,
            ],
        }
    )

    for indicator in INDICATORS:
        reference_zones[
            f"{indicator}_lower"
        ] = [
            df[indicator].quantile(0.05),
            df[indicator].quantile(0.10),
            df[indicator].quantile(0.25),
        ]

        reference_zones[
            f"{indicator}_upper"
        ] = [
            df[indicator].quantile(0.95),
            df[indicator].quantile(0.90),
            df[indicator].quantile(0.75),
        ]

    reference_zones.to_csv(
        OUTPUT_DIR
        / "autonomy_candidate_reference_zones.csv",
        index=False,
    )

    # ------------------------------------------------------------
    # 5. Country-year extremes
    # ------------------------------------------------------------

    extreme_rows = []

    for indicator in INDICATORS:
        minimum_row = df.loc[
            df[indicator].idxmin()
        ]

        maximum_row = df.loc[
            df[indicator].idxmax()
        ]

        extreme_rows.append(
            {
                "indicator": indicator,
                "extreme": "minimum",
                "country": minimum_row["country"],
                "year": int(minimum_row["year"]),
                "value": minimum_row[indicator],
            }
        )

        extreme_rows.append(
            {
                "indicator": indicator,
                "extreme": "maximum",
                "country": maximum_row["country"],
                "year": int(maximum_row["year"]),
                "value": maximum_row[indicator],
            }
        )

    extremes = pd.DataFrame(extreme_rows)

    extremes.to_csv(
        OUTPUT_DIR
        / "autonomy_country_year_extremes.csv",
        index=False,
    )

    # ------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------

    print()
    print("Pooled descriptive statistics:")
    print(pooled_stats)

    print()
    print("Pooled percentiles:")
    print(pooled_percentiles)

    print()
    print("Candidate reference zones:")
    print(reference_zones)

    print()
    print("Country-year extremes:")
    print(extremes)

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print("Strategic Autonomy distribution analysis completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
