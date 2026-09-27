"""
JESI Strategic Autonomy Scoring
Master Version 1.0

Scores Strategic Autonomy indicators using empirical
P10-P90 reference bounds.

No missing-value imputation is permitted.
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024_complete.csv"
)

OUTPUT_FILE = Path(
    "data/processed/autonomy_indicator_scores_2015_2024.csv"
)

INDICATORS = [
    "eci",
    "high_tech_exports",
    "import_product_concentration",
]


def normalize_positive(value, lower, upper):
    if upper == lower:
        raise ValueError(
            "Upper and lower reference values "
            "cannot be equal."
        )

    score = (
        (value - lower)
        / (upper - lower)
    )

    return max(
        0.0,
        min(
            1.0,
            score,
        ),
    )


def normalize_negative(value, lower, upper):
    if upper == lower:
        raise ValueError(
            "Upper and lower reference values "
            "cannot be equal."
        )

    score = (
        (upper - value)
        / (upper - lower)
    )

    return max(
        0.0,
        min(
            1.0,
            score,
        ),
    )


def main():
    print("=" * 70)
    print("JESI Strategic Autonomy Scoring")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    for indicator in INDICATORS:
        df[indicator] = pd.to_numeric(
            df[indicator],
            errors="coerce",
        )

    missing = (
        df[INDICATORS]
        .isna()
        .sum()
    )

    if missing.any():
        print()
        print(
            "SCORING BLOCKED:"
        )
        print(
            "Missing source observations "
            "remain in the dataset."
        )
        print()
        print(missing)

        raise ValueError(
            "Strategic Autonomy scoring cannot proceed "
            "until the official-source coverage issue "
            "is resolved. No imputation is permitted."
        )

    bounds = {}

    for indicator in INDICATORS:
        lower = df[
            indicator
        ].quantile(0.10)

        upper = df[
            indicator
        ].quantile(0.90)

        bounds[indicator] = {
            "lower": lower,
            "upper": upper,
        }

    df["eci_score"] = df[
        "eci"
    ].apply(
        lambda x: normalize_positive(
            x,
            bounds["eci"]["lower"],
            bounds["eci"]["upper"],
        )
    )

    df["high_tech_exports_score"] = df[
        "high_tech_exports"
    ].apply(
        lambda x: normalize_positive(
            x,
            bounds[
                "high_tech_exports"
            ]["lower"],
            bounds[
                "high_tech_exports"
            ]["upper"],
        )
    )

    df[
        "import_product_concentration_score"
    ] = df[
        "import_product_concentration"
    ].apply(
        lambda x: normalize_negative(
            x,
            bounds[
                "import_product_concentration"
            ]["lower"],
            bounds[
                "import_product_concentration"
            ]["upper"],
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        "P10-P90 reference bounds:"
    )

    for indicator, values in bounds.items():
        print(
            f"{indicator}: "
            f"{values['lower']:.6f} -> "
            f"{values['upper']:.6f}"
        )

    print()
    print(
        "Output:",
        OUTPUT_FILE,
    )

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print(
        "Strategic Autonomy scoring completed."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
