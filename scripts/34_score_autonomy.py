"""
JESI Strategic Autonomy Scoring
Master Version 1.0

Scores Strategic Autonomy indicators using empirical
P10-P90 reference bounds.

Missing official-source observations are preserved
as exclusions. No imputation is performed.
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/raw/autonomy_indicators_2015_2024_complete.csv"
)

OUTPUT_FILE = Path(
    "data/processed/autonomy_indicator_scores_2015_2024.csv"
)

EXCLUDED_FILE = Path(
    "data/processed/"
    "strategic_autonomy_excluded_observations_2015_2024.csv"
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

    required_columns = {
        "country_code",
        "country",
        "year",
        *INDICATORS,
    }

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Input file is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    for indicator in INDICATORS:
        df[indicator] = pd.to_numeric(
            df[indicator],
            errors="coerce",
        )

    # ---------------------------------------------------------------
    # Identify official-source exclusions
    # ---------------------------------------------------------------

    complete_mask = (
        df[INDICATORS]
        .notna()
        .all(axis=1)
    )

    excluded = df.loc[
        ~complete_mask,
        [
            "country_code",
            "country",
            "year",
            *INDICATORS,
        ],
    ].copy()

    if not excluded.empty:
        excluded["missing_indicators"] = (
            excluded.apply(
                lambda row: ",".join(
                    indicator
                    for indicator in INDICATORS
                    if pd.isna(row[indicator])
                ),
                axis=1,
            )
        )

        excluded = excluded[
            [
                "country_code",
                "country",
                "year",
                "missing_indicators",
            ]
        ].sort_values(
            [
                "country_code",
                "year",
            ]
        )

    # ---------------------------------------------------------------
    # Complete-case scoring dataset
    # ---------------------------------------------------------------

    scored = df.loc[
        complete_mask
    ].copy()

    if scored.empty:
        raise ValueError(
            "No complete Strategic Autonomy observations "
            "are available for scoring."
        )

    bounds = {}

    for indicator in INDICATORS:
        lower = scored[
            indicator
        ].quantile(0.10)

        upper = scored[
            indicator
        ].quantile(0.90)

        bounds[indicator] = {
            "lower": lower,
            "upper": upper,
        }

    # ---------------------------------------------------------------
    # Normalize indicators
    # ---------------------------------------------------------------

    scored["eci_score"] = scored[
        "eci"
    ].apply(
        lambda x: normalize_positive(
            x,
            bounds["eci"]["lower"],
            bounds["eci"]["upper"],
        )
    )

    scored["high_tech_exports_score"] = scored[
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

    scored[
        "import_product_concentration_score"
    ] = scored[
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

    # ---------------------------------------------------------------
    # Save outputs
    # ---------------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    scored.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    excluded.to_csv(
        EXCLUDED_FILE,
        index=False,
    )

    # ---------------------------------------------------------------
    # Console diagnostics
    # ---------------------------------------------------------------

    print()
    print(
        "Official-source coverage:"
    )

    print(
        f"Total benchmark observations: {len(df)}"
    )

    print(
        f"Complete observations scored: {len(scored)}"
    )

    print(
        f"Excluded observations: {len(excluded)}"
    )

    if not excluded.empty:
        print()
        print(
            "Excluded country-year observations:"
        )

        print(
            excluded.to_string(
                index=False
            )
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
        "Scored output:",
        OUTPUT_FILE,
    )

    print(
        "Exclusion output:",
        EXCLUDED_FILE,
    )

    print()
    print("=" * 70)
    print("STATUS: GREEN")
    print(
        "Strategic Autonomy scoring completed "
        "using complete official-source observations."
    )
    print(
        "No missing observation was imputed."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
