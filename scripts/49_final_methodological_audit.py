"""
JAS Unified Economic Strength Index (JESI)
Final Methodological Audit

Repository-level methodological compliance audit.

This audit does NOT:
- rerun Scripts 44-48
- modify production JESI
- modify weights
- modify normalization
- modify aggregation
- impute data
- remove indicators
- reweight pillars

Audit scope:
1. Production specification consistency
2. Research-validation separation
3. No-imputation safeguards
4. Reproducibility
5. Evidence integrity
6. Documentation consistency
7. Workflow isolation
"""

from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}

EXPECTED_COUNTRIES = {
    "Bangladesh",
    "India",
    "Indonesia",
    "Malaysia",
    "Vietnam",
}

EXPECTED_YEARS = set(range(2016, 2024))

EXPECTED_OBSERVATIONS = 40
EXPECTED_COMPLETE_CASES = 34


PRODUCTION_FILES = [
    "scripts/36_calculate_jesi.py",
    "data/results/jesi_country_year_2016_2023.csv",
    "data/results/jesi_excluded_country_years_2016_2023.csv",
    "data/results/jesi_sample_coverage_2016_2023.csv",
]

VALIDATION_SCRIPTS = [
    "scripts/44_analyze_indicator_redundancy.py",
    "scripts/45_normalization_sensitivity.py",
    "scripts/46_weight_sensitivity.py",
    "scripts/47_aggregation_sensitivity.py",
    "scripts/48_historical_validation.py",
]

DOCUMENTATION_FILES = [
    "README.md",
    "methodology/JESI_Master_V1.0.md",
    "docs/JESI_Final_Results_Report.md",
    "METHODOLOGY_NOTICE.md",
]

HARD_FAILURES = []
WARNINGS = []
PASSES = []


def fail(message):
    HARD_FAILURES.append(message)


def warn(message):
    WARNINGS.append(message)


def passed(message):
    PASSES.append(message)


def read(path):
    full = ROOT / path

    if not full.exists():
        fail(f"Missing required file: {path}")
        return ""

    return full.read_text(encoding="utf-8")


