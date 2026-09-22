"""
Final repository audit for the JAS Unified Economic Strength Index (JESI).

This audit checks:
1. Required repository files and pipeline scripts.
2. Required final JESI output files.
3. Final result schemas and basic validity.
4. README final-results markers.
5. Final research report presence.
6. Reproducibility-critical repository structure.

The audit is non-destructive.
"""

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_COUNTRIES = {"BGD", "IND", "IDN", "MYS", "VNM"}
EXPECTED_YEARS = set(range(2016, 2024))
EXPECTED_OBSERVATIONS = 40


REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "requirements.txt",
    "methodology/JESI_Master_V1.0.md",
    "src/__init__.py",
    "src/normalization.py",
    "src/pillar_construction.py",
    "src/jesi_calculation.py",
    "src/data_cleaning.py",
    "src/data_download.py",
    "src/nonlinear_resilience_scoring.py",
    "src/robustness_tests.py",
    "tests/test_jesi.py",
    "scripts/11_score_resilience_pillar.py",
    "scripts/20_construct_productivity_pillar.py",
    "scripts/25_construct_connectivity_pillar.py",
    "scripts/27_score_growth.py",
    "scripts/28_construct_growth_pillar.py",
    "scripts/35_construct_autonomy_pillar.py",
    "scripts/36_calculate_jesi.py",
    "scripts/37_robustness_tests.py",
    "scripts/38_generate_final_jesi_results.py",
    "scripts/39_validate_final_jesi.py",
    "scripts/40_generate_jesi_report.py",
    "scripts/41_update_readme_jesi.py",
    "scripts/42_final_repository_audit.py",
]


EXPECTED_OUTPUTS = [
    "data/results/jesi_country_year_2016_2023.csv",
    "data/results/jesi_country_ranking_2016_2023.csv",
    "data/results/jesi_robustness_country_results.csv",
    "data/results/jesi_robustness_correlations.csv",
    "data/results/jesi_robustness_summary.csv",
    "data/results/final_jesi_country_results.csv",
    "data/results/final_jesi_yearly_summary.csv",
    "data/results/JESI_final_research_table.csv",
    "docs/JESI_Final_Results_Report.md",
]


def fail(message):
    """Print an audit failure message and exit."""
    print(f"ERROR: {message}")
    sys.exit(1)


def check_required_files():
    """Check that all required repository files exist."""
    missing = [
        path for path in REQUIRED_FILES
        if not (ROOT / path).is_file()
    ]

    if missing:
        print("Missing required repository files:")
        for path in missing:
            print(f"  - {path}")
        fail("Repository structure is incomplete.")

    print("PASS: Required repository files are present.")


def check_expected_outputs():
    """Check that final generated outputs exist."""
    missing = [
        path for path in EXPECTED_OUTPUTS
        if not (ROOT / path).is_file()
    ]

    if missing:
        print("Missing final generated outputs:")
        for path in missing:
            print(f"  - {path}")
        fail(
            "Final outputs are incomplete. "
            "Run the JESI final-results pipeline before completing the audit."
        )

    print("PASS: Required final output files are present.")


def read_csv(path):
    """Read a CSV file with a clear audit error."""
    full_path = ROOT / path

    try:
        return pd.read_csv(full_path)
    except Exception as exc:
        fail(f"Could not read {path}: {exc}")


