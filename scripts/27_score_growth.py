"""
Score the JESI Growth pillar.

The script automatically identifies the Growth indicator columns from
the available Growth CSV instead of depending on one exact column name.

Indicators:
1. Real GDP Growth Rate
2. GNI per Capita Growth

Output:
data/processed/growth_pillar_scores_2015_2024.csv
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
    """Stop the pipeline with a clear error."""
    raise RuntimeError(message)


def normalize_name(value):
    """Normalize a column name for flexible matching."""
    return (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace("/", " ")
        .replace("%", " percent ")
    )


def find_column(df, patterns):
    """
    Find a column using normalized pattern matching.

    Exact normalized matches are preferred, followed by substring
    matches.
    """
    normalized_columns = {
        normalize_name(column): column
        for column in df.columns
    }

    normalized_patterns = [
        normalize_name(pattern)
        for pattern in patterns
    ]

    # Exact match.
    for pattern in normalized_patterns:
        if pattern in normalized_columns:
            return normalized_columns[pattern]

    # Substring match.
    for column_normalized, original_column in normalized_columns.items():
        for pattern in normalized_patterns:
            if pattern in column_normalized:
                return original_column

    return None


def load_growth_data():
    """Load and identify the Growth indicators."""
    if not INPUT_FILE.is_file():
        fail(
            f"Missing Growth input file: "
            f"{INPUT_FILE.relative_to(ROOT)}"
        )

    df = pd.read_csv(INPUT_FILE)

    if df.empty:
        fail("Growth input CSV is empty.")

    country_column = find_column(
        df,
        [
            "country code",
            "country_code",
            "country",
            "iso3",
            "iso code",
        ],
    )

    year_column = find_column(
        df,
        [
            "year",
            "date",
        ],
    )

    # Real GDP growth aliases.
    real_gdp_column = find_column(
        df,
        [
            "real gdp growth rate",
            "real gdp growth",
            "real_gdp_growth_rate",
            "real_gdp_growth",
            "gdp growth rate",
            "gdp growth",
            "gdp growth annual percent",
            "gdp growth annual",
            "real gdp annual growth",
            "annual gdp growth",
            "ny gdp mktp kd zg",
        ],
    )

    # GNI per-capita growth aliases.
    gni_column = find_column(
        df,
        [
            "gni per capita growth",
            "gni_per_capita_growth",
            "gni per capita growth rate",
            "gni growth per capita",
            "gni per capita annual growth",
            "gni per capita growth annual",
            "ny gnp pcap kd zg",
        ],
    )

    if country_column is None:
        fail(
            "Could not identify the country column.\n"
            f"Available columns: {list(df.columns)}"
        )

    if year_column is None:
        fail(
            "Could not identify the year column.\n"
            f"Available columns: {list(df.columns)}"
        )

    if real_gdp_column is None:
        fail(
            "Could not identify the Real GDP Growth column.\n"
            f"Available columns: {list(df.columns)}"
        )

    if gni_column is None:
        fail(
            "Could not identify the GNI per Capita Growth column.\n"
            f"Available columns: {list(df.columns)}"
        )

    print(f"Country column: {country_column}")
    print(f"Year column: {year_column}")
    print(f"Real GDP Growth column: {real_gdp_column}")
    print(f"GNI per Capita Growth column: {gni_column}")

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
        & df["year"].between(
            START_YEAR,
            END_YEAR,
        )
    ].copy()

    if df.empty:
        fail(
            "No Growth observations remain after country/year filtering."
        )

    return df


def build_pooled_percentiles(df):
    """Create the pooled Growth benchmark file."""
    rows = []

    for indicator in [
        "real_gdp_growth",
        "gni_per_capita_growth",
    ]:
        values = (
            pd.to_numeric(
                df[indicator],
                errors="coerce",
            )
            .dropna()
        )

        if values.empty:
            fail(
                f"No valid values available for {indicator}."
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

    result = pd.DataFrame(rows)

    PERCENTILE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        PERCENTILE_FILE,
        index=False,
    )

    print(
        "Created pooled Growth percentile file: "
        f"{PERCENTILE_FILE.relative_to(ROOT)}"
    )


def percentile_score(series):
    """
    Convert an indicator into a pooled percentile rank.

    Higher values receive higher scores.
    Scores are kept strictly above zero for compatibility with
    the geometric JESI aggregation.
    """
    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    if values.isna().any():
        fail(
            "Missing values detected while calculating Growth scores."
        )

    n = len(values)

    if n == 0:
        fail("Cannot score an empty indicator.")

    if n == 1:
        return pd.Series(
            [1.0],
            index=series.index,
        )

    ranks = values.rank(
        method="average",
        ascending=True,
    )

    scores = (ranks - 1) / (n - 1)

    # JESI geometric aggregation cannot accept zero.
    scores = scores.clip(
        lower=0.001,
        upper=1.0,
    )

    return scores


def score_growth(df):
    """Calculate the two Growth indicator scores and pillar score."""
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


def validate_output(df):
    """Validate the final Growth pillar output."""
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
        if column not in df.columns
    ]

    if missing:
        fail(
            f"Growth output is missing columns: {missing}"
        )

    if df.duplicated(
        ["country_code", "year"]
    ).any():
        fail(
            "Duplicate country-year observations found "
            "in Growth output."
        )

    if df["growth_score"].isna().any():
        fail("Growth pillar contains missing scores.")

    if not (
        (df["growth_score"] > 0)
        & (df["growth_score"] <= 1)
    ).all():
        fail(
            "Growth pillar scores must be within (0, 1]."
        )


def main():
    """Run the complete Growth scoring stage."""
    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Growth Pillar Scoring")
    print("=" * 70)

    df = load_growth_data()

    print(
        f"Loaded {len(df)} Growth observations."
    )

    build_pooled_percentiles(df)

    result = score_growth(df)

    result = result[
        result["year"].between(
            START_YEAR,
            END_YEAR,
        )
    ].copy()

    result["year"] = result["year"].astype(int)

    validate_output(result)

    result = result[
        [
            "country_code",
            "year",
            "real_gdp_growth",
            "gni_per_capita_growth",
            "gdp_growth_score",
            "gni_growth_score",
            "growth_score",
        ]
    ]

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "Growth pillar output:"
    )
    print(
        OUTPUT_FILE.relative_to(ROOT)
    )

    print(
        f"Rows written: {len(result)}"
    )

    print("=" * 70)
    print("Growth pillar scoring completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
