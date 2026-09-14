"""
JAS-JESI Real Data Pipeline
Step 3: Construct Growth Pillar

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This script constructs the normalized Growth (G)
pillar score from:

1. Real GDP Growth Rate
2. GNI per Capita Growth

A country-year is excluded from Growth pillar
construction when either required indicator
is missing.
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/raw/growth_indicators_2015_2025.csv"
)

OUTPUT_DIR = Path("data/raw")

OUTPUT_FILE = (
    OUTPUT_DIR
    / "growth_pillar_2015_2025.csv"
)


GDP_GROWTH = "NY.GDP.MKTP.KD.ZG"
GNI_GROWTH = "NY.GNP.PCAP.KD.ZG"


def normalize_positive(
    value,
    minimum,
    maximum,
):
    """
    Normalize a positive-direction indicator
    to a 0–1 scale.
    """

    if maximum == minimum:
        raise ValueError(
            "Maximum and minimum cannot be equal."
        )

    return (
        (value - minimum)
        / (maximum - minimum)
    )


def main():
    """
    Construct normalized Growth pillar scores.
    """

    print(
        "Constructing JESI Growth pillar..."
    )
    print()

    dataframe = pd.read_csv(
        INPUT_FILE
    )

    dataframe = dataframe[
        dataframe["indicator"].isin(
            [
                GDP_GROWTH,
                GNI_GROWTH,
            ]
        )
    ].copy()

    pivoted = dataframe.pivot_table(
        index=[
            "country",
            "year",
        ],
        columns="indicator",
        values="value",
        aggfunc="first",
    ).reset_index()

    pivoted = pivoted.rename(
        columns={
            GDP_GROWTH: "gdp_growth",
            GNI_GROWTH: "gni_pc_growth",
        }
    )

    pivoted["growth_complete"] = (
        pivoted["gdp_growth"].notna()
        & pivoted["gni_pc_growth"].notna()
    )

    complete = pivoted[
        pivoted["growth_complete"]
    ].copy()

    print(
        f"Total country-year observations: "
        f"{len(pivoted)}"
    )

    print(
        f"Complete Growth observations: "
        f"{len(complete)}"
    )

    print(
        f"Excluded incomplete observations: "
        f"{len(pivoted) - len(complete)}"
    )

    print()

    if complete.empty:
        raise ValueError(
            "No complete Growth observations available."
        )

    gdp_min = complete[
        "gdp_growth"
    ].min()

    gdp_max = complete[
        "gdp_growth"
    ].max()

    gni_min = complete[
        "gni_pc_growth"
    ].min()

    gni_max = complete[
        "gni_pc_growth"
    ].max()

    complete[
        "gdp_growth_norm"
    ] = complete[
        "gdp_growth"
    ].apply(
        normalize_positive,
        args=(
            gdp_min,
            gdp_max,
        ),
    )

    complete[
        "gni_pc_growth_norm"
    ] = complete[
        "gni_pc_growth"
    ].apply(
        normalize_positive,
        args=(
            gni_min,
            gni_max,
        ),
    )

    complete["G"] = (
        complete[
            "gdp_growth_norm"
        ]
        + complete[
            "gni_pc_growth_norm"
        ]
    ) / 2

    result = complete[
        [
            "country",
            "year",
            "gdp_growth",
            "gni_pc_growth",
            "gdp_growth_norm",
            "gni_pc_growth_norm",
            "G",
        ]
    ].sort_values(
        [
            "country",
            "year",
        ]
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "Growth pillar construction completed."
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print()

    print(result.head(10))


if __name__ == "__main__":
    main()
