"""
JAS-JESI Connectivity Pillar Construction

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

This script constructs the Connectivity (C) pillar
from normalized World Bank indicators.

Connectivity indicators:
    1. Trade Openness
    2. FDI Net Inflows (% GDP)
    3. Internet Users (% population)

Period:
    2015–2024
"""

from pathlib import Path

import pandas as pd

from src.connectivity_pillar import (
    construct_connectivity_score,
    normalize_positive,
)


INPUT_FILE = Path(
    "data/raw/connectivity_indicators_2015_2024.csv"
)

OUTPUT_FILE = Path(
    "data/raw/connectivity_pillar_2015_2024.csv"
)


INDICATORS = {
    "NE.TRD.GNFS.ZS": "trade_openness",
    "BX.KLT.DINV.WD.GD.ZS": "fdi_inflows",
    "IT.NET.USER.ZS": "internet_use",
}


def main():
    print("Constructing JESI Connectivity pillar...")

    data = pd.read_csv(INPUT_FILE)

    data["indicator_name"] = data["indicator"].map(
        INDICATORS
    )

    data = data.dropna(
        subset=[
            "country",
            "year",
            "indicator",
            "value",
        ]
    )

    pivot = data.pivot_table(
        index=[
            "country",
            "year",
        ],
        columns="indicator_name",
        values="value",
        aggfunc="first",
    ).reset_index()

    required_columns = [
        "trade_openness",
        "fdi_inflows",
        "internet_use",
    ]

    pivot = pivot.dropna(
        subset=required_columns
    ).copy()

    print(
        f"Complete country-years: {len(pivot)}"
    )

    normalized_columns = []

    for column in required_columns:
        minimum = pivot[column].min()
        maximum = pivot[column].max()

        normalized_column = (
            f"{column}_normalized"
        )

        pivot[normalized_column] = (
            pivot[column]
            .apply(
                lambda value: normalize_positive(
                    value,
                    minimum,
                    maximum,
                )
            )
        )

        normalized_columns.append(
            normalized_column
        )

    pivot["C"] = pivot.apply(
        lambda row: construct_connectivity_score(
            row["trade_openness_normalized"],
            row["fdi_inflows_normalized"],
            row["internet_use_normalized"],
        ),
        axis=1,
    )

    output = pivot[
        [
            "country",
            "year",
            "trade_openness",
            "fdi_inflows",
            "internet_use",
            "trade_openness_normalized",
            "fdi_inflows_normalized",
            "internet_use_normalized",
            "C",
        ]
    ]

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("Connectivity pillar construction completed.")
    print(f"Rows: {len(output)}")
    print(f"Saved to: {OUTPUT_FILE}")
    print()
    print(output.head(10))


if __name__ == "__main__":
    main()