def main():

    print("=" * 78)
    print("JAS-JESI FINAL METHODOLOGICAL AUDIT")
    print("=" * 78)

    # ================================================================
    # 1. REQUIRED REPOSITORY STRUCTURE
    # ================================================================

    required_files = (
        PRODUCTION_FILES
        + VALIDATION_SCRIPTS
        + DOCUMENTATION_FILES
        + [
            ".github/workflows/research-validation.yml",
            ".github/workflows/final-jesi.yml",
            "scripts/42_final_repository_audit.py",
        ]
    )

    for path in required_files:

        if (ROOT / path).exists():

            passed(
                f"Required file present: {path}"
            )

        else:

            fail(
                f"Required file missing: {path}"
            )

    # ================================================================
    # 2. LOAD CORE DOCUMENTATION
    # ================================================================

    production = read(
        "scripts/36_calculate_jesi.py"
    )

    master = read(
        "methodology/JESI_Master_V1.0.md"
    )

    readme = read(
        "README.md"
    )

    final_report = read(
        "docs/JESI_Final_Results_Report.md"
    )

    notice = read(
        "METHODOLOGY_NOTICE.md"
    )

    # ================================================================
    # 3. PRODUCTION WEIGHTS
    # ================================================================

    expected_weights = {
        "G": r"G\s*[=:]\s*0\.20",
        "P": r"P\s*[=:]\s*0\.25",
        "C": r"C\s*[=:]\s*0\.20",
        "R": r"R\s*[=:]\s*0\.20",
        "A": r"A\s*[=:]\s*0\.15",
    }

    for pillar, pattern in expected_weights.items():

        if re.search(pattern, production):

            passed(
                f"Production weight {pillar} = "
                f"{WEIGHTS[pillar]:.2f} verified."
            )

        else:

            fail(
                f"Production weight for {pillar} "
                "could not be verified."
            )

    if np.isclose(
        sum(WEIGHTS.values()),
        1.0,
    ):

        passed(
            "Production weights sum to 1."
        )

    else:

        fail(
            "Production weights do not sum to 1."
        )

    # ================================================================
    # 4. PRODUCTION AGGREGATION
    # ================================================================

    if re.search(
        r"100\s*\*\s*weighted_geometric_mean",
        production,
    ):

        passed(
            "Production calculation uses "
            "weighted geometric aggregation."
        )

    else:

        fail(
            "Production calculation does not visibly "
            "use weighted geometric aggregation."
        )

    for label, content in [
        ("README", readme),
        ("Master methodology", master),
        ("Final results report", final_report),
    ]:

        if "weighted geometric" in content.lower():

            passed(
                f"{label} documents weighted geometric "
                "production aggregation."
            )

        else:

            fail(
                f"{label} does not document weighted "
                "geometric production aggregation."
            )

    # ================================================================
    # 5. RESEARCH VALIDATION SEPARATION
    # ================================================================

    validation_workflow = read(
        ".github/workflows/research-validation.yml"
    )

    for script in VALIDATION_SCRIPTS:

        filename = Path(script).name

        if filename in validation_workflow:

            passed(
                f"Research-validation workflow includes "
                f"{filename}."
            )

        else:

            fail(
                f"Research-validation workflow does not "
                f"include {filename}."
            )

    if re.search(
        r"permissions:\s*\n\s*contents:\s*read",
        validation_workflow,
    ):

        passed(
            "Research-validation workflow has "
            "read-only contents permission."
        )

    else:

        fail(
            "Research-validation workflow is not "
            "explicitly read-only."
        )

    if "git diff --exit-code" in validation_workflow:

        passed(
            "Research-validation workflow checks "
            "for tracked-file modification."
        )

    else:

        fail(
            "Research-validation workflow lacks "
            "a tracked-file modification check."
        )

    if "Production JESI modification:  NONE" in validation_workflow:

        passed(
            "Production modification is explicitly "
            "declared as NONE."
        )

    else:

        warn(
            "Production-modification statement was not found "
            "in the expected form."
        )

    # ================================================================
    # 6. METHODOLOGICAL SAFEGUARDS
    # ================================================================

    safeguards = [
        "No imputation",
        "No interpolation",
        "No fabricated",
        "No automatic",
        "production methodology",
    ]

    for script in VALIDATION_SCRIPTS:

        content = read(script)

        lower = content.lower()

        missing = [
            phrase
            for phrase in safeguards
            if phrase.lower() not in lower
        ]

        if missing:

            warn(
                f"{script} does not explicitly contain "
                f"all standard safeguard language: "
                f"{', '.join(missing)}"
            )

        else:

            passed(
                f"Safeguard language present in {script}."
            )

    # ================================================================
    # 7. PRODUCTION COMPLETE-CASE LOGIC
    # ================================================================

    if (
        "No missing observation is imputed"
        in production
    ):

        passed(
            "Production explicitly documents "
            "no missing-observation imputation."
        )

    else:

        warn(
            "Production does not contain the exact "
            "no-imputation statement."
        )

    if "complete-case" in production.lower():

        passed(
            "Production explicitly documents "
            "complete-case methodology."
        )

    else:

        warn(
            "Production does not explicitly contain "
            "complete-case terminology."
        )

    if (
        "jesI[pillar_columns].notna().all(axis=1)"
        in production
    ):

        passed(
            "Production complete-case mask is "
            "explicitly implemented."
        )

    else:

        fail(
            "Production complete-case mask could "
            "not be verified."
        )

    # ================================================================
    # 8. PRODUCTION OUTPUT INTEGRITY
    # ================================================================

    output_path = (
        ROOT
        / "data/results/"
        / "jesi_country_year_2016_2023.csv"
    )

    if output_path.exists():

        try:

            df = pd.read_csv(
                output_path
            )

            # --------------------------------------------------------
            # Row count
            # --------------------------------------------------------

            if len(df) != EXPECTED_COMPLETE_CASES:

                fail(
                    "Production country-year output has "
                    f"{len(df)} rows; expected "
                    f"{EXPECTED_COMPLETE_CASES}."
                )

            else:

                passed(
                    "Production country-year output "
                    "contains 34 complete-case observations."
                )

            # --------------------------------------------------------
            # Countries
            # --------------------------------------------------------

            if set(df["country"]) != EXPECTED_COUNTRIES:

                fail(
                    "Production output country set does "
                    "not match the five-country benchmark."
                )

            else:

                passed(
                    "Production output country set "
                    "matches the benchmark."
                )

            # --------------------------------------------------------
            # Years
            # --------------------------------------------------------

            years = set(
                pd.to_numeric(
                    df["year"],
                    errors="raise",
                ).astype(int)
            )

            if not years.issubset(
                EXPECTED_YEARS
            ):

                fail(
                    "Production output contains years "
                    "outside 2016–2023."
                )

            else:

                passed(
                    "Production output years are "
                    "within 2016–2023."
                )

            # --------------------------------------------------------
            # Duplicate country-years
            # --------------------------------------------------------

            if df.duplicated(
                [
                    "country_code",
                    "year",
                ]
            ).any():

                fail(
                    "Duplicate production "
                    "country-year observations detected."
                )

            else:

                passed(
                    "No duplicate production "
                    "country-year observations detected."
                )

            # --------------------------------------------------------
            # Pillar ranges
            # --------------------------------------------------------

            for column in [
                "G",
                "P",
                "C",
                "R",
                "A",
            ]:

                if column not in df.columns:

                    fail(
                        f"Production output missing "
                        f"pillar column {column}."
                    )

                    continue

                invalid = (
                    (df[column] <= 0)
                    | (df[column] > 1)
                ).any()

                if invalid:

                    fail(
                        f"Production pillar {column} "
                        "contains values outside (0, 1]."
                    )

                else:

                    passed(
                        f"Production pillar {column} "
                        "is within (0, 1]."
                    )

            # --------------------------------------------------------
            # Formula reproduction
            # --------------------------------------------------------

            if "JESI" not in df.columns:

                fail(
                    "Production output missing JESI column."
                )

            else:

                expected = (
                    100
                    * np.exp(
                        sum(
                            WEIGHTS[p]
                            * np.log(
                                df[p].astype(float)
                            )
                            for p in [
                                "G",
                                "P",
                                "C",
                                "R",
                                "A",
                            ]
                        )
                    )
                )

                actual = df[
                    "JESI"
                ].astype(float)

                max_error = float(
                    np.max(
                        np.abs(
                            expected - actual
                        )
                    )
                )

                if max_error > 1e-9:

                    fail(
                        "Production JESI values do not "
                        "reproduce the documented formula; "
                        f"max error={max_error:.3e}."
                    )

                else:

                    passed(
                        "Production JESI values reproduce "
                        "the documented formula."
                    )

        except Exception as exc:

            fail(
                "Unable to validate production output: "
                f"{exc}"
            )

    # ================================================================
    # 9. COVERAGE RECONCILIATION
    # ================================================================

    coverage_path = (
        ROOT
        / "data/results/"
        / "jesi_sample_coverage_2016_2023.csv"
    )

    if coverage_path.exists():

        try:

            coverage = pd.read_csv(
                coverage_path
            )

            row = coverage.iloc[0]

            expected_fields = {
                "theoretical_observations": 40,
                "complete_observations": 34,
                "excluded_observations": 6,
            }

            for column, expected_value in expected_fields.items():

                actual = int(
                    row[column]
                )

                if actual != expected_value:

                    fail(
                        f"Coverage field {column}="
                        f"{actual}; expected "
                        f"{expected_value}."
                    )

                else:

                    passed(
                        f"Coverage field {column} "
                        f"matches expected value "
                        f"{expected_value}."
                    )

        except Exception as exc:

            fail(
                "Unable to validate sample coverage: "
                f"{exc}"
            )

    # ================================================================
    # 10. EXCLUSION ACCOUNTING
    # ================================================================

    excluded_path = (
        ROOT
        / "data/results/"
        / "jesi_excluded_country_years_2016_2023.csv"
    )

    if excluded_path.exists():

        try:

            excluded = pd.read_csv(
                excluded_path
            )

            expected_excluded = (
                EXPECTED_OBSERVATIONS
                - EXPECTED_COMPLETE_CASES
            )

            if len(excluded) != expected_excluded:

                fail(
                    "Excluded-observation report contains "
                    f"{len(excluded)} rows; expected "
                    f"{expected_excluded}."
                )

            else:

                passed(
                    "Excluded-observation report reconciles "
                    "with the 40→34 complete-case sample."
                )

        except Exception as exc:

            fail(
                "Unable to validate excluded-observation "
                f"report: {exc}"
            )

    # ================================================================
    # 11. HISTORICAL VALIDATION
    # ================================================================

    historical = read(
        "scripts/48_historical_validation.py"
    )

    for phrase in [
        "Historical validation",
        "No imputation",
        "first-difference",
        "Spearman",
    ]:

        if phrase.lower() in historical.lower():

            passed(
                "Historical validation contains "
                f"documented element: {phrase}"
            )

        else:

            fail(
                "Historical validation is missing "
                f"documented element: {phrase}"
            )

    # ================================================================
    # 12. EXISTING REPOSITORY AUDIT
    # ================================================================

    final_workflow = read(
        ".github/workflows/final-jesi.yml"
    )

    if (
        "scripts/42_final_repository_audit.py"
        in final_workflow
    ):

        passed(
            "Final JESI workflow includes "
            "repository integrity audit (42)."
        )

    else:

        fail(
            "Final JESI workflow does not include "
            "repository integrity audit (42)."
        )

    # ================================================================
    # 13. DOCUMENTATION STATUS CONSISTENCY
    # ================================================================

    combined_master = (
        readme
        + "\n"
        + master
    )

    if (
        "empirical validation program has now been completed"
        in combined_master.lower()
    ):

        passed(
            "README/Master documentation states "
            "validation completion."
        )

    else:

        warn(
            "README/Master documentation does not "
            "contain the expected validation-completion statement."
        )

    # Important documentation conflict found during repository review.
    if (
        "remains subject to:" in notice.lower()
        and
        "final methodological evaluation" in notice.lower()
    ):

        warn(
            "METHODOLOGY_NOTICE.md still describes final "
            "methodological evaluation as pending, while "
            "README/Master V1.0 describe the validation program "
            "as completed. Documentation status should be reconciled."
        )

    else:

        passed(
            "Methodology notice does not contain a "
            "conflicting pending-evaluation statement."
        )

    # ================================================================
    # 14. LOCKED METHODOLOGICAL SEQUENCE
    # ================================================================

    sequence_pattern = (
        r"JESI Concept"
        r".*Pillar validity"
        r".*Indicator validity"
        r".*Redundancy"
        r".*Normalization"
        r".*Weight"
        r".*Aggregation"
        r".*Historical validation"
        r".*Final methodological judgment"
    )

    if re.search(
        sequence_pattern,
        combined_master,
        flags=re.I | re.S,
    ):

        passed(
            "Locked methodological sequence is "
            "documented in the repository."
        )

    else:

        fail(
            "Locked methodological sequence could "
            "not be verified."
        )

    # ================================================================
    # 15. FINAL STATUS
    # ================================================================

    print()
    print("=" * 78)
    print("AUDIT RESULTS")
    print("=" * 78)

    for item in PASSES:
        print(
            f"PASS: {item}"
        )

    for item in WARNINGS:
        print(
            f"WARNING: {item}"
        )

    for item in HARD_FAILURES:
        print(
            f"FAIL: {item}"
        )

    print()
    print("=" * 78)

    print(
        f"PASS COUNT: {len(PASSES)}"
    )

    print(
        f"WARNING COUNT: {len(WARNINGS)}"
    )

    print(
        f"FAIL COUNT: {len(HARD_FAILURES)}"
    )

    print("=" * 78)

    if HARD_FAILURES:

        print(
            "FINAL STATUS: FAIL"
        )

        return 1

    if WARNINGS:

        print(
            "FINAL STATUS: PASS WITH DOCUMENTATION WARNINGS"
        )

        return 0

    print(
        "FINAL STATUS: CLEAN"
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
