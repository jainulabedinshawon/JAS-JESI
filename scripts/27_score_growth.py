"""
Score the JESI Growth pillar from the long-format Growth dataset.

Input format:
country | year | value | indicator

The script:
1. Loads the World Bank Growth dataset.
2. Identifies GDP growth and GNI per-capita growth indicators.
3. Converts the long-format data into country-year wide format.
4. Calculates pooled percentile scores.
5. Constructs the arithmetic Growth pillar score.
6. Saves the Growth pillar output.

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

COUNTRY_MAP = {
    "bangladesh": "BGD",
    "india": "IND",
    "indonesia": "IDN",
    "malaysia": "MYS",
    "vietnam": "VNM",
    "viet nam": "VNM",
}

START_YEAR = 2015
END_YEAR = 2024


def fail(message):
    """Stop the pipeline with a clear error."""
    raise RuntimeError(message)


def normalize_text(value):
    """Normalize text for indicator matching."""
    return (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace("/", " ")
        .replace("%", " percent ")
    )


def identify_indicator(indicator):
    """
    Classify a raw indicator name as GDP growth or GNI per-capita growth.
    """
    text = normalize_text(indicator)

    # GNI per-capita growth must be checked first because it also
    # contains the word growth.
    if (
        ("gni" in text or "gross national income" in text)
        and ("per capita" in text or "capita" in text)
        and "growth" in text
    ):
        return "gni_per_capita_growth"

    if (
        ("gdp" in text or "gross domestic product" in text)
        and "growth" in text
    ):
        return "real_gdp_growth"

    return None


def load_growth_data():
    """Load and transform the long-format Growth dataset."""
    if not INPUT_FILE.is_file():
        fail(
            "Missing Growth input file: "
            f"{INPUT_FILE.relative_to(ROOT)}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = {
        "country",
        "year",
        "value",
        "indicator",
    }

    missing = required_columns - set(df.columns)

    if missing:
        fail(
            "Growth input file is missing columns: "
            f"{sorted(missing)}"
        )

    if df.empty:
        fail("Growth input CSV is empty.")

    print(
        "Available Growth indicators:"
    )

    for indicator in sorted(
        df["indicator"].dropna().astype(str).unique()
    ):
        print(f"  - {indicator}")

    df["country"] = (
        df["country"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["country_code"] = df["country"].map(COUNTRY_MAP)

    unknown_countries = sorted(
        set(df.loc[df["country_code"].isna(), "country"])
    )

    if unknown_countries:
        print(
            "Warning: Unrecognized countries ignored: "
            f"{unknown_countries}"
        )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce",
    )

    df["indicator_type"] = df["indicator"].map(
        identify_indicator
    )

    recognized = df[
        df["country_code"].isin(EXPECTED_COUNTRIES)
        & df["year"].between(
            START_YEAR,
            END_YEAR,
        )
        & df["indicator_type"].notna()
    ].copy()

    if recognized.empty:
        fail(
            "No recognizable Growth indicators were found."
        )

    print(
        "Recognized indicators:"
    )

    for indicator_type in sorted(
        recognized["indicator_type"].unique()
    ):
        print(f"  - {indicator_type}")

    # Keep only the observations needed for JESI Growth.
    recognized = recognized[
        [
            "country_code",
            "year",
            "indicator_type",
            "value",
        ]
    ].copy()

    # Detect duplicate country-year-indicator observations.
    duplicates = recognized.duplicated(
        [
            "country_code",
            "year",
            "indicator_type",
        ],
        keep=False,
    )

    if duplicates.any():
        duplicate_rows = recognized.loc[duplicates].sort_values(
            [
                "country_code",
                "year",
                "indicator_type",
            ]
        )

        print(
            "Duplicate Growth observations detected:"
        )
        print(duplicate_rows.to_string(index=False))

        fail(
            "Duplicate country-year-indicator observations "
            "were found."
        )

    wide = recognized.pivot(
        index=[
            "country_code",
            "year",
        ],
        columns="indicator_type",
        values="value",
    ).reset_index()

    wide.columns.name = None

    required_indicators = {
        "real_gdp_growth",
        "gni_per_capita_growth",
    }

    missing_indicators = (
        required_indicators
        - set(wide.columns)
    )

    if missing_indicators:
        fail(
            "Required Growth indicators were not found: "
            f"{sorted(missing_indicators)}"
        )

    wide = wide[
        [
            "country_code",
            "year",
            "real_gdp_growth",
            "gni_per_capita_growth",
        ]
    ].copy()

    return wide


def build_pooled_percentiles(df):
    """Create pooled Growth distribution statistics."""
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
        "Created pooled Growth distribution file: "
        f"{PERCENTILE_FILE.relative_to(ROOT)}"
    )


def percentile_score(series):
    """
    Convert an indicator into a pooled percentile-rank score.

    Higher values receive higher scores.

    A small positive floor is applied because JESI uses geometric
    aggregation and therefore cannot accept zero pillar components.
    """
    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    if values.isna().any():
        fail(
            "Missing values detected while calculating "
            "Growth scores."
        )

    if values.empty:
        fail(
            "Cannot calculate a score from an empty indicator."
        )

    if len(values) == 1:
        return pd.Series(
            [1.0],
            index=series.index,
        )

    ranks = values.rank(
        method="average",
        ascending=True,
    )

    scores = (ranks - 1) / (len(values) - 1)

    return scores.clip(
        lower=0.001,
        upper=1.0,
    )


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
            "Growth output is missing columns: "
            f"{missing}"
        )

    if df.duplicated(
        ["country_code", "year"]
    ).any():
        fail(
            "Duplicate country-year observations found "
            "in Growth output."
        )

    countries = set(
        df["country_code"].astype(str)
    )

    if countries != EXPECTED_COUNTRIES:
        fail(
            "Unexpected country set in Growth output. "
            f"Expected {sorted(EXPECTED_COUNTRIES)}, "
            f"found {sorted(countries)}."
        )

    if df["growth_score"].isna().any():
        fail(
            "Growth pillar contains missing scores."
        )

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
        f"Loaded {len(df)} country-year Growth observations."
    )

    # The pooled distribution file is generated from the actual
    # indicator observations used by the scoring stage.
    build_pooled_percentiles(df)

    result = score_growth(df)

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
    ].copy()

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
    print(
        "Growth pillar scoring completed successfully."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
