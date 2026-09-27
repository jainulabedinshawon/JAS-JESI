"""
JAS Unified Economic Strength Index (JESI)
Final Master Calculation

Combines the five normalized pillars:

G = Growth
P = Productivity
C = Connectivity
R = Resilience
A = Strategic Autonomy

Baseline weights:
G = 0.20
P = 0.25
C = 0.20
R = 0.20
A = 0.15

JESI = 100 * G^0.20 * P^0.25 * C^0.20 * R^0.20 * A^0.15

Final common benchmark:
5 countries, 2016-2023 = 40 theoretical country-year observations.

Important:
The theoretical benchmark is 40 observations, but the baseline
JESI calculation uses complete-case observations only.

No missing observation is imputed.

Country-year matching is performed using country_code + year,
not country-name strings, to avoid source-specific naming
differences such as "Vietnam" vs "Viet Nam".
"""

from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/processed")
OUTPUT_DIR = Path("data/results")

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

EXPECTED_YEARS = set(range(2016, 2024))

COUNTRY_NAMES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
    "VNM": "Vietnam",
}

EXPECTED_FULL_OBSERVATIONS = (
    len(EXPECTED_COUNTRIES)
    * len(EXPECTED_YEARS)
)


def weighted_geometric_mean(values, weights):
    """
    Calculate the weighted geometric mean.
    """

    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)

    if len(values) != len(weights):
        raise ValueError(
            "Values and weights must have the same length."
        )

    if np.any(~np.isfinite(values)):
        raise ValueError(
            "JESI pillar scores contain non-finite values."
        )

    if np.any(values <= 0):
        raise ValueError(
            "JESI pillar scores must be greater than zero."
        )

    if np.any(values > 1):
        raise ValueError(
            "JESI pillar scores must not exceed 1."
        )

    if np.any(weights < 0):
        raise ValueError(
            "JESI weights cannot be negative."
        )

    if not np.isclose(weights.sum(), 1.0):
        raise ValueError(
            "JESI weights must sum to 1."
        )

    return float(
        np.exp(
            np.sum(
                weights * np.log(values)
            )
        )
    )


def load_pillar_file(filename, score_column, pillar):
    """
    Load a pillar dataset and return standardized country-year scores.
    """

    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Missing pillar file: {path}"
        )

    df = pd.read_csv(path)

    required = {
        "country_code",
        "country",
        "year",
        score_column,
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"{path} is missing columns: {sorted(missing)}"
        )

    result = df[
        [
            "country_code",
            "country",
            "year",
            score_column,
        ]
    ].copy()

    result["country_code"] = (
        result["country_code"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    result["year"] = pd.to_numeric(
        result["year"],
        errors="coerce",
    )

    if result["year"].isna().any():
        raise ValueError(
            f"{path} contains invalid year values."
        )

    result["year"] = result["year"].astype(int)

    result = result.rename(
        columns={score_column: pillar}
    )

    return result


def load_resilience_file():
    """
    Load the resilience pillar.

    The resilience constructor currently does not include
    country_code, so country codes are assigned from the
    fixed five-country benchmark sample.

    Country-year matching downstream uses country_code + year.
    """

    filename = "resilience_pillar_scores_2015_2024.csv"
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Missing resilience pillar file: {path}"
        )

    df = pd.read_csv(path)

    required = {
        "country",
        "year",
        "resilience_score",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"{path} is missing columns: {sorted(missing)}"
        )

    country_map = {
        "Bangladesh": "BGD",
        "India": "IND",
        "Indonesia": "IDN",
        "Malaysia": "MYS",
        "Vietnam": "VNM",
        "Viet Nam": "VNM",
    }

    df["country_code"] = (
        df["country"]
        .map(country_map)
    )

    if df["country_code"].isna().any():
        unknown = sorted(
            df.loc[
                df["country_code"].isna(),
                "country",
            ]
            .dropna()
            .unique()
        )

        raise ValueError(
            "Unknown country names found in resilience data: "
            f"{unknown}"
        )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    if df["year"].isna().any():
        raise ValueError(
            f"{path} contains invalid year values."
        )

    df["year"] = df["year"].astype(int)

    result = df[
        [
            "country_code",
            "country",
            "year",
            "resilience_score",
        ]
    ].copy()

    result = result.rename(
        columns={
            "resilience_score": "R"
        }
    )

    return result


def validate_unique_country_year(df, name):
    """
    Validate that each country-year appears only once.
    """

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
            f"{name} contains duplicate country-year observations:\n"
            f"{duplicates[['country_code', 'country', 'year']].to_string(index=False)}"
        )


