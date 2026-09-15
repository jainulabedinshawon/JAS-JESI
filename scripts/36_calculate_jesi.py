"""
JAS Unified Economic Strength Index (JESI)
Final Master Calculation

Combines the five normalized pillars:

G = Growth
P = Productivity
C = Connectivity
R = Resilience
A = Strategic Autonomy

Baseline weights:
G = 0.20
P = 0.25
C = 0.20
R = 0.20
A = 0.15

JESI = 100 * G^0.20 * P^0.25 * C^0.20 * R^0.20 * A^0.15
"""

from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/processed")
OUTPUT_DIR = Path("data/results")


WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}


def weighted_geometric_mean(values, weights):
    """
    Calculate the weighted geometric mean.
    """

    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)

    if np.any(values <= 0):
        raise ValueError(
            "JESI pillar scores must be greater than zero."
        )

    if not np.isclose(weights.sum(), 1.0):
        raise ValueError(
            "JESI weights must sum to 1."
        )

    return float(
        np.exp(
            np.sum(weights * np.log(values))
        )
    )


def load_pillar_file(filename, score_column, pillar):
    """
    Load a pillar dataset and return country-year scores.
    """

    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Missing pillar file: {path}"
        )

    df = pd.read_csv(path)

    required = {
        "country_code",
        "country",
        "year",
        score_column,
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"{path} is missing columns: {sorted(missing)}"
        )

    result = df[
        [
            "country_code",
            "country",
            "year",
            score_column,
        ]
    ].copy()

    result = result.rename(
        columns={score_column: pillar}
    )

    return result


def main():
    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Final JESI Calculation")
    print("=" * 70)

    # ------------------------------------------------------------
    # Load five pillar datasets
    # ------------------------------------------------------------

    growth = load_pillar_file(
        "growth_pillar_2015_2024.csv",
        "growth_pillar",
        "G",
    )

    productivity = load_pillar_file(
        "productivity_pillar_2016_2023.csv",
        "productivity_pillar",
        "P",
    )

    connectivity = load_pillar_file(
        "connectivity_pillar_2015_2024.csv",
        "connectivity_pillar",
        "C",
    )

    resilience = load_pillar_file(
        "resilience_pillar_2015_2024.csv",
        "resilience_pillar",
        "R",
    )

    autonomy = load_pillar_file(
        "strategic_autonomy_pillar_2015_2024.csv",
        "strategic_autonomy_arithmetic",
        "A",
    )

    # ------------------------------------------------------------
    # Merge on country and year
    # ------------------------------------------------------------

    jesI = growth.merge(
        productivity,
        on=["country_code", "country", "year"],
        how="inner",
    )

    jesI = jesI.merge(
        connectivity,
        on=["country_code", "country", "year"],
        how="inner",
    )

    jesI = jesI.merge(
        resilience,
        on=["country_code", "country", "year"],
        how="inner",
    )

    jesI = jesI.merge(
        autonomy,
        on=["country_code", "country", "year"],
        how="inner",
    )

    # ------------------------------------------------------------
    # Validate common sample
    # ------------------------------------------------------------

    pillar_columns = ["G", "P", "C", "R", "A"]

    if jesI.empty:
        raise ValueError(
            "No common country-year observations found "
            "across all five JESI pillars."
        )

    if jesI[pillar_columns].isna().any().any():
        raise ValueError(
            "Missing pillar values detected in final JESI dataset."
        )

    for column in pillar_columns:
        if (
            (jesI[column] < 0).any()
            or (jesI[column] > 1).any()
        ):
            raise ValueError(
                f"{column} contains values outside [0, 1]."
            )

    # ------------------------------------------------------------
    # Calculate JESI
    # ------------------------------------------------------------

    weights = [
        WEIGHTS["G"],
        WEIGHTS["P"],
        WEIGHTS["C"],
        WEIGHTS["R"],
        WEIGHTS["A"],
    ]

    jesI["JESI"] = jesI.apply(
        lambda row: 100
        * weighted_geometric_mean(
            row[pillar_columns].values,
            weights,
        ),
        axis=1,
    )

    # ------------------------------------------------------------
    # Country average JESI
    # ------------------------------------------------------------

    country_results = (
        jesI.groupby(
            ["country_code", "country"]
        )["JESI"]
        .agg(
            JESI_mean="mean",
            JESI_std="std",
            JESI_min="min",
            JESI_max="max",
            observations="count",
        )
        .reset_index()
    )

    country_results["rank"] = (
        country_results["JESI_mean"]
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
    # Save results
    # ------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    country_year_file = (
        OUTPUT_DIR
        / "jesi_country_year_2016_2023.csv"
    )

    ranking_file = (
        OUTPUT_DIR
        / "jesi_country_ranking_2016_2023.csv"
    )

    jesI.to_csv(
        country_year_file,
        index=False,
    )

    country_results.to_csv(
        ranking_file,
        index=False,
    )

    # ------------------------------------------------------------
    # Console output
    # ------------------------------------------------------------

    print()
    print("Common JESI observations:")
    print(len(jesI))

    print()
    print(
        f"Years: {jesI['year'].min()}–"
        f"{jesI['year'].max()}"
    )

    print()
    print("Country-year JESI:")
    print(
        jesI[
            [
                "country_code",
                "country",
                "year",
                "G",
                "P",
                "C",
                "R",
                "A",
                "JESI",
            ]
        ]
    )

    print()
    print("Final country ranking:")
    print(country_results)

    print()
    print(f"Saved: {country_year_file}")
    print(f"Saved: {ranking_file}")

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print("Final JESI calculation completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
