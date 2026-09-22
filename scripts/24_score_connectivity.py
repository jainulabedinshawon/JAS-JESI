"""
JESI Connectivity Indicator Scoring

Input:
    data/raw/connectivity_indicators_2015_2024.csv
    data/processed/connectivity_pooled_percentiles.csv

Output:
    data/processed/connectivity_indicator_scores_2015_2024.csv

Method:
    Pooled percentile-rank scoring.

Indicators:
    - Trade Openness
    - FDI Inflows (% GDP)
    - Internet Use (% population)
"""

from pathlib import Path

import numpy as np
import pandas as pd


RAW_INPUT_FILE = Path(
    "data/raw/connectivity_indicators_2015_2024.csv"
)

PERCENTILE_FILE = Path(
    "data/processed/connectivity_pooled_percentiles.csv"
)

OUTPUT_FILE = Path(
    "data/processed/connectivity_indicator_scores_2015_2024.csv"
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

INDICATORS = {
    "trade_openness": "connectivity_trade_score",
    "fdi_inflows": "connectivity_fdi_score",
    "internet_use": "connectivity_internet_score",
}


def percentile_rank_score(value, series):
    """
    Convert an observation into its pooled empirical percentile rank.

    The score is bounded in (0, 1].
    Higher values receive higher scores.
    """
    if pd.isna(value):
        return np.nan

    clean = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if clean.empty:
        return np.nan

    return float(
        (clean <= value).mean()
    )


def validate_percentile_file():
    """Validate the distribution-analysis output."""
    if not PERCENTILE_FILE.exists():
        raise FileNotFoundError(
            "Missing Connectivity percentile file: "
            f"{PERCENTILE_FILE}"
        )

    percentiles = pd.read_csv(
        PERCENTILE_FILE
    )

    required_columns = {
        "indicator",
        "percentile",
        "value",
    }

    missing = sorted(
        required_columns - set(percentiles.columns)
    )

    if missing:
        raise ValueError(
            "Connectivity percentile file is missing "
            f"columns: {missing}"
        )

    expected_indicators = set(
        INDICATORS.keys()
    )

    actual_indicators = set(
        percentiles["indicator"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    missing_indicators = sorted(
        expected_indicators - actual_indicators
    )

    if missing_indicators:
        raise ValueError(
            "Connectivity percentile file is missing "
            f"indicators: {missing_indicators}"
        )

    return percentiles


def main():
    print("=" * 72)
    print("JESI CONNECTIVITY INDICATOR SCORING")
    print("=" * 72)

    if not RAW_INPUT_FILE.exists():
        raise FileNotFoundError(
            "Missing raw Connectivity input: "
            f"{RAW_INPUT_FILE}"
        )

    dataframe = pd.read_csv(
        RAW_INPUT_FILE
    )

    required_columns = {
        "country_code",
        "country",
        "year",
        "trade_openness",
        "fdi_inflows",
        "internet_use",
    }

    missing = sorted(
        required_columns - set(dataframe.columns)
    )

    if missing:
        raise ValueError(
            "Raw Connectivity data is missing "
            f"columns: {missing}"
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
            f"rows, found {len(dataframe)}."
        )

    # ---------------------------------------------------------------
    # Duplicate validation
    # ---------------------------------------------------------------
    duplicate_mask = dataframe.duplicated(
        subset=["country_code", "year"],
        keep=False,
    )

    if duplicate_mask.any():
        duplicates = (
            dataframe.loc[
                duplicate_mask,
                ["country_code", "year"],
            ]
            .drop_duplicates()
            .sort_values(
                ["country_code", "year"]
            )
        )

        raise ValueError(
            "Duplicate country-year observations found:\n"
            f"{duplicates.to_string(index=False)}"
        )

    # ---------------------------------------------------------------
    # Numeric conversion
    # ---------------------------------------------------------------
    for indicator in INDICATORS:
        dataframe[indicator] = pd.to_numeric(
            dataframe[indicator],
            errors="coerce",
        )

    # ---------------------------------------------------------------
    # Validate pooled percentile-analysis output
    # ---------------------------------------------------------------
    percentiles = validate_percentile_file()

    # The percentile file is intentionally used as a validation
    # dependency. Final observation-level scores are calculated
    # directly from the pooled raw distribution so that every
    # country-year receives its empirical percentile rank.
    print(
        f"Validated percentile analysis file: "
        f"{PERCENTILE_FILE}"
    )

    # ---------------------------------------------------------------
    # Percentile scoring
    # ---------------------------------------------------------------
    for indicator, score_column in INDICATORS.items():
        dataframe[score_column] = dataframe[
            indicator
        ].apply(
            lambda value: percentile_rank_score(
                value,
                dataframe[indicator],
            )
        )

    score_columns = list(
        INDICATORS.values()
    )

    # ---------------------------------------------------------------
    # Score validation
    # ---------------------------------------------------------------
    for column in score_columns:
        valid = dataframe[column].dropna()

        if valid.empty:
            raise ValueError(
                f"No valid Connectivity scores "
                f"were produced for {column}."
            )

        if (valid <= 0).any() or (valid > 1).any():
            raise ValueError(
                f"Invalid values detected in {column}. "
                "Expected scores in (0, 1]."
            )

    # ---------------------------------------------------------------
    # Missing-data validation
    # ---------------------------------------------------------------
    for indicator, score_column in INDICATORS.items():
        raw_missing = dataframe[indicator].isna().sum()
        score_missing = dataframe[score_column].isna().sum()

        if raw_missing != score_missing:
            raise ValueError(
                f"Unexpected missing-data mismatch for "
                f"{indicator}: raw={raw_missing}, "
                f"score={score_missing}"
            )

    # ---------------------------------------------------------------
    # Output
    # ---------------------------------------------------------------
    output_columns = [
        "country",
        "country_code",
        "year",
        "trade_openness",
        "fdi_inflows",
        "internet_use",
        "connectivity_trade_score",
        "connectivity_fdi_score",
        "connectivity_internet_score",
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
    # Final checks
    # ---------------------------------------------------------------
    if len(output) != EXPECTED_ROWS:
        raise ValueError(
            f"Final Connectivity output contains "
            f"{len(output)} rows; expected "
            f"{EXPECTED_ROWS}."
        )

    print()
    print("CONNECTIVITY SCORING COMPLETED")
    print("=" * 72)
    print(f"Rows: {len(output)}")
    print(
        "Score columns:",
        ", ".join(score_columns),
    )
    print(
        f"Saved: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
