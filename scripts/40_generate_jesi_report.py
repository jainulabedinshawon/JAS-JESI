"""
JAS Unified Economic Strength Index (JESI)
Final Research Report Generator

Creates a concise research-ready Markdown report
from the validated JESI outputs.
"""

from pathlib import Path

import pandas as pd


RESULTS_DIR = Path("data/results")

OUTPUT_FILE = Path(
    "docs/JESI_Final_Results_Report.md"
)

FINAL_FILE = (
    RESULTS_DIR
    / "final_jesi_country_results.csv"
)

ROBUSTNESS_FILE = (
    RESULTS_DIR
    / "jesi_robustness_country_results.csv"
)

CORRELATION_FILE = (
    RESULTS_DIR
    / "jesi_robustness_correlations.csv"
)

YEARLY_FILE = (
    RESULTS_DIR
    / "final_jesi_yearly_summary.csv"
)


def check_file(path):
    """Check that a required file exists."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required file is missing: {path}"
        )


def format_number(value, decimals=3):
    """Format numeric values for the report."""

    if pd.isna(value):
        return "N/A"

    return f"{float(value):.{decimals}f}"


def main():
    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Final Research Report Generator")
    print("=" * 70)

    # ---------------------------------------------------------------
    # Check required files
    # ---------------------------------------------------------------

    required_files = [
        FINAL_FILE,
        ROBUSTNESS_FILE,
        CORRELATION_FILE,
        YEARLY_FILE,
    ]

    for path in required_files:
        check_file(path)

    # ---------------------------------------------------------------
    # Load data
    # ---------------------------------------------------------------

    final_df = pd.read_csv(
        FINAL_FILE
    )

    robustness_df = pd.read_csv(
        ROBUSTNESS_FILE
    )

    correlation_df = pd.read_csv(
        CORRELATION_FILE
    )

    yearly_df = pd.read_csv(
        YEARLY_FILE
    )

    # ---------------------------------------------------------------
    # Validate minimum schemas
    # ---------------------------------------------------------------

    final_required = {
        "rank",
        "country_code",
        "country",
        "G",
        "P",
        "C",
        "R",
        "A",
        "JESI",
        "JESI_std",
        "observations",
    }

    missing = (
        final_required
        - set(final_df.columns)
    )

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

    missing = (
        robustness_required
        - set(robustness_df.columns)
    )

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

    missing = (
        yearly_required
        - set(yearly_df.columns)
    )

    if missing:
        raise ValueError(
            "Yearly JESI results are missing columns: "
            f"{sorted(missing)}"
        )

    # ---------------------------------------------------------------
    # Sort final country results
    # ---------------------------------------------------------------

    final_df = final_df.sort_values(
        "rank"
    ).reset_index(drop=True)

    robustness_df = robustness_df.sort_values(
        "country_code"
    ).reset_index(drop=True)

    yearly_df = yearly_df.sort_values(
        "year"
    ).reset_index(drop=True)

    # ---------------------------------------------------------------
    # Country results table
    # ---------------------------------------------------------------

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
            "JESI": "JESI",
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
        country_table[column] = country_table[
            column
        ].map(format_number)

    country_table[
        "Rank"
    ] = country_table[
        "Rank"
    ].astype(int)

    country_table[
        "Observations"
    ] = country_table[
        "Observations"
    ].astype(int)

    # ---------------------------------------------------------------
    # Robustness table
    # ---------------------------------------------------------------

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
        robustness_table[column] = robustness_table[
            column
        ].map(format_number)

    # ---------------------------------------------------------------
    # Yearly summary table
    # ---------------------------------------------------------------

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
        yearly_table[column] = yearly_table[
            column
        ].map(format_number)

    yearly_table[
        "Year"
    ] = yearly_table[
        "Year"
    ].astype(int)

    yearly_table[
        "Observations"
    ] = yearly_table[
        "Observations"
    ].astype(int)

    # ---------------------------------------------------------------
    # Robustness correlations
    # ---------------------------------------------------------------

    correlation_lines = []

    for _, row in correlation_df.iterrows():
        comparison = row["comparison"]
        correlation = row[
            "spearman_correlation"
        ]

        correlation_lines.append(
            f"- **{comparison}:** "
            f"{format_number(correlation, 4)}"
        )

    correlation_text = "\n".join(
        correlation_lines
    )

    # ---------------------------------------------------------------
    # Study period and sample
    # ---------------------------------------------------------------

    start_year = int(
        yearly_df["year"].min()
    )

    end_year = int(
        yearly_df["year"].max()
    )

    country_count = int(
        final_df["country_code"].nunique()
    )

    total_observations = int(
        yearly_df["observations"].sum()
    )

    # ---------------------------------------------------------------
    # Markdown report
    # ---------------------------------------------------------------

    report = f"""# JAS Unified Economic Strength Index (JESI)