def check_country_year_results():
    """Validate the main country-year JESI result file."""
    path = "data/results/jesi_country_year_2016_2023.csv"
    df = read_csv(path)

    required = {
        "country_code",
        "year",
        "G",
        "P",
        "C",
        "R",
        "A",
        "JESI",
    }

    missing = required - set(df.columns)
    if missing:
        fail(
            f"{path} is missing required columns: "
            f"{sorted(missing)}"
        )

    if df.duplicated(["country_code", "year"]).any():
        fail(f"{path} contains duplicate country-year observations.")

    countries = set(df["country_code"].astype(str))
    if countries != EXPECTED_COUNTRIES:
        fail(
            f"{path} has unexpected countries: "
            f"{sorted(countries)}"
        )

    years = set(pd.to_numeric(df["year"], errors="coerce").dropna().astype(int))
    if years != EXPECTED_YEARS:
        fail(
            f"{path} has unexpected years: "
            f"{sorted(years)}"
        )

    if len(df) != EXPECTED_OBSERVATIONS:
        fail(
            f"{path} contains {len(df)} rows; "
            f"expected {EXPECTED_OBSERVATIONS}."
        )

    for column in ["G", "P", "C", "R", "A", "JESI"]:
        values = pd.to_numeric(df[column], errors="coerce")

        if values.isna().any():
            fail(f"{path} contains missing/non-numeric values in {column}.")

        if not ((values > 0) & (values <= 1)).all():
            fail(
                f"{path} contains values outside (0, 1] "
                f"in {column}."
            )

    print("PASS: Country-year JESI results are valid.")


def check_country_ranking():
    """Validate the country-level ranking output."""
    path = "data/results/jesi_country_ranking_2016_2023.csv"
    df = read_csv(path)

    required = {
        "country_code",
        "JESI",
        "rank",
    }

    missing = required - set(df.columns)
    if missing:
        fail(
            f"{path} is missing required columns: "
            f"{sorted(missing)}"
        )

    countries = set(df["country_code"].astype(str))

    if countries != EXPECTED_COUNTRIES:
        fail(
            f"{path} has unexpected countries: "
            f"{sorted(countries)}"
        )

    if len(df) != len(EXPECTED_COUNTRIES):
        fail(
            f"{path} contains {len(df)} rows; "
            f"expected {len(EXPECTED_COUNTRIES)}."
        )

    ranks = pd.to_numeric(df["rank"], errors="coerce")

    if ranks.isna().any():
        fail(f"{path} contains invalid rank values.")

    if set(ranks.astype(int)) != set(range(1, 6)):
        fail(f"{path} must contain ranks 1 through 5.")

    print("PASS: Country ranking output is valid.")


def check_final_country_results():
    """Validate final country-level research results."""
    path = "data/results/final_jesi_country_results.csv"
    df = read_csv(path)

    required = {
        "country_code",
        "G_mean",
        "P_mean",
        "C_mean",
        "R_mean",
        "A_mean",
        "JESI_mean",
        "JESI_std",
        "observations",
        "rank",
        "JESI_score_100",
    }

    missing = required - set(df.columns)

    if missing:
        fail(
            f"{path} is missing required columns: "
            f"{sorted(missing)}"
        )

    countries = set(df["country_code"].astype(str))

    if countries != EXPECTED_COUNTRIES:
        fail(
            f"{path} has unexpected countries: "
            f"{sorted(countries)}"
        )

    if len(df) != 5:
        fail(
            f"{path} contains {len(df)} rows; expected 5."
        )

    observations = pd.to_numeric(
        df["observations"],
        errors="coerce",
    )

    if observations.isna().any():
        fail(f"{path} contains invalid observation counts.")

    if not (observations == 8).all():
        fail(
            f"{path} must contain 8 observations per country."
        )

    score = pd.to_numeric(
        df["JESI_score_100"],
        errors="coerce",
    )

    if score.isna().any():
        fail(f"{path} contains invalid JESI_score_100 values.")

    if not ((score > 0) & (score <= 100)).all():
        fail(
            f"{path} contains JESI_score_100 values outside (0, 100]."
        )

    print("PASS: Final country-level research results are valid.")


