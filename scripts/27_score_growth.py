"""
JAS Unified Economic Strength Index
Growth Pillar Scoring

Purpose
-------
Convert long-format World Bank Growth data into percentile-based
indicator scores and a Growth pillar score.

Supported World Bank indicators:
- NY.GDP.MKTP.KD.ZG  -> Real GDP Growth
- NY.GNP.PCAP.KD.ZG  -> GNI per Capita Growth

Input
-----
data/raw/growth_indicators_2015_2025.csv

Expected columns
----------------
country, year, value, indicator

Outputs
-------
data/processed/growth_pooled_percentiles.csv
data/processed/growth_pillar_scores_2015_2024.csv
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

INPUT_FILE = Path("data/raw/growth_indicators_2015_2025.csv")

PERCENTILE_OUTPUT = Path(
    "data/processed/growth_pooled_percentiles.csv"
)

PILLAR_OUTPUT = Path(
    "data/processed/growth_pillar_scores_2015_2024.csv"
)

EXPECTED_COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
    "VNM": "Vietnam",
}

EXPECTED_YEARS = set(range(2015, 2025))


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def fail(message: str) -> None:
    """Stop execution with a clear error message."""
    raise RuntimeError(message)


def normalize_text(value) -> str:
    """Normalize text for robust indicator/country matching."""
    if pd.isna(value):
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


def country_to_code(value) -> str:
    """Map country names/codes to the JESI country code."""
    text = normalize_text(value)

    mapping = {
        "bangladesh": "BGD",
        "bgd": "BGD",
        "india": "IND",
        "ind": "IND",
        "indonesia": "IDN",
        "idn": "IDN",
        "malaysia": "MYS",
        "mys": "MYS",
        "vietnam": "VNM",
        "viet nam": "VNM",
        "vnm": "VNM",
    }

    return mapping.get(text, "")


def identify_indicator(value) -> str:
    """
    Identify the Growth indicator.

    Returns
    -------
    str
        'real_gdp_growth',
        'gni_per_capita_growth',
        or '' if unrecognized.
    """
    text = normalize_text(value)

    # Exact World Bank indicator codes.
    if text == "ny.gdp.mktp.kd.zg":
        return "real_gdp_growth"

    if text == "ny.gnp.pcap.kd.zg":
        return "gni_per_capita_growth"

    # Descriptive-name fallbacks.
    compact = text.replace(" ", "")

    if (
        "gdp" in compact
        and "growth" in compact
    ):
        return "real_gdp_growth"

    if (
        ("gni" in compact or "grossnationalincome" in compact)
        and ("capita" in compact or "percapita" in compact)
        and "growth" in compact
    ):
        return "gni_per_capita_growth"

    return ""


def percentile_score(series: pd.Series) -> pd.Series:
    """
    Convert an indicator into pooled percentile scores.

    Missing observations remain missing.

    A very small positive floor is applied to valid percentile
    scores so that the geometric JESI aggregation never receives
    an exact zero.
    """
    numeric = pd.to_numeric(series, errors="coerce")

    result = numeric.rank(
        method="average",
        pct=True,
        na_option="keep",
    )

    result = result.clip(lower=0.001, upper=1.0)

    return result


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------

def load_growth_data() -> pd.DataFrame:
    """Load and reshape the raw long-format Growth dataset."""

    if not INPUT_FILE.exists():
        fail(f"Missing Growth input file: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)

    required_columns = {
        "country",
        "year",
        "value",
        "indicator",
    }

    missing = required_columns.difference(df.columns)

    if missing:
        fail(
            "Growth input file is missing required columns: "
            f"{sorted(missing)}"
        )

    # -------------------------------------------------------------
    # Country mapping
    # -------------------------------------------------------------

    df["country_code"] = df["country"].apply(country_to_code)

    df = df[df["country_code"].isin(EXPECTED_COUNTRIES)].copy()

    if df.empty:
        fail(
            "No recognized JESI countries were found in the Growth data."
        )

    # -------------------------------------------------------------
    # Year normalization
    # -------------------------------------------------------------

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df = df[df["year"].notna()].copy()
    df["year"] = df["year"].astype(int)

    df = df[
        df["year"].isin(EXPECTED_YEARS)
    ].copy()

    if df.empty:
        fail(
            "No Growth observations remain for the expected "
            "2015-2024 period."
        )

    # -------------------------------------------------------------
    # Indicator identification
    # -------------------------------------------------------------

    df["indicator_type"] = df["indicator"].apply(
        identify_indicator
    )

    recognized = df[
        df["indicator_type"].isin(
            {
                "real_gdp_growth",
                "gni_per_capita_growth",
            }
        )
    ].copy()

    if recognized.empty:
        available = sorted(
            df["indicator"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        fail(
            "No recognizable Growth indicators were found.\n"
            "Growth Pillar Scoring\n"
            "Available Growth indicators:\n"
            + "\n".join(
                f"  - {item}"
                for item in available
            )
        )

    # -------------------------------------------------------------
    # Numeric values
    # -------------------------------------------------------------

    recognized["value"] = pd.to_numeric(
        recognized["value"],
        errors="coerce",
    )

    # -------------------------------------------------------------
    # Duplicate validation
    # -------------------------------------------------------------

    duplicate_check = recognized[
        recognized.duplicated(
            subset=[
                "country_code",
                "year",
                "indicator_type",
            ],
            keep=False,
        )
    ]

    if not duplicate_check.empty:
        fail(
            "Duplicate Growth observations detected for "
            "country-year-indicator combinations:\n"
            + duplicate_check[
                [
                    "country_code",
                    "year",
                    "indicator_type",
                ]
            ]
            .drop_duplicates()
            .to_string(index=False)
        )

    # -------------------------------------------------------------
    # Pivot to one row per country-year
    # -------------------------------------------------------------

    pivot = (
        recognized
        .pivot(
            index=[
                "country_code",
                "year",
            ],
            columns="indicator_type",
            values="value",
        )
        .reset_index()
    )

    pivot.columns.name = None

    required_indicators = {
        "real_gdp_growth",
        "gni_per_capita_growth",
    }

    missing_indicator_columns = (
        required_indicators
        .difference(pivot.columns)
    )

    if missing_indicator_columns:
        fail(
            "The following required Growth indicators are missing "
            f"after reshaping: {sorted(missing_indicator_columns)}"
        )

    # Add readable country name.
    pivot["country"] = pivot["country_code"].map(
        EXPECTED_COUNTRIES
    )

    # -------------------------------------------------------------
    # Known missing GNI observations
    # -------------------------------------------------------------
    #
    # Bangladesh 2015-2017 has missing GNI per Capita Growth in
    # the World Bank source used by this project.
    #
    # These observations are retained in the raw/reshaped data,
    # but they cannot receive a two-indicator Growth pillar score.
    #

    pivot = pivot[
        [
            "country_code",
            "country",
            "year",
            "real_gdp_growth",
            "gni_per_capita_growth",
        ]
    ].sort_values(
        [
            "country_code",
            "year",
        ]
    )

    return pivot.reset_index(drop=True)


# ---------------------------------------------------------------------
# Percentile construction
# ---------------------------------------------------------------------

def build_percentile_scores(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Create pooled percentile scores across all countries/years."""

    result = df.copy()

    result["real_gdp_growth_percentile"] = percentile_score(
        result["real_gdp_growth"]
    )

    result["gni_per_capita_growth_percentile"] = percentile_score(
        result["gni_per_capita_growth"]
    )

    # Growth pillar can only be constructed where both indicators
    # are available.
    result["growth_score"] = (
        result[
            [
                "real_gdp_growth_percentile",
                "gni_per_capita_growth_percentile",
            ]
        ]
        .mean(
            axis=1,
            skipna=False,
        )
    )

    # Keep valid scores strictly positive and <= 1.
    result.loc[
        result["growth_score"].notna(),
        "growth_score",
    ] = result.loc[
        result["growth_score"].notna(),
        "growth_score",
    ].clip(
        lower=0.001,
        upper=1.0,
    )

    return result


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def validate_percentile_output(df: pd.DataFrame) -> None:
    """Validate the generated Growth percentile dataset."""

    required = {
        "country_code",
        "country",
        "year",
        "real_gdp_growth",
        "gni_per_capita_growth",
        "real_gdp_growth_percentile",
        "gni_per_capita_growth_percentile",
        "growth_score",
    }

    missing = required.difference(df.columns)

    if missing:
        fail(
            "Growth percentile output is missing columns: "
            f"{sorted(missing)}"
        )

    duplicates = df[
        df.duplicated(
            subset=[
                "country_code",
                "year",
            ],
            keep=False,
        )
    ]

    if not duplicates.empty:
        fail(
            "Duplicate country-year rows detected in Growth output."
        )

    # Percentile values must be within range whenever present.
    for column in [
        "real_gdp_growth_percentile",
        "gni_per_capita_growth_percentile",
        "growth_score",
    ]:
        values = df[column].dropna()

        if not values.between(
            0.001,
            1.0,
        ).all():
            fail(
                f"Invalid values found in {column}."
            )


