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

PILLARS = [
    "G",
    "P",
    "C",
    "R",
    "A",
]


def validate_input(df):
    """Validate the country-year JESI dataset."""

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
            "Input JESI dataset is missing columns: "
            f"{sorted(missing)}"
        )

    if df.empty:
        raise ValueError(
            "Input JESI dataset is empty."
        )

    duplicates = df[
        df.duplicated(
            subset=[
                "country_code",
                "year",
            ],
            keep=False,
        )
    ]

    if not duplicates.empty:
        raise ValueError(
            "Duplicate country-year observations found."
        )

    if df["JESI"].isna().any():
        raise ValueError(
            "Missing JESI values found."
        )

    for pillar in PILLARS:
        if df[pillar].isna().any():
            raise ValueError(
                f"Missing values found in pillar {pillar}."
            )

        if (
            (df[pillar] < 0).any()
            or (df[pillar] > 1).any()
        ):
            raise ValueError(
                f"Pillar {pillar} contains values "
                "outside [0, 1]."
            )

    if (
        (df["JESI"] < 0).any()
        or (df["JESI"] > 100).any()
    ):
        raise ValueError(
            "JESI values must be between 0 and 100."
        )


def main():
    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Final Research Results Generator")
    print("=" * 70)

    # ---------------------------------------------------------------
    # Check input file
    # ---------------------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing JESI input file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    validate_input(df)

    # ---------------------------------------------------------------
    # Country-level averages
    # ---------------------------------------------------------------

    country_results = (
        df.groupby(
            [
                "country_code",
                "country",
            ]
        )
        .agg(
            G=("G", "mean"),
            P=("P", "mean"),
            C=("C", "mean"),
            R=("R", "mean"),
            A=("A", "mean"),
            JESI=("JESI", "mean"),
            observations=("JESI", "count"),
        )
        .reset_index()
    )

    # ---------------------------------------------------------------
    # Country-level JESI standard deviation
    # ---------------------------------------------------------------

    country_std = (
        df.groupby(
            [
                "country_code",
                "country",
            ]
        )["JESI"]
        .std()
        .reset_index(
            name="JESI_std"
        )
    )

    country_results = country_results.merge(
        country_std,
        on=[
            "country_code",
            "country",
        ],
        how="left",
    )

    # ---------------------------------------------------------------
    # Validate country observations
    # ---------------------------------------------------------------

    if (
        country_results["observations"] < 1
    ).any():
        raise ValueError(
            "One or more countries have no observations."
        )

    # ---------------------------------------------------------------
    # Country ranking
    # ---------------------------------------------------------------

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
    ).reset_index(drop=True)

    # ---------------------------------------------------------------
    # Presentation score
    # ---------------------------------------------------------------

    country_results["JESI_score_100"] = (
        country_results["JESI"]
    )

    # ---------------------------------------------------------------
    # Year-level JESI summary
    # ---------------------------------------------------------------

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
        .sort_values("year")
        .reset_index(drop=True)
    )

    # ---------------------------------------------------------------
    # Validate yearly results
    # ---------------------------------------------------------------

    if yearly_results.empty:
        raise ValueError(
            "Year-level JESI summary is empty."
        )

    if (
        yearly_results["observations"] < 1
    ).any():
        raise ValueError(
            "One or more years have no observations."
        )

    # ---------------------------------------------------------------
    # Final research-ready table
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Output directory
    # ---------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Output files
    # ---------------------------------------------------------------

    country_file = (
        OUTPUT_DIR
        / "final_jesi_country_results.csv"
    )

    yearly_file = (
        OUTPUT_DIR
        / "final_jesi_yearly_summary.csv"
    )

    research_file = (
        OUTPUT_DIR
        / "JESI_final_research_table.csv"
    )

    country_results.to_csv(
        country_file,
        index=False,
    )

    yearly_results.to_csv(
        yearly_file,
        index=False,
    )

    research_table.to_csv(
        research_file,
        index=False,
    )

    # ---------------------------------------------------------------
    # Console output
    # ---------------------------------------------------------------

    print()
    print("Final country-level JESI results:")
    print(
        country_results.to_string(
            index=False
        )
    )

    print()
    print("Year-level JESI summary:")
    print(
        yearly_results.to_string(
            index=False
        )
    )

    print()
    print("Final research-ready table:")
    print(
        research_table.to_string(
            index=False
        )
    )

    print()
    print(
        f"Saved: {country_file}"
    )

    print(
        f"Saved: {yearly_file}"
    )

    print(
        f"Saved: {research_file}"
    )

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print(
        "Final JESI research results generated successfully."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
