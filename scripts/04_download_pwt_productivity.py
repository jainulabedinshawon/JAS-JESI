"""
JAS-JESI Real Data Pipeline
Step 2: Download PWT 11.0 TFP Data

JAS Unified Economic Strength Index (JESI)
Master Version 1.0

Productivity indicator:

Total Factor Productivity Growth
Source: Penn World Table 11.0
Variable: rtfpna

Countries:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia

Period:
    2015–2023
"""

from pathlib import Path

import pandas as pd


PWT_URL = (
    "https://dataverse.nl/api/access/datafile/554105"
)

COUNTRIES = [
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
]

START_YEAR = 2015
END_YEAR = 2023

OUTPUT_DIR = Path("data/raw")

OUTPUT_FILE = (
    OUTPUT_DIR
    / "pwt_tfp_growth_2015_2023.csv"
)


def main():
    """
    Download PWT 11.0 and construct annual TFP growth.
    """

    print(
        "Downloading PWT 11.0 TFP data..."
    )

    print(
        f"Countries: {COUNTRIES}"
    )

    print(
        f"Years: {START_YEAR}-{END_YEAR}"
    )

    dataframe = pd.read_excel(
        PWT_URL,
        sheet_name=0,
    )

    required_columns = [
        "country",
        "year",
        "rtfpna",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing PWT columns: {missing_columns}"
        )

    dataframe = dataframe[
        dataframe["country"].isin(COUNTRIES)
        & dataframe["year"].between(
            START_YEAR - 1,
            END_YEAR,
        )
    ].copy()

    dataframe = dataframe.sort_values(
        [
            "country",
            "year",
        ]
    )

    dataframe["tfp_growth"] = (
        dataframe
        .groupby("country")["rtfpna"]
        .pct_change()
        * 100
    )

    dataframe = dataframe[
        dataframe["year"].between(
            START_YEAR,
            END_YEAR,
        )
    ]

    result = dataframe[
        [
            "country",
            "year",
            "rtfpna",
            "tfp_growth",
        ]
    ].copy()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        "PWT TFP download completed."
    )

    print(
        f"Rows: {len(result)}"
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
