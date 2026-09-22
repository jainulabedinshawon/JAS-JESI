"""
JAS Unified Economic Strength Index (JESI)
README Integration Generator

Updates README.md with the validated final JESI
research table.
"""

from pathlib import Path

import pandas as pd


README_FILE = Path("README.md")

RESULTS_FILE = Path(
    "data/results/JESI_final_research_table.csv"
)

MARKER_START = (
    "<!-- JESI_FINAL_RESULTS_START -->"
)

MARKER_END = (
    "<!-- JESI_FINAL_RESULTS_END -->"
)


def main():
    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("README Integration Generator")
    print("=" * 70)

    # ---------------------------------------------------------------
    # Check required files
    # ---------------------------------------------------------------

    if not README_FILE.exists():
        raise FileNotFoundError(
            f"README file not found: {README_FILE}"
        )

    if not RESULTS_FILE.exists():
        raise FileNotFoundError(
            f"Final JESI research table not found: "
            f"{RESULTS_FILE}"
        )

    # ---------------------------------------------------------------
    # Load final research table
    # ---------------------------------------------------------------

    df = pd.read_csv(
        RESULTS_FILE
    )

    required_columns = {
        "rank",
        "country_code",
        "country",
        "Growth",
        "Productivity",
        "Connectivity",
        "Resilience",
        "Strategic_Autonomy",
        "JESI",
    }

    missing = (
        required_columns
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            "Final JESI research table is missing "
            f"columns: {sorted(missing)}"
        )

    if df.empty:
        raise ValueError(
            "Final JESI research table is empty."
        )

    # ---------------------------------------------------------------
    # Validate values
    # ---------------------------------------------------------------

    if df["JESI"].isna().any():
        raise ValueError(
            "Final JESI table contains missing JESI values."
        )

    if (
        (df["JESI"] <= 0).any()
        or (df["JESI"] > 100).any()
    ):
        raise ValueError(
            "JESI values must be between 0 and 100."
        )

    for column in [
        "Growth",
        "Productivity",
        "Connectivity",
        "Resilience",
        "Strategic_Autonomy",
    ]:
        if df[column].isna().any():
            raise ValueError(
                f"Missing values found in {column}."
            )

        if (
            (df[column] <= 0).any()
            or (df[column] > 1).any()
        ):
            raise ValueError(
                f"{column} contains values outside (0, 1]."
            )

    # ---------------------------------------------------------------
    # Sort by rank
    # ---------------------------------------------------------------

    df = df.sort_values(
        "rank"
    ).reset_index(drop=True)

    # ---------------------------------------------------------------
    # Build README table
    # ---------------------------------------------------------------

    table = df[
        [
            "rank",
            "country_code",
            "country",
            "Growth",
            "Productivity",
            "Connectivity",
            "Resilience",
            "Strategic_Autonomy",
            "JESI",
        ]
    ].copy()

    table = table.rename(
        columns={
            "rank": "Rank",
            "country_code": "Code",
            "country": "Country",
            "Growth": "Growth",
            "Productivity": "Productivity",
            "Connectivity": "Connectivity",
            "Resilience": "Resilience",
            "Strategic_Autonomy": "Strategic Autonomy",
            "JESI": "JESI",
        }
    )

    numeric_columns = [
        "Growth",
        "Productivity",
        "Connectivity",
        "Resilience",
        "Strategic Autonomy",
        "JESI",
    ]

    for column in numeric_columns:
        table[column] = table[column].map(
            lambda value: f"{float(value):.3f}"
        )

    table["Rank"] = table[
        "Rank"
    ].astype(int)

    markdown_table = table.to_markdown(
        index=False
    )

    # ---------------------------------------------------------------
    # Build final README section
    # ---------------------------------------------------------------

    section = f"""
{MARKER_START}

## JESI Final Empirical Results

The following table is generated automatically from the validated
JESI Master Version 1.0 empirical results.

**Study period:** 2016-2023  
**Benchmark countries:** 5  
**Aggregation:** Weighted geometric mean  
**Baseline weights:** G 0.20, P 0.25, C 0.20, R 0.20, A 0.15

{markdown_table}

> **Research note:** JESI is a proposed composite economic-strength
> framework. These results are specific to the documented methodology,
> benchmark sample, data sources, normalization rules, weighting scheme,
> and study period. They should not be interpreted as an established
> international standard or as a causal measure of economic performance.

{MARKER_END}
"""

    # ---------------------------------------------------------------
    # Read README
    # ---------------------------------------------------------------

    readme_text = README_FILE.read_text(
        encoding="utf-8"
    )

    # ---------------------------------------------------------------
    # Replace existing generated section
    # ---------------------------------------------------------------

    if (
        MARKER_START in readme_text
        and MARKER_END in readme_text
    ):
        start_index = readme_text.index(
            MARKER_START
        )

        end_index = (
            readme_text.index(
                MARKER_END,
                start_index,
            )
            + len(MARKER_END)
        )

        updated_readme = (
            readme_text[:start_index]
            + section.strip()
            + readme_text[end_index:]
        )

        action = "updated"

    elif (
        MARKER_START not in readme_text
        and MARKER_END not in readme_text
    ):
        separator = (
            "\n\n"
            if not readme_text.endswith("\n")
            else "\n"
        )

        updated_readme = (
            readme_text
            + separator
            + section.strip()
            + "\n"
        )

        action = "added"

    else:
        raise ValueError(
            "README contains an incomplete JESI "
            "results marker pair."
        )

    # ---------------------------------------------------------------
    # Write README
    # ---------------------------------------------------------------

    README_FILE.write_text(
        updated_readme,
        encoding="utf-8",
    )

    # ---------------------------------------------------------------
    # Console output
    # ---------------------------------------------------------------

    print()
    print(
        f"JESI README section {action} successfully."
    )

    print(
        f"Updated: {README_FILE}"
    )

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print(
        "README JESI integration completed successfully."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
