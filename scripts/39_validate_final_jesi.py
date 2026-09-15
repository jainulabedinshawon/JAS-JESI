"""
JAS Unified Economic Strength Index (JESI)
Master Validation & Final Consistency Check

Validates the final JESI research outputs.
"""

from pathlib import Path

import numpy as np
import pandas as pd


RESULTS_DIR = Path("data/results")

JESI_FILE = (
    RESULTS_DIR
    / "jesi_country_year_2016_2023.csv"
)

FINAL_FILE = (
    RESULTS_DIR
    / "final_jesi_country_results.csv"
)

RESEARCH_FILE = (
    RESULTS_DIR
    / "JESI_final_research_table.csv"
)

ROBUSTNESS_FILE = (
    RESULTS_DIR
    / "jesi_robustness_country_results.csv"
)

PILLARS = ["G", "P", "C", "R", "A"]

COUNTRY_COUNT = 5

EXPECTED_COUNTRIES = {
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
}


def check_file(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )


def main():
    print("=" * 70)
    print("JESI MASTER VALIDATION")
    print("=" * 70)

    # ------------------------------------------------------------
    # Check required files
    # ------------------------------------------------------------

    required_files = [
        JESI_FILE,
        FINAL_FILE,
        RESEARCH_FILE,
        ROBUSTNESS_FILE,
    ]

    for path in required_files:
        check_file(path)
        print(f"FOUND: {path}")

    # ------------------------------------------------------------
    # Load final country-year data
    # ------------------------------------------------------------

    df = pd.read_csv(JESI_FILE)

    required_columns = {
        "country_code",
        "country",
        "year",
        "JESI",
        *PILLARS,
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {sorted(missing)}"
        )

    # ------------------------------------------------------------
    # Country validation
    # ------------------------------------------------------------

    countries = set(df["country"])

    if countries != EXPECTED_COUNTRIES:
        raise ValueError(
            "Country coverage mismatch.\n"
            f"Expected: {sorted(EXPECTED_COUNTRIES)}\n"
            f"Found: {sorted(countries)}"
        )

    if len(countries) != COUNTRY_COUNT:
        raise ValueError(
            "Unexpected number of countries."
        )

    # ------------------------------------------------------------
    # Year validation
    # ------------------------------------------------------------

    years = sorted(
        df["year"].astype(int).unique()
    )

    if years != list(range(2016, 2024)):
        raise ValueError(
            f"Unexpected year coverage: {years}"
        )

    # ------------------------------------------------------------
    # Duplicate validation
    # ------------------------------------------------------------

    duplicates = df.duplicated(
        subset=["country_code", "year"]
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate country-year observations found."
        )

    # ------------------------------------------------------------
    # Pillar range validation
    # ------------------------------------------------------------

    for pillar in PILLARS:

        values = pd.to_numeric(
            df[pillar],
            errors="coerce",
        )

        if values.isna().any():
            raise ValueError(
                f"{pillar} contains missing/non-numeric values."
            )

        if ((values < 0) | (values > 1)).any():
            raise ValueError(
                f"{pillar} contains values outside [0, 1]."
            )

    # ------------------------------------------------------------
    # JESI range validation
    # ------------------------------------------------------------

    jesi = pd.to_numeric(
        df["JESI"],
        errors="coerce",
    )

    if jesi.isna().any():
        raise ValueError(
            "JESI contains missing/non-numeric values."
        )

    if ((jesi < 0) | (jesi > 100)).any():
        raise ValueError(
            "JESI contains values outside [0, 100]."
        )

    # ------------------------------------------------------------
    # Independent JESI formula verification
    # ------------------------------------------------------------

    weights = np.array(
        [0.20, 0.25, 0.20, 0.20, 0.15]
    )

    pillar_values = df[
        PILLARS
    ].to_numpy(dtype=float)

    recalculated = (
        100
        * np.exp(
            np.sum(
                weights
                * np.log(
                    np.clip(
                        pillar_values,
                        1e-12,
                        1.0,
                    )
                ),
                axis=1,
            )
        )
    )

    difference = np.abs(
        recalculated - df["JESI"].to_numpy()
    )

    if not np.allclose(
        recalculated,
        df["JESI"].to_numpy(),
        atol=1e-8,
    ):
        raise ValueError(
            "Independent JESI formula verification failed."
        )

    print()
    print(
        "Independent JESI formula verification: PASSED"
    )

    print(
        f"Maximum numerical difference: "
        f"{difference.max():.12f}"
    )

    # ------------------------------------------------------------
    # Final country result validation
    # ------------------------------------------------------------

    final_df = pd.read_csv(FINAL_FILE)

    if len(final_df) != COUNTRY_COUNT:
        raise ValueError(
            "Final country result does not contain "
            "exactly five countries."
        )

    if final_df["rank"].duplicated().any():
        raise ValueError(
            "Duplicate country ranks detected."
        )

    expected_ranks = set(
        range(1, COUNTRY_COUNT + 1)
    )

    actual_ranks = set(
        final_df["rank"].astype(int)
    )

    if actual_ranks != expected_ranks:
        raise ValueError(
            "Final ranking does not contain ranks 1–5."
        )

    # ------------------------------------------------------------
    # Research table validation
    # ------------------------------------------------------------

    research_df = pd.read_csv(
        RESEARCH_FILE
    )

    if len(research_df) != COUNTRY_COUNT:
        raise ValueError(
            "Research table does not contain five countries."
        )

    required_research_columns = {
        "rank",
        "country_code",
        "country",
        "Growth",
        "Productivity",
        "Connectivity",
        "Resilience",
        "Strategic_Autonomy",
        "JESI",
    }

    missing_research = (
        required_research_columns
        - set(research_df.columns)
    )

    if missing_research:
        raise ValueError(
            "Research table missing columns: "
            f"{sorted(missing_research)}"
        )

    # ------------------------------------------------------------
    # Robustness output validation
    # ------------------------------------------------------------

    robustness_df = pd.read_csv(
        ROBUSTNESS_FILE
    )

    robustness_columns = {
        "country_code",
        "country",
        "JAS_arithmetic",
        "JAS_geometric",
        "Equal_arithmetic",
        "Equal_geometric",
    }

    missing_robustness = (
        robustness_columns
        - set(robustness_df.columns)
    )

    if missing_robustness:
        raise ValueError(
            "Robustness output missing columns: "
            f"{sorted(missing_robustness)}"
        )

    if len(robustness_df) != COUNTRY_COUNT:
        raise ValueError(
            "Robustness results do not contain five countries."
        )

    # ------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------

    print()
    print("Countries:", len(countries))
    print("Years:", f"{years[0]}–{years[-1]}")
    print("Country-year observations:", len(df))

    print()
    print("JESI range:")
    print(
        f"Minimum: {df['JESI'].min():.4f}"
    )
    print(
        f"Maximum: {df['JESI'].max():.4f}"
    )

    print()
    print("Final country results:")
    print(
        final_df[
            [
                "rank",
                "country",
                "JESI",
            ]
        ].to_string(index=False)
    )

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print("ALL FINAL JESI CONSISTENCY CHECKS PASSED.")
    print("=" * 70)


if __name__ == "__main__":
    main()
