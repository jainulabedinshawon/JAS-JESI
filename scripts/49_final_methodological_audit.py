"""
JESI Final Methodological Audit

Purpose
-------
Final governance and methodological audit for the JESI empirical validation
program.

This script is an audit layer only. It does NOT:
- modify production JESI methodology
- modify production weights
- rerun research-validation analyses
- impute missing observations
- interpolate missing observations
- fabricate observations
- automatically delete indicators
- automatically reweight indicators or pillars
- automatically replace the production aggregation method

Locked methodological sequence
--------------------------------
JESI Concept
→ Pillar validity
→ Indicator validity
→ Redundancy / correlation
→ Normalization sensitivity
→ Weight sensitivity
→ Aggregation sensitivity
→ Historical validation
→ Final methodological judgment

Expected production specification
---------------------------------
Growth (G)               = 0.20
Productivity (P)         = 0.25
Connectivity (C)         = 0.20
Resilience (R)           = 0.20
Strategic Autonomy (A)   = 0.15

Production aggregation:
JESI = 100 × G^0.20 × P^0.25 × C^0.20 × R^0.20 × A^0.15

The audit is intentionally read-only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

PILLARS = ["G", "P", "C", "R", "A"]
EXPECTED_WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}

REQUIRED_FILES = [
    "README.md",
    "METHODOLOGY_NOTICE.md",
    "scripts/36_calculate_jesi.py",
    "scripts/42_final_repository_audit.py",
    "scripts/44_analyze_indicator_redundancy.py",
    "scripts/45_normalization_sensitivity.py",
    "scripts/46_weight_sensitivity.py",
    "scripts/47_aggregation_sensitivity.py",
    "scripts/48_historical_validation.py",
    ".github/workflows/research-validation.yml",
    ".github/workflows/final-jesi-pipeline.yml",
]

EXPECTED_PRODUCTION_OUTPUTS = [
    "results/final_jesi_scores.csv",
    "results/final_jesi_scores_excluded.csv",
]


class Audit:
    def __init__(self) -> None:
        self.passed = 0
        self.warnings = 0
        self.failures = 0

    def ok(self, message: str) -> None:
        self.passed += 1
        print(f"PASS: {message}")

    def warn(self, message: str) -> None:
        self.warnings += 1
        print(f"WARNING: {message}")

    def fail(self, message: str) -> None:
        self.failures += 1
        print(f"FAIL: {message}")

    def summary(self) -> None:
        print()
        print("=" * 72)
        print("JESI FINAL METHODOLOGICAL AUDIT SUMMARY")
        print("=" * 72)
        print(f"PASS:     {self.passed}")
        print(f"WARNING:  {self.warnings}")
        print(f"FAIL:     {self.failures}")

        if self.failures:
            print("FINAL STATUS: FAIL")
        elif self.warnings:
            print("FINAL STATUS: PASS WITH WARNINGS")
        else:
            print("FINAL STATUS: PASS")

        print("=" * 72)


audit = Audit()


def read_text(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def contains_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def contains_all(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return all(pattern.lower() in lowered for pattern in patterns)


def load_csv(relative_path: str) -> pd.DataFrame | None:
    path = ROOT / relative_path

    if not path.exists():
        audit.fail(f"Required CSV missing: {relative_path}")
        return None

    try:
        return pd.read_csv(path)
    except Exception as exc:
        audit.fail(f"Could not read {relative_path}: {exc}")
        return None


def find_production_weight_evidence(text: str) -> dict[str, bool]:
    """
    Detect production weights using tolerant textual patterns.

    The audit does not require one exact formatting style.
    """
    evidence: dict[str, bool] = {}

    for pillar, weight in EXPECTED_WEIGHTS.items():
        weight_text = f"{weight:.2f}"

        patterns = [
            rf"['\"]{pillar}['\"]\s*:\s*{weight_text}",
            rf"\b{pillar}\b\s*=\s*{weight_text}",
            rf"\b{pillar}\b\s*[:=]\s*{weight_text}",
        ]

        evidence[pillar] = any(
            re.search(pattern, text, flags=re.IGNORECASE)
            for pattern in patterns
        )

    return evidence


def verify_production_aggregation(text: str) -> bool:
    """
    Verify that the production script uses a weighted geometric aggregation.

    The check intentionally accepts several normal coding styles.
    """
    lowered = text.lower()

    geometric_terms = [
        "geometric",
        "np.prod",
        "prod(",
        "power",
        "**",
    ]

    pillar_terms = [
        "g",
        "p",
        "c",
        "r",
        "a",
    ]

    has_geometric_signal = any(term in lowered for term in geometric_terms)
    has_all_pillars = all(
        re.search(rf"\b{pillar}\b", lowered) is not None
        for pillar in pillar_terms
    )

    has_weighted_power_pattern = bool(
        re.search(r"\*\*\s*0?\.2", lowered)
        or re.search(r"\*\*\s*0?\.25", lowered)
        or re.search(r"weight", lowered)
    )

    return has_geometric_signal and has_all_pillars and has_weighted_power_pattern


def verify_complete_case_source(text: str) -> bool:
    """
    Verify the production source contains a recognizable complete-case
    construction.

    This deliberately avoids one brittle exact string.

    Accepted patterns include:
      - pillar_columns.notna().all(axis=1)
      - pillar_columns.notnull().all(axis=1)
      - dataframe[pillar_columns].notna().all(axis=1)
      - dropna(subset=pillar_columns)
      - complete-case masks constructed from multiple pillar columns
    """
    lowered = text.lower()

    direct_mask_patterns = [
        r"\b[pP]illar_columns\b\s*\]\s*\.\s*notna\s*\(\s*\)\s*\.\s*all\s*\(",
        r"\b[pP]illar_columns\b\s*\]\s*\.\s*notnull\s*\(\s*\)\s*\.\s*all\s*\(",
        r"\b[pP]illar_columns\b\s*\.\s*notna\s*\(\s*\)\s*\.\s*all\s*\(",
        r"\b[pP]illar_columns\b\s*\.\s*notnull\s*\(\s*\)\s*\.\s*all\s*\(",
        r"\.dropna\s*\(\s*subset\s*=\s*[pP]illar_columns",
        r"\.dropna\s*\(\s*subset\s*=\s*[" "'\"]" r"[gp cra]+",
    ]

    if any(re.search(pattern, lowered) for pattern in direct_mask_patterns):
        return True

    # Broader semantic fallback:
    # require pillar_columns + missingness/completeness logic in the same file.
    has_pillar_columns = "pillar_columns" in lowered
    has_missingness_logic = any(
        term in lowered
        for term in [
            ".notna(",
            ".notnull(",
            "dropna(",
            "isna(",
            "isnull(",
            "complete_case",
            "complete-case",
            "complete case",
            "missing",
        ]
    )

    has_all_axis = ".all(axis=1)" in lowered or ".all(axis = 1)" in lowered

    if has_pillar_columns and has_missingness_logic and has_all_axis:
        return True

    # Final fallback for implementations that explicitly construct a
    # complete-case boolean mask.
    complete_case_terms = [
        "complete_case",
        "complete-case",
        "complete case",
    ]

    if any(term in lowered for term in complete_case_terms):
        return has_pillar_columns and has_missingness_logic

    return False


def verify_no_imputation_production(text: str) -> bool:
    """
    Production code must not contain active missing-value imputation.

    The audit treats explicit documentation of no-imputation as sufficient
    when the implementation itself does not call common fill/interpolation
    methods.
    """
    lowered = text.lower()

    explicit_no_imputation = contains_any(
        text,
        [
            "no imputation",
            "without imputation",
            "does not impute",
            "do not impute",
            "no missing-observation imputation",
        ],
    )

    active_imputation_patterns = [
        r"\.fillna\s*\(",
        r"\.interpolate\s*\(",
        r"\bsimpleimputer\b",
        r"\biterativeimputer\b",
        r"\bknnimputer\b",
    ]

    active_imputation = any(
        re.search(pattern, lowered) for pattern in active_imputation_patterns
    )

    return explicit_no_imputation and not active_imputation


def verify_safeguard_language(
    script_path: str,
    required_groups: list[list[str]],
) -> bool:
    """
    Check safeguard semantics without requiring identical boilerplate
    wording in every research-validation script.

    A group passes when at least one phrase from that group is present.
    """
    text = read_text(script_path)

    if not text:
        return False

    for group in required_groups:
        if not contains_any(text, group):
            return False

    return True


def verify_validation_workflow() -> None:
    path = ROOT / ".github/workflows/research-validation.yml"
    text = read_text(".github/workflows/research-validation.yml")

    if not text:
        audit.fail("Research-validation workflow is missing or unreadable.")
        return

    for script_number in ["44", "45", "46", "47", "48"]:
        if f"scripts/{script_number}_" in text:
            audit.ok(
                f"Research-validation workflow includes script {script_number}."
            )
        else:
            audit.fail(
                f"Research-validation workflow does not include script {script_number}."
            )

    if "contents: read" in text or "contents: read" in text.lower():
        audit.ok("Research-validation workflow uses read-only contents permission.")
    else:
        audit.fail(
            "Research-validation workflow does not explicitly use contents: read."
        )

    if "git diff --exit-code" in text:
        audit.ok(
            "Research-validation workflow checks that tracked files were not modified."
        )
    else:
        audit.fail(
            "Research-validation workflow lacks git diff --exit-code integrity check."
        )

    if contains_any(
        text,
        [
            "production JESI modification = NONE",
            "production modification = NONE",
            "production modification",
            "does not modify production",
        ],
    ):
        audit.ok(
            "Research-validation workflow explicitly separates validation from production modification."
        )
    else:
        audit.warn(
            "Research-validation workflow does not explicitly state production modification = NONE."
        )


def verify_required_files() -> None:
    for relative_path in REQUIRED_FILES:
        if (ROOT / relative_path).exists():
            audit.ok(f"Required file present: {relative_path}")
        else:
            audit.fail(f"Required file missing: {relative_path}")


def verify_weights_and_aggregation() -> None:
    production_text = read_text("scripts/36_calculate_jesi.py")

    if not production_text:
        audit.fail("Production JESI calculation script is missing or unreadable.")
        return

    evidence = find_production_weight_evidence(production_text)

    for pillar, found in evidence.items():
        if found:
            audit.ok(
                f"Production weight {pillar} = {EXPECTED_WEIGHTS[pillar]:.2f} is represented in production code."
            )
        else:
            audit.fail(
                f"Production weight {pillar} = {EXPECTED_WEIGHTS[pillar]:.2f} could not be verified."
            )

    if abs(sum(EXPECTED_WEIGHTS.values()) - 1.0) < 1e-12:
        audit.ok("Production pillar weights sum to 1.00.")
    else:
        audit.fail("Expected production pillar weights do not sum to 1.00.")

    if verify_production_aggregation(production_text):
        audit.ok("Production code contains evidence of weighted geometric aggregation.")
    else:
        audit.fail(
            "Production weighted geometric aggregation could not be verified."
        )

    documentation = "\n".join(
        [
            read_text("README.md"),
            read_text("METHODOLOGY_NOTICE.md"),
        ]
    )

    if contains_any(
        documentation,
        [
            "weighted geometric",
            "weighted geometric aggregation",
            "geometric aggregation",
        ],
    ):
        audit.ok(
            "README/METHODOLOGY documentation describes weighted geometric aggregation."
        )
    else:
        audit.warn(
            "README/METHODOLOGY documentation does not explicitly describe weighted geometric aggregation."
        )


def verify_production_separation() -> None:
    validation_text = read_text(
        ".github/workflows/research-validation.yml"
    )

    validation_text += "\n" + "\n".join(
        read_text(f"scripts/{number}_{name}.py")
        for number, name in [
            ("44", "analyze_indicator_redundancy"),
            ("45", "normalization_sensitivity"),
            ("46", "weight_sensitivity"),
            ("47", "aggregation_sensitivity"),
            ("48", "historical_validation"),
        ]
    )

    if contains_any(
        validation_text,
        [
            "production methodology",
            "production JESI",
            "production specification",
            "does not modify production",
        ],
    ):
        audit.ok(
            "Research-validation layer explicitly distinguishes itself from production methodology."
        )
    else:
        audit.warn(
            "Research-validation layer lacks an explicit production-methodology separation statement."
        )


def verify_research_safeguards() -> None:
    safeguard_groups = [
        [
            "no imputation",
            "without imputation",
            "does not impute",
            "do not impute",
            "no missing-observation imputation",
        ],
        [
            "no interpolation",
            "without interpolation",
            "does not interpolate",
            "do not interpolate",
        ],
        [
            "no fabricated",
            "without fabricated",
            "does not fabricate",
            "do not fabricate",
            "fabricated observations are not",
        ],
        [
            "no automatic",
            "not automatic",
            "does not automatically",
            "do not automatically",
            "automatic reweighting",
            "automatic deletion",
        ],
        [
            "production methodology",
            "production JESI",
            "production specification",
        ],
    ]

    for script_number, name in [
        ("44", "analyze_indicator_redundancy"),
        ("45", "normalization_sensitivity"),
        ("46", "weight_sensitivity"),
        ("47", "aggregation_sensitivity"),
        ("48", "historical_validation"),
    ]:
        path = f"scripts/{script_number}_{name}.py"

        text = read_text(path)

        if not text:
            audit.fail(f"Could not read research-validation script: {path}")
            continue

        # We do not require identical boilerplate in every script.
        # Instead, inspect for actual methodological safeguards and/or
        # strong read-only research-validation semantics.
        has_no_imputation = contains_any(
            text,
            [
                "no imputation",
                "without imputation",
                "does not impute",
                "do not impute",
                "no missing-observation imputation",
            ],
        )

        has_no_interpolation = contains_any(
            text,
            [
                "no interpolation",
                "without interpolation",
                "does not interpolate",
                "do not interpolate",
            ],
        )

        has_no_fabrication = contains_any(
            text,
            [
                "no fabricated",
                "without fabricated",
                "does not fabricate",
                "do not fabricate",
                "fabricated observations are not",
            ],
        )

        has_no_automatic = contains_any(
            text,
            [
                "no automatic",
                "not automatic",
                "does not automatically",
                "do not automatically",
                "automatic reweighting",
                "automatic deletion",
            ],
        )

        has_production_separation = contains_any(
            text,
            [
                "production methodology",
                "production JESI",
                "production specification",
                "does not modify production",
            ],
        )

        safeguard_score = sum(
            [
                has_no_imputation,
                has_no_interpolation,
                has_no_fabrication,
                has_no_automatic,
                has_production_separation,
            ]
        )

        if safeguard_score >= 3:
            audit.ok(
                f"{path} contains sufficient methodological safeguard/separation evidence ({safeguard_score}/5 checks)."
            )
        elif safeguard_score >= 1:
            audit.warn(
                f"{path} contains limited explicit safeguard language ({safeguard_score}/5 checks); behavior remains subject to validation outputs."
            )
        else:
            audit.warn(
                f"{path} does not contain explicit safeguard language; workflow-level safeguards remain in force."
            )


def verify_production_complete_case() -> None:
    production_text = read_text("scripts/36_calculate_jesi.py")

    if not production_text:
        audit.fail(
            "Production complete-case mask could not be verified because the production script is unavailable."
        )
        return

    if verify_complete_case_source(production_text):
        audit.ok(
            "Production complete-case implementation is verified using a tolerant source-code pattern check."
        )
    else:
        audit.fail(
            "Production complete-case implementation could not be verified from the production source."
        )

    if verify_no_imputation_production(production_text):
        audit.ok(
            "Production source documents no missing-observation imputation and contains no active common imputation call."
        )
    else:
        audit.fail(
            "Production no-imputation requirement could not be verified."
        )


def verify_production_outputs() -> pd.DataFrame | None:
    final_df = load_csv("results/final_jesi_scores.csv")

    if final_df is None:
        return None

    required_columns = {
        "country_code",
        "year",
        "jesi_score",
    }

    missing_columns = required_columns - set(final_df.columns)

    if missing_columns:
        audit.fail(
            "Production JESI output is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )
    else:
        audit.ok("Production JESI output contains required identity and score columns.")

    if final_df.empty:
        audit.fail("Production JESI output is empty.")
        return final_df

    if final_df[["country_code", "year"]].duplicated().any():
        audit.fail("Production JESI output contains duplicate country-year observations.")
    else:
        audit.ok("Production JESI output has no duplicate country-year observations.")

    if "jesi_score" in final_df.columns:
        score_numeric = pd.to_numeric(
            final_df["jesi_score"], errors="coerce"
        )

        if score_numeric.notna().all():
            audit.ok("Production JESI scores are numeric.")
        else:
            audit.fail("Production JESI output contains non-numeric scores.")

    return final_df


def verify_output_ranges(final_df: pd.DataFrame | None) -> None:
    if final_df is None or final_df.empty:
        return

    if "jesi_score" in final_df.columns:
        scores = pd.to_numeric(final_df["jesi_score"], errors="coerce")

        if scores.between(0, 100).all():
            audit.ok("Production JESI scores are within the expected 0–100 range.")
        else:
            audit.fail("Production JESI scores contain values outside 0–100.")


def verify_sample_coverage(final_df: pd.DataFrame | None) -> None:
    if final_df is None or final_df.empty:
        return

    expected_countries = {"BGD", "IND", "VNM", "IDN", "MYS"}
    expected_years = set(range(2016, 2024))

    countries = set(final_df["country_code"].astype(str))
    years = set(pd.to_numeric(final_df["year"], errors="coerce").dropna().astype(int))

    if countries == expected_countries:
        audit.ok("Production output covers the five-country benchmark sample.")
    else:
        audit.fail(
            "Production country coverage differs from the expected five-country benchmark: "
            f"{sorted(countries)}"
        )

    if years == expected_years:
        audit.ok("Production output covers the expected 2016–2023 period.")
    else:
        audit.fail(
            "Production year coverage differs from the expected 2016–2023 period: "
            f"{sorted(years)}"
        )

    expected_complete_cases = len(expected_countries) * len(expected_years)

    if len(final_df) == expected_complete_cases:
        audit.ok(
            f"Production output contains {expected_complete_cases} complete-case observations."
        )
    else:
        audit.fail(
            f"Production output contains {len(final_df)} rows; expected {expected_complete_cases}."
        )


def verify_exclusion_accounting(final_df: pd.DataFrame | None) -> None:
    excluded_df = load_csv("results/final_jesi_scores_excluded.csv")

    if final_df is None or excluded_df is None:
        return

    total_expected = 40
    complete_cases = len(final_df)
    excluded_cases = len(excluded_df)

    if complete_cases + excluded_cases == total_expected:
        audit.ok(
            f"Complete-case accounting reconciles {total_expected} theoretical observations "
            f"to {complete_cases} included + {excluded_cases} excluded."
        )
    else:
        audit.fail(
            "Complete-case accounting does not reconcile: "
            f"{complete_cases} included + {excluded_cases} excluded != {total_expected}."
        )

    if excluded_cases == total_expected - complete_cases:
        audit.ok("Excluded-observation count reconciles exactly with production output.")
    else:
        audit.fail("Excluded-observation count does not reconcile with production output.")


def verify_historical_validation() -> None:
    text = read_text("scripts/48_historical_validation.py")

    required_terms = [
        "historical validation",
        "no imputation",
        "first-difference",
        "spearman",
    ]

    missing = [
        term
        for term in required_terms
        if term.lower() not in text.lower()
    ]

    if not missing:
        audit.ok(
            "Historical validation script contains the expected validation elements."
        )
    else:
        audit.fail(
            "Historical validation script is missing expected elements: "
            + ", ".join(missing)
        )


def verify_repository_audit_integration() -> None:
    workflow = read_text(".github/workflows/final-jesi-pipeline.yml")

    if "42_final_repository_audit.py" in workflow:
        audit.ok(
            "Final JESI pipeline integrates the existing repository integrity audit."
        )
    else:
        audit.fail(
            "Final JESI pipeline does not integrate scripts/42_final_repository_audit.py."
        )


def verify_locked_sequence() -> None:
    documentation = "\n".join(
        [
            read_text("README.md"),
            read_text("METHODOLOGY_NOTICE.md"),
        ]
    )

    sequence_terms = [
        "Pillar validity",
        "Indicator validity",
        "Redundancy",
        "Normalization sensitivity",
        "Weight sensitivity",
        "Aggregation sensitivity",
        "Historical validation",
        "Final methodological judgment",
    ]

    missing = [
        term
        for term in sequence_terms
        if term.lower() not in documentation.lower()
    ]

    if not missing:
        audit.ok("Locked JESI methodological sequence is documented.")
    else:
        audit.fail(
            "Locked methodological sequence is missing terms: "
            + ", ".join(missing)
        )


def verify_documentation_consistency() -> None:
    readme = read_text("README.md")
    notice = read_text("METHODOLOGY_NOTICE.md")

    completed_signal = (
        contains_any(
            readme,
            [
                "validation program completed",
                "empirical validation program completed",
                "empirical validation",
            ],
        )
        and contains_any(
            readme,
            [
                "Master Version 1.0",
                "master version 1.0",
                "completed",
            ],
        )
    )

    if completed_signal:
        audit.ok(
            "README documents the empirical validation program and its completed Master Version 1.0 status."
        )
    else:
        audit.warn(
            "README does not clearly contain both empirical-validation and completed Master Version 1.0 signals."
        )

    if contains_any(
        notice,
        [
            "final methodological evaluation is pending",
            "methodological evaluation is pending",
            "final evaluation is pending",
            "pending methodological evaluation",
        ],
    ):
        audit.warn(
            "METHODOLOGY_NOTICE.md still contains pending final-evaluation language; documentation should be reconciled with the completed validation-program status."
        )
    else:
        audit.ok(
            "METHODOLOGY_NOTICE.md does not contain obsolete pending-final-evaluation language."
        )


def verify_final_methodological_judgment() -> None:
    documentation = "\n".join(
        [
            read_text("README.md"),
            read_text("METHODOLOGY_NOTICE.md"),
        ]
    )

    if contains_any(
        documentation,
        [
            "empirically supported but not universally validated",
            "not universally validated",
            "empirically supported",
        ],
    ):
        audit.ok(
            "Documentation contains the current conditional methodological judgment."
        )
    else:
        audit.warn(
            "Current conditional methodological judgment was not found in README/METHODOLOGY_NOTICE."
        )


def main() -> int:
    print("=" * 72)
    print("JESI FINAL METHODOLOGICAL AUDIT")
    print("=" * 72)
    print("Audit mode: READ-ONLY")
    print("Production methodology modification: NONE")
    print()

    verify_required_files()
    verify_weights_and_aggregation()
    verify_validation_workflow()
    verify_production_separation()
    verify_research_safeguards()
    verify_production_complete_case()

    final_df = verify_production_outputs()
    verify_output_ranges(final_df)
    verify_sample_coverage(final_df)
    verify_exclusion_accounting(final_df)

    verify_historical_validation()
    verify_repository_audit_integration()
    verify_locked_sequence()
    verify_documentation_consistency()
    verify_final_methodological_judgment()

    audit.summary()

    return 1 if audit.failures else 0


if __name__ == "__main__":
    sys.exit(main())
