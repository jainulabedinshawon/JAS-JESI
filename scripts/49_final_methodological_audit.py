"""
JESI Final Methodological Audit
Master Version 1.0

READ-ONLY GOVERNANCE AUDIT

This script does not modify production JESI methodology,
weights, normalization, aggregation, or research outputs.

Locked sequence:

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
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_COUNTRIES = {
    "BGD",
    "IND",
    "VNM",
    "IDN",
    "MYS",
}

EXPECTED_YEARS = set(range(2016, 2024))

EXPECTED_WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}

EXPECTED_THEORETICAL = 40
EXPECTED_COMPLETE = 34
EXPECTED_EXCLUDED = 6

EXPECTED_COUNTRY_OBSERVATIONS = {
    "BGD": 2,
    "IND": 8,
    "VNM": 8,
    "IDN": 8,
    "MYS": 8,
}

EXPECTED_EXCLUDED = {
    ("BGD", 2016),
    ("BGD", 2019),
    ("BGD", 2020),
    ("BGD", 2021),
    ("BGD", 2022),
    ("BGD", 2023),
}

REQUIRED_FILES = [
    "README.md",
    "METHODOLOGY_NOTICE.md",
    "requirements.txt",
    "scripts/36_calculate_jesi.py",
    "scripts/42_final_repository_audit.py",
    "scripts/43_analyze_autonomy_coverage.py",
    "scripts/44_analyze_indicator_redundancy.py",
    "scripts/45_normalization_sensitivity.py",
    "scripts/46_weight_sensitivity.py",
    "scripts/47_aggregation_sensitivity.py",
    "scripts/48_historical_validation.py",
    "scripts/50_balanced_panel_sensitivity.py",
    ".github/workflows/python-app.yml",
    ".github/workflows/research-validation.yml",
    ".github/workflows/final-jesi.yml",
    ".github/workflows/final-methodological-audit.yml",
]

PRODUCTION_FILE = (
    ROOT / "data/results/jesi_country_year_2016_2023.csv"
)

EXCLUDED_FILE = (
    ROOT / "data/results/jesi_excluded_country_years_2016_2023.csv"
)

RESEARCH_TABLE_FILE = (
    ROOT / "data/results/JESI_final_research_table.csv"
)

COVERAGE_FILE = (
    ROOT / "data/results/jesi_country_coverage_2016_2023.csv"
)

BALANCED_FILE = (
    ROOT / "data/results/jesi_balanced_panel_country_results.csv"
)


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
        print("JESI FINAL METHODOLOGICAL AUDIT")
        print("=" * 72)
        print(f"PASS:     {self.passed}")
        print(f"WARNING:  {self.warnings}")
        print(f"FAIL:     {self.failures}")

        if self.failures:
            print("FINAL STATUS: FAIL")
        elif self.warnings:
            print("FINAL STATUS: PASS WITH METHODOLOGICAL WARNINGS")
        else:
            print("FINAL STATUS: PASS")

        print("=" * 72)


audit = Audit()


def read_text(path: str) -> str:
    file_path = ROOT / path

    if not file_path.exists():
        return ""

    try:
        return file_path.read_text(encoding="utf-8")
    except Exception:
        return ""


def load_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        audit.fail(f"Missing required CSV: {path.relative_to(ROOT)}")
        return None

    try:
        return pd.read_csv(path)
    except Exception as exc:
        audit.fail(f"Could not read {path}: {exc}")
        return None


def verify_required_files() -> None:
    for path in REQUIRED_FILES:
        if (ROOT / path).exists():
            audit.ok(f"Required file present: {path}")
        else:
            audit.fail(f"Required file missing: {path}")


def verify_weights() -> None:
    text = read_text("scripts/36_calculate_jesi.py")

    if not text:
        audit.fail("Production JESI calculation script unavailable.")
        return

    for pillar, weight in EXPECTED_WEIGHTS.items():
        pattern = rf"['\"]{pillar}['\"]\s*[:=]\s*{weight:.2f}"

        if re.search(pattern, text):
            audit.ok(f"Production weight {pillar} = {weight:.2f}")
        else:
            audit.fail(
                f"Production weight {pillar} = {weight:.2f} "
                "could not be verified."
            )

    if abs(sum(EXPECTED_WEIGHTS.values()) - 1.0) < 1e-12:
        audit.ok("Production weights sum to 1.00.")
    else:
        audit.fail("Production weights do not sum to 1.00.")


def verify_no_imputation() -> None:
    text = read_text("scripts/36_calculate_jesi.py").lower()

    active_patterns = [
        r"\.fillna\s*\(",
        r"\.interpolate\s*\(",
        r"\bsimpleimputer\b",
        r"\biterativeimputer\b",
        r"\bknnimputer\b",
    ]

    active = any(
        re.search(pattern, text)
        for pattern in active_patterns
    )

    if active:
        audit.fail(
            "Active missing-value imputation/interpolation operation "
            "detected in production calculation."
        )
    else:
        audit.ok(
            "No active common imputation/interpolation operation "
            "detected in production calculation."
        )


def verify_production_panel() -> None:
    df = load_csv(PRODUCTION_FILE)

    if df is None:
        return

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
        audit.fail(
            "Production output missing columns: "
            + ", ".join(sorted(missing))
        )
        return

    if len(df) == EXPECTED_COMPLETE:
        audit.ok("Production complete-case sample contains 34 observations.")
    else:
        audit.fail(
            f"Expected {EXPECTED_COMPLETE} complete observations; "
            f"found {len(df)}."
        )

    duplicated = df.duplicated(
        ["country_code", "year"]
    ).any()

    if duplicated:
        audit.fail("Duplicate country-year observations detected.")
    else:
        audit.ok("No duplicate country-year observations.")


def verify_theoretical_and_excluded_counts() -> None:
    df = load_csv(PRODUCTION_FILE)
    excluded = load_csv(EXCLUDED_FILE)

    if df is None:
        return

    if excluded is None:
        return

    total = len(df) + len(excluded)

    if total == EXPECTED_THEORETICAL:
        audit.ok(
            "40 theoretical observations reconcile to included + excluded."
        )
    else:
        audit.fail(
            f"Theoretical reconciliation failed: "
            f"{total} instead of {EXPECTED_THEORETICAL}."
        )

    if len(excluded) == EXPECTED_EXCLUDED:
        audit.ok("Exactly 6 country-year observations are excluded.")
    else:
        audit.fail(
            f"Expected 6 excluded observations; found {len(excluded)}."
        )


def verify_excluded_observations() -> None:
    excluded = load_csv(EXCLUDED_FILE)

    if excluded is None:
        return

    if not {"country_code", "year"}.issubset(excluded.columns):
        audit.fail(
            "Excluded-observation file lacks country_code/year."
        )
        return

    actual = {
        (str(row.country_code), int(row.year))
        for row in excluded.itertuples()
    }

    if actual == EXPECTED_EXCLUDED:
        audit.ok(
            "Excluded country-years match the documented missing-data pattern."
        )
    else:
        audit.fail(
            "Excluded country-years do not match the expected documented pattern."
        )


def verify_country_coverage() -> None:
    df = load_csv(PRODUCTION_FILE)

    if df is None:
        return

    counts = (
        df.groupby("country_code")
        .size()
        .to_dict()
    )

    for country in EXPECTED_COUNTRIES:
        expected = EXPECTED_COUNTRY_OBSERVATIONS[country]
        actual = int(counts.get(country, 0))

        if actual == expected:
            audit.ok(
                f"{country}: {actual}/{len(EXPECTED_YEARS)} "
                "complete observations."
            )
        else:
            audit.fail(
                f"{country}: expected {expected}, found {actual}."
            )

    if set(counts) == EXPECTED_COUNTRIES:
        audit.ok("All five benchmark countries are represented.")
    else:
        audit.fail(
            "Country coverage does not match the expected five-country sample."
        )


def verify_research_table() -> None:
    df = load_csv(RESEARCH_TABLE_FILE)

    if df is None:
        return

    required = {
        "country_code",
        "observations",
        "expected_observations",
        "missing_observations",
        "coverage_pct",
        "balanced_panel_eligible",
    }

    missing = required - set(df.columns)

    if missing:
        audit.fail(
            "Final research table missing coverage columns: "
            + ", ".join(sorted(missing))
        )
        return

    audit.ok(
        "Final research table contains country-level observation coverage."
    )

    for row in df.itertuples():
        country = str(row.country_code)

        if country not in EXPECTED_COUNTRY_OBSERVATIONS:
            continue

        expected = EXPECTED_COUNTRY_OBSERVATIONS[country]

        if int(row.observations) == expected:
            audit.ok(
                f"Research table observation count verified for {country}."
            )
        else:
            audit.fail(
                f"Research table observation count mismatch for {country}."
            )


def verify_coverage_file() -> None:
    df = load_csv(COVERAGE_FILE)

    if df is None:
        return

    required = {
        "country_code",
        "observations",
        "expected_observations",
        "missing_observations",
        "coverage_pct",
        "balanced_panel_eligible",
    }

    if required.issubset(df.columns):
        audit.ok(
            "Country coverage artifact contains complete methodological metadata."
        )
    else:
        audit.fail(
            "Country coverage artifact lacks required methodological metadata."
        )


def verify_balanced_panel() -> None:
    if not BALANCED_FILE.exists():
        audit.warn(
            "Balanced-panel sensitivity artifact is not present yet."
        )
        return

    df = load_csv(BALANCED_FILE)

    if df is None:
        return

    if "country_code" not in df.columns:
        audit.fail(
            "Balanced-panel sensitivity output lacks country_code."
        )
        return

    countries = set(df["country_code"].astype(str))

    if "BGD" not in countries:
        audit.warn(
            "Balanced-panel output does not contain Bangladesh; "
            "verify the sensitivity script's eligibility output."
        )

    eligible_column = "balanced_panel_eligible"

    if eligible_column in df.columns:
        eligible = set(
            df.loc[
                df[eligible_column].astype(bool),
                "country_code",
            ].astype(str)
        )

        expected_eligible = {
            "IND",
            "VNM",
            "IDN",
            "MYS",
        }

        if eligible == expected_eligible:
            audit.ok(
                "Balanced-panel eligibility identifies the four "
                "fully covered countries."
            )
        else:
            audit.fail(
                "Balanced-panel eligibility does not match expected coverage."
            )
    else:
        audit.warn(
            "Balanced-panel artifact lacks explicit eligibility column."
        )


def verify_documentation_language() -> None:
    combined = (
        read_text("README.md")
        + "\n"
        + read_text("METHODOLOGY_NOTICE.md")
    ).lower()

    required_phrases = [
        "complete-case",
        "no imputation",
        "2016-2023",
        "not universally validated",
    ]

    for phrase in required_phrases:
        if phrase in combined:
            audit.ok(
                f"Documentation contains required methodological phrase: {phrase}"
            )
        else:
            audit.warn(
                f"Documentation does not explicitly contain: {phrase}"
            )


def verify_research_validation_scripts() -> None:
    for number in ["44", "45", "46", "47", "48"]:
        matches = list(
            (ROOT / "scripts").glob(f"{number}_*.py")
        )

        if matches:
            audit.ok(
                f"Research-validation script {number} present."
            )
        else:
            audit.fail(
                f"Research-validation script {number} missing."
            )


def verify_workflow_permissions() -> None:
    for workflow in [
        ".github/workflows/python-app.yml",
        ".github/workflows/research-validation.yml",
        ".github/workflows/final-methodological-audit.yml",
    ]:
        text = read_text(workflow)

        if "contents: read" in text:
            audit.ok(
                f"{workflow} declares read-only contents permission."
            )
        else:
            audit.fail(
                f"{workflow} does not declare contents: read."
            )

    final = read_text(".github/workflows/final-jesi.yml")

    if "contents: write" in final:
        audit.ok(
            "Final JESI workflow retains write permission because it commits generated outputs."
        )
    else:
        audit.warn(
            "Final JESI workflow has no contents: write permission; "
            "verify whether generated-output commits are still intended."
        )


def verify_action_pinning() -> None:
    workflows = list(
        (ROOT / ".github/workflows").glob("*.yml")
    )

    unpinned = []

    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")

        for line in text.splitlines():
            if "uses:" not in line:
                continue

            if "actions/" in line and "@v" in line:
                unpinned.append(
                    f"{workflow.name}: {line.strip()}"
                )

    if unpinned:
        audit.warn(
            "Version-tagged GitHub Actions remain unpinned."
        )
    else:
        audit.ok(
            "GitHub Actions are pinned to immutable commit references."
        )


def main() -> None:
    verify_required_files()
    verify_weights()
    verify_no_imputation()

    verify_production_panel()
    verify_theoretical_and_excluded_counts()
    verify_excluded_observations()
    verify_country_coverage()

    verify_research_table()
    verify_coverage_file()
    verify_balanced_panel()

    verify_documentation_language()
    verify_research_validation_scripts()
    verify_workflow_permissions()
    verify_action_pinning()

    audit.summary()

    if audit.failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
