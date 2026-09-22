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

Final common sample:
5 countries, 2016-2023 = 40 country-year observations.
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

EXPECTED_COUNTRIES = {
    "BGD",
    "IND",
    "IDN",
    "MYS",
    "VNM",
}

EXPECTED_YEARS = set(range(2016, 2024))


def weighted_geometric_mean(values, weights):
    """
    Calculate the weighted geometric mean.
    """

    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)

    if len(values) != len(weights):
        raise ValueError(
            "Values and weights must have the same length."
        )

    if np.any(~np.isfinite(values)):
        raise ValueError(
            "JESI pillar scores contain non-finite values."
        )

    if np.any(values <= 0):
        raise ValueError(
            "JESI pillar scores must be greater than zero."
        )

    if np.any(values > 1):
        raise ValueError(
            "JESI pillar scores must not exceed 1."
        )

    if np.any(weights < 0):
        raise ValueError(
            "JESI weights cannot be negative."
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
    Load a pillar dataset and return standardized country-year scores.
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


def load_resilience_file():
    """
    Load the resilience pillar.

    The current resilience constructor does not include country_code,
    so country codes are assigned from the fixed five-country benchmark
    sample after validating the country names.
    """

    filename = "resilience_pillar_scores_2015_2024.csv"
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Missing resilience pillar file: {path}"
        )

    df = pd.read_csv(path)

    required = {
        "country",
        "year",
        "resilience_score",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"{path} is missing columns: {sorted(missing)}"
        )

    country_map = {
        "Bangladesh": "BGD",
        "India": "IND",
        "Indonesia": "IDN",
        "Malaysia": "MYS",
        "Vietnam": "VNM",
        "Viet Nam": "VNM",
    }

    df["country_code"] = df["country"].map(country_map)

    if df["country_code"].isna().any():
        unknown = sorted(
            df.loc[
                df["country_code"].isna(),
                "country",
            ].dropna().unique()
        )

        raise ValueError(
            "Unknown country names found in resilience data: "
            f"{unknown}"
        )

    result = df[
        [
            "country_code",
            "country",
            "year",
            "resilience_score",
        ]
    ].copy()

    result = result.rename(
        columns={"resilience_score": "R"}
    )

    return result


def validate_unique_country_year(df, name):
    """
    Validate that each country-year appears only once.
    """

    duplicates = df[
        df.duplicated(
            subset=["country_code", "year"],
            keep=False,
        )
    ]

    if not duplicates.empty:
        raise ValueError(
            f"{name} contains duplicate country-year observations:\n"
            f"{duplicates[['country_code', 'country', 'year']].to_string(index=False)}"
        )