def standardize_country_names(df):
    """
    Standardize presentation country names using country codes.

    Country-code identity is used for matching.
    """

    df["country"] = (
        df["country_code"]
        .map(COUNTRY_NAMES)
    )

    if df["country"].isna().any():
        unknown_codes = sorted(
            df.loc[
                df["country"].isna(),
                "country_code",
            ]
            .dropna()
            .unique()
        )

        raise ValueError(
            "Unknown country codes found: "
            f"{unknown_codes}"
        )

    return df


def build_expected_panel():
    """
    Build the theoretical five-country × eight-year panel.
    """

    rows = []

    for country_code in sorted(EXPECTED_COUNTRIES):
        for year in sorted(EXPECTED_YEARS):
            rows.append(
                {
                    "country_code": country_code,
                    "country": COUNTRY_NAMES[country_code],
                    "year": year,
                }
            )

    return pd.DataFrame(rows)


def main():
    print("=" * 72)
    print("JAS Unified Economic Strength Index")
    print("Final JESI Calculation")
    print("=" * 72)

    # ---------------------------------------------------------------
    # Load five pillar datasets
    # ---------------------------------------------------------------

    growth = load_pillar_file(
        "growth_pillar_scores_2015_2024.csv",
        "growth_score",
        "G",
    )

    productivity = load_pillar_file(
        "productivity_pillar_scores_2016_2023.csv",
        "productivity_score",
        "P",
    )

    connectivity = load_pillar_file(
        "connectivity_pillar_scores_2015_2024.csv",
        "connectivity_score",
        "C",
    )

    resilience = load_resilience_file()

    autonomy = load_pillar_file(
        "strategic_autonomy_pillar_2015_2024.csv",
        "strategic_autonomy_arithmetic",
        "A",
    )

    pillars = {
        "Growth": growth,
        "Productivity": productivity,
        "Connectivity": connectivity,
        "Resilience": resilience,
        "Strategic Autonomy": autonomy,
    }

    # ---------------------------------------------------------------
    # Validate individual pillar datasets
    # ---------------------------------------------------------------

    for name, pillar_df in pillars.items():

        validate_unique_country_year(
            pillar_df,
            name,
        )

        pillar_df["country_code"] = (
            pillar_df["country_code"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        unexpected_codes = (
            set(pillar_df["country_code"].dropna())
            - EXPECTED_COUNTRIES
        )

        if unexpected_codes:
            raise ValueError(
                f"{name} contains unexpected country codes: "
                f"{sorted(unexpected_codes)}"
            )

        missing_countries = (
            EXPECTED_COUNTRIES
            - set(
                pillar_df["country_code"]
                .dropna()
            )
        )

        if missing_countries:
            raise ValueError(
                f"{name} is missing expected countries: "
                f"{sorted(missing_countries)}"
            )

    # ---------------------------------------------------------------
    # Restrict all pillars to the theoretical common period
    # ---------------------------------------------------------------

    for name, pillar_df in pillars.items():

        pillar_df.drop(
            pillar_df[
                ~pillar_df["year"].isin(
                    EXPECTED_YEARS
                )
            ].index,
            inplace=True,
        )

        pillar_df.drop(
            pillar_df[
                ~pillar_df["country_code"].isin(
                    EXPECTED_COUNTRIES
                )
            ].index,
            inplace=True,
        )

    # ---------------------------------------------------------------
    # Standardize country names
    # ---------------------------------------------------------------

    for pillar_df in pillars.values():
        standardize_country_names(
            pillar_df
        )

    # ---------------------------------------------------------------
    # Merge using country_code + year ONLY
    # ---------------------------------------------------------------

    jesI = build_expected_panel()

    for name, pillar_df in pillars.items():

        merge_columns = [
            "country_code",
            "year",
            *[
                column
                for column in pillar_df.columns
                if column in ["G", "P", "C", "R", "A"]
            ],
        ]

        selected = pillar_df[
            merge_columns
        ].copy()

        jesI = jesI.merge(
            selected,
            on=[
                "country_code",
                "year",
            ],
            how="left",
            validate="one_to_one",
        )

    # ---------------------------------------------------------------
    # Validate theoretical panel
    # ---------------------------------------------------------------

    if len(jesI) != EXPECTED_FULL_OBSERVATIONS:
        raise ValueError(
            "Theoretical JESI panel size changed unexpectedly. "
            f"Expected {EXPECTED_FULL_OBSERVATIONS}, "
            f"found {len(jesI)}."
        )

    if set(jesI["country_code"]) != EXPECTED_COUNTRIES:
        raise ValueError(
            "Theoretical JESI panel does not contain exactly "
            "the expected five countries."
        )

    if set(jesI["year"]) != EXPECTED_YEARS:
        raise ValueError(
            "Theoretical JESI panel does not contain exactly "
            "the expected years 2016-2023."
        )

    # ---------------------------------------------------------------
    # Identify incomplete country-year observations
    # ---------------------------------------------------------------

    pillar_columns = [
        "G",
        "P",
        "C",
        "R",
        "A",
    ]

    complete_mask = (
        jesI[pillar_columns]
        .notna()
        .all(axis=1)
    )

    excluded = jesI.loc[
        ~complete_mask,
        [
            "country_code",
            "country",
            "year",
        ] + pillar_columns,
    ].copy()

    if not excluded.empty:

        missing_records = []

        for _, row in excluded.iterrows():

            missing_pillars = [
                pillar
                for pillar in pillar_columns
                if pd.isna(row[pillar])
            ]

            missing_records.append(
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
                    "missing_pillars": ",".join(
                        missing_pillars
                    ),
                }
            )

        exclusion_report = pd.DataFrame(
            missing_records
        )

    else:

        exclusion_report = pd.DataFrame(
            columns=[
                "country_code",
                "country",
                "year",
                "missing_pillars",
            ]
        )

    complete = jesI.loc[
        complete_mask
    ].copy()

    # ---------------------------------------------------------------
    # No silent imputation
    # ---------------------------------------------------------------

    if len(complete) == 0:
        raise ValueError(
            "No complete country-year observations remain "
            "after applying the no-imputation rule."
        )

    print()
    print(
        "JESI theoretical panel:"
    )
    print(
        f"Expected country-year observations: "
        f"{EXPECTED_FULL_OBSERVATIONS}"
    )

    print(
        f"Complete observations: "
        f"{len(complete)}"
    )

    print(
        f"Excluded observations: "
        f"{len(excluded)}"
    )

    retention = (
        len(complete)
        / EXPECTED_FULL_OBSERVATIONS
        * 100
    )

    print(
        f"Complete-case retention: "
        f"{retention:.2f}%"
    )

    if not excluded.empty:
        print()
        print(
            "Excluded country-year observations:"
        )
        print(
            exclusion_report.to_string(
                index=False
            )
        )

    # ---------------------------------------------------------------
    # Validate complete-case panel
    # ---------------------------------------------------------------

    validate_unique_country_year(
        complete,
        "Complete JESI",
    )

    if set(
        complete["country_code"]
    ) != EXPECTED_COUNTRIES:
        raise ValueError(
            "Complete JESI dataset does not contain "
            "all five countries."
        )

    if set(
        complete["year"]
    ) != EXPECTED_YEARS:
        raise ValueError(
            "Complete JESI dataset does not contain "
            "the full 2016-2023 period."
        )

    # ---------------------------------------------------------------
    # Validate pillar scores
    # ---------------------------------------------------------------

    for column in pillar_columns:

        complete[column] = pd.to_numeric(
            complete[column],
            errors="coerce",
        )

        if complete[column].isna().any():
            raise ValueError(
                f"Missing pillar values detected in {column}."
            )

        if (
            (complete[column] <= 0).any()
            or (complete[column] > 1).any()
        ):
            raise ValueError(
                f"{column} contains values outside "
                "the valid JESI range (0, 1]."
            )

    # ---------------------------------------------------------------
    # Calculate baseline JESI
    # ---------------------------------------------------------------

    complete["JESI"] = complete.apply(
        lambda row: (
            100
            * weighted_geometric_mean(
                [
                    row["G"],
                    row["P"],
                    row["C"],
                    row["R"],
                    row["A"],
                ],
                [
                    WEIGHTS["G"],
                    WEIGHTS["P"],
                    WEIGHTS["C"],
                    WEIGHTS["R"],
                    WEIGHTS["A"],
                ],
            )
        ),
        axis=1,
    )

    # ---------------------------------------------------------------
    # Validate calculated JESI
    # ---------------------------------------------------------------

    if complete["JESI"].isna().any():
        raise ValueError(
            "Calculated JESI contains missing values."
        )

    if (
        (complete["JESI"] <= 0).any()
        or (complete["JESI"] > 100).any()
    ):
        raise ValueError(
            "Calculated JESI contains values outside "
            "(0, 100]."
        )

    # ---------------------------------------------------------------
    # Sort final country-year results
    # ---------------------------------------------------------------

    complete = complete.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)

    # ---------------------------------------------------------------
    # Output directories
    # ---------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Save main JESI dataset
    # ---------------------------------------------------------------

    output_file = (
        OUTPUT_DIR
        / "jesi_country_year_2016_2023.csv"
    )

    complete[
        [
            "country_code",
            "country",
            "year",
            "G",
            "P",
            "C",
            "R",
            "A",
            "JESI",
        ]
    ].to_csv(
        output_file,
        index=False,
    )

    # ---------------------------------------------------------------
    # Save exclusion report
    # ---------------------------------------------------------------

    exclusion_file = (
        OUTPUT_DIR
        / "jesi_excluded_country_years_2016_2023.csv"
    )

    exclusion_report.to_csv(
        exclusion_file,
        index=False,
    )

    # ---------------------------------------------------------------
    # Save coverage summary
    # ---------------------------------------------------------------

    coverage_file = (
        OUTPUT_DIR
        / "jesi_sample_coverage_2016_2023.csv"
    )

    coverage = pd.DataFrame(
        [
            {
                "theoretical_observations": (
                    EXPECTED_FULL_OBSERVATIONS
                ),
                "complete_observations": (
                    len(complete)
                ),
                "excluded_observations": (
                    len(excluded)
                ),
                "complete_case_retention_pct": (
                    retention
                ),
                "imputation_used": False,
            }
        ]
    )

    coverage.to_csv(
        coverage_file,
        index=False,
    )

    # ---------------------------------------------------------------
    # Country-level summary
    # ---------------------------------------------------------------

    country_summary = (
        complete.groupby(
            [
                "country_code",
                "country",
            ]
        )
        .agg(
            JESI_mean=("JESI", "mean"),
            JESI_std=("JESI", "std"),
            JESI_min=("JESI", "min"),
            JESI_max=("JESI", "max"),
            observations=("JESI", "count"),
        )
        .reset_index()
    )

    country_summary["rank"] = (
        country_summary["JESI_mean"]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    country_summary = country_summary.sort_values(
        "rank"
    ).reset_index(drop=True)

    country_summary.to_csv(
        OUTPUT_DIR
        / "jesi_country_ranking_2016_2023.csv",
        index=False,
    )

    # ---------------------------------------------------------------
    # Year-level summary
    # ---------------------------------------------------------------

    yearly_summary = (
        complete.groupby("year")
        .agg(
            JESI_mean=("JESI", "mean"),
            JESI_median=("JESI", "median"),
            JESI_min=("JESI", "min"),
            JESI_max=("JESI", "max"),
            observations=("JESI", "count"),
        )
        .reset_index()
    )

    yearly_summary.to_csv(
        OUTPUT_DIR
        / "jesi_yearly_summary_2016_2023.csv",
        index=False,
    )

    # ---------------------------------------------------------------
    # Final console summary
    # ---------------------------------------------------------------

    print()
    print("=" * 72)
    print("JESI CALCULATION COMPLETED")
    print("=" * 72)

    print(
        f"Complete observations: {len(complete)}"
    )

    print(
        f"Excluded observations: {len(excluded)}"
    )

    print(
        f"Retention: {retention:.2f}%"
    )

    print()
    print(
        f"Main output: {output_file}"
    )

    print(
        f"Exclusion report: {exclusion_file}"
    )

    print(
        f"Coverage summary: {coverage_file}"
    )

    print()
    print(
        "Baseline JESI formula:"
    )

    print(
        "JESI = 100 × "
        "G^0.20 × "
        "P^0.25 × "
        "C^0.20 × "
        "R^0.20 × "
        "A^0.15"
    )

    print()
    print(
        "STATUS: GREEN"
    )

    print(
        "No missing observation was imputed."
    )

    print("=" * 72)


if __name__ == "__main__":
    main()
