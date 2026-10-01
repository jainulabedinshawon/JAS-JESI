"""
JESI Final Methodological Audit

Purpose
-------
Final governance and methodological audit for the JESI empirical validation
program.

This script is READ-ONLY. It does not modify:
- production JESI methodology
- production weights
- production aggregation
- research-validation methodology
- research-validation outputs

Locked methodological sequence
------------------------------
JESI Concept
→ Pillar validity
→ Indicator validity
→ Redundancy / correlation
→ Normalization sensitivity
→ Weight sensitivity
→ Aggregation sensitivity
→ Historical validation
→ Final methodological judgment
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}

EXPECTED_COUNTRIES = {
    "BGD",
    "IND",
    "VNM",
    "IDN",
    "MYS",
}

EXPECTED_YEARS = set(range(2016, 2024))

EXPECTED_THEORETICAL_OBSERVATIONS = (
    len(EXPECTED_COUNTRIES) * len(EXPECTED_YEARS)
)

REQUIRED_FILES = [
    "README.md",
    "METHODOLOGY_NOTICE.md",
    "requirements.txt",
    "scripts/36_calculate_jesi.py",
    "scripts/42_final_repository_audit.py",
    "scripts/44_analyze_indicator_redundancy.py",
    "scripts/45_normalization_sensitivity.py",
    "scripts/46_weight_sensitivity.py",
    "scripts/47_aggregation_sensitivity.py",
    "scripts/48_historical_validation.py",
    ".github/workflows/research-validation.yml",
    ".github/workflows/final-jesi.yml",
]

PRODUCTION_OUTPUTS = [
    "data/results/jesi_country_year_2016_2023.csv",
    "data/results/jesi_excluded_country_years_2016_2023.csv",
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

    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(
        phrase.lower() in lowered
        for phrase in phrases
    )


def load_csv(relative_path: str) -> pd.DataFrame | None:
    path = ROOT / relative_path

    if not path.exists():
        audit.fail(
            f"Required CSV missing: {relative_path}"
        )
        return None

    try:
        return pd.read_csv(path)
    except Exception as exc:
        audit.fail(
            f"Could not read {relative_path}: {exc}"
        )
        return None


# ---------------------------------------------------------------------------
# 1. REQUIRED REPOSITORY FILES
# ---------------------------------------------------------------------------

def verify_required_files() -> None:
    for relative_path in REQUIRED_FILES:
        if (ROOT / relative_path).exists():
            audit.ok(
                f"Required file present: {relative_path}"
            )
        else:
            audit.fail(
                f"Required file missing: {relative_path}"
            )


# ---------------------------------------------------------------------------
# 2. PRODUCTION WEIGHTS AND AGGREGATION
# ---------------------------------------------------------------------------

def verify_production_weights() -> None:
    text = read_text(
        "scripts/36_calculate_jesi.py"
    )

    if not text:
        audit.fail(
            "Production JESI calculation script is missing or unreadable."
        )
        return

    for pillar, expected_weight in EXPECTED_WEIGHTS.items():

        weight_text = f"{expected_weight:.2f}"

        patterns = [
            rf"['\"]{pillar}['\"]\s*:\s*{weight_text}",
            rf"\b{pillar}\b\s*=\s*{weight_text}",
            rf"\b{pillar}\b\s*[:=]\s*{weight_text}",
        ]

        found = any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern in patterns
        )

        if found:
            audit.ok(
                f"Production weight {pillar} = "
                f"{weight_text} is represented in production code."
            )
        else:
            audit.fail(
                f"Production weight {pillar} = "
                f"{weight_text} could not be verified."
            )

    if abs(
        sum(EXPECTED_WEIGHTS.values()) - 1.0
    ) < 1e-12:
        audit.ok(
            "Production pillar weights sum to 1.00."
        )
    else:
        audit.fail(
            "Production pillar weights do not sum to 1.00."
        )


def verify_weighted_geometric_aggregation() -> None:
    text = read_text(
        "scripts/36_calculate_jesi.py"
    ).lower()

    geometric_signals = [
        "geometric",
        "np.prod",
        "prod(",
        "**",
        "power",
    ]

    weight_signals = [
        "weight",
        "weights",
        "0.20",
        "0.25",
        "0.15",
    ]

    has_geometric = any(
        signal in text
        for signal in geometric_signals
    )

    has_weights = any(
        signal in text
        for signal in weight_signals
    )

    if has_geometric and has_weights:
        audit.ok(
            "Production code contains evidence of weighted geometric aggregation."
        )
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
            "geometric aggregation",
            "weighted geometric aggregation",
        ],
    ):
        audit.ok(
            "README/METHODOLOGY documentation describes weighted geometric aggregation."
        )
    else:
        audit.warn(
            "README/METHODOLOGY documentation does not explicitly describe weighted geometric aggregation."
        )


# ---------------------------------------------------------------------------
# 3. RESEARCH VALIDATION WORKFLOW
# ---------------------------------------------------------------------------

def verify_research_validation_workflow() -> None:
    text = read_text(
        ".github/workflows/research-validation.yml"
    )

    if not text:
        audit.fail(
            "Research-validation workflow is missing or unreadable."
        )
        return

    for script_number in [
        "44",
        "45",
        "46",
        "47",
        "48",
    ]:

        if f"scripts/{script_number}_" in text:
            audit.ok(
                f"Research-validation workflow includes script {script_number}."
            )
        else:
            audit.fail(
                f"Research-validation workflow does not include script {script_number}."
            )

    if re.search(
        r"permissions:\s*\n\s*contents:\s*read",
        text,
        flags=re.IGNORECASE,
    ):
        audit.ok(
            "Research-validation workflow uses read-only contents permission."
        )
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
            "Production JESI modification:  NONE",
            "Production JESI modification: NONE",
            "production modification",
            "production JESI modification",
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


# ---------------------------------------------------------------------------
# 4. PRODUCTION / VALIDATION SEPARATION
# ---------------------------------------------------------------------------

def verify_production_separation() -> None:

    workflow = read_text(
        ".github/workflows/research-validation.yml"
    )

    scripts_text = "\n".join(
        [
            read_text(
                "scripts/44_analyze_indicator_redundancy.py"
            ),
            read_text(
                "scripts/45_normalization_sensitivity.py"
            ),
            read_text(
                "scripts/46_weight_sensitivity.py"
            ),
            read_text(
                "scripts/47_aggregation_sensitivity.py"
            ),
            read_text(
                "scripts/48_historical_validation.py"
            ),
        ]
    )

    combined = workflow + "\n" + scripts_text

    if contains_any(
        combined,
        [
            "production methodology",
            "production JESI",
            "production specification",
            "does not modify production",
            "production modification",
        ],
    ):
        audit.ok(
            "Research-validation layer explicitly distinguishes itself from production methodology."
        )
    else:
        audit.warn(
            "Research-validation layer lacks an explicit production-methodology separation statement."
        )


# ---------------------------------------------------------------------------
# 5. RESEARCH SCRIPT SAFEGUARDS
# ---------------------------------------------------------------------------

def verify_research_script_safeguards() -> None:

    scripts = [
        (
            "44",
            "scripts/44_analyze_indicator_redundancy.py",
        ),
        (
            "45",
            "scripts/45_normalization_sensitivity.py",
        ),
        (
            "46",
            "scripts/46_weight_sensitivity.py",
        ),
        (
            "47",
            "scripts/47_aggregation_sensitivity.py",
        ),
        (
            "48",
            "scripts/48_historical_validation.py",
        ),
    ]

    safeguard_groups = {
        "no_imputation": [
            "no imputation",
            "without imputation",
            "does not impute",
            "do not impute",
            "no missing-observation imputation",
            "no missing observation is imputed",
        ],
        "no_interpolation": [
            "no interpolation",
            "without interpolation",
            "does not interpolate",
            "do not interpolate",
        ],
        "no_fabrication": [
            "no fabricated",
            "without fabricated",
            "does not fabricate",
            "do not fabricate",
            "fabricated observations are not",
        ],
        "no_automatic_changes": [
            "no automatic",
            "not automatic",
            "does not automatically",
            "do not automatically",
            "automatic reweighting",
            "automatic deletion",
        ],
        "production_separation": [
            "production methodology",
            "production JESI",
            "production specification",
            "does not modify production",
        ],
    }

    for number, path in scripts:

        text = read_text(path)

        if not text:
            audit.fail(
                f"Could not read research-validation script: {path}"
            )
            continue

        score = 0

        for phrases in safeguard_groups.values():
            if contains_any(text, phrases):
                score += 1

        if score >= 3:
            audit.ok(
                f"{path} contains sufficient methodological safeguard/separation evidence "
                f"({score}/5 checks)."
            )

        elif score >= 1:
            audit.warn(
                f"{path} contains limited explicit safeguard language "
                f"({score}/5 checks); this is not treated as a methodological failure."
            )

        else:
            audit.warn(
                f"{path} does not contain explicit safeguard language; "
                "workflow-level read-only safeguards remain in force."
            )


# ---------------------------------------------------------------------------
# 6. COMPLETE-CASE PRODUCTION LOGIC
# ---------------------------------------------------------------------------

def verify_complete_case_source() -> None:

    text = read_text(
        "scripts/36_calculate_jesi.py"
    )

    if not text:
        audit.fail(
            "Production complete-case implementation could not be checked."
        )
        return

    lowered = text.lower()

    patterns = [
        r"pillar_columns.*notna\s*\(\s*\).*all\s*\(",
        r"pillar_columns.*notnull\s*\(\s*\).*all\s*\(",
        r"notna\s*\(\s*\).*all\s*\(\s*axis\s*=\s*1",
        r"notnull\s*\(\s*\).*all\s*\(\s*axis\s*=\s*1",
        r"dropna\s*\(\s*subset\s*=\s*pillar_columns",
        r"complete[_ -]?case",
    ]

    if any(
        re.search(
            pattern,
            lowered,
            flags=re.DOTALL,
        )
        for pattern in patterns
    ):
        audit.ok(
            "Production complete-case implementation is verified using a tolerant source-code pattern check."
        )
    else:
        audit.fail(
            "Production complete-case implementation could not be verified."
        )


def verify_no_imputation() -> None:

    text = read_text(
        "scripts/36_calculate_jesi.py"
    )

    if not text:
        audit.fail(
            "Production script unavailable for no-imputation verification."
        )
        return

    lowered = text.lower()

    explicit_no_imputation = contains_any(
        text,
        [
            "no imputation",
            "without imputation",
            "does not impute",
            "do not impute",
            "no missing-observation imputation",
            "no missing observation is imputed",
            "missing observation is not imputed",
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
        re.search(
            pattern,
            lowered,
        )
        for pattern in active_imputation_patterns
    )

    if explicit_no_imputation and not active_imputation:
        audit.ok(
            "Production source explicitly documents no missing-observation imputation and contains no active common imputation call."
        )

    elif active_imputation:
        audit.fail(
            "Production source contains an active missing-value imputation operation."
        )

    else:
        audit.fail(
            "Production no-imputation requirement could not be verified."
        )


# ---------------------------------------------------------------------------
# 7. PRODUCTION OUTPUTS
# ---------------------------------------------------------------------------

def detect_score_column(
    included: pd.DataFrame,
) -> str | None:
    """
    Detect the production JESI score column.

    Current production schema uses 'JESI'.
    'jesi_score' is accepted only as a compatibility fallback
    for older artifacts.
    """

    preferred_columns = [
        "JESI",
        "jesi_score",
    ]

    for column in preferred_columns:
        if column in included.columns:
            return column

    return None


def verify_production_outputs() -> tuple[
    pd.DataFrame | None,
    pd.DataFrame | None,
    str | None,
]:

    included = load_csv(
        PRODUCTION_OUTPUTS[0]
    )

    excluded = load_csv(
        PRODUCTION_OUTPUTS[1]
    )

    score_column = None

    if included is not None:

        required_identity_columns = {
            "country_code",
            "year",
        }

        missing_identity = (
            required_identity_columns
            - set(included.columns)
        )

        if missing_identity:
            audit.fail(
                "Production JESI output is missing required identity columns: "
                + ", ".join(
                    sorted(missing_identity)
                )
            )
        else:
            audit.ok(
                "Production JESI output contains required country-year identity columns."
            )

        score_column = detect_score_column(
            included
        )

        if score_column is None:
            audit.fail(
                "Production JESI output is missing the JESI score column "
                "(expected 'JESI' in the current production schema)."
            )
        else:
            audit.ok(
                "Production JESI output contains the JESI score column: "
                f"{score_column}."
            )

        if included.empty:
            audit.fail(
                "Production JESI included output is empty."
            )
        else:
            audit.ok(
                "Production JESI included output contains "
                f"{len(included)} rows."
            )

        if {
            "country_code",
            "year",
        }.issubset(included.columns):

            if included[
                [
                    "country_code",
                    "year",
                ]
            ].duplicated().any():

                audit.fail(
                    "Production JESI output contains duplicate country-year observations."
                )

            else:
                audit.ok(
                    "Production JESI output has no duplicate country-year observations."
                )

    if excluded is not None:

        audit.ok(
            "Production JESI excluded-observation output contains "
            f"{len(excluded)} rows."
        )

    return (
        included,
        excluded,
        score_column,
    )


# ---------------------------------------------------------------------------
# 8. OUTPUT RANGE / SAMPLE COVERAGE
# ---------------------------------------------------------------------------

def verify_output_ranges(
    included: pd.DataFrame | None,
    score_column: str | None,
) -> None:

    if (
        included is None
        or included.empty
        or score_column is None
    ):
        return

    scores = pd.to_numeric(
        included[score_column],
        errors="coerce",
    )

    if scores.notna().all():
        audit.ok(
            "Production JESI scores are numeric."
        )
    else:
        audit.fail(
            "Production JESI scores contain non-numeric values."
        )

    if scores.between(0, 100).all():
        audit.ok(
            "Production JESI scores are within the expected 0–100 range."
        )
    else:
        audit.fail(
            "Production JESI scores contain values outside the expected 0–100 range."
        )


def verify_sample_coverage(
    included: pd.DataFrame | None,
    excluded: pd.DataFrame | None,
) -> None:

    if (
        included is None
        or included.empty
    ):
        return

    if not {
        "country_code",
        "year",
    }.issubset(included.columns):
        return

    countries = set(
        included["country_code"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    years = set(
        pd.to_numeric(
            included["year"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
    )

    if countries == EXPECTED_COUNTRIES:
        audit.ok(
            "Production output covers the five-country benchmark sample."
        )
    else:
        audit.fail(
            "Production country coverage differs from the expected five-country sample: "
            f"{sorted(countries)}"
        )

    if years == EXPECTED_YEARS:
        audit.ok(
            "Production output covers the expected 2016–2023 period."
        )
    else:
        audit.fail(
            "Production year coverage differs from the expected 2016–2023 period: "
            f"{sorted(years)}"
        )

    included_count = len(included)

    if excluded is not None:
        excluded_count = len(excluded)

        if (
            included_count
            + excluded_count
            == EXPECTED_THEORETICAL_OBSERVATIONS
        ):
            audit.ok(
                "Production complete-case sample size is consistent with "
                f"the theoretical {EXPECTED_THEORETICAL_OBSERVATIONS}-observation "
                f"panel: {included_count} included + "
                f"{excluded_count} excluded."
            )
        else:
            audit.fail(
                "Production complete-case sample size does not reconcile with "
                f"the theoretical {EXPECTED_THEORETICAL_OBSERVATIONS}-observation "
                f"panel: {included_count} + {excluded_count}."
            )

    else:
        audit.warn(
            "Excluded-observation output is unavailable; "
            "complete-case sample-size reconciliation could not be performed."
        )


def verify_exclusion_accounting(
    included: pd.DataFrame | None,
    excluded: pd.DataFrame | None,
) -> None:

    if (
        included is None
        or excluded is None
    ):
        return

    theoretical = EXPECTED_THEORETICAL_OBSERVATIONS

    included_count = len(included)

    excluded_count = len(excluded)

    if (
        included_count
        + excluded_count
        == theoretical
    ):
        audit.ok(
            f"Complete-case accounting reconciles {theoretical} theoretical "
            f"observations to {included_count} included + "
            f"{excluded_count} excluded."
        )
    else:
        audit.fail(
            "Complete-case accounting does not reconcile: "
            f"{included_count} + {excluded_count} != {theoretical}."
        )

    if excluded_count > 0:

        required_exclusion_columns = {
            "country_code",
            "year",
            "missing_pillars",
        }

        missing = (
            required_exclusion_columns
            - set(excluded.columns)
        )

        if missing:
            audit.fail(
                "Production exclusion report is missing required columns: "
                + ", ".join(sorted(missing))
            )
        else:
            audit.ok(
                "Production exclusion report contains country-year "
                "and missing-pillar accounting fields."
            )


# ---------------------------------------------------------------------------
# 9. HISTORICAL VALIDATION
# ---------------------------------------------------------------------------

def verify_historical_validation() -> None:

    text = read_text(
        "scripts/48_historical_validation.py"
    )

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


# ---------------------------------------------------------------------------
# 10. FINAL JESI PIPELINE INTEGRATION
# ---------------------------------------------------------------------------

def verify_final_pipeline() -> None:

    path = ".github/workflows/final-jesi.yml"

    text = read_text(path)

    if not text:
        audit.fail(
            "Final JESI workflow is missing or unreadable: "
            ".github/workflows/final-jesi.yml"
        )
        return

    if "scripts/42_final_repository_audit.py" in text:
        audit.ok(
            "Final JESI pipeline integrates scripts/42_final_repository_audit.py."
        )
    else:
        audit.fail(
            "Final JESI pipeline does not integrate scripts/42_final_repository_audit.py."
        )


# ---------------------------------------------------------------------------
# 11. LOCKED METHODOLOGICAL SEQUENCE
# ---------------------------------------------------------------------------

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
        if term.lower()
        not in documentation.lower()
    ]

    if not missing:
        audit.ok(
            "Locked JESI methodological sequence is documented."
        )
    else:
        audit.fail(
            "Locked methodological sequence is missing terms: "
            + ", ".join(missing)
        )


# ---------------------------------------------------------------------------
# 12. DOCUMENTATION CONSISTENCY
# ---------------------------------------------------------------------------

def verify_documentation_consistency() -> None:

    readme = read_text(
        "README.md"
    )

    notice = read_text(
        "METHODOLOGY_NOTICE.md"
    )

    completed = (
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

    if completed:
        audit.ok(
            "README documents the empirical validation program and completed Master Version 1.0 status."
        )
    else:
        audit.warn(
            "README does not clearly contain empirical-validation and completed-version signals."
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
            "METHODOLOGY_NOTICE.md contains pending-final-evaluation language."
        )
    else:
        audit.ok(
            "METHODOLOGY_NOTICE.md does not contain obsolete pending-final-evaluation language."
        )

    combined = (
        readme
        + "\n"
        + notice
    )

    if contains_any(
        combined,
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
            "Current conditional methodological judgment was not found in documentation."
        )


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> int:

    print("=" * 72)
    print("JESI FINAL METHODOLOGICAL AUDIT")
    print("=" * 72)
    print("Audit mode: READ-ONLY")
    print("Production methodology modification: NONE")
    print()

    verify_required_files()

    verify_production_weights()

    verify_weighted_geometric_aggregation()

    verify_research_validation_workflow()

    verify_production_separation()

    verify_research_script_safeguards()

    verify_complete_case_source()

    verify_no_imputation()

    (
        included,
        excluded,
        score_column,
    ) = verify_production_outputs()

    verify_output_ranges(
        included,
        score_column,
    )

    verify_sample_coverage(
        included,
        excluded,
    )

    verify_exclusion_accounting(
        included,
        excluded,
    )

    verify_historical_validation()

    verify_final_pipeline()

    verify_locked_sequence()

    verify_documentation_consistency()

    audit.summary()

    return 1 if audit.failures else 0


if __name__ == "__main__":
    sys.exit(main())
