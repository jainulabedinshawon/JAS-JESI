"""
JAS Unified Economic Strength Index (JESI)
Final Research Report Generator

Creates a concise research-ready Markdown report
from the final JESI outputs.
"""

from pathlib import Path

import pandas as pd


RESULTS_DIR = Path("data/results")
OUTPUT_FILE = Path(
    "docs/JESI_Final_Results_Report.md"
)

FINAL_FILE = (
    RESULTS_DIR / "final_jesi_country_results.csv"
)

ROBUSTNESS_FILE = (
    RESULTS_DIR / "jesi_robustness_country_results.csv"
)

YEARLY_FILE = (
    RESULTS_DIR / "final_jesi_yearly_summary.csv"
)


def main():
    print("=" * 70)
    print("JESI FINAL RESEARCH REPORT GENERATOR")
    print("=" * 70)

    required_files = [
        FINAL_FILE,
        ROBUSTNESS_FILE,
        YEARLY_FILE,
    ]

    for file in required_files:
        if not file.exists():
            raise FileNotFoundError(
                f"Missing required file: {file}"
            )

    final_df = pd.read_csv(FINAL_FILE)
    robustness_df = pd.read_csv(ROBUSTNESS_FILE)
    yearly_df = pd.read_csv(YEARLY_FILE)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------
    # Country results table
    # ------------------------------------------------------------

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
        ]
    ].copy()

    country_table.columns = [
        "Rank",
        "Country",
        "Growth",
        "Productivity",
        "Connectivity",
        "Resilience",
        "Strategic Autonomy",
        "JESI",
    ]

    country_table = country_table.sort_values(
        "Rank"
    )

    # ------------------------------------------------------------
    # Robustness table
    # ------------------------------------------------------------

    robustness_columns = [
        "country",
        "JAS_arithmetic",
        "JAS_geometric",
        "Equal_arithmetic",
        "Equal_geometric",
    ]

    robustness_table = robustness_df[
        robustness_columns
    ].copy()

    robustness_table.columns = [
        "Country",
        "JAS Arithmetic",
        "JAS Geometric",
        "Equal Arithmetic",
        "Equal Geometric",
    ]

    # ------------------------------------------------------------
    # Yearly summary
    # ------------------------------------------------------------

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

    yearly_table.columns = [
        "Year",
        "Mean JESI",
        "Median JESI",
        "Minimum JESI",
        "Maximum JESI",
        "Observations",
    ]

    # ------------------------------------------------------------
    # Report
    # ------------------------------------------------------------

    report = []

    report.append(
        "# JAS Unified Economic Strength Index (JESI)"
    )

    report.append(
        "## Final Empirical Results Report"
    )

    report.append("")

    report.append(
        "> A Data-Driven Framework for Measuring "
        "Structural Economic Strength."
    )

    report.append("")

    report.append(
        "### 1. Framework"
    )

    report.append("")

    report.append(
        "JESI evaluates structural economic strength "
        "through five pillars:"
    )

    report.append("")

    report.append(
        "- **G — Growth**: 20%"
    )
    report.append(
        "- **P — Productivity**: 25%"
    )
    report.append(
        "- **C — Connectivity**: 20%"
    )
    report.append(
        "- **R — Resilience**: 20%"
    )
    report.append(
        "- **A — Strategic Autonomy**: 15%"
    )

    report.append("")

    report.append(
        "The baseline index uses a weighted geometric "
        "aggregation of the five normalized pillars."
    )

    report.append("")

    report.append(
        "### 2. Final Country Results"
    )

    report.append("")

    report.append(
        country_table.to_markdown(
            index=False,
            floatfmt=".4f",
        )
    )

    report.append("")

    report.append(
        "### 3. Robustness Results"
    )

    report.append("")

    report.append(
        "The robustness analysis compares the "
        "JAS strategic weights with equal weights "
        "and compares arithmetic and geometric aggregation."
    )

    report.append("")

    report.append(
        robustness_table.to_markdown(
            index=False,
            floatfmt=".4f",
        )
    )

    report.append("")

    report.append(
        "### 4. Year-Level JESI Summary"
    )

    report.append("")

    report.append(
        yearly_table.to_markdown(
            index=False,
            floatfmt=".4f",
        )
    )

    report.append("")

    report.append(
        "### 5. Interpretation"
    )

    report.append("")

    report.append(
        "JESI is designed to complement GDP-based "
        "economic comparisons by incorporating "
        "growth, productivity, global connectivity, "
        "shock resilience, and strategic autonomy."
    )

    report.append("")

    report.append(
        "The index should be interpreted as a "
        "composite measurement framework rather "
        "than a causal model. Results remain "
        "sensitive to data revisions, normalization "
        "choices, indicator availability, and weighting assumptions."
    )

    report.append("")

    report.append(
        "### 6. Benchmark Sample"
    )

    report.append("")

    report.append(
        "- Countries: Bangladesh, India, Viet Nam, "
        "Indonesia, Malaysia"
    )

    report.append(
        "- Common empirical period: 2016–2023"
    )

    report.append(
        "- JESI scale: 0–100"
    )

    report.append(
        "- Baseline weights: JAS Strategic Weights"
    )

    report.append("")

    report.append(
        "### 7. Reproducibility"
    )

    report.append("")

    report.append(
        "All calculations are implemented through "
        "the repository's Python pipeline and can be "
        "reproduced from the underlying processed datasets."
    )

    report.append("")

    report.append(
        "### 8. Research Status"
    )

    report.append("")

    report.append(
        "**Status: Final empirical pipeline generated.**"
    )

    report.append("")

    report.append(
        "Further research may include historical "
        "backtesting, alternative normalization, "
        "additional countries, statistical weight "
        "estimation, and external validation."
    )

    OUTPUT_FILE.write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    print()
    print(f"Report created: {OUTPUT_FILE}")

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print("Final JESI research report generated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
