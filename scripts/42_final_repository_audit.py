"""
JESI Final Repository Audit
JAS Unified Economic Strength Index (JESI)

Purpose:
    Perform a final non-destructive audit of the JESI repository.

This script does NOT modify files.
It checks whether the core JESI pipeline, outputs,
documentation, tests, and methodology files are present.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    # Core source modules
    "src/__init__.py",
    "src/normalization.py",
    "src/pillar_construction.py",
    "src/jesi_calculation.py",
    "src/data_cleaning.py",
    "src/data_download.py",
    "src/growth_pillar.py",
    "src/connectivity_pillar.py",
    "src/nonlinear_resilience_scoring.py",
    "src/robustness_tests.py",

    # Tests
    "tests/test_jesi.py",

    # Main pipeline scripts
    "scripts/01_download_growth_data.py",
    "scripts/03_construct_growth_pillar.py",

    "scripts/12_download_productivity_data.py",
    "scripts/20_construct_productivity_pillar.py",

    "scripts/21_download_connectivity_data.py",
    "scripts/25_construct_connectivity_pillar.py",

    "scripts/08_download_resilience_data.py",
    "scripts/11_score_resilience.py",

    "scripts/29_download_autonomy_data.py",
    "scripts/35_construct_autonomy_pillar.py",

    # Final integration
    "scripts/36_calculate_jesi.py",
    "scripts/37_robustness_tests.py",
    "scripts/38_generate_final_jesi_results.py",
    "scripts/39_validate_final_jesi.py",
    "scripts/40_generate_jesi_report.py",
    "scripts/41_update_readme_jesi.py",

    # Final audit
    "scripts/42_final_repository_audit.py",

    # Documentation
    "README.md",
    "LICENSE",
    "requirements.txt",

    # Methodology
    "methodology/JESI_Master_V1.0.md",
]


EXPECTED_OUTPUTS = [
    "data/results/jesi_country_year_2016_2023.csv",
    "data/results/jesi_country_ranking_2016_2023.csv",
    "data/results/jesi_robustness_country_results.csv",
    "data/results/jesi_robustness_correlations.csv",
    "data/results/final_jesi_country_results.csv",
    "data/results/final_jesi_yearly_summary.csv",
    "data/results/JESI_final_research_table.csv",
    "docs/JESI_Final_Results_Report.md",
]


def check_files(file_list, category):
    print(f"\n[{category}]")

    missing = []
    present = []

    for relative_path in file_list:
        path = ROOT / relative_path

        if path.exists():
            print(f"  PASS  {relative_path}")
            present.append(relative_path)
        else:
            print(f"  FAIL  {relative_path}")
            missing.append(relative_path)

    return present, missing


def main():
    print("=" * 72)
    print("JESI FINAL REPOSITORY AUDIT")
    print("JAS Unified Economic Strength Index")
    print("=" * 72)

    print(f"\nRepository root: {ROOT}")

    all_missing = []

    _, missing_required = check_files(
        REQUIRED_FILES,
        "REQUIRED REPOSITORY FILES",
    )
    all_missing.extend(missing_required)

    _, missing_outputs = check_files(
        EXPECTED_OUTPUTS,
        "EXPECTED FINAL OUTPUTS",
    )
    all_missing.extend(missing_outputs)

    print("\n[DIRECTORY CHECKS]")

    directories = [
        "src",
        "scripts",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "docs",
        "methodology",
        ".github/workflows",
    ]

    for directory in directories:
        path = ROOT / directory

        if path.is_dir():
            print(f"  PASS  {directory}/")
        else:
            print(f"  FAIL  {directory}/")
            all_missing.append(directory)

    print("\n[FINAL AUDIT SUMMARY]")
    print("-" * 72)

    if all_missing:
        print("STATUS: FAIL")
        print(f"Missing items: {len(all_missing)}")

        for item in all_missing:
            print(f"  - {item}")

        raise SystemExit(1)

    print("STATUS: GREEN")
    print("All required JESI repository components are present.")
    print("Core pipeline structure: PASS")
    print("Final results structure: PASS")
    print("Documentation structure: PASS")
    print("Methodology structure: PASS")
    print("Test structure: PASS")
    print()
    print("FINAL REPOSITORY AUDIT: GREEN")
    print("No further numbered JESI pipeline scripts are required.")


if __name__ == "__main__":
    main()
