"""
JAS Unified Economic Strength Index (JESI)
README Integration Generator

Adds a concise final-results section to README.md
using the generated JESI research table.
"""

from pathlib import Path

import pandas as pd


README_FILE = Path("README.md")

RESULTS_FILE = Path(
    "data/results/JESI_final_research_table.csv"
)

MARKER_START = "<!-- JESI_FINAL_RESULTS_START -->"
MARKER_END = "<!-- JESI_FINAL_RESULTS_END -->"


def main():
    print("=" * 70)
    print("JESI README FINAL RESULTS INTEGRATION")
    print("=" * 70)

    if not README_FILE.exists():
        raise FileNotFoundError(
            f"Missing README file: {README_FILE}"
        )

    if not RESULTS_FILE.exists():
        raise FileNotFoundError(
            f"Missing final results file: {RESULTS_FILE}"
        )

    df = pd.read_csv(RESULTS_FILE)

    required_columns = {
        "rank",
        "country",
        "Growth",
        "Productivity",
        "Connectivity",
        "Resilience",
        "Strategic_Autonomy",
        "JESI",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing result columns: {sorted(missing)}"
        )

    df = df.sort_values("rank")

    table = df[
        [
            "rank",
            "country",
            "Growth",
            "Productivity",
            "Connectivity",
            "Resilience",
            "Strategic_Autonomy",
            "JESI",
        ]
    ].copy()

    table.columns = [
        "Rank",
        "Country",
        "Growth",
        "Productivity",
        "Connectivity",
        "Resilience",
        "Strategic Autonomy",
        "JESI",
    ]

    markdown_table = table.to_markdown(
        index=False,
        floatfmt=".4f",
    )

    section = f"""
{MARKER_START}

## Final JESI Empirical Results

The **JAS Unified Economic Strength Index (JESI)** measures
structural economic strength through five pillars:

- **Growth (G)** — 20%
- **Productivity (P)** — 25%
- **Connectivity (C)** — 20%
- **Resilience (R)** — 20%
- **Strategic Autonomy (A)** — 15%

### Final Country Results

{markdown_table}

### Benchmark

- Countries: Bangladesh, India, Viet Nam, Indonesia, Malaysia
- Common empirical period: 2016–2023
- Index scale: 0–100
- Baseline aggregation: weighted geometric mean
- Baseline weights: JAS Strategic Weights

### Interpretation

JESI is designed to complement conventional GDP-based
comparisons by incorporating structural growth capacity,
productivity, global connectivity, resilience to shocks,
and strategic economic autonomy.

The index is a composite measurement framework and should
not be interpreted as a causal model. Results are sensitive
to data revisions, indicator selection, normalization,
weighting assumptions, and sample coverage.

### Reproducibility

The empirical results are generated through the repository's
Python pipeline. Source data, processing scripts, validation
steps, scoring procedures, and robustness tests are maintained
within the repository.

{MARKER_END}
"""

    readme = README_FILE.read_text(
        encoding="utf-8"
    )

    # Remove previous generated section.
    if MARKER_START in readme and MARKER_END in readme:
        start = readme.index(MARKER_START)
        end = readme.index(MARKER_END) + len(MARKER_END)

        readme = (
            readme[:start]
            + readme[end:]
        )

    # Append final section.
    readme = readme.rstrip() + "\n\n" + section.strip() + "\n"

    README_FILE.write_text(
        readme,
        encoding="utf-8",
    )

    print()
    print(f"Updated: {README_FILE}")

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print("README integration completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
