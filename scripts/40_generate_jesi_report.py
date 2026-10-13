
"""
JAS Unified Economic Strength Index (JESI)
Final Research Report Generator

Preserves the production ranking and adds a separate
balanced-panel comparison and automated coverage validation.
"""

from pathlib import Path

import pandas as pd


RESULTS_DIR = Path("data/results")
OUTPUT_FILE = Path("docs/JESI_Final_Results_Report.md")

FINAL_FILE = RESULTS_DIR / "final_jesi_country_results.csv"
ROBUSTNESS_FILE = RESULTS_DIR / "jesi_robustness_country_results.csv"
CORRELATION_FILE = RESULTS_DIR / "jesi_robustness_correlations.csv"
YEARLY_FILE = RESULTS_DIR / "final_jesi_yearly_summary.csv"

PILLAR_COLUMNS = ["G", "P", "C", "R", "A"]
COVERAGE_COLUMNS = {
    "expected_observations",
    "coverage_pct",
    "balanced_panel_eligible",
}


def check_file(path):
    """Fail clearly if a required input file is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required file is missing: {path}"
        )


def format_number(value, decimals=3):
    """Format numeric values for Markdown tables."""
    if pd.isna(value):
        return "N/A"
    return f"{float(value):.{decimals}f}"


def parse_boolean_series(series, column_name):
    """Convert common CSV boolean representations safely."""
    mapping = {
        "true": True,
        "false": False,
        "1": True,
        "0": False,
    }

    parsed = series.astype(str).str.strip().str.lower().map(mapping)

    if parsed.isna().any():
        raise ValueError(
            f"Invalid boolean values in {column_name}."
        )

    return parsed.astype(bool)


def validate_coverage(final_df):
    """
    Validate coverage metadata without changing production scores
    or production ranks.
    """
    final_df = final_df.copy()

    final_df["observations"] = pd.to_numeric(
        final_df["observations"], errors="coerce"
    )
    final_df["expected_observations"] = pd.to_numeric(
        final_df["expected_observations"], errors="coerce"
    )
    final_df["coverage_pct"] = pd.to_numeric(
        final_df["coverage_pct"], errors="coerce"
    )

    numeric_columns = [
        "observations",
        "expected_observations",
        "coverage_pct",
    ]

    if final_df[numeric_columns].isna().any().any():
        raise ValueError(
            "Coverage metadata contains missing or invalid numeric values."
        )

    if (final_df["expected_observations"] <= 0).any():
        raise ValueError(
            "Expected observation counts must be positive."
        )

    if (final_df["observations"] < 0).any():
        raise ValueError(
            "Observation counts cannot be negative."
        )

    if (
        final_df["observations"]
        > final_df["expected_observations"]
    ).any():
        raise ValueError(
            "Observed counts exceed expected observations."
        )

    if final_df["country_code"].duplicated().any():
        raise ValueError(
            "Duplicate country codes in final country results."
        )

    if final_df["country_code"].isna().any():
        raise ValueError(
            "Missing country codes in final country results."
        )

    final_df["balanced_panel_eligible"] = parse_boolean_series(
        final_df["balanced_panel_eligible"],
        "balanced_panel_eligible",
    )

    calculated_coverage = (
        final_df["observations"]
        / final_df["expected_observations"]
        * 100
    )

    if not (
        (calculated_coverage - final_df["coverage_pct"]).abs()
        <= 0.11
    ).all():
        raise ValueError(
            "Coverage percentage is inconsistent with observation counts."
        )

    expected_balanced = (
        final_df["observations"]
        == final_df["expected_observations"]
    )

    if not (
        expected_balanced
        == final_df["balanced_panel_eligible"]
    ).all():
        raise ValueError(
            "Balanced-panel eligibility flags are inconsistent "
            "with observation coverage."
        )

    return final_df


def make_coverage_table(final_df):
    """Create a transparent country coverage table."""
    table = final_df[
        [
            "country",
            "observations",
            "expected_observations",
            "coverage_pct",
            "balanced_panel_eligible",
        ]
    ].copy()

    table = table.rename(
        columns={
            "country": "Country",
            "observations": "Complete observations",
            "expected_observations": "Expected observations",
            "coverage_pct": "Coverage (%)",
            "balanced_panel_eligible": "Balanced-panel eligible",
        }
    )

    table["Coverage (%)"] = table["Coverage (%)"].map(
        lambda value: format_number(value, 1)
    )
    table["Complete observations"] = table[
        "Complete observations"
    ].astype(int)
    table["Expected observations"] = table[
        "Expected observations"
    ].astype(int)
    table["Balanced-panel eligible"] = table[
        "Balanced-panel eligible"
    ].map({True: "Yes", False: "No"})

    return table


def make_balanced_ranking(final_df):
    """
    Use existing production country-average JESI scores.
    Do not recalculate or modify the production ranking.
    """
    eligible = final_df[
        final_df["balanced_panel_eligible"]
    ].copy()

    if eligible.empty:
        return None

    eligible["Balanced Rank"] = (
        eligible["JESI"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    eligible = eligible.sort_values(
        ["JESI", "country_code"],
        ascending=[False, True],
    )

    table = eligible[
        [
            "Balanced Rank",
            "country",
            "JESI",
            "observations",
            "coverage_pct",
        ]
    ].copy()

    table = table.rename(
        columns={
            "country": "Country",
            "JESI": "JESI",
            "observations": "Complete observations",
            "coverage_pct": "Coverage (%)",
        }
    )

    table["JESI"] = table["JESI"].map(format_number)
    table["Coverage (%)"] = table["Coverage (%)"].map(
        lambda value: format_number(value, 1)
    )
    table["Complete observations"] = table[
        "Complete observations"
    ].astype(int)

    return table


def main():
    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Final Research Report Generator")
    print("=" * 70)

    for path in [
        FINAL_FILE,
        ROBUSTNESS_FILE,
        CORRELATION_FILE,
        YEARLY_FILE,
    ]:
        check_file(path)

    final_df = pd.read_csv(FINAL_FILE)
    robustness_df = pd.read_csv(ROBUSTNESS_FILE)
    correlation_df = pd.read_csv(CORRELATION_FILE)
    yearly_df = pd.read_csv(YEARLY_FILE)

    final_required = {
        "rank",
        "country_code",
        "country",
        *PILLAR_COLUMNS,
        "JESI",
        "JESI_std",
        "observations",
        *COVERAGE_COLUMNS,
    }

    missing = final_required - set(final_df.columns)
    if missing:
        raise ValueError(
            "Final JESI results are missing columns: "
            f"{sorted(missing)}"
        )

    robustness_required = {
        "country_code",
        "country",
        "JAS_arithmetic",
        "JAS_geometric",
        "Equal_arithmetic",
        "Equal_geometric",
    }

    missing = robustness_required - set(robustness_df.columns)
    if missing:
        raise ValueError(
            "Robustness results are missing columns: "
            f"{sorted(missing)}"
        )

    yearly_required = {
        "year",
        "mean",
        "median",
        "minimum",
        "maximum",
        "observations",
    }

    missing = yearly_required - set(yearly_df.columns)
    if missing:
        raise ValueError(
            "Yearly JESI results are missing columns: "
            f"{sorted(missing)}"
        )

    # Coverage validation is independent of production score calculation.
    final_df = validate_coverage(final_df)

    for column in [
        "rank",
        "JESI",
        "JESI_std",
        *PILLAR_COLUMNS,
    ]:
        final_df[column] = pd.to_numeric(
            final_df[column], errors="coerce"
        )

    if final_df[
        ["rank", "JESI", "JESI_std", *PILLAR_COLUMNS]
    ].isna().any().any():
        raise ValueError(
            "Final country results contain invalid score or rank values."
        )

    # Preserve the original production ranking exactly.
    final_df = final_df.sort_values(
        "rank"
    ).reset_index(drop=True)

    robustness_df = robustness_df.sort_values(
        "country_code"
    ).reset_index(drop=True)

    yearly_df = yearly_df.sort_values(
        "year"
    ).reset_index(drop=True)

    # Main production results table: no rank or score recalculation.
    country_table = final_df[
        [
            "rank",
            "country",
            "G",
            "P",
            "C",
            "R",
            "A",
            "JESI",
            "JESI_std",
            "observations",
        ]
    ].copy()

    country_table = country_table.rename(
        columns={
            "rank": "Rank",
            "country": "Country",
            "G": "Growth",
            "P": "Productivity",
            "C": "Connectivity",
            "R": "Resilience",
            "A": "Strategic Autonomy",
            "JESI_std": "JESI SD",
            "observations": "Observations",
        }
    )

    for column in [
        "Growth",
        "Productivity",
        "Connectivity",
        "Resilience",
        "Strategic Autonomy",
        "JESI",
        "JESI SD",
    ]:
        country_table[column] = country_table[column].map(
            format_number
        )

    country_table["Rank"] = country_table["Rank"].astype(int)
    country_table["Observations"] = country_table[
        "Observations"
    ].astype(int)

    # Separate comparable ranking, based on the same JESI scores.
    balanced_table = make_balanced_ranking(final_df)
    coverage_table = make_coverage_table(final_df)

    if balanced_table is None:
        balanced_section = (
            "**No country currently satisfies the balanced-panel "
            "eligibility criteria.** No comparable ranking is reported. "
            "The production ranking above remains unchanged."
        )
    else:
        balanced_section = (
            "This separate ranking includes only countries marked "
            "`balanced_panel_eligible = True`. It uses the existing "
            "country-average JESI scores and does not alter the "
            "production ranking or methodology.\n\n"
            + balanced_table.to_markdown(index=False)
        )

    # Dynamic coverage caveat for Bangladesh, when present.
    bangladesh = final_df[
        (
            final_df["country_code"].astype(str).str.upper()
            == "BGD"
        )
        | (
            final_df["country"].astype(str).str.lower()
            == "bangladesh"
        )
    ]

    if not bangladesh.empty:
        row = bangladesh.iloc[0]
        observed = int(row["observations"])
        expected = int(row["expected_observations"])
        coverage = float(row["coverage_pct"])

        if not bool(row["balanced_panel_eligible"]):
            bangladesh_caveat = (
                f"**Bangladesh coverage caveat:** Bangladesh has "
                f"{observed}/{expected} complete observations "
                f"({coverage:.1f}% coverage) for the defined study "
                "period. It is excluded from the balanced-panel "
                "comparable ranking because it does not satisfy the "
                "full-coverage criterion. Its production score and "
                "position remain visible in the main ranking, but "
                "they should not be interpreted as directly comparable "
                "with countries having complete eight-year coverage."
            )
        else:
            bangladesh_caveat = (
                "Bangladesh satisfies the current balanced-panel "
                "coverage criteria. Its inclusion is determined "
                "automatically from the validated coverage metadata."
            )
    else:
        bangladesh_caveat = (
            "Bangladesh is not present in the current final country "
            "results. No Bangladesh-specific coverage statement can "
            "be verified from this input."
        )

    robustness_table = robustness_df[
        [
            "country",
            "JAS_arithmetic",
            "JAS_geometric",
            "Equal_arithmetic",
            "Equal_geometric",
        ]
    ].copy()

    robustness_table = robustness_table.rename(
        columns={
            "country": "Country",
            "JAS_arithmetic": "JAS Arithmetic",
            "JAS_geometric": "JAS Geometric",
            "Equal_arithmetic": "Equal Arithmetic",
            "Equal_geometric": "Equal Geometric",
        }
    )

    for column in [
        "JAS Arithmetic",
        "JAS Geometric",
        "Equal Arithmetic",
        "Equal Geometric",
    ]:
        robustness_table[column] = robustness_table[column].map(
            format_number
        )

    yearly_table = yearly_df[
        [
            "year",
            "mean",
            "median",
            "minimum",
            "maximum",
            "observations",
        ]
    ].copy()

    yearly_table = yearly_table.rename(
        columns={
            "year": "Year",
            "mean": "Mean JESI",
            "median": "Median JESI",
            "minimum": "Minimum",
            "maximum": "Maximum",
            "observations": "Observations",
        }
    )

    for column in [
        "Mean JESI",
        "Median JESI",
        "Minimum",
        "Maximum",
    ]:
        yearly_table[column] = yearly_table[column].map(
            format_number
        )

    yearly_table["Year"] = yearly_table["Year"].astype(int)
    yearly_table["Observations"] = yearly_table[
        "Observations"
    ].astype(int)

    correlation_lines = []
    for _, row in correlation_df.iterrows():
        correlation_lines.append(
            f"- **{row['comparison']}:** "
            f"{format_number(row['spearman_correlation'], 4)}"
        )

    correlation_text = "\n".join(correlation_lines)
    if not correlation_text:
        correlation_text = "No correlation results are available."

    start_year = int(yearly_df["year"].min())
    end_year = int(yearly_df["year"].max())
    country_count = int(final_df["country_code"].nunique())
    total_observations = int(yearly_df["observations"].sum())

    report = f"""# JAS Unified Economic Strength Index (JESI)

