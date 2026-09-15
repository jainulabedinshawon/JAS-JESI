"""
JESI Productivity P1 Scoring Module

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

P1 Indicator:
    GDP per Person Employed

World Bank Indicator:
    SL.GDP.PCAP.EM.KD

Baseline normalization:
    Empirical P10-P90 reference range

Robustness alternatives:
    1. Full-sample min-max
    2. Empirical P05-P95
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/raw/"
    "productivity_p1_gdp_per_person_employed_2015_2024.csv"
)

OUTPUT_FILE = Path(
    "data/processed/"
    "productivity_p1_scores_2015_2024.csv"
)


INDICATOR = "SL.GDP.PCAP.EM.KD"

COUNTRIES = [
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
]

START_YEAR = 2015
END_YEAR = 2024


# Empirically calibrated reference range
# based on the 2015-2024 five-country sample.
P10_LOWER = 16916.369067
P90_UPPER = 62856.237770

P05_LOWER = 15673.558895
P95_UPPER = 65282.187498


def normalize_positive(
    value,
    lower,
    upper,
):
    """
    Normalize a positive-direction indicator
    to a 0-1 score using lower and upper
    reference values.
    """

    if upper <= lower:
        raise ValueError(
            "Upper reference value must be greater "
            "than lower reference value."
        )

    score = (
        float(value) - lower
    ) / (
        upper - lower
    )

    return max(
        0.0,
        min(1.0, score),
    )


def validate_input(dataframe):
    """
    Validate the P1 input dataset.
    """

    required_columns = {
        "country",
        "year",
        "value",
        "indicator",
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

    if dataframe["year"].min() != START_YEAR:
        raise ValueError(
            "Unexpected minimum year."
        )

    if dataframe["year"].max() != END_YEAR:
        raise ValueError(
            "Unexpected maximum year."
        )

    if set(dataframe["indicator"]) != {INDICATOR}:
        raise ValueError(
            "Unexpected indicator."
        )

    if dataframe[
        ["country", "year", "indicator"]
    ].duplicated().any():
        raise ValueError(
            "Duplicate country-year-indicator "
            "observations found."
        )

    if dataframe["value"].isna().any():
        raise ValueError(
            "Missing P1 values found."
        )

    if (dataframe["value"] <= 0).any():
        raise ValueError(
            "P1 values must be positive."
        )


def main():
    """
    Calculate baseline and robustness P1 scores.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    dataframe = pd.read_csv(
        INPUT_FILE
    )

    validate_input(dataframe)

    dataframe = dataframe.copy()

    sample_min = dataframe["value"].min()
    sample_max = dataframe["value"].max()

    dataframe["p1_score"] = dataframe[
        "value"
    ].apply(
        lambda value: normalize_positive(
            value,
            P10_LOWER,
            P90_UPPER,
        )
    )

    dataframe["p1_minmax_score"] = dataframe[
        "value"
    ].apply(
        lambda value: normalize_positive(
            value,
            sample_min,
            sample_max,
        )
    )

    dataframe["p1_p05_p95_score"] = dataframe[
        "value"
    ].apply(
        lambda value: normalize_positive(
            value,
            P05_LOWER,
            P95_UPPER,
        )
    )

    dataframe = dataframe.sort_values(
        [
            "country",
            "year",
        ]
    ).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("=" * 72)
    print("JESI PRODUCTIVITY P1 SCORING")
    print("=" * 72)

    print()
    print("Indicator:")
    print(INDICATOR)

    print()
    print("Baseline normalization:")
    print("Empirical P10-P90")

    print()
    print(
        f"P10 lower bound: {P10_LOWER:.6f}"
    )

    print(
        f"P90 upper bound: {P90_UPPER:.6f}"
    )

    print()
    print("Robustness alternatives:")
    print("1. Full-sample min-max")
    print("2. Empirical P05-P95")

    print()
    print("P1 SCORE SUMMARY")
    print("=" * 72)

    print(
        dataframe[
            [
                "country",
                "year",
                "value",
                "p1_score",
            ]
        ].to_string(index=False)
    )

    print()
    print("OUTPUT")
    print("=" * 72)

    print(
        f"Saved: {OUTPUT_FILE}"
    )

    print()
    print(
        "JESI Productivity P1 scoring "
        "completed successfully."
    )


if __name__ == "__main__":
    main()
