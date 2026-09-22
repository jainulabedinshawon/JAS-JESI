"""
JAS Unified Economic Strength Index (JESI)
Final Results Validation

Validates the final JESI pipeline outputs for:

1. Required files and schemas
2. Country-year completeness
3. Duplicate country-year observations
4. Pillar score ranges
5. JESI score range
6. Mathematical consistency
7. Country-level aggregation consistency
8. Ranking integrity
9. Year-level summary consistency
10. Robustness output consistency

This script is non-destructive.
It does not modify any existing data or documentation files.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

RESULTS_DIR = Path("data/results")

COUNTRIES = [
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
]

START_YEAR = 2016
END_YEAR = 2023

EXPECTED_YEARS = END_YEAR - START_YEAR + 1
EXPECTED_COUNTRY_COUNT = len(COUNTRIES)
EXPECTED_COUNTRY_YEAR_COUNT = (
    EXPECTED_COUNTRY_COUNT * EXPECTED_YEARS
)

PILLARS = ["G", "P", "C", "R", "A"]

WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}


# ============================================================
# REQUIRED FILES
# ============================================================

COUNTRY_YEAR_FILE = (
    RESULTS_DIR / "jesi_country_year_2016_2023.csv"
)

COUNTRY_RESULTS_FILE = (
    RESULTS_DIR / "final_jesi_country_results.csv"
)

YEARLY_FILE = (
    RESULTS_DIR / "final_jesi_yearly_summary.csv"
)

RESEARCH_TABLE_FILE = (
    RESULTS_DIR / "JESI_final_research_table.csv"
)

ROBUSTNESS_FILE = (
    RESULTS_DIR / "jesi_robustness_country_results.csv"
)

CORRELATION_FILE = (
    RESULTS_DIR / "jesi_robustness_correlations.csv"
)


# ============================================================
# VALIDATION HELPERS
# ============================================================

errors = []
warnings = []


def fail(message):
    errors.append(message)
    print(f"FAIL  {message}")


def warn(message):
    warnings.append(message)
    print(f"WARN  {message}")


def pass_check(message):
    print(f"PASS  {message}")


def require_columns(df, required, filename):
    missing = set(required) - set(df.columns)

    if missing:
        fail(
            f"{filename} missing columns: "
            f"{sorted(missing)}"
        )
        return False

    return True


def check_range(df, columns, minimum, maximum, filename):
    for column in columns:

        if column not in df.columns:
            continue

        invalid = (
            (df[column] < minimum)
            | (df[column] > maximum)
        ).sum()

        if invalid:
            fail(
                f"{filename}: {invalid} values in "
                f"{column} outside [{minimum}, {maximum}]."
            )
        else:
            pass_check(
                f"{filename}: {column} within "
                f"[{minimum}, {maximum}]."
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("JESI FINAL RESULTS VALIDATION")
    print("JAS Unified Economic Strength Index")
    print("=" * 72)

    print()
    print(f"Validation period: {START_YEAR}-{END_YEAR}")
    print(
        f"Countries: {', '.join(COUNTRIES)}"
    )

    # --------------------------------------------------------
    # 1. FILE EXISTENCE
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("1. REQUIRED OUTPUT FILES")
    print("=" * 72)

    required_files = [
        COUNTRY_YEAR_FILE,
        COUNTRY_RESULTS_FILE,
        YEARLY_FILE,
        RESEARCH_TABLE_FILE,
        ROBUSTNESS_FILE,
        CORRELATION_FILE,
    ]

    for file in required_files:

        if file.exists():
            pass_check(str(file))
        else:
            fail(f"Missing required file: {file}")

    if errors:
        raise SystemExit(1)

    # --------------------------------------------------------
    # LOAD FILES
    # --------------------------------------------------------

    country_year = pd.read_csv(
        COUNTRY_YEAR_FILE
    )

    country_results = pd.read_csv(
        COUNTRY_RESULTS_FILE
    )

    yearly = pd.read_csv(
        YEARLY_FILE
    )

    research = pd.read_csv(
        RESEARCH_TABLE_FILE
    )

    robustness = pd.read_csv(
        ROBUSTNESS_FILE
    )

    correlations = pd.read_csv(
        CORRELATION_FILE
    )

    # --------------------------------------------------------
    # 2. COUNTRY-YEAR SCHEMA
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("2. COUNTRY-YEAR DATASET")
    print("=" * 72)

    country_year_required = {
        "country_code",
        "country",
        "year",
        *PILLARS,
        "JESI",
    }

    if require_columns(
        country_year,
        country_year_required,
        COUNTRY_YEAR_FILE.name,
    ):
        pass_check(
            "Country-year schema is complete."
        )

    # --------------------------------------------------------
    # 3. COUNTRY-YEAR COMPLETENESS
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("3. COUNTRY-YEAR COMPLETENESS")
    print("=" * 72)

    actual_rows = len(country_year)

    print(
        f"Expected observations: "
        f"{EXPECTED_COUNTRY_YEAR_COUNT}"
    )

    print(
        f"Actual observations: "
        f"{actual_rows}"
    )

    if actual_rows != EXPECTED_COUNTRY_YEAR_COUNT:
        fail(
            "Country-year observation count does not "
            "match expected balanced sample."
        )
    else:
        pass_check(
            "Country-year observation count is correct."
        )

    # --------------------------------------------------------
    # 4. YEAR RANGE
    # --------------------------------------------------------

    if "year" in country_year.columns:

        min_year = country_year["year"].min()
        max_year = country_year["year"].max()

        if (
            min_year != START_YEAR
            or max_year != END_YEAR
        ):
            fail(
                f"Unexpected year range: "
                f"{min_year}-{max_year}."
            )
        else:
            pass_check(
                f"Year range is {START_YEAR}-{END_YEAR}."
            )

    # --------------------------------------------------------
    # 5. COUNTRY COVERAGE
    # --------------------------------------------------------

    if "country" in country_year.columns:

        actual_countries = sorted(
            country_year["country"]
            .dropna()
            .unique()
            .tolist()
        )

        expected_countries = sorted(
            COUNTRIES
        )

        if actual_countries != expected_countries:
            fail(
                "Country coverage mismatch. "
                f"Expected {expected_countries}, "
                f"found {actual_countries}."
            )
        else:
            pass_check(
                "Country coverage is correct."
            )

    # --------------------------------------------------------
    # 6. DUPLICATE COUNTRY-YEAR CHECK
    # --------------------------------------------------------

    duplicates = country_year.duplicated(
        subset=[
            "country_code",
            "country",
            "year",
        ]
    ).sum()

    if duplicates:
        fail(
            f"Found {duplicates} duplicate "
            "country-year observations."
        )
    else:
        pass_check(
            "No duplicate country-year observations."
        )

    # --------------------------------------------------------
    # 7. MISSING VALUES
    # --------------------------------------------------------

    required_numeric = [
        *PILLARS,
        "JESI",
    ]

    missing_values = country_year[
        required_numeric
    ].isna().sum()

    if missing_values.sum() > 0:
        fail(
            "Missing values detected in final "
            "pillar/JESI scores: "
            f"{missing_values.to_dict()}"
        )
    else:
        pass_check(
            "No missing pillar or JESI values."
        )

    # --------------------------------------------------------
    # 8. PILLAR RANGE
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("4. SCORE RANGE VALIDATION")
    print("=" * 72)

    check_range(
        country_year,
        PILLARS,
        0.0,
        1.0,
        COUNTRY_YEAR_FILE.name,
    )

    check_range(
        country_year,
        ["JESI"],
        0.0,
        100.0,
        COUNTRY_YEAR_FILE.name,
    )

    # --------------------------------------------------------
    # 9. MATHEMATICAL CONSISTENCY
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("5. MATHEMATICAL CONSISTENCY")
    print("=" * 72)

    expected_jesi = (
        100
        * (
            country_year["G"] ** WEIGHTS["G"]
        )
        * (
            country_year["P"] ** WEIGHTS["P"]
        )
        * (
            country_year["C"] ** WEIGHTS["C"]
        )
        * (
            country_year["R"] ** WEIGHTS["R"]
        )
        * (
            country_year["A"] ** WEIGHTS["A"]
        )
    )

    difference = (
        country_year["JESI"]
        - expected_jesi
    ).abs()

    max_difference = difference.max()

    print(
        f"Maximum JESI calculation difference: "
        f"{max_difference:.12f}"
    )

    if max_difference > 1e-8:
        fail(
            "JESI values do not match the "
            "baseline weighted geometric formula."
        )
    else:
        pass_check(
            "JESI values match the baseline "
            "weighted geometric formula."
        )

    # --------------------------------------------------------
    # 10. COUNTRY-LEVEL FINAL RESULTS
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("6. COUNTRY-LEVEL FINAL RESULTS")
    print("=" * 72)

    country_required = {
        "country_code",
        "country",
        "G",
        "P",
        "C",
        "R",
        "A",
        "JESI",
        "JESI_std",
        "rank",
        "JESI_score_100",
    }

    if require_columns(
        country_results,
        country_required,
        COUNTRY_RESULTS_FILE.name,
    ):
        pass_check(
            "Country-level result schema is complete."
        )

    if len(country_results) != EXPECTED_COUNTRY_COUNT:
        fail(
            "Unexpected number of country-level "
            "results."
        )
    else:
        pass_check(
            "Country-level result count is correct."
        )

    # --------------------------------------------------------
    # 11. COUNTRY AGGREGATION CONSISTENCY
    # --------------------------------------------------------

    expected_country = (
        country_year.groupby(
            ["country_code", "country"]
        )
        .agg(
            G=("G", "mean"),
            P=("P", "mean"),
            C=("C", "mean"),
            R=("R", "mean"),
            A=("A", "mean"),
            JESI=("JESI", "mean"),
            JESI_std=("JESI", "std"),
        )
        .reset_index()
    )

    comparison = country_results.merge(
        expected_country,
        on=[
            "country_code",
            "country",
        ],
        suffixes=(
            "_reported",
            "_expected",
        ),
    )

    for column in [
        "G",
        "P",
        "C",
        "R",
        "A",
        "JESI",
        "JESI_std",
    ]:

        reported = (
            f"{column}_reported"
        )

        expected = (
            f"{column}_expected"
        )

        if (
            reported not in comparison.columns
            or expected not in comparison.columns
        ):
            continue

        max_diff = (
            comparison[reported]
            - comparison[expected]
        ).abs().max()

        if pd.isna(max_diff):
            continue

        if max_diff > 1e-8:
            fail(
                f"Country aggregation mismatch "
                f"for {column}: {max_diff:.12f}"
            )
        else:
            pass_check(
                f"Country aggregation consistent "
                f"for {column}."
            )

    # --------------------------------------------------------
    # 12. RANKING INTEGRITY
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("7. RANKING INTEGRITY")
    print("=" * 72)

    expected_rank = (
        country_results["JESI"]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    if not (
        expected_rank.values
        == country_results["rank"].values
    ).all():

        fail(
            "Country ranking does not match "
            "reported JESI ranking."
        )

    else:

        pass_check(
            "Country ranking is mathematically consistent."
        )

    # --------------------------------------------------------
    # 13. RANK RANGE
    # --------------------------------------------------------

    valid_rank_values = set(
        range(
            1,
            EXPECTED_COUNTRY_COUNT + 1,
        )
    )

    actual_rank_values = set(
        country_results["rank"]
    )

    if not actual_rank_values.issubset(
        valid_rank_values
    ):
        fail(
            "Invalid ranking values detected."
        )
    else:
        pass_check(
            "Ranking values are within valid range."
        )

    # --------------------------------------------------------
    # 14. RESEARCH TABLE
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("8. RESEARCH TABLE")
    print("=" * 72)

    research_required = {
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

    if require_columns(
        research,
        research_required,
        RESEARCH_TABLE_FILE.name,
    ):
        pass_check(
            "Research table schema is complete."
        )

    if len(research) != EXPECTED_COUNTRY_COUNT:
        fail(
            "Research table country count is incorrect."
        )
    else:
        pass_check(
            "Research table country count is correct."
        )

    # --------------------------------------------------------
    # 15. YEARLY SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("9. YEARLY SUMMARY")
    print("=" * 72)

    yearly_required = {
        "year",
        "mean",
        "median",
        "minimum",
        "maximum",
        "observations",
    }

    if require_columns(
        yearly,
        yearly_required,
        YEARLY_FILE.name,
    ):
        pass_check(
            "Yearly summary schema is complete."
        )

    if len(yearly) != EXPECTED_YEARS:
        fail(
            "Yearly summary does not contain "
            "the expected number of years."
        )
    else:
        pass_check(
            "Yearly summary contains all expected years."
        )

    if "observations" in yearly.columns:

        if not (
            yearly["observations"]
            == EXPECTED_COUNTRY_COUNT
        ).all():

            fail(
                "Yearly summary contains unexpected "
                "observation counts."
            )

        else:

            pass_check(
                "Each year contains all countries."
            )

    # --------------------------------------------------------
    # 16. YEARLY SUMMARY CONSISTENCY
    # --------------------------------------------------------

    expected_yearly = (
        country_year.groupby("year")["JESI"]
        .agg(
            mean="mean",
            median="median",
            minimum="min",
            maximum="max",
            observations="count",
        )
        .reset_index()
    )

    yearly_compare = yearly.merge(
        expected_yearly,
        on="year",
        suffixes=(
            "_reported",
            "_expected",
        ),
    )

    for column in [
        "mean",
        "median",
        "minimum",
        "maximum",
        "observations",
    ]:

        reported = (
            f"{column}_reported"
        )

        expected = (
            f"{column}_expected"
        )

        if (
            reported not in yearly_compare.columns
            or expected not in yearly_compare.columns
        ):
            continue

        max_diff = (
            yearly_compare[reported]
            - yearly_compare[expected]
        ).abs().max()

        if max_diff > 1e-8:
            fail(
                f"Yearly summary mismatch "
                f"for {column}."
            )
        else:
            pass_check(
                f"Yearly summary consistent "
                f"for {column}."
            )

    # --------------------------------------------------------
    # 17. ROBUSTNESS OUTPUT
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("10. ROBUSTNESS OUTPUT")
    print("=" * 72)

    robustness_required = {
        "country_code",
        "country",
        "JAS_arithmetic",
        "JAS_geometric",
        "Equal_arithmetic",
        "Equal_geometric",
        "JAS_arithmetic_rank",
        "JAS_geometric_rank",
        "Equal_arithmetic_rank",
        "Equal_geometric_rank",
        "rank_diff_JAS_vs_Equal",
        "rank_diff_Arithmetic_vs_Geometric",
    }

    if require_columns(
        robustness,
        robustness_required,
        ROBUSTNESS_FILE.name,
    ):
        pass_check(
            "Robustness result schema is complete."
        )

    if len(robustness) != EXPECTED_COUNTRY_COUNT:
        fail(
            "Robustness result country count is incorrect."
        )
    else:
        pass_check(
            "Robustness result country count is correct."
        )

    # --------------------------------------------------------
    # 18. ROBUSTNESS SCORE RANGE
    # --------------------------------------------------------

    robustness_scores = [
        "JAS_arithmetic",
        "JAS_geometric",
        "Equal_arithmetic",
        "Equal_geometric",
    ]

    check_range(
        robustness,
        robustness_scores,
        0.0,
        100.0,
        ROBUSTNESS_FILE.name,
    )

    # --------------------------------------------------------
    # 19. CORRELATION OUTPUT
    # --------------------------------------------------------

    correlation_required = {
        "comparison",
        "spearman_correlation",
    }

    if require_columns(
        correlations,
        correlation_required,
        CORRELATION_FILE.name,
    ):
        pass_check(
            "Robustness correlation schema is complete."
        )

    # --------------------------------------------------------
    # 20. FINAL SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 72)

    print(
        f"Errors: {len(errors)}"
    )

    print(
        f"Warnings: {len(warnings)}"
    )

    if warnings:
        print()
        print("Warnings:")

        for warning in warnings:
            print(
                f"  - {warning}"
            )

    if errors:

        print()
        print("Validation failures:")

        for error in errors:
            print(
                f"  - {error}"
            )

        print()
        print("STATUS: FAIL")

        raise SystemExit(1)

    print()
    print("STATUS: GREEN")
    print(
        "Final JESI outputs passed structural, "
        "range, mathematical, aggregation, "
        "ranking, yearly-summary, and robustness checks."
    )


if __name__ == "__main__":
    main()
