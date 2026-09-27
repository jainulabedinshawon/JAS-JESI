"""
JESI Strategic Autonomy Coverage Impact Analysis
Master Version 1.0

Script 43:
Analyzes the coverage and missing-data impact of the
Strategic Autonomy high-tech export indicator before
any scoring, pillar construction, or missing-data policy
changes are made.

Purpose:
    - Quantify overall indicator coverage.
    - Quantify country-level coverage.
    - Quantify year-level coverage.
    - Identify exact missing country-years.
    - Measure the impact on the final JESI sample
      (2016-2023).
    - Measure complete-case retention.
    - Identify the balanced-panel country sample.
    - Measure consecutive missing-data gaps.
    - Produce reproducible CSV outputs.

Important methodological rule:
    This script does NOT impute, interpolate, replace,
    or otherwise modify missing observations.

    Missing observations remain missing.

Strategic Autonomy indicators:
    - Economic Complexity Index (ECI)
    - High-Tech Exports
    - Import Product Concentration

Current source dataset:
    data/raw/autonomy_indicators_2015_2024.csv

Expected benchmark:
    5 countries
    2015-2024
    50 country-year observations
"""

from pathlib import Path

import numpy as np
import pandas as pd


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

INPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024.csv"
)

OUTPUT_DIR = Path(
    "data/processed"
)

COVERAGE_FILE = OUTPUT_DIR / (
    "strategic_autonomy_coverage_summary_2015_2024.csv"
)

COUNTRY_FILE = OUTPUT_DIR / (
    "strategic_autonomy_country_coverage_2015_2024.csv"
)

YEAR_FILE = OUTPUT_DIR / (
    "strategic_autonomy_year_coverage_2015_2024.csv"
)

MISSING_FILE = OUTPUT_DIR / (
    "strategic_autonomy_missing_observations_2015_2024.csv"
)

JESI_SAMPLE_FILE = OUTPUT_DIR / (
    "strategic_autonomy_jesi_sample_impact_2016_2023.csv"
)

BALANCED_FILE = OUTPUT_DIR / (
    "strategic_autonomy_balanced_panel_2016_2023.csv"
)

GAP_FILE = OUTPUT_DIR / (
    "strategic_autonomy_missing_gap_analysis_2015_2024.csv"
)


COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Viet Nam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}

EXPECTED_YEARS = set(
    range(2015, 2025)
)

FINAL_JESI_YEARS = set(
    range(2016, 2024)
)

EXPECTED_COUNTRY_COUNT = len(
    COUNTRIES
)

EXPECTED_BENCHMARK_ROWS = (
    EXPECTED_COUNTRY_COUNT
    * len(EXPECTED_YEARS)
)

EXPECTED_FINAL_JESI_ROWS = (
    EXPECTED_COUNTRY_COUNT
    * len(FINAL_JESI_YEARS)
)

INDICATORS = [
    "eci",
    "high_tech_exports",
    "import_product_concentration",
]

REQUIRED_COLUMNS = [
    "country_code",
    "country",
    "year",
    "eci",
    "high_tech_exports",
    "import_product_concentration",
]


# -------------------------------------------------------------------
# Input validation
# -------------------------------------------------------------------

