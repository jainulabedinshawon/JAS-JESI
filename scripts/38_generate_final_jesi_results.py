"""
JAS Unified Economic Strength Index (JESI)
Final Research Results Generator

Generates:
1. Country-level final JESI results
2. Pillar-level country averages
3. Year-level JESI summary
4. Final research-ready table
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/results/jesi_country_year_2016_2023.csv"
)

OUTPUT_DIR = Path("data/results")


PILLARS = ["G", "P", "C", "R", "A"]


def main():
    print("=" * 70)
    print("JESI Final Research Results")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_csv(INPUT_FILE)

    required = {
        "country_code",
        "country",
        "year",
        "JESI",
        *PILLARS,
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if df.empty:
        raise ValueError(
            "Final JESI dataset is empty."
        )

    # ------------------------------------------------------------
    # Country-level pillar and JESI averages
    # ------------------------------------------------------------

    aggregation = {
        "G": "mean",
        "P": "mean",
        "C": "mean",
        "R": "mean",
        "A": "mean",
        "JESI": "mean",
    }

    country_results = (
        df.groupby(
            ["country_code", "country"]
        )
        .agg(aggregation)
        .reset_index()
    )

    # ------------------------------------------------------------
    # Country-level standard deviation
    # ------------------------------------------------------------

    country_std = (
        df.groupby(
            ["country_code", "country"]
        )["JESI"]
        .std()
        .reset_index(
            name="JESI_std"
        )
    )

    country_results = country_results.merge(
        country_std,
        on=["country_code", "country"],
        how="left",
    )

    # ------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------

    country_results["rank"] = (
        country_results["JESI"]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    country_results = country_results.sort_values(
        "rank"
    )

    # ------------------------------------------------------------
    # Final score on 0–100 scale
    # ------------------------------------------------------------

    country_results["JESI_score_100"] = (
        country_results["JESI"]
    )

    # ------------------------------------------------------------
    # Year-level summary
    # ------------------------------------------------------------

    yearly_results = (
        df.groupby("year")["JESI"]
        .agg(
            mean="mean",
            median="median",
            minimum="min",
            maximum="max",
            observations="count",
        )
        .reset_index()
    )

    # ------------------------------------------------------------
    # Research-ready table
    # ------------------------------------------------------------

    research_table = country_results[
        [
            "rank",
            "country_code",
            "country",
            "G",
            "P",
            "C",
            "R",
            "A",
            "JESI_score_100",
            "JESI_std",
        ]
    ].copy()

    research_table = research_table.rename(
        columns={
            "G": "Growth",
            "P": "Productivity",
            "C": "Connectivity",
            "R": "Resilience",
            "A": "Strategic_Autonomy",
            "JESI_score_100": "JESI",
        }
    )

    # ------------------------------------------------------------
    # Save outputs
    # ------------------------------------------------------------

    country_results.to_csv(
        OUTPUT_DIR
        / "final_jesi_country_results.csv",
        index=False,
    )

    yearly_results.to_csv(
        OUTPUT_DIR
        / "final_jesi_yearly_summary.csv",
        index=False,
    )

    research_table.to_csv(
        OUTPUT_DIR
        / "JESI_final_research_table.csv",
        index=False,
    )

    # ------------------------------------------------------------
    # Console output
    # ------------------------------------------------------------

    print()
    print("FINAL JESI RESEARCH TABLE")
    print("-" * 70)
    print(research_table.to_string(index=False))

    print()
    print("Yearly summary")
    print("-" * 70)
    print(yearly_results.to_string(index=False))

    print()
    print("Files generated:")
    print(
        "1. data/results/final_jesi_country_results.csv"
    )
    print(
        "2. data/results/final_jesi_yearly_summary.csv"
    )
    print(
        "3. data/results/JESI_final_research_table.csv"
    )

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print("Final JESI research results generated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
