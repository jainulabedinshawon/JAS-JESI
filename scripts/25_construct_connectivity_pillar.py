"""
JESI Connectivity Pillar Construction

Input:
    data/processed/connectivity_indicator_scores_2015_2024.csv

Output:
    data/processed/connectivity_pillar_scores_2015_2024.csv

Baseline:
    Arithmetic mean of the three Connectivity indicator scores.

Alternative:
    Geometric mean of the three Connectivity indicator scores.

Indicators:
    - Trade Openness
    - FDI Inflows (% GDP)
    - Internet Use (% population)
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

EXPECTED_CODES = {
    "BGD",
    "IND",
    "IDN",
    "MYS",
    "VNM",
}

EXPECTED_YEARS = set(range(2015, 2025))

EXPECTED_ROWS = 50

SCORE_COLUMNS = [
    "connectivity_trade_score",
    "connectivity_fdi_score",
    "connectivity_internet_score",
]


def main():
    print("=" * 72)
    print("JESI CONNECTIVITY PILLAR CONSTRUCTION")
    print("=" * 72)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing Connectivity score file: {INPUT_FILE}"
        )

    dataframe = pd.read_csv(INPUT_FILE)

    required_columns = {
        "country",
        "country_code",
        "year",
        "trade_openness",
        "fdi_inflows",
        "internet_use",
        *SCORE_COLUMNS,
    }

    missing = sorted(
        required_columns - set(dataframe.columns)
    )

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    # ---------------------------------------------------------------
    # Standardize country/year fields
    # ---------------------------------------------------------------
    dataframe["country_code"] = (
        dataframe["country_code"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    dataframe["year"] = pd.to_numeric(
        dataframe["year"],
        errors="coerce",
    )

    dataframe = dataframe[
        dataframe["country_code"].isin(
            EXPECTED_CODES
        )
        & dataframe["year"].isin(
            EXPECTED_YEARS
        )
    ].copy()

    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_ROWS} Connectivity "
            f"observations, found {len(dataframe)}."
        )

    # ---------------------------------------------------------------
    # Duplicate validation
    # ---------------------------------------------------------------
    if dataframe.duplicated(
        subset=["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate Connectivity country-year "
            "observations detected."
        )

    # ---------------------------------------------------------------
    # Numeric score validation
    # ---------------------------------------------------------------
    for column in SCORE_COLUMNS:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        valid = dataframe[column].dropna()

        if valid.empty:
            raise ValueError(
                f"No valid observations found in {column}."
            )

        if (valid <= 0).any() or (valid > 1).any():
            raise ValueError(
                f"Invalid values in {column}. "
                "Expected scores in (0, 1]."
            )

    # ---------------------------------------------------------------
    # Construct Connectivity pillar
    # ---------------------------------------------------------------
    dataframe["connectivity_score"] = (
        dataframe[SCORE_COLUMNS]
        .mean(axis=1)
    )

    dataframe["connectivity_geometric"] = (
        dataframe[SCORE_COLUMNS]
        .prod(axis=1)
        ** (1.0 / len(SCORE_COLUMNS))
    )

    # ---------------------------------------------------------------
    # Missing-data validation
    # ---------------------------------------------------------------
    required_complete = dataframe[
        SCORE_COLUMNS
    ].notna().all(axis=1)

    if not required_complete.all():
        missing_rows = dataframe.loc[
            ~required_complete,
            [
                "country_code",
                "year",
            ] + SCORE_COLUMNS,
        ]

        raise ValueError(
            "Missing Connectivity indicator scores "
            "prevent pillar construction:\n"
            f"{missing_rows.to_string(index=False)}"
        )

    # ---------------------------------------------------------------
    # Pillar score range validation
    # ---------------------------------------------------------------
    for column in [
        "connectivity_score",
        "connectivity_geometric",
    ]:
        valid = dataframe[column].dropna()

        if (valid <= 0).any() or (valid > 1).any():
            raise ValueError(
                f"Invalid pillar values in {column}. "
                "Expected values in (0, 1]."
            )

    # ---------------------------------------------------------------
    # Output
    # ---------------------------------------------------------------
    output_columns = [
        "country",
        "country_code",
        "year",
        "connectivity_trade_score",
        "connectivity_fdi_score",
        "connectivity_internet_score",
        "connectivity_score",
        "connectivity_geometric",
    ]

    output = dataframe[
        output_columns
    ].copy()

    output = output.sort_values(
        ["country_code", "year"]
    ).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # ---------------------------------------------------------------
    # Final validation
    # ---------------------------------------------------------------
    if len(output) != EXPECTED_ROWS:
        raise ValueError(
            f"Final Connectivity pillar output contains "
            f"{len(output)} rows; expected {EXPECTED_ROWS}."
        )

    print()
    print("CONNECTIVITY PILLAR COMPLETED")
    print("=" * 72)
    print(f"Rows: {len(output)}")
    print(
        "Baseline: arithmetic mean"
    )
    print(
        "Alternative: geometric mean"
    )
    print(
        f"Saved: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