def load_and_validate_input():
    """Load the autonomy dataset and validate its structure."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Input dataset is missing required columns: "
            f"{missing_columns}"
        )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    if df["year"].isna().any():
        raise ValueError(
            "Year column contains missing or non-numeric values."
        )

    df["year"] = df["year"].astype(int)

    for indicator in INDICATORS:
        df[indicator] = pd.to_numeric(
            df[indicator],
            errors="coerce",
        )

    if len(df) != EXPECTED_BENCHMARK_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_BENCHMARK_ROWS} rows, "
            f"found {len(df)}."
        )

    if set(df["country_code"]) != set(COUNTRIES):
        raise ValueError(
            "Country-code coverage does not match the JESI sample."
        )

    if set(df["year"]) != EXPECTED_YEARS:
        raise ValueError(
            "Year coverage is not exactly 2015-2024."
        )

    if df.duplicated(
        ["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations detected."
        )

    return df


# -------------------------------------------------------------------
# Overall indicator coverage
# -------------------------------------------------------------------

def calculate_indicator_coverage(df):
    """Calculate overall coverage for every autonomy indicator."""

    records = []

    total_rows = len(df)

    for indicator in INDICATORS:
        available = int(
            df[indicator].notna().sum()
        )

        missing = int(
            df[indicator].isna().sum()
        )

        coverage = (
            available / total_rows
            if total_rows
            else np.nan
        )

        records.append(
            {
                "indicator": indicator,
                "expected_observations": total_rows,
                "available_observations": available,
                "missing_observations": missing,
                "coverage_percent": (
                    coverage * 100
                ),
                "missing_percent": (
                    (1 - coverage) * 100
                ),
            }
        )

    return pd.DataFrame(
        records
    )


# -------------------------------------------------------------------
# Country-level coverage
# -------------------------------------------------------------------

def calculate_country_coverage(df):
    """Calculate indicator coverage by country."""

    records = []

    for country_code, country_name in COUNTRIES.items():

        country_df = df[
            df["country_code"]
            == country_code
        ].copy()

        expected = len(
            EXPECTED_YEARS
        )

        record = {
            "country_code": country_code,
            "country": country_name,
            "expected_observations": expected,
        }

        for indicator in INDICATORS:
            available = int(
                country_df[indicator].notna().sum()
            )

            missing = int(
                country_df[indicator].isna().sum()
            )

            coverage = (
                available / expected
                if expected
                else np.nan
            )

            record[
                f"{indicator}_available"
            ] = available

            record[
                f"{indicator}_missing"
            ] = missing

            record[
                f"{indicator}_coverage_percent"
            ] = coverage * 100

        records.append(
            record
        )

    return pd.DataFrame(
        records
    )


# -------------------------------------------------------------------
# Year-level coverage
# -------------------------------------------------------------------

def calculate_year_coverage(df):
    """Calculate indicator coverage by year."""

    records = []

    for year in sorted(
        EXPECTED_YEARS
    ):

        year_df = df[
            df["year"] == year
        ].copy()

        expected = EXPECTED_COUNTRY_COUNT

        record = {
            "year": year,
            "expected_observations": expected,
        }

        for indicator in INDICATORS:
            available = int(
                year_df[indicator].notna().sum()
            )

            missing = int(
                year_df[indicator].isna().sum()
            )

            coverage = (
                available / expected
                if expected
                else np.nan
            )

            record[
                f"{indicator}_available"
            ] = available

            record[
                f"{indicator}_missing"
            ] = missing

            record[
                f"{indicator}_coverage_percent"
            ] = coverage * 100

        records.append(
            record
        )

    return pd.DataFrame(
        records
    )


# -------------------------------------------------------------------
# Exact missing observations
# -------------------------------------------------------------------

def identify_missing_observations(df):
    """Identify every missing country-year-indicator observation."""

    records = []

    for _, row in df.iterrows():

        for indicator in INDICATORS:

            if pd.isna(
                row[indicator]
            ):
                records.append(
                    {
                        "country_code": row[
                            "country_code"
                        ],
                        "country": row[
                            "country"
                        ],
                        "year": int(
                            row["year"]
                        ),
                        "indicator": indicator,
                    }
                )

    return pd.DataFrame(
        records,
        columns=[
            "country_code",
            "country",
            "year",
            "indicator",
        ],
    )


# -------------------------------------------------------------------
# Final JESI sample impact
# -------------------------------------------------------------------

def calculate_final_jesi_impact(df):
    """
    Measure the effect of missing autonomy observations on
    the current final JESI calculation period: 2016-2023.
    """

    final_df = df[
        df["year"].isin(
            FINAL_JESI_YEARS
        )
    ].copy()

    if len(final_df) != EXPECTED_FINAL_JESI_ROWS:
        raise ValueError(
            "Unexpected number of rows in the "
            "2016-2023 JESI sample."
        )

    # A country-year is complete only when all three
    # Strategic Autonomy indicators are available.
    final_df[
        "strategic_autonomy_complete"
    ] = ~final_df[
        INDICATORS
    ].isna().any(axis=1)

    expected = len(
        final_df
    )

    complete = int(
        final_df[
            "strategic_autonomy_complete"
        ].sum()
    )

    excluded = expected - complete

    retention = (
        complete / expected
        if expected
        else np.nan
    )

    summary = pd.DataFrame(
        [
            {
                "sample": "JESI final sample",
                "period": "2016-2023",
                "expected_country_years": expected,
                "complete_country_years": complete,
                "excluded_country_years": excluded,
                "retention_percent": (
                    retention * 100
                ),
            }
        ]
    )

    country_records = []

    for country_code, country_name in COUNTRIES.items():

        country_df = final_df[
            final_df["country_code"]
            == country_code
        ].copy()

        country_expected = len(
            FINAL_JESI_YEARS
        )

        country_complete = int(
            country_df[
                "strategic_autonomy_complete"
            ].sum()
        )

        country_excluded = (
            country_expected
            - country_complete
        )

        country_retention = (
            country_complete
            / country_expected
            if country_expected
            else np.nan
        )

        country_records.append(
            {
                "country_code": country_code,
                "country": country_name,
                "period": "2016-2023",
                "expected_country_years": (
                    country_expected
                ),
                "complete_country_years": (
                    country_complete
                ),
                "excluded_country_years": (
                    country_excluded
                ),
                "retention_percent": (
                    country_retention * 100
                ),
            }
        )

    country_impact = pd.DataFrame(
        country_records
    )

    return (
        summary,
        country_impact,
        final_df,
    )


# -------------------------------------------------------------------
# Balanced-panel analysis
# -------------------------------------------------------------------

def calculate_balanced_panel(
    final_df,
):
    """
    Identify countries with complete Strategic Autonomy
    indicator coverage for every year from 2016-2023.
    """

    records = []

    for country_code, country_name in COUNTRIES.items():

        country_df = final_df[
            final_df["country_code"]
            == country_code
        ].copy()

        complete = bool(
            country_df[
                "strategic_autonomy_complete"
            ].all()
        )

        complete_years = int(
            country_df[
                "strategic_autonomy_complete"
            ].sum()
        )

        records.append(
            {
                "country_code": country_code,
                "country": country_name,
                "period": "2016-2023",
                "required_years": len(
                    FINAL_JESI_YEARS
                ),
                "complete_years": complete_years,
                "balanced_panel_eligible": complete,
            }
        )

    panel = pd.DataFrame(
        records
    )

    eligible = panel[
        panel["balanced_panel_eligible"]
    ].copy()

    eligible_country_count = len(
        eligible
    )

    balanced_observations = (
        eligible_country_count
        * len(FINAL_JESI_YEARS)
    )

    summary_row = pd.DataFrame(
        [
            {
                "period": "2016-2023",
                "total_countries": (
                    EXPECTED_COUNTRY_COUNT
                ),
                "balanced_panel_countries": (
                    eligible_country_count
                ),
                "balanced_panel_observations": (
                    balanced_observations
                ),
                "full_sample_observations": (
                    EXPECTED_FINAL_JESI_ROWS
                ),
                "observation_retention_percent": (
                    balanced_observations
                    / EXPECTED_FINAL_JESI_ROWS
                    * 100
                ),
            }
        ]
    )

    return (
        panel,
        summary_row,
    )


# -------------------------------------------------------------------
# Consecutive missing-gap analysis
# -------------------------------------------------------------------

def calculate_missing_gaps(df):
    """
    Calculate missing years and the longest consecutive
    missing-data gap for each country-indicator pair.
    """

    records = []

    for country_code, country_name in COUNTRIES.items():

        country_df = df[
            df["country_code"]
            == country_code
        ].sort_values(
            "year"
        ).copy()

        for indicator in INDICATORS:

            missing_years = sorted(
                country_df.loc[
                    country_df[indicator].isna(),
                    "year",
                ].astype(int).tolist()
            )

            if not missing_years:
                longest_gap = 0
            else:
                longest_gap = 1
                current_gap = 1

                for index in range(
                    1,
                    len(missing_years),
                ):
                    if (
                        missing_years[index]
                        == missing_years[index - 1]
                        + 1
                    ):
                        current_gap += 1
                    else:
                        current_gap = 1

                    longest_gap = max(
                        longest_gap,
                        current_gap,
                    )

            missing_year_text = (
                ", ".join(
                    str(year)
                    for year in missing_years
                )
                if missing_years
                else ""
            )

            records.append(
                {
                    "country_code": country_code,
                    "country": country_name,
                    "indicator": indicator,
                    "missing_observations": len(
                        missing_years
                    ),
                    "missing_years": (
                        missing_year_text
                    ),
                    "longest_consecutive_missing_gap": (
                        longest_gap
                    ),
                }
            )

    return pd.DataFrame(
        records
    )


# -------------------------------------------------------------------
# Complete-case country-year summary
# -------------------------------------------------------------------

def calculate_complete_case_summary(
    df,
):
    """
    Identify country-years where all three Strategic
    Autonomy indicators are simultaneously available.
    """

    working = df.copy()

    working[
        "strategic_autonomy_complete"
    ] = ~working[
        INDICATORS
    ].isna().any(axis=1)

    country_records = []

    for country_code, country_name in COUNTRIES.items():

        country_df = working[
            working["country_code"]
            == country_code
        ].copy()

        expected = len(
            EXPECTED_YEARS
        )

        complete = int(
            country_df[
                "strategic_autonomy_complete"
            ].sum()
        )

        excluded = (
            expected
            - complete
        )

        country_records.append(
            {
                "country_code": country_code,
                "country": country_name,
                "period": "2015-2024",
                "expected_country_years": expected,
                "complete_country_years": complete,
                "excluded_country_years": excluded,
                "retention_percent": (
                    complete
                    / expected
                    * 100
                ),
            }
        )

    return pd.DataFrame(
        country_records
    )


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    """Run Strategic Autonomy coverage-impact analysis."""

    print("=" * 72)
    print(
        "JESI STRATEGIC AUTONOMY "
        "COVERAGE IMPACT ANALYSIS"
    )
    print("=" * 72)

    print()
    print(
        "Input:",
        INPUT_FILE,
    )

    print(
        "Benchmark period: 2015-2024"
    )

    print(
        "Final JESI sample period: 2016-2023"
    )

    print()

    # ---------------------------------------------------------------
    # Load
    # ---------------------------------------------------------------

    df = load_and_validate_input()

    print(
        "Input validation: GREEN"
    )

    print(
        f"Rows: {len(df)}"
    )

    print(
        f"Countries: {df['country_code'].nunique()}"
    )

    print(
        f"Years: {df['year'].nunique()}"
    )

    # ---------------------------------------------------------------
    # Overall indicator coverage
    # ---------------------------------------------------------------

    coverage = calculate_indicator_coverage(
        df
    )

    print()
    print(
        "Overall indicator coverage:"
    )
    print(
        coverage.to_string(
            index=False
        )
    )

    # ---------------------------------------------------------------
    # Country coverage
    # ---------------------------------------------------------------

    country_coverage = calculate_country_coverage(
        df
    )

    print()
    print(
        "Country-level coverage:"
    )
    print(
        country_coverage.to_string(
            index=False
        )
    )

    # ---------------------------------------------------------------
    # Year coverage
    # ---------------------------------------------------------------

    year_coverage = calculate_year_coverage(
        df
    )

    print()
    print(
        "Year-level coverage:"
    )
    print(
        year_coverage.to_string(
            index=False
        )
    )

    # ---------------------------------------------------------------
    # Missing observations
    # ---------------------------------------------------------------

    missing = identify_missing_observations(
        df
    )

    print()
    print(
        "Exact missing observations:"
    )

    if missing.empty:
        print(
            "None"
        )
    else:
        print(
            missing.to_string(
                index=False
            )
        )

    # ---------------------------------------------------------------
    # Complete-case summary
    # ---------------------------------------------------------------

    complete_case = calculate_complete_case_summary(
        df
    )

    print()
    print(
        "Complete-case coverage by country:"
    )
    print(
        complete_case.to_string(
            index=False
        )
    )

    # ---------------------------------------------------------------
    # Final JESI sample impact
    # ---------------------------------------------------------------

    (
        final_summary,
        final_country_impact,
        final_df,
    ) = calculate_final_jesi_impact(
        df
    )

    print()
    print(
        "Final JESI sample impact:"
    )
    print(
        final_summary.to_string(
            index=False
        )
    )

    print()
    print(
        "Final JESI country-level impact:"
    )
    print(
        final_country_impact.to_string(
            index=False
        )
    )

    # ---------------------------------------------------------------
    # Balanced panel
    # ---------------------------------------------------------------

    (
        balanced_panel,
        balanced_summary,
    ) = calculate_balanced_panel(
        final_df
    )

    print()
    print(
        "Balanced-panel eligibility:"
    )
    print(
        balanced_panel.to_string(
            index=False
        )
    )

    print()
    print(
        "Balanced-panel summary:"
    )
    print(
        balanced_summary.to_string(
            index=False
        )
    )

    # ---------------------------------------------------------------
    # Missing-gap analysis
    # ---------------------------------------------------------------

    gap_analysis = calculate_missing_gaps(
        df
    )

    print()
    print(
        "Missing-gap analysis:"
    )
    print(
        gap_analysis.to_string(
            index=False
        )
    )

    # ---------------------------------------------------------------
    # Overall final impact metrics
    # ---------------------------------------------------------------

    complete_country_years = int(
        final_df[
            "strategic_autonomy_complete"
        ].sum()
    )

    excluded_country_years = (
        EXPECTED_FINAL_JESI_ROWS
        - complete_country_years
    )

    final_retention = (
        complete_country_years
        / EXPECTED_FINAL_JESI_ROWS
        * 100
    )

    print()
    print(
        "Final JESI coverage metrics:"
    )

    print(
        f"Expected 2016-2023 observations: "
        f"{EXPECTED_FINAL_JESI_ROWS}"
    )

    print(
        f"Complete observations: "
        f"{complete_country_years}"
    )

    print(
        f"Excluded observations: "
        f"{excluded_country_years}"
    )

    print(
        f"Complete-case retention: "
        f"{final_retention:.2f}%"
    )

    # ---------------------------------------------------------------
    # Save outputs
    # ---------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    coverage.to_csv(
        COVERAGE_FILE,
        index=False,
    )

    country_coverage.to_csv(
        COUNTRY_FILE,
        index=False,
    )

    year_coverage.to_csv(
        YEAR_FILE,
        index=False,
    )

    missing.to_csv(
        MISSING_FILE,
        index=False,
    )

    final_impact_output = pd.concat(
        [
            final_summary.assign(
                level="overall"
            ),
            final_country_impact.assign(
                level="country"
            ),
        ],
        ignore_index=True,
        sort=False,
    )

    final_impact_output.to_csv(
        JESI_SAMPLE_FILE,
        index=False,
    )

    balanced_output = pd.concat(
        [
            balanced_summary.assign(
                level="summary"
            ),
            balanced_panel.assign(
                level="country"
            ),
        ],
        ignore_index=True,
        sort=False,
    )

    balanced_output.to_csv(
        BALANCED_FILE,
        index=False,
    )

    gap_analysis.to_csv(
        GAP_FILE,
        index=False,
    )

    # ---------------------------------------------------------------
    # Final status
    # ---------------------------------------------------------------

    print()
    print(
        "Output files:"
    )

    print(
        f"- {COVERAGE_FILE}"
    )

    print(
        f"- {COUNTRY_FILE}"
    )

    print(
        f"- {YEAR_FILE}"
    )

    print(
        f"- {MISSING_FILE}"
    )

    print(
        f"- {JESI_SAMPLE_FILE}"
    )

    print(
        f"- {BALANCED_FILE}"
    )

    print(
        f"- {GAP_FILE}"
    )

    print()
    print("=" * 72)
    print(
        "STATUS: GREEN"
    )
    print(
        "Strategic Autonomy coverage-impact analysis "
        "completed without imputation."
    )
    print(
        "No missing observation was modified, replaced, "
        "or fabricated."
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