## Final Empirical Results Report

**Version:** Master Version 1.0  
**Study period:** {start_year}-{end_year}  
**Benchmark countries:** {country_count}  
**Country-year observations:** {total_observations}

---

## 1. Framework

The JAS Unified Economic Strength Index (JESI) evaluates economic
strength through five structural pillars:

- **G — Growth**
- **P — Productivity**
- **C — Connectivity**
- **R — Resilience**
- **A — Strategic Autonomy**

| Pillar | Weight |
|---|---:|
| Growth | 0.20 |
| Productivity | 0.25 |
| Connectivity | 0.20 |
| Resilience | 0.20 |
| Strategic Autonomy | 0.15 |

The baseline aggregation is:

`JESI = 100 × G^0.20 × P^0.25 × C^0.20 × R^0.20 × A^0.15`

All pillar scores are normalized to the interval (0, 1].

---

## 2. Main Production Country Ranking

The table below preserves the production ranks and country-average JESI
scores generated by the validated pipeline. Coverage analysis does not
modify this table.

{country_table.to_markdown(index=False)}

---

## 3. Balanced-Panel Comparable Ranking

{balanced_section}

### Data Coverage

{coverage_table.to_markdown(index=False)}

### Data Coverage Caveat

{bangladesh_caveat}

Countries with incomplete coverage remain visible in the main production
ranking, but are excluded from the separate balanced-panel comparison.
No missing observations are imputed, interpolated, or fabricated.

