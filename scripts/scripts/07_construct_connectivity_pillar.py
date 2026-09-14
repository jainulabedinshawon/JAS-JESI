"""
JAS-JESI Real Data Pipeline
Step 3: Construct Connectivity Pillar

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

Connectivity indicators:

1. Trade Openness
2. FDI Net Inflows (% of GDP)
3. Individuals Using Internet (% of population)

A country-year is excluded when any required
Connectivity indicator is missing.
"""

from pathlib import Path

import pandas as pd

from src.connectivity_pillar import (
    normalize_positive,
    construct_connectivity_score,
)


INPUT_FILE = Path(
    "data/raw/connectivity_indicators_2015_2024.csv"
)

OUTPUT_DIR = Path("data/raw")

OUTPUT_FILE = (
    OUTPUT_DIR
    / "connectivity_pillar_2015_2024.csv"
)


TRADE = "NE.TRD.GNFS.ZS"
FDI = "BX.KLT.DINV.WD.GD.ZS"
INTERNET = "IT.NET.USER.ZS"


def main():
    """
    Construct normalized Connectivity pillar scores.
    """

    print(
        "Constructing JESI Connectivity pillar..."
    )
    print()

    dataframe = pd.read_csv(
        INPUT_FILE
    )

    dataframe = dataframe[
        dataframe["indicator"].isin(
            [
                TRADE,
                FDI,
                INTERNET,
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
            TRADE: "trade_openness",
            FDI: "fdi_inflows",
            INTERNET: "internet_use",
        }
    )

    required = [
        "trade_openness",
        "fdi_inflows",
        "internet_use",
    ]

    pivoted["connectivity_complete"] = (
        pivoted[required]
        .notna()
        .all(axis=1)
    )

    complete = pivoted[
        pivoted["connectivity_complete"]
    ].copy()

    print(
        f"Total country-year observations: "
        f"{len(pivoted)}"
    )

    print(
        f"Complete Connectivity observations: "
        f"{len(complete)}"
    )

    print(
        f"Excluded incomplete observations: "
        f"{len(pivoted) - len(complete)}"
    )

    print()

    if complete.empty:
        raise ValueError(
            "No complete Connectivity observations available."
        )

    trade_min = complete[
        "trade_openness"
    ].min()

    trade_max = complete[
        "trade_openness"
    ].max()

    fdi_min = complete[
        "fdi_inflows"
    ].min()

    fdi_max = complete[
        "fdi_inflows"
    ].max()

    internet_min = complete[
        "internet_use"
    ].min()

    internet_max = complete[
        "internet_use"
    ].max()

    complete[
        "trade_openness_norm"
    ] = complete[
        "trade_openness"
    ].apply(
        normalize_positive,
        args=(
            trade_min,
            trade_max,
        ),
    )

    complete[
        "fdi_inflows_norm"
    ] = complete[
        "fdi_inflows"
    ].apply(
        normalize_positive,
        args=(
            fdi_min,
            fdi_max,
        ),
    )

    complete[
        "internet_use_norm"
    ] = complete[
        "internet_use"
    ].apply(
        normalize_positive,
        args=(
            internet_min,
            internet_max,
        ),
    )

    complete["C"] = complete.apply(
        lambda row: construct_connectivity_score(
            trade_openness=row[
                "trade_openness_norm"
            ],
            fdi_inflows=row[
                "fdi_inflows_norm"
            ],
            internet_use=row[
                "internet_use_norm"
            ],
        ),
        axis=1,
    )

    result = complete[
        [
            "country",
            "year",
            "trade_openness",
            "fdi_inflows",
            "internet_use",
            "trade_openness_norm",
            "fdi_inflows_norm",
            "internet_use_norm",
            "C",
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
        "Connectivity pillar construction completed."
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print()
    print(
        result.head(10)
    )


if __name__ == "__main__":
    main()