## Final Empirical Results Report

**Version:** Master Version 1.0  
**Study period:** {start_year}-{end_year}  
**Benchmark countries:** {country_count}  
**Country-year observations:** {total_observations}

---

## 1. Framework

The JAS Unified Economic Strength Index (JESI) is a multidimensional
framework designed to evaluate economic strength through five structural
pillars:

- **G — Growth**
- **P — Productivity**
- **C — Connectivity**
- **R — Resilience**
- **A — Strategic Autonomy**

The baseline weighting structure is:

| Pillar | Weight |
|---|---:|
| Growth | 0.20 |
| Productivity | 0.25 |
| Connectivity | 0.20 |
| Resilience | 0.20 |
| Strategic Autonomy | 0.15 |

The baseline aggregation is a weighted geometric index:

`JESI = 100 × G^0.20 × P^0.25 × C^0.20 × R^0.20 × A^0.15`

All pillar scores are normalized to the interval (0, 1].

---

## 2. Final Country Results

{country_table.to_markdown(index=False)}

---

## 3. Robustness Analysis

The robustness module compares the baseline strategic weighting with
equal weighting and compares arithmetic with geometric aggregation.

{robustness_table.to_markdown(index=False)}

### Rank Correlations

{correlation_text}

These correlations describe the degree of rank-order similarity between
the tested specifications. They are sensitivity measures rather than
proof that one specification is universally superior.

---

## 4. Year-Level JESI Summary

{yearly_table.to_markdown(index=False)}

---

## 5. Interpretation

The final JESI results provide a multidimensional representation of
economic strength across the five benchmark countries during the
{start_year}-{end_year} common sample.

The pillar structure allows economic performance to be examined beyond
a single output measure by separating growth, productivity, connectivity,
resilience, and strategic autonomy.

Country-level differences should therefore be interpreted together with
the underlying pillar scores rather than through the composite score
alone.

The robustness results indicate how sensitive the measured country
ordering is to alternative weighting and aggregation specifications.
They should be treated as methodological sensitivity evidence, not as
proof of causal relationships.

---

## 6. Methodological Status

JESI is a proposed composite economic-strength framework developed by
JAS. The present results represent an empirical implementation of the
specified Master Version 1.0 methodology for the stated benchmark
sample and period.

The index should not be interpreted as an established international
standard or as a causal measure of economic performance.

Important methodological limitations include:

1. Indicator availability and missing observations.
2. Cross-country comparability of source data.
3. Sensitivity to normalization choices.
4. Sensitivity to pillar weights.
5. Sensitivity to aggregation method.
6. Data revisions and measurement error.
7. The limited benchmark-country and time-period sample.
8. The distinction between association and causality.

---

## 7. Reproducibility

The empirical pipeline is implemented through the repository scripts.

The final calculation produces:

- Country-year JESI scores
- Country-level averages
- Country rankings
- Robustness results
- Year-level summaries
- Final research-ready tables
- This research report

The final validation script checks data completeness, duplicate
country-year observations, score ranges, mathematical consistency,
country aggregation, ranking integrity, yearly aggregation, research
table consistency, and robustness-output integrity.

---

## 8. Research Status

**Pipeline status: Empirical results generated and validated.**

The reported results are specific to the documented JESI Master Version
1.0 methodology, benchmark sample, data sources, normalization rules,
weights, and aggregation choices.

Further research should examine historical back-testing, alternative
normalization methods, alternative indicator sets, statistical weighting
approaches, broader country coverage, and external validation.
"""

    # ---------------------------------------------------------------
    # Write report
    # ---------------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    # ---------------------------------------------------------------
    # Console output
    # ---------------------------------------------------------------

    print()
    print(
        f"Saved: {OUTPUT_FILE}"
    )

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print(
        "JESI research report generated successfully."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
