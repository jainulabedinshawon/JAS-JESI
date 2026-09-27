"""
JESI Strategic Autonomy Coverage Impact Analysis
Master Version 1.0

Script 43:
Analyzes Strategic Autonomy indicator coverage and
missing-data impact before scoring or pillar construction.

Important methodological rule:
    No silent imputation.

This script does NOT:
    - impute
    - interpolate
    - replace
    - fabricate
    - proxy missing observations

Sources:
    1. Strategic Autonomy base dataset from Script 29
    2. Official UNCTAD import concentration dataset
       from Script 31

Strategic Autonomy indicators:
    - Economic Complexity Index (ECI)
    - High-Tech Exports
    - Import Product Concentration

Benchmark:
    5 countries
    2015-2024
    50 country-year observations

Final JESI sample:
    2016-2023
"""

from pathlib import Path

import numpy as np
import pandas as pd


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

BASE_INPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024.csv"
)

CONCENTRATION_INPUT_FILE = Path(
    "data/raw/import_product_concentration_2015_2024.csv"
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


# -------------------------------------------------------------------
# Base dataset loading
# -------------------------------------------------------------------

def load_base_data():
    """Load and validate Script 29 Strategic Autonomy data."""

    if not BASE_INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing base input file: {BASE_INPUT_FILE}"
        )

    df = pd.read_csv(
        BASE_INPUT_FILE
    )

    required_columns = [
        "country_code",
        "country",
        "year",
        "eci",
        "high_tech_exports",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Base dataset is missing required columns: "
            f"{missing_columns}"
        )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    if df["year"].isna().any():
        raise ValueError(
            "Base year column contains missing or "
            "non-numeric values."
        )

    df["year"] = df["year"].astype(int)

    for indicator in [
        "eci",
        "high_tech_exports",
    ]:
        df[indicator] = pd.to_numeric(
            df[indicator],
            errors="coerce",
        )

    if len(df) != EXPECTED_BENCHMARK_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_BENCHMARK_ROWS} base rows, "
            f"found {len(df)}."
        )

    if set(df["country_code"]) != set(COUNTRIES):
        raise ValueError(
            "Base country-code coverage does not match "
            "the JESI sample."
        )

    if set(df["year"]) != EXPECTED_YEARS:
        raise ValueError(
            "Base year coverage is not exactly 2015-2024."
        )

    if df.duplicated(
        ["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations detected "
            "in base data."
        )

    return df


# -------------------------------------------------------------------
# UNCTAD concentration loading
# -------------------------------------------------------------------

def load_concentration_data():
    """Load and validate official UNCTAD concentration data."""

    if not CONCENTRATION_INPUT_FILE.exists():
        raise FileNotFoundError(
            "Missing UNCTAD concentration file: "
            f"{CONCENTRATION_INPUT_FILE}"
        )

    concentration = pd.read_csv(
        CONCENTRATION_INPUT_FILE
    )

    required_columns = [
        "country_code",
        "country",
        "year",
        "import_product_concentration",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in concentration.columns
    ]

    if missing_columns:
        raise ValueError(
            "UNCTAD concentration data is missing "
            f"required columns: {missing_columns}"
        )

    concentration["year"] = pd.to_numeric(
        concentration["year"],
        errors="coerce",
    )

    concentration[
        "import_product_concentration"
    ] = pd.to_numeric(
        concentration[
            "import_product_concentration"
        ],
        errors="coerce",
    )

    if concentration["year"].isna().any():
        raise ValueError(
            "UNCTAD concentration year contains "
            "missing or non-numeric values."
        )

    if concentration[
        "import_product_concentration"
    ].isna().any():
        raise ValueError(
            "UNCTAD concentration contains missing values."
        )

    concentration["year"] = (
        concentration["year"].astype(int)
    )

    if len(concentration) != EXPECTED_BENCHMARK_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_BENCHMARK_ROWS} UNCTAD "
            f"rows, found {len(concentration)}."
        )

    if set(
        concentration["country_code"]
    ) != set(COUNTRIES):
        raise ValueError(
            "UNCTAD country-code coverage does not match "
            "the JESI sample."
        )

    if set(
        concentration["year"]
    ) != EXPECTED_YEARS:
        raise ValueError(
            "UNCTAD year coverage is not exactly 2015-2024."
        )

    if concentration.duplicated(
        ["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations detected "
            "in UNCTAD concentration data."
        )

    values = concentration[
        "import_product_concentration"
    ]

    if (
        (values < 0)
        | (values > 1)
    ).any():
        raise ValueError(
            "UNCTAD import concentration contains values "
            "outside the expected [0, 1] range."
        )

    return concentration[
        [
            "country_code",
            "country",
            "year",
            "import_product_concentration",
        ]
    ].copy()


# -------------------------------------------------------------------
# Build integrated dataset
# -------------------------------------------------------------------

def build_integrated_dataset(
    base,
    concentration,
):
    """Integrate official UNCTAD concentration into base data."""

    if (
        base["country_code"].astype(str)
        .str.len()
        .eq(0)
        .any()
    ):
        raise ValueError(
            "Base dataset contains empty country codes."
        )

    integrated = base.drop(
        columns=[
            "import_product_concentration"
        ],
        errors="ignore",
    ).merge(
        concentration[
            [
                "country_code",
                "year",
                "import_product_concentration",
            ]
        ],
        on=[
            "country_code",
            "year",
        ],
        how="left",
        validate="one_to_one",
    )

    if len(integrated) != EXPECTED_BENCHMARK_ROWS:
        raise ValueError(
            "Integrated dataset does not contain the "
            "expected 50 country-year observations."
        )

    missing_concentration = int(
        integrated[
            "import_product_concentration"
        ].isna().sum()
    )

    if missing_concentration:
        raise ValueError(
            "UNCTAD integration produced "
            f"{missing_concentration} missing "
            "import concentration observations."
        )

    return integrated.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(
        drop=True
    )


# -------------------------------------------------------------------
# Overall indicator coverage
# -------------------------------------------------------------------

def calculate_indicator_coverage(
    df,
):
    """Calculate overall coverage for each indicator."""

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

def calculate_country_coverage(
    df,
):
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

def calculate_year_coverage(
    df,
):
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

def identify_missing_observations(
    df,
):
    """Identify every missing country-year-indicator."""

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
# Complete-case summary
# -------------------------------------------------------------------

def calculate_complete_case_summary(
    df,
):
    """Calculate complete Strategic Autonomy country-years."""

    working = df.copy()

    working[
        "strategic_autonomy_complete"
    ] = ~working[
        INDICATORS
    ].isna().any(axis=1)

    records = []

    for country_code, country_name in COUNTRIES.items():

        country_df = working[
            working["country_code"]
            == country_code
        ]

        expected = len(
            EXPECTED_YEARS
        )

        complete = int(
            country_df[
                "strategic_autonomy_complete"
            ].sum()
        )

        excluded = (
            expected - complete
        )

        records.append(
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
        records
    )


# -------------------------------------------------------------------
# Final JESI sample impact
# -------------------------------------------------------------------

def calculate_final_jesi_impact(
    df,
):
    """Measure missing-data impact on 2016-2023 JESI sample."""

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

    excluded = (
        expected - complete
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
                    complete
                    / expected
                    * 100
                ),
            }
        ]
    )

    country_records = []

    for country_code, country_name in COUNTRIES.items():

        country_df = final_df[
            final_df["country_code"]
            == country_code
        ]

        expected_country = len(
            FINAL_JESI_YEARS
        )

        complete_country = int(
            country_df[
                "strategic_autonomy_complete"
            ].sum()
        )

        excluded_country = (
            expected_country
            - complete_country
        )

        country_records.append(
            {
                "country_code": country_code,
                "country": country_name,
                "period": "2016-2023",
                "expected_country_years": (
                    expected_country
                ),
                "complete_country_years": (
                    complete_country
                ),
                "excluded_country_years": (
                    excluded_country
                ),
                "retention_percent": (
                    complete_country
                    / expected_country
                    * 100
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
    """Identify countries with complete 2016-2023 coverage."""

    records = []

    for country_code, country_name in COUNTRIES.items():

        country_df = final_df[
            final_df["country_code"]
            == country_code
        ]

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

    eligible_count = int(
        panel[
            "balanced_panel_eligible"
        ].sum()
    )

    balanced_observations = (
        eligible_count
        * len(FINAL_JESI_YEARS)
    )

    summary = pd.DataFrame(
        [
            {
                "period": "2016-2023",
                "total_countries": EXPECTED_COUNTRY_COUNT,
                "balanced_panel_countries": eligible_count,
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
        summary,
    )


# -------------------------------------------------------------------
# Missing-gap analysis
# -------------------------------------------------------------------

def calculate_missing_gaps(
    df,
):
    """Calculate consecutive missing-data gaps."""

    records = []

    for country_code, country_name in COUNTRIES.items():

        country_df = df[
            df["country_code"]
            == country_code
        ].sort_values(
            "year"
        )

        for indicator in INDICATORS:

            missing_years = sorted(
                country_df.loc[
                    country_df[indicator].isna(),
                    "year",
                ].astype(int).tolist()
            )

            longest_gap = 0

            if missing_years:

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

            records.append(
                {
                    "country_code": country_code,
                    "country": country_name,
                    "indicator": indicator,
                    "missing_observations": len(
                        missing_years
                    ),
                    "missing_years": ", ".join(
                        str(year)
                        for year in missing_years
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
# Main
# -------------------------------------------------------------------

def main():
    """Run the complete Strategic Autonomy coverage analysis."""

    print("=" * 72)
    print(
        "JESI STRATEGIC AUTONOMY "
        "COVERAGE IMPACT ANALYSIS"
    )
    print("=" * 72)

    print()
    print(
        "Base input:",
        BASE_INPUT_FILE,
    )

    print(
        "UNCTAD input:",
        CONCENTRATION_INPUT_FILE,
    )

    print(
        "Benchmark period: 2015-2024"
    )

    print(
        "Final JESI sample period: 2016-2023"
    )

    print()

    # ---------------------------------------------------------------
    # Load base data
    # ---------------------------------------------------------------

    base = load_base_data()

    print(
        "Base Strategic Autonomy validation: GREEN"
    )

    print(
        f"Base rows: {len(base)}"
    )

    # ---------------------------------------------------------------
    # Load UNCTAD data
    # ---------------------------------------------------------------

    concentration = load_concentration_data()

    print(
        "UNCTAD import concentration validation: GREEN"
    )

    print(
        f"UNCTAD rows: {len(concentration)}"
    )

    # ---------------------------------------------------------------
    # Integrate
    # ---------------------------------------------------------------

    df = build_integrated_dataset(
        base,
        concentration,
    )

    print(
        "Integrated Strategic Autonomy dataset: GREEN"
    )

    print(
        f"Integrated rows: {len(df)}"
    )

    # ---------------------------------------------------------------
    # Indicator coverage
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
    # Final JESI impact
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
    # Gap analysis
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
    # Final metrics
    # ---------------------------------------------------------------

    complete_observations = int(
        final_df[
            "strategic_autonomy_complete"
        ].sum()
    )

    excluded_observations = (
        EXPECTED_FINAL_JESI_ROWS
        - complete_observations
    )

    retention = (
        complete_observations
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
        f"{complete_observations}"
    )

    print(
        f"Excluded observations: "
        f"{excluded_observations}"
    )

    print(
        f"Complete-case retention: "
        f"{retention:.2f}%"
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

    final_output = pd.concat(
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

    final_output.to_csv(
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
        "Strategic Autonomy coverage analysis "
        "completed without imputation."
    )
    print(
        "Official UNCTAD concentration data was "
        "integrated before coverage analysis."
    )
    print(
        "No missing observation was modified, "
        "replaced, or fabricated."
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
