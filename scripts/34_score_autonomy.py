"""
JESI Strategic Autonomy Scoring
Master Version 1.0

Scores Strategic Autonomy indicators using empirical
P10–P90 reference bounds.

Positive indicators:
    ECI
    High-Tech Exports

Negative indicator:
    Import Product Concentration
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
            "Upper and lower reference values cannot be equal."
        )

    score = (value - lower) / (upper - lower)

    return max(0.0, min(1.0, score))


def normalize_negative(value, lower, upper):
    if upper == lower:
        raise ValueError(
            "Upper and lower reference values cannot be equal."
        )

    score = (upper - value) / (upper - lower)

    return max(0.0, min(1.0, score))


def main():
    print("=" * 70)
    print("JESI Strategic Autonomy Scoring")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    for indicator in INDICATORS:
        df[indicator] = pd.to_numeric(
            df[indicator],
            errors="coerce",
        )

    if df[INDICATORS].isna().any().any():
        raise ValueError(
            "Missing values detected in Strategic Autonomy indicators."
        )

    # ------------------------------------------------------------
    # Empirical P10–P90 reference bounds
    # ------------------------------------------------------------

    bounds = {}

    for indicator in INDICATORS:
        lower = df[indicator].quantile(0.10)
        upper = df[indicator].quantile(0.90)

        bounds[indicator] = {
            "lower": lower,
            "upper": upper,
        }

    # ------------------------------------------------------------
    # Score indicators
    # ------------------------------------------------------------

    df["eci_score"] = df["eci"].apply(
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
            bounds["high_tech_exports"]["lower"],
            bounds["high_tech_exports"]["upper"],
        )
    )

    # Higher import concentration = weaker autonomy.
    df["import_product_concentration_score"] = df[
        "import_product_concentration"
    ].apply(
        lambda x: normalize_negative(
            x,
            bounds["import_product_concentration"]["lower"],
            bounds["import_product_concentration"]["upper"],
        )
    )

    # ------------------------------------------------------------
    # Save
    # ------------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # ------------------------------------------------------------
    # Print reference bounds
    # ------------------------------------------------------------

    print()
    print("P10–P90 reference bounds:")

    for indicator, values in bounds.items():
        print(
            f"{indicator}: "
            f"{values['lower']:.6f} → "
            f"{values['upper']:.6f}"
        )

    print()
    print("Score summary:")

    score_columns = [
        "eci_score",
        "high_tech_exports_score",
        "import_product_concentration_score",
    ]

    print(df[score_columns].describe())

    print()
    print(f"Output: {OUTPUT_FILE}")

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print("Strategic Autonomy indicator scoring completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
