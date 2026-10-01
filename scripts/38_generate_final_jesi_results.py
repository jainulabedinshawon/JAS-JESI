"""
JAS Unified Economic Strength Index (JESI)
Final Research Results Generator

Generates:

1. Country-level final JESI results
2. Pillar-level country averages
3. Year-level JESI summary
4. Final research-ready table
5. Country coverage metadata

Important methodological rule:
    The production JESI remains based on the complete-case
    country-year sample.

    Unequal country observation counts are NOT silently treated
    as equivalent coverage.

    Coverage, missing observations, and balanced-panel eligibility
    are explicitly reported for research transparency.

This script does NOT change:
    - production pillar scores
    - production weights
    - production normalization
    - production aggregation
    - complete-case methodology
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/results/jesi_country_year_2016_2023.csv"
)

OUTPUT_DIR = Path("data/results")

PILLARS = [
    "G",
    "P",
    "C",
    "R",
    "A",
]

EXPECTED_COUNTRIES = {
    "BGD",
    "IND",
    "IDN",
    "MYS",
    "VNM",
}

EXPECTED_YEARS = set(
    range(2016, 2024)
)

EXPECTED_YEARS_PER_COUNTRY = len(
    EXPECTED_YEARS
)


def validate_input(df):
    """Validate the country-year JESI dataset."""

    required = {
        "country_code",
        "country",
        "year",
        "JESI",
        *PILLARS,
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            "Input JESI dataset is missing columns: "
            f"{sorted(missing)}"
        )

    if df.empty:
        raise ValueError(
            "Input JESI dataset is empty."
        )

    actual_countries = set(
        df["country_code"]
    )

    if actual_countries != EXPECTED_COUNTRIES:
        raise ValueError(
            "Unexpected country set in JESI dataset. "
            f"Expected: {sorted(EXPECTED_COUNTRIES)}; "
            f"Found: {sorted(actual_countries)}"
        )

    actual_years = set(
        df["year"]
    )

    if not actual_years.issubset(
        EXPECTED_YEARS
    ):
        unexpected_years = (
            actual_years
            - EXPECTED_YEARS
        )

        raise ValueError(
            "Unexpected years found in JESI dataset: "
            f"{sorted(unexpected_years)}"
        )

    if actual_years != EXPECTED_YEARS:
        missing_years = (
            EXPECTED_YEARS
            - actual_years
        )

        raise ValueError(
            "Input JESI dataset does not contain all "
            f"expected years 2016-2023. "
            f"Missing years: {sorted(missing_years)}"
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
        raise ValueError(
            "Duplicate country-year observations found:\n"
            f"{duplicates.to_string(index=False)}"
        )

    if df["JESI"].isna().any():
        raise ValueError(
            "Missing JESI values found."
        )

    for pillar in PILLARS:

        if df[pillar].isna().any():
            raise ValueError(
                f"Missing values found in pillar {pillar}."
            )

        if (
            (df[pillar] <= 0).any()
            or (df[pillar] > 1).any()
        ):
            raise ValueError(
                f"Pillar {pillar} contains values "
                "outside (0, 1]."
            )

    if (
        (df["JESI"] <= 0).any()
        or (df["JESI"] > 100).any()
    ):
        raise ValueError(
            "JESI values must be between 0 and 100."
        )


def calculate_country_coverage(df):
    """
    Calculate country-level observation coverage.

    This is descriptive metadata only.

    It does not alter the production JESI sample.
    """

    coverage = (
        df.groupby(
            [
                "country_code",
                "country",
            ]
        )["year"]
        .agg(
            observations="count",
            first_year="min",
            last_year="max",
        )
        .reset_index()
    )

    coverage["expected_observations"] = (
        EXPECTED_YEARS_PER_COUNTRY
    )

    coverage["missing_observations"] = (
        coverage["expected_observations"]
        - coverage["observations"]
    )

    coverage["coverage_pct"] = (
        coverage["observations"]
        / coverage["expected_observations"]
        * 100
    )

    coverage["balanced_panel_eligible"] = (
        coverage["observations"]
        == EXPECTED_YEARS_PER_COUNTRY
    )

    return coverage


def validate_country_coverage(coverage):
    """
    Validate that coverage metadata is internally consistent.

    Unequal coverage is reported as a methodological caution,
    not treated as a data error.

    The production methodology remains complete-case analysis.
    """

    if coverage.empty:
        raise ValueError(
            "Country coverage table is empty."
        )

    if set(
        coverage["country_code"]
    ) != EXPECTED_COUNTRIES:
        raise ValueError(
            "Country coverage does not contain "
            "the expected five countries."
        )

    if (
        coverage["observations"] < 1
    ).any():
        raise ValueError(
            "At least one country has zero observations."
        )

    expected_missing = (
        coverage["expected_observations"]
        - coverage["observations"]
    )

    if not (
        expected_missing
        == coverage["missing_observations"]
    ).all():
        raise ValueError(
            "Country missing-observation counts "
            "are internally inconsistent."
        )

    expected_coverage = (
        coverage["observations"]
        / coverage["expected_observations"]
        * 100
    )

    if not (
        expected_coverage
        .round(10)
        == coverage["coverage_pct"]
        .round(10)
    ).all():
        raise ValueError(
            "Country coverage percentages "
            "are internally inconsistent."
        )

    expected_balanced = (
        coverage["observations"]
        == EXPECTED_YEARS_PER_COUNTRY
    )

    if not (
        expected_balanced
        == coverage["balanced_panel_eligible"]
    ).all():
        raise ValueError(
            "Balanced-panel eligibility flags "
            "are internally inconsistent."
        )


def main():
    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Final Research Results Generator")
    print("=" * 70)

    # ---------------------------------------------------------------
    # Check input file
    # ---------------------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing JESI input file: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    validate_input(df)

    # ---------------------------------------------------------------
    # Country coverage
    # ---------------------------------------------------------------

    coverage = calculate_country_coverage(
        df
    )

    validate_country_coverage(
        coverage
    )

    unequal_coverage = (
        coverage["observations"]
        != EXPECTED_YEARS_PER_COUNTRY
    ).any()

    # ---------------------------------------------------------------
    # Country-level averages
    # ---------------------------------------------------------------

    country_results = (
        df.groupby(
            [
                "country_code",
                "country",
            ]
        )
        .agg(
            G=("G", "mean"),
            P=("P", "mean"),
            C=("C", "mean"),
            R=("R", "mean"),
            A=("A", "mean"),
            JESI=("JESI", "mean"),
            observations=("JESI", "count"),
        )
        .reset_index()
    )

    # ---------------------------------------------------------------
    # Merge coverage metadata into country results
    # ---------------------------------------------------------------

    country_results = country_results.merge(
        coverage[
            [
                "country_code",
                "observations",
                "expected_observations",
                "missing_observations",
                "coverage_pct",
                "balanced_panel_eligible",
            ]
        ],
        on=[
            "country_code",
            "observations",
        ],
        how="left",
        validate="one_to_one",
    )

    # ---------------------------------------------------------------
    # Country-level JESI standard deviation
    # ---------------------------------------------------------------

    country_std = (
        df.groupby(
            [
                "country_code",
                "country",
            ]
        )["JESI"]
        .std()
        .reset_index(
            name="JESI_std"
        )
    )

    country_results = country_results.merge(
        country_std,
        on=[
            "country_code",
            "country",
        ],
        how="left",
        validate="one_to_one",
    )

    # ---------------------------------------------------------------
    # Validate country observations
    # ---------------------------------------------------------------

    if (
        country_results["observations"] < 1
    ).any():
        raise ValueError(
            "One or more countries have no observations."
        )

    # ---------------------------------------------------------------
    # Country ranking
    # ---------------------------------------------------------------

    country_results["rank"] = (
        country_results["JESI"]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    country_results = country_results.sort_values(
        "rank"
    ).reset_index(drop=True)

    # ---------------------------------------------------------------
    # Presentation score
    # ---------------------------------------------------------------

    country_results["JESI_score_100"] = (
        country_results["JESI"]
    )

    # ---------------------------------------------------------------
    # Year-level JESI summary
    # ---------------------------------------------------------------

    yearly_results = (
        df.groupby("year")["JESI"]
        .agg(
            mean="mean",
            median="median",
            minimum="min",
            maximum="max",
            observations="count",
        )
        .reset_index()
        .sort_values("year")
        .reset_index(drop=True)
    )

    # ---------------------------------------------------------------
    # Validate yearly results
    # ---------------------------------------------------------------

    if yearly_results.empty:
        raise ValueError(
            "Year-level JESI summary is empty."
        )

    if (
        yearly_results["observations"] < 1
    ).any():
        raise ValueError(
            "One or more years have no observations."
        )

    # ---------------------------------------------------------------
    # Final research-ready table
    #
    # IMPORTANT:
    # Observation and coverage metadata are deliberately included
    # so that unequal country coverage cannot be hidden in the
    # research-facing table.
    # ---------------------------------------------------------------

    research_table = country_results[
        [
            "rank",
            "country_code",
            "country",
            "G",
            "P",
            "C",
            "R",
            "A",
            "JESI_score_100",
            "JESI_std",
            "observations",
            "expected_observations",
            "missing_observations",
            "coverage_pct",
            "balanced_panel_eligible",
        ]
    ].copy()

    research_table = research_table.rename(
        columns={
            "G": "Growth",
            "P": "Productivity",
            "C": "Connectivity",
            "R": "Resilience",
            "A": "Strategic_Autonomy",
            "JESI_score_100": "JESI",
        }
    )

    # ---------------------------------------------------------------
    # Output directory
    # ---------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Output files
    # ---------------------------------------------------------------

    country_file = (
        OUTPUT_DIR
        / "final_jesi_country_results.csv"
    )

    yearly_file = (
        OUTPUT_DIR
        / "final_jesi_yearly_summary.csv"
    )

    research_file = (
        OUTPUT_DIR
        / "JESI_final_research_table.csv"
    )

    coverage_file = (
        OUTPUT_DIR
        / "jesi_country_coverage_2016_2023.csv"
    )

    country_results.to_csv(
        country_file,
        index=False,
    )

    yearly_results.to_csv(
        yearly_file,
        index=False,
    )

    research_table.to_csv(
        research_file,
        index=False,
    )

    coverage.to_csv(
        coverage_file,
        index=False,
    )

    # ---------------------------------------------------------------
    # Console output
    # ---------------------------------------------------------------

    print()
    print("Country coverage:")
    print(
        coverage.to_string(
            index=False
        )
    )

    print()
    print("Final country-level JESI results:")
    print(
        country_results.to_string(
            index=False
        )
    )

    print()
    print("Year-level JESI summary:")
    print(
        yearly_results.to_string(
            index=False
        )
    )

    print()
    print("Final research-ready table:")
    print(
        research_table.to_string(
            index=False
        )
    )

    print()
    print(
        f"Saved: {country_file}"
    )

    print(
        f"Saved: {yearly_file}"
    )

    print(
        f"Saved: {research_file}"
    )

    print(
        f"Saved: {coverage_file}"
    )

    print()

    if unequal_coverage:
        print(
            "METHODOLOGICAL CAUTION:"
        )
        print(
            "Country-level observation coverage is unequal."
        )
        print(
            "The production complete-case methodology "
            "has NOT been changed."
        )
        print(
            "Balanced-panel sensitivity analysis should "
            "be considered separately."
        )
    else:
        print(
            "Country-level observation coverage is balanced."
        )

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print(
        "Final JESI research results generated successfully."
    )
    print(
        "Country observation coverage is explicitly reported."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