def check_yearly_summary():
    """Validate yearly summary output."""
    path = "data/results/final_jesi_yearly_summary.csv"
    df = read_csv(path)

    if "year" not in df.columns:
        fail(f"{path} is missing the year column.")

    years = set(
        pd.to_numeric(df["year"], errors="coerce")
        .dropna()
        .astype(int)
    )

    if years != EXPECTED_YEARS:
        fail(
            f"{path} has unexpected years: "
            f"{sorted(years)}"
        )

    if len(df) != 8:
        fail(
            f"{path} contains {len(df)} rows; expected 8."
        )

    print("PASS: Yearly JESI summary is valid.")


def check_research_table():
    """Validate the final research table."""
    path = "data/results/JESI_final_research_table.csv"
    df = read_csv(path)

    required = {
        "country_code",
        "JESI_mean",
        "JESI_score_100",
        "rank",
    }

    missing = required - set(df.columns)

    if missing:
        fail(
            f"{path} is missing required columns: "
            f"{sorted(missing)}"
        )

    if len(df) != 5:
        fail(
            f"{path} contains {len(df)} rows; expected 5."
        )

    print("PASS: Final research table is valid.")


def check_robustness_outputs():
    """Validate the robustness-testing outputs."""
    country_path = (
        "data/results/jesi_robustness_country_results.csv"
    )
    corr_path = (
        "data/results/jesi_robustness_correlations.csv"
    )
    summary_path = (
        "data/results/jesi_robustness_summary.csv"
    )

    country_df = read_csv(country_path)
    corr_df = read_csv(corr_path)
    summary_df = read_csv(summary_path)

    required_country = {
        "country_code",
        "JAS_arithmetic",
        "JAS_geometric",
        "Equal_arithmetic",
        "Equal_geometric",
    }

    missing_country = required_country - set(country_df.columns)

    if missing_country:
        fail(
            f"{country_path} is missing required columns: "
            f"{sorted(missing_country)}"
        )

    if set(country_df["country_code"].astype(str)) != EXPECTED_COUNTRIES:
        fail(
            f"{country_path} does not contain exactly the "
            "five expected countries."
        )

    if corr_df.empty:
        fail(f"{corr_path} is empty.")

    if summary_df.empty:
        fail(f"{summary_path} is empty.")

    print("PASS: Robustness outputs are present and structurally valid.")


def check_readme():
    """Check that README contains the generated final-results section."""
    path = ROOT / "README.md"

    text = path.read_text(encoding="utf-8")

    start_marker = "<!-- JESI_FINAL_RESULTS_START -->"
    end_marker = "<!-- JESI_FINAL_RESULTS_END -->"

    if start_marker not in text:
        fail("README.md is missing JESI final-results start marker.")

    if end_marker not in text:
        fail("README.md is missing JESI final-results end marker.")

    if text.index(start_marker) >= text.index(end_marker):
        fail("README.md contains invalid JESI final-results marker order.")

    print("PASS: README final-results section is integrated.")


def check_final_report():
    """Check that the final research report exists and is non-empty."""
    path = ROOT / "docs/JESI_Final_Results_Report.md"

    text = path.read_text(encoding="utf-8").strip()

    if not text:
        fail("Final JESI research report is empty.")

    required_phrases = [
        "JAS Unified Economic Strength Index",
        "JESI",
        "Methodology",
        "Limitations",
    ]

    missing = [
        phrase for phrase in required_phrases
        if phrase not in text
    ]

    if missing:
        fail(
            "Final JESI research report is missing expected sections: "
            f"{missing}"
        )

    print("PASS: Final JESI research report is present and populated.")


def main():
    """Run the complete final repository audit."""
    print("=" * 70)
    print("JAS-JESI FINAL REPOSITORY AUDIT")
    print("=" * 70)

    check_required_files()
    check_expected_outputs()
    check_country_year_results()
    check_country_ranking()
    check_final_country_results()
    check_yearly_summary()
    check_research_table()
    check_robustness_outputs()
    check_readme()
    check_final_report()

    print("=" * 70)
    print("AUDIT STATUS: GREEN")
    print("JESI final repository structure and outputs passed audit.")
    print("=" * 70)


if __name__ == "__main__":
    main()
