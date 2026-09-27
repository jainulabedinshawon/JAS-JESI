"""
JESI Strategic Autonomy Pillar Construction
Master Version 1.0

Constructs the Strategic Autonomy pillar from
three normalized indicator scores.

No missing score is allowed.
No imputation is performed.
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/processed/autonomy_indicator_scores_2015_2024.csv"
)

OUTPUT_FILE = Path(
    "data/processed/strategic_autonomy_pillar_2015_2024.csv"
)

SCORE_COLUMNS = [
    "eci_score",
    "high_tech_exports_score",
    "import_product_concentration_score",
]


def main():
    print("=" * 70)
    print("JESI Strategic Autonomy Pillar Construction")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    missing_columns = [
        column
        for column in SCORE_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing score columns: "
            f"{missing_columns}"
        )

    missing_scores = (
        df[SCORE_COLUMNS]
        .isna()
        .sum()
    )

    if missing_scores.any():
        print()
        print(
            "PILLAR CONSTRUCTION BLOCKED:"
        )
        print(
            missing_scores
        )

        raise ValueError(
            "Strategic Autonomy pillar cannot be "
            "constructed because indicator scores "
            "contain missing values."
        )

    for column in SCORE_COLUMNS:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if df[column].isna().any():
            raise ValueError(
                f"{column} contains invalid values."
            )

        if (
            (df[column] < 0).any()
            or (df[column] > 1).any()
        ):
            raise ValueError(
                f"{column} contains values outside [0, 1]."
            )

    df[
        "strategic_autonomy_arithmetic"
    ] = df[
        SCORE_COLUMNS
    ].mean(
        axis=1
    )

    geometric_values = np.clip(
        df[
            SCORE_COLUMNS
        ].to_numpy(
            dtype=float
        ),
        1e-12,
        1.0,
    )

    df[
        "strategic_autonomy_geometric"
    ] = np.exp(
        np.log(
            geometric_values
        ).mean(
            axis=1
        )
    )

    output_columns = [
        "country_code",
        "country",
        "year",
        "eci_score",
        "high_tech_exports_score",
        "import_product_concentration_score",
        "strategic_autonomy_arithmetic",
        "strategic_autonomy_geometric",
    ]

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df[
        output_columns
    ].to_csv(
        OUTPUT_FILE,
        index=False,
    )

    summary = (
        df.groupby(
            "country"
        )[
            [
                "strategic_autonomy_arithmetic",
                "strategic_autonomy_geometric",
            ]
        ]
        .mean()
        .sort_values(
            "strategic_autonomy_arithmetic",
            ascending=False,
        )
    )

    summary_file = Path(
        "data/processed/"
        "strategic_autonomy_country_summary_2015_2024.csv"
    )

    summary.to_csv(
        summary_file
    )

    print()
    print(
        "Strategic Autonomy pillar constructed."
    )

    print()
    print(
        "Output:",
        OUTPUT_FILE,
    )

    print(
        "Summary:",
        summary_file,
    )

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print(
        "Strategic Autonomy pillar construction completed."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