def main():
    print("=" * 70)
    print("JAS Unified Economic Strength Index")
    print("Final JESI Calculation")
    print("=" * 70)

    # ---------------------------------------------------------------
    # Load five pillar datasets
    # ---------------------------------------------------------------

    growth = load_pillar_file(
        "growth_pillar_scores_2015_2024.csv",
        "growth_score",
        "G",
    )

    productivity = load_pillar_file(
        "productivity_pillar_scores_2016_2023.csv",
        "productivity_score",
        "P",
    )

    connectivity = load_pillar_file(
        "connectivity_pillar_scores_2015_2024.csv",
        "connectivity_score",
        "C",
    )

    resilience = load_resilience_file()

    autonomy = load_pillar_file(
        "strategic_autonomy_pillar_2015_2024.csv",
        "strategic_autonomy_arithmetic",
        "A",
    )

    # ---------------------------------------------------------------
    # Validate individual pillar datasets
    # ---------------------------------------------------------------

    pillars = {
        "Growth": growth,
        "Productivity": productivity,
        "Connectivity": connectivity,
        "Resilience": resilience,
        "Strategic Autonomy": autonomy,
    }

    for name, pillar_df in pillars.items():
        validate_unique_country_year(
            pillar_df,
            name,
        )

    # ---------------------------------------------------------------
    # Restrict all pillars to the common final sample
    # ---------------------------------------------------------------

    for name, pillar_df in pillars.items():
        pillar_df.drop(
            pillar_df[
                ~pillar_df["year"].isin(EXPECTED_YEARS)
            ].index,
            inplace=True,
        )

        pillar_countries = set(
            pillar_df["country_code"].dropna().unique()
        )

        missing_countries = EXPECTED_COUNTRIES - pillar_countries

        if missing_countries:
            raise ValueError(
                f"{name} is missing expected countries: "
                f"{sorted(missing_countries)}"
            )

    growth = growth[
        growth["country_code"].isin(EXPECTED_COUNTRIES)
    ].copy()

    productivity = productivity[
        productivity["country_code"].isin(EXPECTED_COUNTRIES)
    ].copy()

    connectivity = connectivity[
        connectivity["country_code"].isin(EXPECTED_COUNTRIES)
    ].copy()

    resilience = resilience[
        resilience["country_code"].isin(EXPECTED_COUNTRIES)
    ].copy()

    autonomy = autonomy[
        autonomy["country_code"].isin(EXPECTED_COUNTRIES)
    ].copy()

    # ---------------------------------------------------------------
    # Merge all five pillars
    # ---------------------------------------------------------------

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

    pillar_columns = [
        "G",
        "P",
        "C",
        "R",
        "A",
    ]

    # ---------------------------------------------------------------
    # Validate final common sample
    # ---------------------------------------------------------------

    if jesI.empty:
        raise ValueError(
            "No common country-year observations found across "
            "all five JESI pillars."
        )

    expected_observations = (
        len(EXPECTED_COUNTRIES)
        * len(EXPECTED_YEARS)
    )

    if len(jesI) != expected_observations:
        raise ValueError(
            "Unexpected number of common JESI observations. "
            f"Expected {expected_observations}, "
            f"found {len(jesI)}."
        )

    if set(jesI["country_code"]) != EXPECTED_COUNTRIES:
        raise ValueError(
            "Final JESI dataset does not contain exactly "
            "the expected five countries."
        )

    if set(jesI["year"]) != EXPECTED_YEARS:
        raise ValueError(
            "Final JESI dataset does not contain exactly "
            "the expected years 2016-2023."
        )

    validate_unique_country_year(
        jesI,
        "Final JESI",
    )

    # ---------------------------------------------------------------
    # Validate pillar scores
    # ---------------------------------------------------------------

    if jesI[pillar_columns].isna().any().any():
        missing_counts = (
            jesI[pillar_columns]
            .isna()
            .sum()
        )

        raise ValueError(
            "Missing pillar values detected:\n"
            f"{missing_counts}"
        )

    for column in pillar_columns:
        if (
            (jesI[column] <= 0).any()
            or (jesI[column] > 1).any()
        ):
            raise ValueError(
                f"{column} contains values outside "
                "the valid JESI range (0, 1]."
            )

    # ---------------------------------------------------------------
    # Calculate JESI
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Validate calculated JESI
    # ---------------------------------------------------------------

    if jesI["JESI"].isna().any():
        raise ValueError(
            "Calculated JESI contains missing values."
        )

    if (
        (jesI["JESI"] <= 0).any()
        or (jesI["JESI"] > 100).any()
    ):
        raise ValueError(
            "Calculated JESI values must be in the range (0, 100]."
        )

    # ---------------------------------------------------------------
    # Country-level results
    # ---------------------------------------------------------------

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

    if len(country_results) != len(EXPECTED_COUNTRIES):
        raise ValueError(
            "Final country-level results do not contain "
            "exactly five countries."
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
    ).reset_index(drop=True)

    # ---------------------------------------------------------------
    # Save outputs
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Console output
    # ---------------------------------------------------------------

    print()
    print("Common JESI observations:")
    print(len(jesI))

    print()
    print(
        f"Years: "
        f"{jesI['year'].min()}–"
        f"{jesI['year'].max()}"
    )

    print()
    print("Countries:")
    print(
        sorted(
            jesI["country_code"].unique()
        )
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
        ].to_string(index=False)
    )

    print()
    print("Final country results:")
    print(
        country_results.to_string(
            index=False
        )
    )

    print()
    print(f"Saved: {country_year_file}")
    print(f"Saved: {ranking_file}")

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print(
        "Final JESI calculation completed successfully."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