If future data updates change coverage eligibility, this section and the
balanced-panel ranking are regenerated from the validated coverage
metadata. Inconsistent coverage flags cause report generation to fail.

---

## 4. Robustness Analysis

The robustness module compares baseline strategic weighting with equal
weighting and arithmetic with geometric aggregation.

{robustness_table.to_markdown(index=False)}

### Rank Correlations

{correlation_text}

These correlations measure rank-order similarity across tested
specifications. They are sensitivity measures, not proof that one
specification is universally superior.

---

## 5. Year-Level JESI Summary

{yearly_table.to_markdown(index=False)}

---

## 6. Interpretation

The main ranking presents the production results using all available
validated country observations. The balanced-panel table is a separate
comparability analysis limited to countries satisfying the full-coverage
criterion.

The balanced-panel table uses the same country-average JESI scores as
the main table. Its rank numbers are calculated only within the eligible
subset; they do not replace the production ranks.

Country differences should be interpreted together with the five pillar
scores, data coverage, and robustness evidence. The results do not
establish causal relationships.

---

## 7. Methodological Status and Limitations

JESI is a proposed composite economic-strength framework developed by
JAS. These results implement the specified Master Version 1.0 methodology
for the documented benchmark sample and period. JESI is not presented
as an established international standard or a causal measure.