def build_final_pillar_output(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the Growth pillar output used by downstream JESI scripts.

    Rows with incomplete two-indicator Growth data are excluded from
    the pillar score output. This allows known World Bank missing
    observations to remain documented upstream without breaking
    the final JESI sample.
    """

    scored = df[
        df["growth_score"].notna()
    ].copy()

    if scored.empty:
        fail(
            "No complete Growth pillar observations are available."
        )

    # Final pillar output.
    output = scored[
        [
            "country_code",
            "country",
            "year",
            "real_gdp_growth",
            "gni_per_capita_growth",
            "real_gdp_growth_percentile",
            "gni_per_capita_growth_percentile",
            "growth_score",
        ]
    ].copy()

    output = output.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)

    return output


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:
    """Run the complete Growth pillar scoring pipeline."""

    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Growth Pillar Scoring")
    print("=" * 70)

    # Load and reshape.
    df = load_growth_data()

    print(
        f"Loaded {len(df)} country-year observations "
        "after reshaping."
    )

    print(
        "Recognized indicators:"
    )
    print(
        "  - NY.GDP.MKTP.KD.ZG -> Real GDP Growth"
    )
    print(
        "  - NY.GNP.PCAP.KD.ZG -> GNI per Capita Growth"
    )

    # Build percentile scores.
    scored = build_percentile_scores(df)

    # Validate.
    validate_percentile_output(scored)

    # Create output directory.
    PERCENTILE_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save full percentile dataset.
    scored.to_csv(
        PERCENTILE_OUTPUT,
        index=False,
    )

    # Build final complete-case Growth pillar.
    pillar = build_final_pillar_output(scored)

    # -------------------------------------------------------------
    # Final pillar validation
    # -------------------------------------------------------------

    expected_country_codes = set(
        EXPECTED_COUNTRIES.keys()
    )

    actual_country_codes = set(
        pillar["country_code"].unique()
    )

    if actual_country_codes != expected_country_codes:
        fail(
            "Growth pillar country coverage mismatch.\n"
            f"Expected: {sorted(expected_country_codes)}\n"
            f"Found: {sorted(actual_country_codes)}"
        )

    if pillar["growth_score"].isna().any():
        fail(
            "Growth pillar contains missing growth_score values."
        )

    if not pillar["growth_score"].between(
        0.001,
        1.0,
    ).all():
        fail(
            "Growth pillar scores are outside the valid "
            "0.001-1.0 range."
        )

    # Save final pillar output.
    pillar.to_csv(
        PILLAR_OUTPUT,
        index=False,
    )

    print()
    print(
        f"Percentile output written to: "
        f"{PERCENTILE_OUTPUT}"
    )

    print(
        f"Growth pillar output written to: "
        f"{PILLAR_OUTPUT}"
    )

    print()
    print(
        f"Final Growth pillar observations: {len(pillar)}"
    )

    print(
        "Country coverage:"
    )

    for code in sorted(
        pillar["country_code"].unique()
    ):
        count = int(
            (
                pillar["country_code"]
                == code
            ).sum()
        )

        print(
            f"  - {code}: {count} observations"
        )

    print()
    print(
        "Growth Pillar Scoring completed successfully."
    )

    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise
