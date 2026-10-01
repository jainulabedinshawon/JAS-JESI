"""
JESI Balanced-Panel Sensitivity Analysis
Master Version 1.0

Purpose
-------
Evaluate the effect of unequal country-year coverage without changing
the baseline production JESI result.

Production methodology remains unchanged:

- no imputation
- no interpolation
- no fabricated observations
- no automatic reweighting
- no deletion from the production result

This is a separate research-validation sensitivity analysis.

Final production sample:
    5 countries
    2016-2023
    40 theoretical observations
    34 complete observations

A country is balanced-panel eligible only if all eight years contain
complete G/P/C/R/A/JESI observations.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT / "data/results/jesi_country_year_2016_2023.csv"
)

OUTPUT_DIR = ROOT / "data/results"

COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "VNM": "Vietnam",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
}

YEARS = set(range(2016, 2024))

PILLARS = [
    "G",
    "P",
    "C",
    "R",
    "A",
]

REQUIRED_COLUMNS = [
    "country_code",
    "year",
    *PILLARS,
    "JESI",
]


def load_data() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing production JESI file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    missing = set(REQUIRED_COLUMNS) - set(df.columns)

    if missing:
        raise ValueError(
            "Production JESI file is missing columns: "
            + ", ".join(sorted(missing))
        )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    if df["year"].isna().any():
        raise ValueError(
            "Production JESI year column contains invalid values."
        )

    df["year"] = df["year"].astype(int)

    if df.duplicated(
        ["country_code", "year"]
    ).any():
        raise ValueError(
            "Duplicate country-year observations detected."
        )

    return df


def calculate_country_panel_status(
    df: pd.DataFrame,
) -> pd.DataFrame:
    records = []

    for country_code, country_name in COUNTRIES.items():

        country_df = df[
            df["country_code"] == country_code
        ].copy()

        observed_years = set(
            country_df["year"].astype(int)
        )

        complete_rows = (
            country_df[
                PILLARS + ["JESI"]
            ]
            .notna()
            .all(axis=1)
        )

        complete_years = int(
            complete_rows.sum()
        )

        expected_years = len(YEARS)

        balanced = (
            observed_years == YEARS
            and complete_years == expected_years
        )

        records.append(
            {
                "country_code": country_code,
                "country": country_name,
                "period": "2016-2023",
                "expected_observations": expected_years,
                "observed_observations": len(country_df),
                "complete_observations": complete_years,
                "missing_observations": (
                    expected_years - complete_years
                ),
                "coverage_pct": (
                    complete_years
                    / expected_years
                    * 100
                ),
                "balanced_panel_eligible": balanced,
            }
        )

    return pd.DataFrame(records)


def calculate_balanced_results(
    df: pd.DataFrame,
    status: pd.DataFrame,
) -> pd.DataFrame:
    eligible = set(
        status.loc[
            status["balanced_panel_eligible"],
            "country_code",
        ]
    )

    records = []

    for country_code in sorted(eligible):

        country_df = df[
            df["country_code"] == country_code
        ].copy()

        record = {
            "country_code": country_code,
            "country": COUNTRIES[country_code],
            "observations": len(country_df),
        }

        for column in PILLARS + ["JESI"]:
            record[f"{column}_mean"] = (
                pd.to_numeric(
                    country_df[column],
                    errors="coerce",
                ).mean()
            )

        records.append(record)

    return pd.DataFrame(records)


def calculate_summary(
    status: pd.DataFrame,
    balanced_results: pd.DataFrame,
) -> pd.DataFrame:
    eligible_count = int(
        status[
            "balanced_panel_eligible"
        ].sum()
    )

    theoretical = len(COUNTRIES) * len(YEARS)

    balanced_observations = (
        eligible_count * len(YEARS)
    )

    return pd.DataFrame(
        [
            {
                "period": "2016-2023",
                "countries": len(COUNTRIES),
                "theoretical_observations": theoretical,
                "complete_case_observations": 34,
                "balanced_panel_countries": eligible_count,
                "balanced_panel_observations": (
                    balanced_observations
                ),
                "balanced_panel_retention_pct": (
                    balanced_observations
                    / theoretical
                    * 100
                ),
                "production_methodology_changed": False,
                "imputation_used": False,
                "reweighting_used": False,
            }
        ]
    )


def main() -> None:
    df = load_data()

    status = calculate_country_panel_status(df)

    balanced_results = calculate_balanced_results(
        df,
        status,
    )

    summary = calculate_summary(
        status,
        balanced_results,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    status.to_csv(
        OUTPUT_DIR
        / "jesi_balanced_panel_country_results.csv",
        index=False,
    )

    balanced_results.to_csv(
        OUTPUT_DIR
        / "jesi_balanced_panel_country_means.csv",
        index=False,
    )

    summary.to_csv(
        OUTPUT_DIR
        / "jesi_balanced_panel_summary.csv",
        index=False,
    )

    print("=" * 72)
    print("JESI BALANCED-PANEL SENSITIVITY")
    print("=" * 72)
    print(status.to_string(index=False))
    print()
    print(summary.to_string(index=False))
    print()
    print("Production JESI methodology: UNCHANGED")
    print("Imputation: NONE")
    print("Interpolation: NONE")
    print("Reweighting: NONE")
    print("Production result modified: NO")
    print("=" * 72)


if __name__ == "__main__":
    main()
