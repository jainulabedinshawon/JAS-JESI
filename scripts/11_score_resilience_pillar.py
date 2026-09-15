"""
JESI Resilience Pillar Scoring

Purpose:
    Convert validated resilience indicator data into
    country-year Resilience pillar scores.

Indicators:
    R1: FX Reserves / Import Cover
    R2: Government Gross Debt / GDP
    R3: Current Account Balance / GDP

Methodology:
    R1 -> Positive min-max normalization
    R2 -> Nonlinear P10-P90 reference-zone scoring
    R3 -> Nonlinear P10-P90 reference-zone scoring

Final Resilience pillar:
    R = (R1 + R2 + R3) / 3

Input:
    data/raw/resilience_indicators_2015_2024.csv

Output:
    data/processed/resilience_pillar_scores_2015_2024.csv
"""

from pathlib import Path

import pandas as pd

from src.nonlinear_resilience_scoring import (
    score_fx_reserves,
    score_government_debt,
    score_current_account,
    calculate_resilience_pillar,
)


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = BASE_DIR / "data" / "raw" / (
    "resilience_indicators_2015_2024.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / (
    "resilience_pillar_scores_2015_2024.csv"
)

EXPECTED_COUNTRIES = {
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
}

EXPECTED_YEARS = set(range(2015, 2025))

EXPECTED_INDICATORS = {
    "FI.RES.TOTL.MO",
    "GGXWDG_NGDP",
    "BN.CAB.XOKA.GD.ZS",
}


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def validate_input(df):
    """Validate the raw resilience dataset."""

    required_columns = {
        "country",
        "year",
        "value",
        "indicator",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce",
    )

    if df["year"].isna().any():
        raise ValueError("Found invalid year values.")

    if df["value"].isna().any():
        raise ValueError(
            "Found missing or non-numeric indicator values."
        )

    df["year"] = df["year"].astype(int)

    countries = set(df["country"].unique())
    years = set(df["year"].unique())
    indicators = set(df["indicator"].unique())

    if countries != EXPECTED_COUNTRIES:
        raise ValueError(
            "Country coverage does not match the expected "
            "five-country sample."
        )

    if years != EXPECTED_YEARS:
        raise ValueError(
            "Year coverage does not match 2015-2024."
        )

    if indicators != EXPECTED_INDICATORS:
        raise ValueError(
            "Indicator coverage does not match the expected "
            "three resilience indicators."
        )

    expected_rows = (
        len(EXPECTED_COUNTRIES)
        * len(EXPECTED_YEARS)
        * len(EXPECTED_INDICATORS)
    )

    if len(df) != expected_rows:
        raise ValueError(
            f"Unexpected row count: {len(df)}. "
            f"Expected {expected_rows}."
        )

    duplicates = df.duplicated(
        subset=[
            "country",
            "year",
            "indicator",
        ]
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate country-year-indicator records found."
        )

    return df


# ---------------------------------------------------------------------
# Reshape data
# ---------------------------------------------------------------------

def prepare_country_year_data(df):
    """
    Convert long-format indicator data into one row
    per country-year.
    """

    pivoted = df.pivot(
        index=["country", "year"],
        columns="indicator",
        values="value",
    ).reset_index()

    pivoted.columns.name = None

    required_columns = [
        "FI.RES.TOTL.MO",
        "GGXWDG_NGDP",
        "BN.CAB.XOKA.GD.ZS",
    ]

    for column in required_columns:
        if column not in pivoted.columns:
            raise ValueError(
                f"Missing indicator after reshaping: {column}"
            )

    return pivoted


# ---------------------------------------------------------------------
# Calculate R1 reference range
# ---------------------------------------------------------------------

def calculate_fx_reference_range(df):
    """
    Calculate the empirical minimum and maximum of
    FX Reserves / Import Cover over the full sample.
    """

    minimum = df["FI.RES.TOTL.MO"].min()
    maximum = df["FI.RES.TOTL.MO"].max()

    if maximum <= minimum:
        raise ValueError(
            "FX reserves maximum must be greater than minimum."
        )

    return minimum, maximum


# ---------------------------------------------------------------------
# Calculate resilience scores
# ---------------------------------------------------------------------

