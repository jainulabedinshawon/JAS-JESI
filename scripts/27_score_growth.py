"""
Score the Growth pillar for JESI.

This script:
1. Loads the validated Growth indicator dataset.
2. Generates pooled percentile benchmarks when they are absent.
3. Converts Growth indicators to percentile scores.
4. Constructs the arithmetic Growth pillar score.
5. Saves the Growth pillar output used by the final JESI pipeline.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT
    / "data"
    / "raw"
    / "growth_indicators_2015_2025.csv"
)

PERCENTILE_FILE = (
    ROOT
    / "data"
    / "processed"
    / "growth_pooled_percentiles.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "growth_pillar_scores_2015_2024.csv"
)

EXPECTED_COUNTRIES = {
    "BGD",
    "IND",
    "IDN",
    "MYS",
    "VNM",
}

START_YEAR = 2015
END_YEAR = 2024


def fail(message):
    """Raise a clear pipeline error."""
    raise RuntimeError(message)


def detect_column(df, candidates):
    """Return the first matching column from a list of candidates."""
    normalized = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for candidate in candidates:
        key = candidate.strip().lower()
        if key in normalized:
            return normalized[key]

    return None


def percentile_score(series):
    """
    Convert a numeric series into percentile scores on (0, 1].

    Rank-based percentile scoring is used so that larger values
    receive higher scores.
    """
    numeric = pd.to_numeric(series, errors="coerce")

    if numeric.isna().any():
        fail(
            "Cannot calculate percentile scores because the "
            "indicator contains missing or non-numeric values."
        )

    n = len(numeric)

    if n == 0:
        fail("Cannot calculate percentile scores from an empty series.")

    if n == 1:
        return pd.Series([1.0], index=series.index)

    ranks = numeric.rank(method="average", ascending=True)

    scores = (ranks - 1) / (n - 1)

    return scores.clip(lower=0.0, upper=1.0)


def load_growth_data():
    """Load and validate the Growth dataset."""
    if not INPUT_FILE.is_file():
        fail(f"Missing Growth input file: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    country_column = detect_column(
        df,
        [
            "country_code",
            "Country Code",
            "country",
            "Country",
        ],
    )

    year_column = detect_column(
        df,
        [
            "year",
            "Year",
        ],
    )

    real_gdp_column = detect_column(
        df,
        [
            "Real GDP Growth Rate",
            "real_gdp_growth",
            "real_gdp_growth_rate",
            "GDP Growth",
            "GDP growth",
        ],
    )

    gni_column = detect_column(
        df,
        [
            "GNI per Capita Growth",
            "gni_per_capita_growth",
            "GNI per capita growth",
        ],
    )

    if country_column is None:
        fail("Could not identify the country-code column.")

    if year_column is None:
        fail("Could not identify the year column.")

    if real_gdp_column is None:
        fail("Could not identify the Real GDP Growth column.")

    if gni_column is None:
        fail("Could not identify the GNI per Capita Growth column.")

    df = df.rename(
        columns={
            country_column: "country_code",
            year_column: "year",
            real_gdp_column: "real_gdp_growth",
            gni_column: "gni_per_capita_growth",
        }
    )

    df["country_code"] = (
        df["country_code"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["real_gdp_growth"] = pd.to_numeric(
        df["real_gdp_growth"],
        errors="coerce",
    )

    df["gni_per_capita_growth"] = pd.to_numeric(
        df["gni_per_capita_growth"],
        errors="coerce",
    )

    df = df[
        df["country_code"].isin(EXPECTED_COUNTRIES)
        & df["year"].between(START_YEAR, END_YEAR)
    ].copy()

    if df.empty:
        fail("No valid Growth observations remain after filtering.")

    return df


def build_pooled_percentiles(df):
    """
    Build pooled percentile benchmark values.

    The percentile file stores the pooled distribution used by
    the Growth scoring stage.
    """
    rows = []

    for indicator in [
        "real_gdp_growth",
        "gni_per_capita_growth",
    ]:
        values = pd.to_numeric(
            df[indicator],
            errors="coerce",
        ).dropna()

        if values.empty:
            fail(
                f"No valid observations available for {indicator}."
            )

        rows.append(
            {
                "indicator": indicator,
                "count": int(values.count()),
                "min": float(values.min()),
                "p01": float(values.quantile(0.01)),
                "p05": float(values.quantile(0.05)),
                "p10": float(values.quantile(0.10)),
                "p25": float(values.quantile(0.25)),
                "p50": float(values.quantile(0.50)),
                "p75": float(values.quantile(0.75)),
                "p90": float(values.quantile(0.90)),
                "p95": float(values.quantile(0.95)),
                "p99": float(values.quantile(0.99)),
                "max": float(values.max()),
            }
        )

    percentile_df = pd.DataFrame(rows)

    PERCENTILE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    percentile_df.to_csv(
        PERCENTILE_FILE,
        index=False,
    )

    return percentile_df


def score_growth(df):
    """Calculate Growth indicator and pillar scores."""
    result = df.copy()

    result["gdp_growth_score"] = percentile_score(
        result["real_gdp_growth"]
    )

    result["gni_growth_score"] = percentile_score(
        result["gni_per_capita_growth"]
    )

    result["growth_score"] = (
        result["gdp_growth_score"]
        + result["gni_growth_score"]
    ) / 2.0

    return result


def main():
    """Run the Growth scoring pipeline."""
    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Growth Pillar Scoring")
    print("=" * 70)

    df = load_growth_data()

    print(f"Loaded {len(df)} Growth observations.")

    # Generate the pooled benchmark file required by the
    # Growth scoring pipeline.
    build_pooled_percentiles(df)

    result = score_growth(df)

    result = result[
        result["year"].between(
            START_YEAR,
            END_YEAR,
        )
    ].copy()

    required_columns = [
        "country_code",
        "year",
        "real_gdp_growth",
        "gni_per_capita_growth",
        "gdp_growth_score",
        "gni_growth_score",
        "growth_score",
    ]

    missing = [
        column
        for column in required_columns
        if column not in result.columns
    ]

    if missing:
        fail(
            "Growth output is missing columns: "
            f"{missing}"
        )

    result = result[required_columns]

    result["year"] = result["year"].astype(int)

    if result.duplicated(
        ["country_code", "year"]
    ).any():
        fail(
            "Duplicate country-year observations found "
            "in Growth results."
        )

    if result["growth_score"].isna().any():
        fail("Growth pillar contains missing scores.")

    if not (
        (result["growth_score"] > 0)
        & (result["growth_score"] <= 1)
    ).all():
        fail(
            "Growth pillar scores must be within (0, 1]."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"Growth pillar output written to: "
        f"{OUTPUT_FILE.relative_to(ROOT)}"
    )

    print(
        f"Rows written: {len(result)}"
    )

    print("=" * 70)
    print("Growth pillar scoring completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