Important limitations include:

1. Indicator availability and missing observations.
2. Cross-country comparability of source data.
3. Sensitivity to normalization choices.
4. Sensitivity to pillar weights.
5. Sensitivity to aggregation method.
6. Data revisions and measurement error.
7. The limited benchmark-country and time-period sample.
8. The distinction between association and causality.

No production methodology, score, or rank is changed by this report's
balanced-panel presentation.

---

## 8. Reproducibility and Validation

The empirical pipeline produces country-year JESI scores, country-level
averages, rankings, robustness results, year-level summaries, and
research-ready tables.

This report validates that:

- Required coverage fields are present.
- Country codes are unique.
- Observation counts do not exceed expected counts.
- Coverage percentages agree with observation counts.
- Balanced-panel eligibility agrees with coverage metadata.
- The main production ranking is retained.
- The balanced-panel ranking contains eligible countries only.
- If no country is eligible, no false ranking is created.

---

## 9. Research Status

**Report status: Generated after coverage consistency validation.**

Results remain specific to the documented JESI Master Version 1.0
methodology, benchmark sample, source data, normalization rules,
weights, and aggregation choices.

Further research should examine historical back-testing, alternative
normalization methods, alternative indicator sets, broader country
coverage, and external validation.
"""

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(report, encoding="utf-8")

    print()
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Production countries: {country_count}")
    print(
        "Balanced-panel eligible countries: "
        f"{int(final_df['balanced_panel_eligible'].sum())}"
    )
    print("Coverage consistency validation: PASSED")
    print("Production ranks and scores modified: NO")
    print("=" * 70)
    print("STATUS: GREEN")
    print("JESI research report generated successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
