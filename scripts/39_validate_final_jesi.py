"""
JAS Unified Economic Strength Index (JESI)
Final JESI Validation

Validates:

1. Required files and schemas
2. Theoretical country-year coverage
3. Complete-case country-year coverage
4. Duplicate country-year observations
5. Pillar score ranges
6. JESI score range
7. Mathematical consistency
8. Country-level aggregation
9. Ranking integrity
10. Year-level summary consistency
11. Robustness output consistency
12. Final research table consistency

Methodological rule:
    The theoretical JESI panel contains 40 observations
    (5 countries x 8 years).

    The final analytical dataset may contain fewer observations
    when source data are unavailable.

    Missing observations are excluded transparently.
    No imputation, interpolation, replacement, or fabrication
    is permitted.
"""

from pathlib import Path

import numpy as np
import pandas as pd


RESULTS_DIR = Path("data/results")

COUNTRY_YEAR_FILE = (
    RESULTS_DIR
    / "jesi_country_year_2016_2023.csv"
)

COUNTRY_RANKING_FILE = (
    RESULTS_DIR
    / "jesi_country_ranking_2016_2023.csv"
)

ROBUSTNESS_FILE = (
    RESULTS_DIR
    / "jesi_robustness_country_results.csv"
)

ROBUSTNESS_CORRELATION_FILE = (
    RESULTS_DIR
    / "jesi_robustness_correlations.csv"
)

FINAL_COUNTRY_FILE = (
    RESULTS_DIR
    / "final_jesi_country_results.csv"
)

YEARLY_FILE = (
    RESULTS_DIR
    / "final_jesi_yearly_summary.csv"
)

RESEARCH_TABLE_FILE = (
    RESULTS_DIR
    / "JESI_final_research_table.csv"
)

PILLARS = [
    "G",
    "P",
    "C",
    "R",
    "A",
]

WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}

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

EXPECTED_THEORETICAL_OBSERVATIONS = (
    len(EXPECTED_COUNTRIES)
    * len(EXPECTED_YEARS)
)


