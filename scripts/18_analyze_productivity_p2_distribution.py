"""
JESI Productivity P2 Distribution Analysis

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

P2 Indicator:
    Total Factor Productivity (TFP) Growth

Source:
    Penn World Table (PWT) 11.0

Analysis period:
    2016-2023

Note:
    2015 is excluded from growth-distribution analysis
    because TFP growth requires the previous year's
    TFP level.
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/raw/"
    "productivity_p2_tfp_growth_2015_2023.csv"
)

OUTPUT_DIR = Path(
    "data/processed"
)

COUNTRIES = [
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
]

START_YEAR = 2016
END_YEAR = 2023

PERCENTILES = [
    1,
    5,
    10,
    25,
    50,
    75,
    90,
    95,
    99,
]


def validate_input(dataframe):
    """
    Validate the P2 dataset before analysis.
    """

    required_columns = {
        "country_code",
        "country",
        "year",
        "tfp",
        "tfp_growth",
    }

    missing_columns = (
        required_columns
        - set(dataframe.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if set(dataframe["country"]) != set(COUNTRIES):
        raise ValueError(
            "Unexpected country set."
        )


def prepare_growth_data(dataframe):
    """
    Select valid TFP growth observations
    for distribution analysis.
    """

    growth_data = dataframe[
        dataframe["tfp_growth"].notna()
    ].copy()

    growth_data = growth_data[
        growth_data["year"].between(
            START_YEAR,
            END_YEAR,
        )
    ].copy()

    if growth_data.empty:
        raise ValueError(
            "No valid TFP growth observations "
            "found."
        )

    expected_rows = (
        len(COUNTRIES)
        * (END_YEAR - START_YEAR + 1)
    )

    if len(growth_data) != expected_rows:
        raise ValueError(
            "Unexpected number of TFP growth "
            f"observations. Expected "
            f"{expected_rows}, found "
            f"{len(growth_data)}."
        )

    if growth_data["tfp_growth"].isna().any():
        raise ValueError(
            "Missing TFP growth observations "
            "remain after filtering."
        )

    return growth_data


def calculate_pooled_statistics(
    growth_data,
):
    """
    Calculate pooled descriptive statistics.
    """

    statistics = (
        growth_data["tfp_growth"]
        .describe()
        .rename(
            {
                "count": "count",
                "mean": "mean",
                "std": "std",
                "min": "minimum",
                "25%": "p25",
                "50%": "median",
                "75%": "p75",
                "max": "maximum",
            }
        )
        .to_frame(
            name="tfp_growth"
        )
    )

    return statistics


def calculate_country_statistics(
    growth_data,
):
    """
    Calculate country-level descriptive statistics.
    """

    return (
        growth_data
        .groupby("country")["tfp_growth"]
        .agg(
            [
                "count",
                "mean",
                "std",
                "min",
                "median",
                "max",
            ]
        )
        .reset_index()
        .sort_values("country")
    )


def calculate_percentiles(
    growth_data,
):
    """
    Calculate pooled empirical percentiles.
    """

    records = []

    values = growth_data[
        "tfp_growth"
    ]

    for percentile in PERCENTILES:
        records.append(
            {
                "indicator": "TFP_GROWTH",
                "indicator_name": (
                    "Total Factor Productivity Growth"
                ),
                "percentile": percentile,
                "value": values.quantile(
                    percentile / 100
                ),
            }
        )

    return pd.DataFrame(records)


def calculate_country_year_extremes(
    growth_data,
):
    """
    Identify minimum and maximum TFP growth
    observations by country-year.
    """

    minimum_row = growth_data.loc[
        growth_data["tfp_growth"].idxmin()
    ]

    maximum_row = growth_data.loc[
        growth_data["tfp_growth"].idxmax()
    ]

    records = [
        {
            "indicator": "TFP_GROWTH",
            "indicator_name": (
                "Total Factor Productivity Growth"
            ),
            "extreme_type": "minimum",
            "country": minimum_row["country"],
            "year": int(minimum_row["year"]),
            "value": minimum_row["tfp_growth"],
        },
        {
            "indicator": "TFP_GROWTH",
            "indicator_name": (
                "Total Factor Productivity Growth"
            ),
            "extreme_type": "maximum",
            "country": maximum_row["country"],
            "year": int(maximum_row["year"]),
            "value": maximum_row["tfp_growth"],
        },
    ]

    return pd.DataFrame(records)


def calculate_reference_zones(
    percentile_data,
):
    """
    Calculate candidate empirical reference zones.

    These are descriptive candidates only.
    They are not automatically treated as final
    theoretical thresholds.
    """

    p05 = percentile_data.loc[
        percentile_data["percentile"] == 5,
        "value",
    ].iloc[0]

    p10 = percentile_data.loc[
        percentile_data["percentile"] == 10,
        "value",
    ].iloc[0]

    p25 = percentile_data.loc[
        percentile_data["percentile"] == 25,
        "value",
    ].iloc[0]

    p75 = percentile_data.loc[
        percentile_data["percentile"] == 75,
        "value",
    ].iloc[0]

    p90 = percentile_data.loc[
        percentile_data["percentile"] == 90,
        "value",
    ].iloc[0]

    p95 = percentile_data.loc[
        percentile_data["percentile"] == 95,
        "value",
    ].iloc[0]

    return pd.DataFrame(
        [
            {
                "indicator": "TFP_GROWTH",
                "indicator_name": (
                    "Total Factor Productivity Growth"
                ),
                "reference_zone": "P05-P95",
                "lower_bound": p05,
                "upper_bound": p95,
                "interpretation": (
                    "Descriptive empirical candidate "
                    "only; not a final scoring threshold."
                ),
            },
            {
                "indicator": "TFP_GROWTH",
                "indicator_name": (
                    "Total Factor Productivity Growth"
                ),
                "reference_zone": "P10-P90",
                "lower_bound": p10,
                "upper_bound": p90,
                "interpretation": (
                    "Descriptive empirical candidate "
                    "only; not a final scoring threshold."
                ),
            },
            {
                "indicator": "TFP_GROWTH",
                "indicator_name": (
                    "Total Factor Productivity Growth"
                ),
                "reference_zone": "P25-P75",
                "lower_bound": p25,
                "upper_bound": p75,
                "interpretation": (
                    "Descriptive empirical candidate "
                    "only; not a final scoring threshold."
                ),
            },
        ]
    )


def main():
    """
    Run the complete P2 distribution analysis.
    """

    print("=" * 72)
    print("JESI PRODUCTIVITY P2 DISTRIBUTION ANALYSIS")
    print("=" * 72)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    dataframe = pd.read_csv(
        INPUT_FILE
    )

    validate_input(
        dataframe
    )

    growth_data = prepare_growth_data(
        dataframe
    )

    pooled_statistics = (
        calculate_pooled_statistics(
            growth_data
        )
    )

    country_statistics = (
        calculate_country_statistics(
            growth_data
        )
    )

    percentile_data = (
        calculate_percentiles(
            growth_data
        )
    )

    country_year_extremes = (
        calculate_country_year_extremes(
            growth_data
        )
    )

    reference_zones = (
        calculate_reference_zones(
            percentile_data
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pooled_file = (
        OUTPUT_DIR
        / "productivity_p2_pooled_descriptive_statistics.csv"
    )

    country_file = (
        OUTPUT_DIR
        / "productivity_p2_country_statistics.csv"
    )

    percentile_file = (
        OUTPUT_DIR
        / "productivity_p2_pooled_percentiles.csv"
    )

    extremes_file = (
        OUTPUT_DIR
        / "productivity_p2_country_year_extremes.csv"
    )

    reference_file = (
        OUTPUT_DIR
        / "productivity_p2_candidate_reference_zones.csv"
    )

    pooled_statistics.to_csv(
        pooled_file
    )

    country_statistics.to_csv(
        country_file,
        index=False,
    )

    percentile_data.to_csv(
        percentile_file,
        index=False,
    )

    country_year_extremes.to_csv(
        extremes_file,
        index=False,
    )

    reference_zones.to_csv(
        reference_file,
        index=False,
    )

    print()
    print("P2 ANALYSIS PERIOD")
    print("=" * 72)

    print(
        f"{START_YEAR}-{END_YEAR}"
    )

    print()
    print("VALID TFP GROWTH OBSERVATIONS")
    print("=" * 72)

    print(
        len(growth_data)
    )

    print()
    print("POOLED DESCRIPTIVE STATISTICS")
    print("=" * 72)

    print(
        pooled_statistics.to_string()
    )

    print()
    print("COUNTRY STATISTICS")
    print("=" * 72)

    print(
        country_statistics.to_string(
            index=False
        )
    )

    print()
    print("POOLED PERCENTILES")
    print("=" * 72)

    print(
        percentile_data.to_string(
            index=False
        )
    )

    print()
    print("COUNTRY-YEAR EXTREMES")
    print("=" * 72)

    print(
        country_year_extremes.to_string(
            index=False
        )
    )

    print()
    print("CANDIDATE EMPIRICAL REFERENCE ZONES")
    print("=" * 72)

    print(
        reference_zones.to_string(
            index=False
        )
    )

    print()
    print("OUTPUT FILES")
    print("=" * 72)

    print(
        f"Saved: {pooled_file}"
    )

    print(
        f"Saved: {country_file}"
    )

    print(
        f"Saved: {percentile_file}"
    )

    print(
        f"Saved: {extremes_file}"
    )

    print(
        f"Saved: {reference_file}"
    )

    print()
    print(
        "JESI Productivity P2 distribution "
        "analysis completed successfully."
    )


if __name__ == "__main__":
    main()