def calculate_scores(df, fx_minimum, fx_maximum):
    """Calculate R1, R2, R3 and final Resilience scores."""

    results = []

    for _, row in df.iterrows():

        fx_score = score_fx_reserves(
            row["FI.RES.TOTL.MO"],
            minimum=fx_minimum,
            maximum=fx_maximum,
        )

        debt_score = score_government_debt(
            row["GGXWDG_NGDP"]
        )

        current_account_score = score_current_account(
            row["BN.CAB.XOKA.GD.ZS"]
        )

        resilience_score = calculate_resilience_pillar(
            fx_score,
            debt_score,
            current_account_score,
        )

        results.append(
            {
                "country": row["country"],
                "year": int(row["year"]),
                "fx_reserves_months": row[
                    "FI.RES.TOTL.MO"
                ],
                "government_debt_gdp": row[
                    "GGXWDG_NGDP"
                ],
                "current_account_gdp": row[
                    "BN.CAB.XOKA.GD.ZS"
                ],
                "R1_fx_reserves_score": fx_score,
                "R2_debt_score": debt_score,
                "R3_current_account_score": (
                    current_account_score
                ),
                "resilience_score": resilience_score,
                "resilience_score_100": (
                    resilience_score * 100
                ),
            }
        )

    return pd.DataFrame(results)


# ---------------------------------------------------------------------
# Validate scores
# ---------------------------------------------------------------------

def validate_scores(scores):
    """Validate the final Resilience pillar scores."""

    expected_rows = (
        len(EXPECTED_COUNTRIES)
        * len(EXPECTED_YEARS)
    )

    if len(scores) != expected_rows:
        raise ValueError(
            f"Unexpected final row count: {len(scores)}. "
            f"Expected {expected_rows}."
        )

    score_columns = [
        "R1_fx_reserves_score",
        "R2_debt_score",
        "R3_current_account_score",
        "resilience_score",
    ]

    for column in score_columns:
        if scores[column].isna().any():
            raise ValueError(
                f"Missing values found in {column}."
            )

        if (
            (scores[column] < 0)
            | (scores[column] > 1)
        ).any():
            raise ValueError(
                f"Scores outside [0, 1] found in {column}."
            )

    if scores[
        ["country", "year"]
    ].duplicated().any():
        raise ValueError(
            "Duplicate country-year resilience scores found."
        )

    return scores


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    print("=" * 72)
    print("JESI RESILIENCE PILLAR SCORING")
    print("=" * 72)
    print()

    print("Input file:")
    print(INPUT_FILE)
    print()

    if not INPUT_FILE.exists():
        print(
            f"ERROR: Input file not found: {INPUT_FILE}"
        )
        return 1

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print()

    try:
        df = validate_input(df)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    print("Input validation: PASSED")
    print()

    country_year_data = prepare_country_year_data(df)

    print(
        f"Country-year observations: "
        f"{len(country_year_data)}"
    )
    print()

    fx_minimum, fx_maximum = (
        calculate_fx_reference_range(
            country_year_data
        )
    )

    print("=" * 72)
    print("R1 FX RESERVES REFERENCE RANGE")
    print("=" * 72)
    print(f"Minimum: {fx_minimum:.6f}")
    print(f"Maximum: {fx_maximum:.6f}")
    print()

    print("=" * 72)
    print("NONLINEAR REFERENCE ZONES")
    print("=" * 72)
    print(
        "Debt P10-P90: "
        f"{29.287000:.6f} - {77.458300:.6f}"
    )
    print(
        "Current Account P10-P90: "
        f"{-2.427516:.6f} - {3.881556:.6f}"
    )
    print()

    scores = calculate_scores(
        country_year_data,
        fx_minimum=fx_minimum,
        fx_maximum=fx_maximum,
    )

    try:
        scores = validate_scores(scores)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    scores = scores.sort_values(
        ["country", "year"]
    ).reset_index(drop=True)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    scores.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("=" * 72)
    print("RESILIENCE PILLAR SUMMARY")
    print("=" * 72)

    print(
        scores[
            [
                "country",
                "year",
                "resilience_score",
                "resilience_score_100",
            ]
        ].to_string(index=False)
    )

    print()
    print("=" * 72)
    print("OUTPUT")
    print("=" * 72)
    print(f"Saved: {OUTPUT_FILE}")
    print()

    print(
        "JESI Resilience Pillar scoring "
        "completed successfully."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