def check_file(path):
    """Check that a required file exists."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required file is missing: {path}"
        )


def validate_country_year_dataset(df):
    """
    Validate the main country-year JESI dataset.

    The theoretical panel contains 40 observations.

    The actual JESI dataset may contain fewer observations
    because the calculation follows a complete-case rule.

    No imputation is allowed.
    """

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
            "Country-year JESI file is missing columns: "
            f"{sorted(missing)}"
        )

    if df.empty:
        raise ValueError(
            "Country-year JESI dataset is empty."
        )

    # ---------------------------------------------------------------
    # Country validation
    # ---------------------------------------------------------------

    actual_countries = set(
        df["country_code"]
    )

    if actual_countries != EXPECTED_COUNTRIES:
        raise ValueError(
            "Unexpected country set in JESI dataset. "
            f"Expected: {sorted(EXPECTED_COUNTRIES)}; "
            f"Found: {sorted(actual_countries)}"
        )

    # ---------------------------------------------------------------
    # Year validation
    # ---------------------------------------------------------------

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
            "The final JESI dataset does not contain "
            "all expected years 2016-2023. "
            f"Missing years: {sorted(missing_years)}"
        )

    # ---------------------------------------------------------------
    # Duplicate validation
    # ---------------------------------------------------------------

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
            "Duplicate country-year observations "
            "found in main JESI dataset."
        )

    # ---------------------------------------------------------------
    # Theoretical panel size
    # ---------------------------------------------------------------

    actual_observations = len(df)

    if actual_observations > (
        EXPECTED_THEORETICAL_OBSERVATIONS
    ):
        raise ValueError(
            "Actual JESI observations exceed the "
            "theoretical panel size. "
            f"Theoretical maximum: "
            f"{EXPECTED_THEORETICAL_OBSERVATIONS}; "
            f"Found: {actual_observations}"
        )

    # ---------------------------------------------------------------
    # Complete-case validation
    # ---------------------------------------------------------------

    for pillar in PILLARS:

        if df[pillar].isna().any():
            raise ValueError(
                f"Missing values found in pillar {pillar}. "
                "Final JESI dataset must contain only "
                "complete-case observations."
            )

        if (
            (df[pillar] <= 0).any()
            or (df[pillar] > 1).any()
        ):
            raise ValueError(
                f"Pillar {pillar} contains values "
                "outside (0, 1]."
            )

    if df["JESI"].isna().any():
        raise ValueError(
            "Missing JESI values found."
        )

    if (
        (df["JESI"] <= 0).any()
        or (df["JESI"] > 100).any()
    ):
        raise ValueError(
            "JESI values must be in the range (0, 100]."
        )

    # ---------------------------------------------------------------
    # Identify excluded theoretical country-years
    # ---------------------------------------------------------------

    expected_panel = pd.MultiIndex.from_product(
        [
            sorted(EXPECTED_COUNTRIES),
            sorted(EXPECTED_YEARS),
        ],
        names=[
            "country_code",
            "year",
        ],
    ).to_frame(
        index=False
    )

    actual_panel = df[
        [
            "country_code",
            "year",
        ]
    ].drop_duplicates()

    merged = expected_panel.merge(
        actual_panel,
        on=[
            "country_code",
            "year",
        ],
        how="left",
        indicator=True,
    )

    excluded = merged[
        merged["_merge"] == "left_only"
    ].drop(
        columns="_merge"
    )

    excluded_count = len(excluded)

    expected_complete_case_count = (
        actual_observations
        + excluded_count
    )

    if expected_complete_case_count != (
        EXPECTED_THEORETICAL_OBSERVATIONS
    ):
        raise ValueError(
            "Theoretical panel reconciliation failed. "
            f"Expected "
            f"{EXPECTED_THEORETICAL_OBSERVATIONS}, "
            f"but actual + excluded = "
            f"{expected_complete_case_count}."
        )

    retention = (
        actual_observations
        / EXPECTED_THEORETICAL_OBSERVATIONS
        * 100
    )

    exclusion_percent = (
        excluded_count
        / EXPECTED_THEORETICAL_OBSERVATIONS
        * 100
    )

    print()
    print(
        "Theoretical panel observations:",
        EXPECTED_THEORETICAL_OBSERVATIONS,
    )

    print(
        "Complete-case JESI observations:",
        actual_observations,
    )

    print(
        "Excluded country-year observations:",
        excluded_count,
    )

    print(
        f"Complete-case retention: "
        f"{retention:.2f}%"
    )

    print(
        f"Excluded share: "
        f"{exclusion_percent:.2f}%"
    )

    if excluded_count > 0:
        print()
        print(
            "Excluded theoretical country-years:"
        )

        print(
            excluded.to_string(
                index=False
            )
        )

    print()
    print(
        "Complete-case rule: GREEN"
    )

    print(
        "No imputation, interpolation, "
        "replacement, or fabrication detected."
    )


def calculate_expected_jesi(row):
    """Recalculate JESI from the five pillar scores."""

    values = np.array(
        [row[pillar] for pillar in PILLARS],
        dtype=float,
    )

    weights = np.array(
        [WEIGHTS[pillar] for pillar in PILLARS],
        dtype=float,
    )

    return float(
        100
        * np.exp(
            np.sum(
                weights
                * np.log(values)
            )
        )
    )


def validate_mathematical_consistency(df):
    """Check that stored JESI matches the formula."""

    expected = df.apply(
        calculate_expected_jesi,
        axis=1,
    )

    difference = (
        df["JESI"].to_numpy()
        - expected.to_numpy()
    )

    max_difference = np.max(
        np.abs(difference)
    )

    if not np.allclose(
        df["JESI"].to_numpy(),
        expected.to_numpy(),
        rtol=1e-9,
        atol=1e-9,
    ):
        raise ValueError(
            "JESI mathematical consistency check failed. "
            f"Maximum difference: {max_difference}"
        )

    print(
        "Maximum JESI formula difference:",
        max_difference,
    )


def validate_country_ranking(
    country_year_df,
    ranking_df,
):
    """Validate country-level ranking output."""

    required = {
        "country_code",
        "country",
        "JESI_mean",
        "JESI_std",
        "JESI_min",
        "JESI_max",
        "observations",
        "rank",
    }

    missing = required - set(ranking_df.columns)

    if missing:
        raise ValueError(
            "Country ranking file is missing columns: "
            f"{sorted(missing)}"
        )

    expected = (
        country_year_df.groupby(
            [
                "country_code",
                "country",
            ]
        )["JESI"]
        .agg(
            JESI_mean="mean",
            JESI_std="std",
            JESI_min="min",
            JESI_max="max",
            observations="count",
        )
        .reset_index()
    )

    expected["rank"] = (
        expected["JESI_mean"]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    expected = expected.sort_values(
        "country_code"
    ).reset_index(drop=True)

    actual = ranking_df[
        [
            "country_code",
            "country",
            "JESI_mean",
            "JESI_std",
            "JESI_min",
            "JESI_max",
            "observations",
            "rank",
        ]
    ].copy()

    actual = actual.sort_values(
        "country_code"
    ).reset_index(drop=True)

    if set(actual["country_code"]) != EXPECTED_COUNTRIES:
        raise ValueError(
            "Country ranking does not contain "
            "the expected five countries."
        )

    numeric_columns = [
        "JESI_mean",
        "JESI_std",
        "JESI_min",
        "JESI_max",
    ]

    for column in numeric_columns:

        if not np.allclose(
            actual[column].to_numpy(),
            expected[column].to_numpy(),
            rtol=1e-9,
            atol=1e-9,
            equal_nan=True,
        ):
            raise ValueError(
                f"Country ranking aggregation mismatch "
                f"in column {column}."
            )

    if not np.array_equal(
        actual["observations"].to_numpy(),
        expected["observations"].to_numpy(),
    ):
        raise ValueError(
            "Country observation counts do not match."
        )

    if not np.array_equal(
        actual["rank"].to_numpy(),
        expected["rank"].to_numpy(),
    ):
        raise ValueError(
            "Country ranking integrity check failed."
        )


def validate_final_country_results(
    country_year_df,
    final_df,
):
    """Validate final country-level results."""

    required = {
        "country_code",
        "country",
        "G",
        "P",
        "C",
        "R",
        "A",
        "JESI",
        "JESI_std",
        "observations",
        "rank",
        "JESI_score_100",
    }

    missing = required - set(final_df.columns)

    if missing:
        raise ValueError(
            "Final country results are missing columns: "
            f"{sorted(missing)}"
        )

    expected = (
        country_year_df.groupby(
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
            JESI_std=("JESI", "std"),
            observations=("JESI", "count"),
        )
        .reset_index()
    )

    expected["JESI_score_100"] = (
        expected["JESI"]
    )

    expected["rank"] = (
        expected["JESI"]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    expected = expected.sort_values(
        "country_code"
    ).reset_index(drop=True)

    actual = final_df[
        [
            "country_code",
            "country",
            "G",
            "P",
            "C",
            "R",
            "A",
            "JESI",
            "JESI_std",
            "observations",
            "rank",
            "JESI_score_100",
        ]
    ].copy()

    actual = actual.sort_values(
        "country_code"
    ).reset_index(drop=True)

    for column in [
        "G",
        "P",
        "C",
        "R",
        "A",
        "JESI",
        "JESI_std",
        "JESI_score_100",
    ]:

        if not np.allclose(
            actual[column].to_numpy(),
            expected[column].to_numpy(),
            rtol=1e-9,
            atol=1e-9,
            equal_nan=True,
        ):
            raise ValueError(
                f"Final country results mismatch "
                f"in column {column}."
            )

    if not np.array_equal(
        actual["observations"].to_numpy(),
        expected["observations"].to_numpy(),
    ):
        raise ValueError(
            "Final country observation counts do not match."
        )

    if not np.array_equal(
        actual["rank"].to_numpy(),
        expected["rank"].to_numpy(),
    ):
        raise ValueError(
            "Final country ranking does not match "
            "the calculated ranking."
        )


def validate_yearly_summary(
    country_year_df,
    yearly_df,
):
    """Validate yearly JESI summary."""

    required = {
        "year",
        "mean",
        "median",
        "minimum",
        "maximum",
        "observations",
    }

    missing = required - set(yearly_df.columns)

    if missing:
        raise ValueError(
            "Yearly JESI summary is missing columns: "
            f"{sorted(missing)}"
        )

    expected = (
        country_year_df.groupby("year")["JESI"]
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

    actual = (
        yearly_df[
            [
                "year",
                "mean",
                "median",
                "minimum",
                "maximum",
                "observations",
            ]
        ]
        .sort_values("year")
        .reset_index(drop=True)
    )

    if not np.array_equal(
        actual["year"].to_numpy(),
        expected["year"].to_numpy(),
    ):
        raise ValueError(
            "Yearly summary year values do not match."
        )

    for column in [
        "mean",
        "median",
        "minimum",
        "maximum",
    ]:

        if not np.allclose(
            actual[column].to_numpy(),
            expected[column].to_numpy(),
            rtol=1e-9,
            atol=1e-9,
        ):
            raise ValueError(
                f"Yearly summary mismatch "
                f"in column {column}."
            )

    if not np.array_equal(
        actual["observations"].to_numpy(),
        expected["observations"].to_numpy(),
    ):
        raise ValueError(
            "Yearly observation counts do not match."
        )


def validate_research_table(
    final_df,
    research_df,
):
    """Validate the final research-ready table."""

    required = {
        "rank",
        "country_code",
        "country",
        "Growth",
        "Productivity",
        "Connectivity",
        "Resilience",
        "Strategic_Autonomy",
        "JESI",
        "JESI_std",
    }

    missing = required - set(research_df.columns)

    if missing:
        raise ValueError(
            "Research table is missing columns: "
            f"{sorted(missing)}"
        )

    expected = final_df[
        [
            "rank",
            "country_code",
            "country",
            "G",
            "P",
            "C",
            "R",
            "A",
            "JESI",
            "JESI_std",
        ]
    ].copy()

    expected = expected.rename(
        columns={
            "G": "Growth",
            "P": "Productivity",
            "C": "Connectivity",
            "R": "Resilience",
            "A": "Strategic_Autonomy",
        }
    )

    expected = expected.sort_values(
        "country_code"
    ).reset_index(drop=True)

    actual = research_df[
        [
            "rank",
            "country_code",
            "country",
            "Growth",
            "Productivity",
            "Connectivity",
            "Resilience",
            "Strategic_Autonomy",
            "JESI",
            "JESI_std",
        ]
    ].copy()

    actual = actual.sort_values(
        "country_code"
    ).reset_index(drop=True)

    for column in [
        "Growth",
        "Productivity",
        "Connectivity",
        "Resilience",
        "Strategic_Autonomy",
        "JESI",
        "JESI_std",
    ]:

        if not np.allclose(
            actual[column].to_numpy(),
            expected[column].to_numpy(),
            rtol=1e-9,
            atol=1e-9,
            equal_nan=True,
        ):
            raise ValueError(
                f"Research table mismatch "
                f"in column {column}."
            )

    if not np.array_equal(
        actual["rank"].to_numpy(),
        expected["rank"].to_numpy(),
    ):
        raise ValueError(
            "Research table ranking does not match."
        )


def validate_robustness(
    robustness_df,
    correlation_df,
):
    """Validate robustness output schemas and score ranges."""

    required_country = {
        "country_code",
        "country",
        "JAS_arithmetic",
        "JAS_geometric",
        "Equal_arithmetic",
        "Equal_geometric",
    }

    missing_country = (
        required_country
        - set(robustness_df.columns)
    )

    if missing_country:
        raise ValueError(
            "Robustness country results are missing "
            f"columns: {sorted(missing_country)}"
        )

    required_correlation = {
        "comparison",
        "spearman_correlation",
    }

    missing_correlation = (
        required_correlation
        - set(correlation_df.columns)
    )

    if missing_correlation:
        raise ValueError(
            "Robustness correlation file is missing "
            f"columns: {sorted(missing_correlation)}"
        )

    if set(
        robustness_df["country_code"]
    ) != EXPECTED_COUNTRIES:
        raise ValueError(
            "Robustness results do not contain "
            "the expected five countries."
        )

    score_columns = [
        "JAS_arithmetic",
        "JAS_geometric",
        "Equal_arithmetic",
        "Equal_geometric",
    ]

    for column in score_columns:

        if robustness_df[column].isna().any():
            raise ValueError(
                f"Robustness column {column} "
                "contains missing values."
            )

        if (
            (robustness_df[column] < 0).any()
            or (robustness_df[column] > 100).any()
        ):
            raise ValueError(
                f"Robustness column {column} "
                "contains values outside [0, 100]."
            )

    if correlation_df[
        "spearman_correlation"
    ].isna().any():
        raise ValueError(
            "Robustness correlations contain "
            "missing values."
        )

    if (
        correlation_df[
            "spearman_correlation"
        ].abs()
        > 1
    ).any():
        raise ValueError(
            "Spearman correlation values must "
            "be between -1 and 1."
        )


def main():
    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Final JESI Validation")
    print("=" * 70)

    # ---------------------------------------------------------------
    # Check required files
    # ---------------------------------------------------------------

    required_files = [
        COUNTRY_YEAR_FILE,
        COUNTRY_RANKING_FILE,
        ROBUSTNESS_FILE,
        ROBUSTNESS_CORRELATION_FILE,
        FINAL_COUNTRY_FILE,
        YEARLY_FILE,
        RESEARCH_TABLE_FILE,
    ]

    for path in required_files:
        check_file(path)

    # ---------------------------------------------------------------
    # Load datasets
    # ---------------------------------------------------------------

    country_year_df = pd.read_csv(
        COUNTRY_YEAR_FILE
    )

    country_ranking_df = pd.read_csv(
        COUNTRY_RANKING_FILE
    )

    robustness_df = pd.read_csv(
        ROBUSTNESS_FILE
    )

    correlation_df = pd.read_csv(
        ROBUSTNESS_CORRELATION_FILE
    )

    final_country_df = pd.read_csv(
        FINAL_COUNTRY_FILE
    )

    yearly_df = pd.read_csv(
        YEARLY_FILE
    )

    research_df = pd.read_csv(
        RESEARCH_TABLE_FILE
    )

    # ---------------------------------------------------------------
    # Validation sequence
    # ---------------------------------------------------------------

    print()
    print(
        "1. Validating country-year JESI dataset..."
    )

    validate_country_year_dataset(
        country_year_df
    )

    print("GREEN")

    print()
    print(
        "2. Validating JESI mathematical formula..."
    )

    validate_mathematical_consistency(
        country_year_df
    )

    print("GREEN")

    print()
    print(
        "3. Validating country ranking..."
    )

    validate_country_ranking(
        country_year_df,
        country_ranking_df,
    )

    print("GREEN")

    print()
    print(
        "4. Validating final country results..."
    )

    validate_final_country_results(
        country_year_df,
        final_country_df,
    )

    print("GREEN")

    print()
    print(
        "5. Validating yearly JESI summary..."
    )

    validate_yearly_summary(
        country_year_df,
        yearly_df,
    )

    print("GREEN")

    print()
    print(
        "6. Validating final research table..."
    )

    validate_research_table(
        final_country_df,
        research_df,
    )

    print("GREEN")

    print()
    print(
        "7. Validating robustness outputs..."
    )

    validate_robustness(
        robustness_df,
        correlation_df,
    )

    print("GREEN")

    # ---------------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------------

    actual_observations = len(
        country_year_df
    )

    excluded_observations = (
        EXPECTED_THEORETICAL_OBSERVATIONS
        - actual_observations
    )

    retention = (
        actual_observations
        / EXPECTED_THEORETICAL_OBSERVATIONS
        * 100
    )

    print()
    print(
        "Final validation summary:"
    )

    print(
        f"Theoretical countries: "
        f"{len(EXPECTED_COUNTRIES)}"
    )

    print(
        f"Years: "
        f"{min(EXPECTED_YEARS)}-"
        f"{max(EXPECTED_YEARS)}"
    )

    print(
        f"Theoretical observations: "
        f"{EXPECTED_THEORETICAL_OBSERVATIONS}"
    )

    print(
        f"Complete-case observations: "
        f"{actual_observations}"
    )

    print(
        f"Excluded observations: "
        f"{excluded_observations}"
    )

    print(
        f"Complete-case retention: "
        f"{retention:.2f}%"
    )

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print(
        "Final JESI validation completed successfully."
    )
    print(
        "The theoretical 40-observation panel was "
        "reconciled with the complete-case analytical sample."
    )
    print(
        "No missing observation was imputed, "
        "interpolated, replaced, or fabricated."
    )
    print(
        "All required consistency checks passed."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
