"""
Score the Connectivity pillar indicators.

Input:
    data/processed/connectivity_distribution_2015_2024.csv

Output:
    data/processed/connectivity_indicator_scores_2015_2024.csv

Method:
    Percentile-based scoring using the pooled distribution.

Indicators:
    - Trade Openness
    - FDI Inflows (% GDP)
    - Internet Users (% population)
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/processed/connectivity_distribution_2015_2024.csv"
)

OUTPUT_FILE = Path(
    "data/processed/connectivity_indicator_scores_2015_2024.csv"
)

EXPECTED_CODES = {"BGD", "IND", "IDN", "MYS", "VNM"}
EXPECTED_YEARS = set(range(2015, 2025))

INDICATORS = {
    "trade_openness": "trade_openness",
    "fdi_inflows": "fdi_inflows_pct_gdp",
    "internet_users": "internet_users_pct",
}


def percentile_score(value, series):
    """Convert a value into a pooled percentile score in (0, 1]."""
    if pd.isna(value):
        return np.nan

    clean = pd.to_numeric(series, errors="coerce").dropna()

    if clean.empty:
        return np.nan

    return float((clean <= value).mean())


def resolve_percentile_column(df, indicator):
    """
    Resolve percentile information from the distribution output.

    The distribution-analysis script may provide either:
      1. P05/P10/P50/P90/P95
      2. percentile-style names such as p05/p10/p50/p90/p95

    Percentile scoring itself is calculated from the raw indicator
    distribution, so the percentile summary columns are not required
    for the final score.
    """
    candidates = [
        indicator,
        indicator.lower(),
    ]

    for column in candidates:
        if column in df.columns:
            return column

    return None


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = {
        "country_code",
        "country",
        "year",
        "trade_openness",
        "fdi_inflows_pct_gdp",
        "internet_users_pct",
    }

    missing = sorted(required_columns - set(df.columns))

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # Standardize types.
    df["country_code"] = (
        df["country_code"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    )

    # Restrict to the intended JESI country/year universe.
    df = df[
        df["country_code"].isin(EXPECTED_CODES)
        & df["year"].isin(EXPECTED_YEARS)
    ].copy()

    if df.empty:
        raise ValueError(
            "No valid Connectivity observations remain "
            "for the expected countries and years."
        )

    # Check duplicates before scoring.
    duplicate_mask = df.duplicated(
        subset=["country_code", "year"],
        keep=False,
    )

    if duplicate_mask.any():
        duplicates = df.loc[
            duplicate_mask,
            ["country_code", "year"]
        ].drop_duplicates()

        raise ValueError(
            "Duplicate country-year observations found:\n"
            f"{duplicates.to_string(index=False)}"
        )

    # Numeric conversion.
    for column in [
        "trade_openness",
        "fdi_inflows_pct_gdp",
        "internet_users_pct",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # Percentile-based indicator scores.
    df["connectivity_trade_score"] = df[
        "trade_openness"
    ].apply(
        lambda value: percentile_score(
            value,
            df["trade_openness"],
        )
    )

    df["connectivity_fdi_score"] = df[
        "fdi_inflows_pct_gdp"
    ].apply(
        lambda value: percentile_score(
            value,
            df["fdi_inflows_pct_gdp"],
        )
    )

    df["connectivity_internet_score"] = df[
        "internet_users_pct"
    ].apply(
        lambda value: percentile_score(
            value,
            df["internet_users_pct"],
        )
    )

    score_columns = [
        "connectivity_trade_score",
        "connectivity_fdi_score",
        "connectivity_internet_score",
    ]

    # Validate score ranges.
    for column in score_columns:
        valid = df[column].dropna()

        if not valid.empty:
            if (valid <= 0).any() or (valid > 1).any():
                raise ValueError(
                    f"Invalid scores in {column}. "
                    "Expected values in (0, 1]."
                )

    # Keep the standardized output interface used by
    # 25_construct_connectivity_pillar.py.
    output_columns = [
        "country",
        "country_code",
        "year",
        "trade_openness",
        "fdi_inflows_pct_gdp",
        "internet_users_pct",
        "connectivity_trade_score",
        "connectivity_fdi_score",
        "connectivity_internet_score",
    ]

    output = df[output_columns].copy()

    output = output.sort_values(
        ["country_code", "year"]
    ).reset_index(drop=True)

    expected_rows = len(EXPECTED_CODES) * len(EXPECTED_YEARS)

    if len(output) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} Connectivity observations "
            f"but found {len(output)}."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"Connectivity indicator scores saved to "
        f"{OUTPUT_FILE}"
    )
    print(f"Rows: {len(output)}")
    print(
        "Score columns:",
        ", ".join(score_columns),
    )


if __name__ == "__main__":
    main()
