"""
JAS Unified Economic Strength Index (JESI)
Weight Sensitivity Analysis

Research-validation layer only.

Purpose
-------
This module evaluates the sensitivity of JESI results to alternative
pillar-weight specifications while preserving the production JESI
methodology.

It does NOT:
- modify production JESI weights
- modify indicator normalization
- modify production pillar construction
- modify missing-data treatment
- modify aggregation methodology
- remove indicators
- reweight indicators automatically
- overwrite production JESI results
- select a preferred weighting specification

Baseline production weights
---------------------------
G = 0.20
P = 0.25
C = 0.20
R = 0.20
A = 0.15

Analytical benchmark
--------------------
Countries:
- Bangladesh
- India
- Indonesia
- Malaysia
- Vietnam

Final comparison period:
- 2016-2023

Expected theoretical panel:
- 5 countries × 8 years = 40 observations

Expected complete-case panel:
- 34 observations

Missing observations are NOT imputed.

Outputs
-------
data/results/jesi_weight_sensitivity_country_year.csv
data/results/jesi_weight_sensitivity_country_summary.csv
data/results/jesi_weight_sensitivity_rank_correlations.csv
data/results/jesi_weight_sensitivity_summary.csv
data/results/jesi_weight_sensitivity_report.md
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT / "data/results"

COUNTRY_YEAR_OUTPUT = (
    OUTPUT_DIR / "jesi_weight_sensitivity_country_year.csv"
)

COUNTRY_SUMMARY_OUTPUT = (
    OUTPUT_DIR / "jesi_weight_sensitivity_country_summary.csv"
)

RANK_OUTPUT = (
    OUTPUT_DIR / "jesi_weight_sensitivity_rank_correlations.csv"
)

SUMMARY_OUTPUT = (
    OUTPUT_DIR / "jesi_weight_sensitivity_summary.csv"
)

REPORT_OUTPUT = (
    OUTPUT_DIR / "jesi_weight_sensitivity_report.md"
)


# ---------------------------------------------------------------------
# VERIFIED ANALYTICAL BENCHMARK
# ---------------------------------------------------------------------

COUNTRIES = [
    "BGD",
    "IND",
    "IDN",
    "MYS",
    "VNM",
]

FINAL_YEARS = list(range(2016, 2024))


# ---------------------------------------------------------------------
# PRODUCTION JESI BASELINE WEIGHTS
# ---------------------------------------------------------------------

BASELINE_WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}


PILLAR_NAMES = {
    "G": "Growth",
    "P": "Productivity",
    "C": "Connectivity",
    "R": "Resilience",
    "A": "Strategic Autonomy",
}


PILLARS = [
    "G",
    "P",
    "C",
    "R",
    "A",
]


# ---------------------------------------------------------------------
# INPUT FILES
# ---------------------------------------------------------------------

PILLAR_FILES = {
    "G": (
        "data/processed/"
        "growth_pillar_scores_2015_2024.csv"
    ),
    "P": (
        "data/processed/"
        "productivity_pillar_scores_2016_2023.csv"
    ),
    "C": (
        "data/processed/"
        "connectivity_indicator_scores_2015_2024.csv"
    ),
    "R": (
        "data/processed/"
        "resilience_pillar_scores_2015_2024.csv"
    ),
    "A": (
        "data/processed/"
        "autonomy_indicator_scores_2015_2024.csv"
    ),
}


# ---------------------------------------------------------------------
# PILLAR SCORE DEFINITIONS
# ---------------------------------------------------------------------

PILLAR_SCORE_COLUMNS = {
    "G": [
        "real_gdp_growth_percentile",
        "gni_per_capita_growth_percentile",
    ],
    "P": [
        "productivity_p1_score",
        "productivity_p2_score",
    ],
    "C": [
        "connectivity_trade_score",
        "connectivity_fdi_score",
        "connectivity_internet_score",
    ],
    "R": [
        "R1_fx_reserves_score",
        "R2_debt_score",
        "R3_current_account_score",
    ],
    "A": [
        "eci_score",
        "high_tech_exports_score",
        "import_product_concentration_score",
    ],
}


# ---------------------------------------------------------------------
# VALIDATION HELPERS
# ---------------------------------------------------------------------

def fail(message):
    """Raise a clear methodological validation error."""

    raise ValueError(message)


def validate_weights(weights, specification_name):
    """
    Validate one complete pillar-weight specification.

    Requirements:
    - exactly five pillars
    - no negative weights
    - all weights finite
    - weights sum to 1 within numerical tolerance
    """

    if set(weights.keys()) != set(PILLARS):
        fail(
            f"{specification_name}: weight specification must "
            f"contain exactly the five JESI pillars {PILLARS}."
        )

    values = np.array(
        [weights[pillar] for pillar in PILLARS],
        dtype=float,
    )

    if not np.isfinite(values).all():
        fail(
            f"{specification_name}: non-finite weight detected."
        )

    if (values < 0).any():
        fail(
            f"{specification_name}: negative weight detected."
        )

    total = float(values.sum())

    if not np.isclose(
        total,
        1.0,
        atol=1e-12,
    ):
        fail(
            f"{specification_name}: weights sum to {total}, "
            "not 1.0."
        )


# ---------------------------------------------------------------------
# GEOMETRIC JESI
# ---------------------------------------------------------------------

def geometric_jesi(
    df,
    weights,
):
    """
    Calculate weighted geometric JESI.

    JESI = 100 × Π(PillarScore ^ PillarWeight)

    Pillar scores must be in [0, 1].

    Zero scores are allowed and produce JESI = 0.

    No clipping is performed.
    """

    pillar_values = df[PILLARS].to_numpy(
        dtype=float
    )

    if not np.isfinite(pillar_values).all():
        fail(
            "Non-finite pillar score detected during JESI "
            "calculation."
        )

    if (
        pillar_values < 0
    ).any() or (
        pillar_values > 1
    ).any():
        fail(
            "Pillar scores outside [0, 1] detected during "
            "JESI calculation."
        )

    weighted_log_terms = np.zeros(
        len(df),
        dtype=float,
    )

    for pillar in PILLARS:

        score = df[pillar].to_numpy(
            dtype=float
        )

        weight = float(
            weights[pillar]
        )

        if weight == 0:
            continue

        positive = score > 0

        weighted_log_terms[positive] += (
            weight
            * np.log(score[positive])
        )

        zero_mask = ~positive

        if zero_mask.any():
            weighted_log_terms[zero_mask] = -np.inf

    result = np.exp(
        weighted_log_terms
    )

    return 100.0 * result


# ---------------------------------------------------------------------
# LOAD ONE PILLAR SOURCE
# ---------------------------------------------------------------------

def load_pillar_source(
    pillar,
):
    """
    Load and validate one persisted pillar source.

    No imputation, interpolation, or replacement is performed.
    """

    relative_file = PILLAR_FILES[pillar]

    path = ROOT / relative_file

    if not path.exists():
        fail(
            f"Missing required source for pillar {pillar}: "
            f"{relative_file}"
        )

    df = pd.read_csv(path)

    if df.empty:
        fail(
            f"Pillar {pillar} source is empty: "
            f"{relative_file}"
        )

    required_columns = {
        "country",
        "year",
        *PILLAR_SCORE_COLUMNS[pillar],
    }

    if "country_code" in df.columns:
        required_columns.add(
            "country_code"
        )

    missing_columns = (
        required_columns - set(df.columns)
    )

    if missing_columns:
        fail(
            f"Pillar {pillar} source is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    # ---------------------------------------------------------------
    # Validate year.
    # ---------------------------------------------------------------

    year = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    if year.isna().any():
        fail(
            f"Pillar {pillar}: non-numeric year values detected."
        )

    df["year"] = year.astype(int)

    # ---------------------------------------------------------------
    # Validate country.
    # ---------------------------------------------------------------

    if df["country"].isna().any():
        fail(
            f"Pillar {pillar}: missing country values detected."
        )

    # ---------------------------------------------------------------
    # Validate country code.
    # ---------------------------------------------------------------

    if "country_code" not in df.columns:

        country_to_code = {
            "Bangladesh": "BGD",
            "India": "IND",
            "Indonesia": "IDN",
            "Malaysia": "MYS",
            "Vietnam": "VNM",
            "Viet Nam": "VNM",
        }

        df["country_code"] = (
            df["country"]
            .map(country_to_code)
        )

        unknown = (
            df.loc[
                df["country_code"].isna(),
                "country",
            ]
            .drop_duplicates()
            .tolist()
        )

        if unknown:
            fail(
                f"Pillar {pillar}: unable to map country names "
                f"to verified country codes: {unknown}"
            )

    # ---------------------------------------------------------------
    # Validate indicator-score columns.
    # ---------------------------------------------------------------

    for column in PILLAR_SCORE_COLUMNS[pillar]:

        numeric = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        non_numeric = (
            df[column].notna()
            & numeric.isna()
        )

        if non_numeric.any():
            fail(
                f"Pillar {pillar}: non-numeric values detected "
                f"in {column}."
            )

        df[column] = numeric

    # ---------------------------------------------------------------
    # Validate country-year uniqueness.
    # ---------------------------------------------------------------

    duplicate_mask = df.duplicated(
        subset=[
            "country_code",
            "year",
        ],
        keep=False,
    )

    if duplicate_mask.any():

        duplicates = (
            df.loc[
                duplicate_mask,
                [
                    "country_code",
                    "year",
                ],
            ]
            .drop_duplicates()
            .to_dict(
                "records"
            )
        )

        fail(
            f"Pillar {pillar}: duplicate country-year "
            f"observations detected: {duplicates}"
        )

    return df


# ---------------------------------------------------------------------
# BUILD PILLAR PANEL
# ---------------------------------------------------------------------

def build_pillar_panel():
    """
    Construct a country-year panel containing the five current JESI
    pillar scores.

    Missing observations remain missing.

    IMPORTANT:
    A pillar is constructed only when ALL required indicator scores
    are present for that country-year.

    No partial mean and no imputation are permitted.
    """

    pillar_panels = []

    for pillar in PILLARS:

        source = load_pillar_source(
            pillar
        )

        score_columns = (
            PILLAR_SCORE_COLUMNS[pillar]
        )

        source = source[
            [
                "country_code",
                "country",
                "year",
                *score_columns,
            ]
        ].copy()

        # -----------------------------------------------------------
        # Complete-case pillar construction.
        #
        # pandas.DataFrame.mean() does not support min_count.
        # Therefore the complete-case condition is enforced
        # explicitly before calculating the arithmetic mean.
        #
        # If ANY required indicator is missing, the pillar score
        # remains NaN.
        # -----------------------------------------------------------

        complete_indicator_mask = (
            source[score_columns]
            .notna()
            .all(axis=1)
        )

        source[pillar] = (
            source[score_columns]
            .mean(
                axis=1,
                skipna=False,
            )
        )

        source.loc[
            ~complete_indicator_mask,
            pillar,
        ] = np.nan

        source = source[
            [
                "country_code",
                "country",
                "year",
                pillar,
            ]
        ]

        pillar_panels.append(
            source
        )

    # ---------------------------------------------------------------
    # Merge all pillars.
    # ---------------------------------------------------------------

    panel = pillar_panels[0].copy()

    for index, next_panel in enumerate(
        pillar_panels[1:],
        start=1,
    ):

        next_pillar = PILLARS[index]

        panel = pd.merge(
            panel,
            next_panel[
                [
                    "country_code",
                    "country",
                    "year",
                    next_pillar,
                ]
            ],
            on=[
                "country_code",
                "country",
                "year",
            ],
            how="outer",
            validate="one_to_one",
        )

    return panel


# ---------------------------------------------------------------------
# BUILD WEIGHT SPECIFICATIONS
# ---------------------------------------------------------------------

def build_weight_specifications():
    """
    Build the complete set of sensitivity specifications.

    Specifications
    --------------
    baseline
        Current production weights.

    equal_weights
        Equal 20% weight across all five pillars.

    For each pillar:
        +5pp
            Increase selected pillar by 0.05 and proportionally
            rescale all other pillars downward.

        -5pp
            Decrease selected pillar by 0.05 and proportionally
            rescale all other pillars upward.

    The proportional-rescaling rule preserves:
        sum(weights) = 1
    """

    specifications = {
        "baseline": dict(
            BASELINE_WEIGHTS
        ),
        "equal_weights": {
            pillar: 0.20
            for pillar in PILLARS
        },
    }

    for target in PILLARS:

        # -----------------------------------------------------------
        # +5 percentage points
        # -----------------------------------------------------------

        positive_name = (
            f"{target}_plus_5pp"
        )

        positive = dict(
            BASELINE_WEIGHTS
        )

        original_target = (
            BASELINE_WEIGHTS[target]
        )

        positive[target] = (
            original_target + 0.05
        )

        remaining_original = (
            1.0 - original_target
        )

        remaining_new = (
            1.0 - positive[target]
        )

        for pillar in PILLARS:

            if pillar == target:
                continue

            positive[pillar] = (
                BASELINE_WEIGHTS[pillar]
                * remaining_new
                / remaining_original
            )

        specifications[
            positive_name
        ] = positive

        # -----------------------------------------------------------
        # -5 percentage points
        # -----------------------------------------------------------

        negative_name = (
            f"{target}_minus_5pp"
        )

        negative = dict(
            BASELINE_WEIGHTS
        )

        negative[target] = (
            original_target - 0.05
        )

        if negative[target] < 0:
            fail(
                f"{negative_name}: negative target weight "
                "would be produced."
            )

        remaining_original = (
            1.0 - original_target
        )

        remaining_new = (
            1.0 - negative[target]
        )

        for pillar in PILLARS:

            if pillar == target:
                continue

            negative[pillar] = (
                BASELINE_WEIGHTS[pillar]
                * remaining_new
                / remaining_original
            )

        specifications[
            negative_name
        ] = negative

    # ---------------------------------------------------------------
    # Validate every specification.
    # ---------------------------------------------------------------

    for name, weights in specifications.items():

        validate_weights(
            weights,
            name,
        )

    return specifications


# ---------------------------------------------------------------------
# COMPLETE-CASE VALIDATION
# ---------------------------------------------------------------------

def validate_complete_case(
    panel,
):
    """
    Restrict the analytical benchmark to the expected final period
    and five-country panel.

    Expected theoretical panel:
        5 × 8 = 40

    Expected complete-case observations:
        34

    No observations are imputed.
    """

    final = panel[
        panel["year"].isin(
            FINAL_YEARS
        )
        & panel["country_code"].isin(
            COUNTRIES
        )
    ].copy()

    theoretical = (
        len(COUNTRIES)
        * len(FINAL_YEARS)
    )

    unique_keys = (
        final[
            [
                "country_code",
                "year",
            ]
        ]
        .drop_duplicates()
    )

    if len(unique_keys) != theoretical:
        fail(
            "The analytical final panel does not contain the "
            f"expected {theoretical} country-year combinations. "
            f"Found {len(unique_keys)}."
        )

    complete = (
        final[PILLARS]
        .notna()
        .all(axis=1)
    )

    scored = final.loc[
        complete
    ].copy()

    expected_complete = 34

    if len(scored) != expected_complete:
        fail(
            "Complete-case benchmark mismatch: expected "
            f"{expected_complete} observations, found "
            f"{len(scored)}."
        )

    # ---------------------------------------------------------------
    # Validate pillar-score range.
    # ---------------------------------------------------------------

    if (
        scored[PILLARS]
        .lt(0)
        .any()
        .any()
    ):
        fail(
            "Negative pillar scores detected in complete-case panel."
        )

    if (
        scored[PILLARS]
        .gt(1)
        .any()
        .any()
    ):
        fail(
            "Pillar scores above 1 detected in complete-case panel."
        )

    return scored


# ---------------------------------------------------------------------
# CALCULATE ALL WEIGHTED JESI SPECIFICATIONS
# ---------------------------------------------------------------------

def calculate_specifications(
    baseline_panel,
    specifications,
):
    """
    Calculate JESI for every weight specification.

    The input pillar scores are unchanged.
    """

    results = []

    for name, weights in specifications.items():

        df = baseline_panel.copy()

        df["JESI"] = geometric_jesi(
            df,
            weights,
        )

        df["specification"] = name

        for pillar in PILLARS:
            df[
                f"weight_{pillar}"
            ] = weights[pillar]

        results.append(
            df[
                [
                    "country_code",
                    "country",
                    "year",
                    *PILLARS,
                    "JESI",
                    "specification",
                    "weight_G",
                    "weight_P",
                    "weight_C",
                    "weight_R",
                    "weight_A",
                ]
            ]
        )

    return pd.concat(
        results,
        ignore_index=True,
    )


# ---------------------------------------------------------------------
# COUNTRY SUMMARY
# ---------------------------------------------------------------------

def build_country_summary(
    country_year,
):
    """
    Calculate country-level mean JESI and ranking for every
    specification.

    Ranking is descriptive only.
    """

    summary = (
        country_year
        .groupby(
            [
                "specification",
                "country_code",
                "country",
            ],
            as_index=False,
        )
        .agg(
            mean_jesi=(
                "JESI",
                "mean",
            ),
            observations=(
                "JESI",
                "count",
            ),
        )
    )

    summary["rank"] = (
        summary
        .groupby(
            "specification"
        )["mean_jesi"]
        .rank(
            method="min",
            ascending=False,
        )
        .astype(int)
    )

    return summary.sort_values(
        [
            "specification",
            "rank",
            "country_code",
        ]
    ).reset_index(
        drop=True
    )


# ---------------------------------------------------------------------
# RANK CORRELATION
# ---------------------------------------------------------------------

def calculate_rank_correlations(
    country_year,
    baseline_name="baseline",
):
    """
    Compare every alternative specification with the production
    baseline using Spearman rank correlation.

    Two analytical levels are reported:
    - country-year observations
    - country mean JESI
    """

    baseline = country_year[
        country_year["specification"]
        == baseline_name
    ]

    alternatives = (
        country_year[
            country_year["specification"]
            != baseline_name
        ]["specification"]
        .drop_duplicates()
        .tolist()
    )

    rows = []

    for specification in alternatives:

        alternative = country_year[
            country_year["specification"]
            == specification
        ]

        merged = pd.merge(
            baseline[
                [
                    "country_code",
                    "year",
                    "JESI",
                ]
            ],
            alternative[
                [
                    "country_code",
                    "year",
                    "JESI",
                ]
            ],
            on=[
                "country_code",
                "year",
            ],
            how="inner",
            suffixes=(
                "_baseline",
                "_alternative",
            ),
        )

        # -----------------------------------------------------------
        # Country-year level
        # -----------------------------------------------------------

        if len(merged) >= 2:

            country_year_rho, country_year_p = (
                spearmanr(
                    merged["JESI_baseline"],
                    merged["JESI_alternative"],
                )
            )

        else:

            country_year_rho = np.nan
            country_year_p = np.nan

        rows.append(
            {
                "specification": specification,
                "analysis_level": "country_year",
                "pairwise_n": len(merged),
                "spearman_rho": country_year_rho,
                "spearman_p_value": country_year_p,
            }
        )

        # -----------------------------------------------------------
        # Country-mean level
        # -----------------------------------------------------------

        baseline_country = (
            merged
            .groupby(
                "country_code"
            )["JESI_baseline"]
            .mean()
        )

        alternative_country = (
            merged
            .groupby(
                "country_code"
            )["JESI_alternative"]
            .mean()
        )

        country_joined = pd.concat(
            [
                baseline_country.rename(
                    "baseline"
                ),
                alternative_country.rename(
                    "alternative"
                ),
            ],
            axis=1,
            join="inner",
        ).dropna()

        if len(country_joined) >= 2:

            country_mean_rho, country_mean_p = (
                spearmanr(
                    country_joined["baseline"],
                    country_joined["alternative"],
                )
            )

        else:

            country_mean_rho = np.nan
            country_mean_p = np.nan

        rows.append(
            {
                "specification": specification,
                "analysis_level": "country_mean",
                "pairwise_n": len(country_joined),
                "spearman_rho": country_mean_rho,
                "spearman_p_value": country_mean_p,
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# SENSITIVITY SUMMARY
# ---------------------------------------------------------------------

def build_sensitivity_summary(
    country_year,
    baseline_name="baseline",
):
    """
    Calculate score and ranking stability diagnostics for every
    alternative weighting specification.
    """

    baseline = country_year[
        country_year["specification"]
        == baseline_name
    ].copy()

    alternatives = (
        country_year[
            country_year["specification"]
            != baseline_name
        ]["specification"]
        .drop_duplicates()
        .tolist()
    )

    rows = []

    for specification in alternatives:

        alternative = country_year[
            country_year["specification"]
            == specification
        ].copy()

        merged = pd.merge(
            baseline[
                [
                    "country_code",
                    "country",
                    "year",
                    "JESI",
                ]
            ],
            alternative[
                [
                    "country_code",
                    "country",
                    "year",
                    "JESI",
                ]
            ],
            on=[
                "country_code",
                "country",
                "year",
            ],
            how="inner",
            suffixes=(
                "_baseline",
                "_alternative",
            ),
        )

        absolute_difference = (
            merged["JESI_alternative"]
            - merged["JESI_baseline"]
        ).abs()

        # -----------------------------------------------------------
        # Country means
        # -----------------------------------------------------------

        baseline_country = (
            merged
            .groupby(
                [
                    "country_code",
                    "country",
                ]
            )["JESI_baseline"]
            .mean()
        )

        alternative_country = (
            merged
            .groupby(
                [
                    "country_code",
                    "country",
                ]
            )["JESI_alternative"]
            .mean()
        )

        country_joined = pd.concat(
            [
                baseline_country.rename(
                    "baseline"
                ),
                alternative_country.rename(
                    "alternative"
                ),
            ],
            axis=1,
            join="inner",
        ).dropna()

        baseline_rank = (
            country_joined["baseline"]
            .rank(
                method="min",
                ascending=False,
            )
        )

        alternative_rank = (
            country_joined["alternative"]
            .rank(
                method="min",
                ascending=False,
            )
        )

        rank_change = (
            alternative_rank
            - baseline_rank
        ).abs()

        # -----------------------------------------------------------
        # Spearman country-mean rank correlation
        # -----------------------------------------------------------

        if len(country_joined) >= 2:

            country_rank_rho = (
                spearmanr(
                    country_joined["baseline"],
                    country_joined["alternative"],
                ).statistic
            )

        else:

            country_rank_rho = np.nan

        rows.append(
            {
                "specification": specification,
                "country_year_n": len(merged),
                "mean_absolute_jesi_difference": (
                    absolute_difference.mean()
                ),
                "max_absolute_jesi_difference": (
                    absolute_difference.max()
                ),
                "mean_country_jesi_difference": (
                    (
                        country_joined["alternative"]
                        - country_joined["baseline"]
                    )
                    .abs()
                    .mean()
                ),
                "max_country_rank_change": (
                    rank_change.max()
                    if not rank_change.empty
                    else np.nan
                ),
                "countries_with_rank_change": int(
                    (rank_change > 0).sum()
                ),
                "country_rank_spearman": (
                    country_rank_rho
                ),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# WEIGHT TABLE
# ---------------------------------------------------------------------

def build_weight_table(
    specifications,
):
    """
    Create an explicit audit table containing every tested
    weight specification.
    """

    rows = []

    for name, weights in specifications.items():

        rows.append(
            {
                "specification": name,
                "G_weight": weights["G"],
                "P_weight": weights["P"],
                "C_weight": weights["C"],
                "R_weight": weights["R"],
                "A_weight": weights["A"],
                "weight_sum": sum(
                    weights.values()
                ),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# MATHEMATICAL VALIDATION
# ---------------------------------------------------------------------

def validate_results(
    country_year,
    specifications,
):
    """
    Recalculate JESI independently for every specification and
    verify exact agreement with persisted analytical results.
    """

    for specification, weights in specifications.items():

        subset = country_year[
            country_year["specification"]
            == specification
        ].copy()

        recalculated = geometric_jesi(
            subset,
            weights,
        )

        difference = (
            recalculated
            - subset["JESI"].to_numpy(
                dtype=float
            )
        )

        max_difference = (
            np.max(
                np.abs(
                    difference
                )
            )
        )

        if max_difference > 1e-10:
            fail(
                f"{specification}: JESI mathematical "
                "validation failed. "
                f"Maximum absolute difference = "
                f"{max_difference}"
            )

        for pillar in PILLARS:

            stored_column = (
                f"weight_{pillar}"
            )

            expected = weights[pillar]

            if not np.allclose(
                subset[stored_column],
                expected,
                atol=1e-12,
            ):
                fail(
                    f"{specification}: stored {pillar} "
                    "weight does not match specification."
                )


# ---------------------------------------------------------------------
# RESEARCH REPORT
# ---------------------------------------------------------------------

def build_report(
    specifications,
    sensitivity_summary,
    rank_results,
):
    """
    Generate an audit-ready Markdown report.

    No ranking preference or recommended weighting is declared.
    """

    lines = []

    lines.append(
        "# JESI Weight Sensitivity Analysis"
    )
    lines.append("")

    lines.append(
        "## Research-validation status"
    )
    lines.append("")

    lines.append(
        "This analysis is a research-validation layer only. "
        "It evaluates the sensitivity of JESI results to alternative "
        "pillar-weight specifications without modifying the production "
        "JESI methodology, production weights, normalization, pillar "
        "construction, missing-data treatment, or final repository "
        "results."
    )
    lines.append("")

    lines.append(
        "## Production baseline"
    )
    lines.append("")

    lines.extend(
        [
            "- Growth (G): 0.20",
            "- Productivity (P): 0.25",
            "- Connectivity (C): 0.20",
            "- Resilience (R): 0.20",
            "- Strategic Autonomy (A): 0.15",
            "",
        ]
    )

    lines.append(
        "The baseline is the current production JESI weighting "
        "specification. This analysis does not replace or revise it."
    )
    lines.append("")

    lines.append(
        "## Analytical benchmark"
    )
    lines.append("")

    lines.extend(
        [
            "- Countries: Bangladesh, India, Indonesia, Malaysia, Vietnam",
            "- Final comparison period: 2016-2023",
            "- Theoretical country-year observations: 40",
            "- Complete-case observations: 34",
            "- Missing-data treatment: no imputation",
            "",
        ]
    )

    lines.append(
        "## Weight sensitivity design"
    )
    lines.append("")

    lines.append(
        "The analysis compares the production baseline with "
        "equal weights and controlled one-pillar perturbations."
    )
    lines.append("")

    lines.append(
        "For each one-pillar perturbation, the selected pillar "
        "is changed by 5 percentage points. The remaining pillar "
        "weights are proportionally rescaled so that the total "
        "weight remains exactly 1."
    )
    lines.append("")

    lines.append(
        "This design isolates the sensitivity associated with "
        "pillar-weight assumptions while keeping the underlying "
        "pillar scores unchanged."
    )
    lines.append("")

    lines.append(
        "## Tested weight specifications"
    )
    lines.append("")

    weight_table = build_weight_table(
        specifications
    )

    lines.append(
        weight_table.to_markdown(
            index=False,
            floatfmt=".6f",
        )
    )
    lines.append("")

    lines.append(
        "## JESI aggregation"
    )
    lines.append("")

    lines.append(
        "For every specification, JESI is calculated using the "
        "same weighted geometric aggregation:"
    )
    lines.append("")

    lines.append(
        "JESI = 100 × Π(Pillar Score ^ Pillar Weight)"
    )
    lines.append("")

    lines.append(
        "The aggregation function itself is not changed by this "
        "sensitivity analysis."
    )
    lines.append("")

    lines.append(
        "## Sensitivity summary"
    )
    lines.append("")

    lines.append(
        sensitivity_summary.to_markdown(
            index=False,
            floatfmt=".6f",
        )
    )
    lines.append("")

    lines.append(
        "## Rank-correlation results"
    )
    lines.append("")

    lines.append(
        rank_results.to_markdown(
            index=False,
            floatfmt=".6f",
        )
    )
    lines.append("")

    lines.append(
        "## Interpretation rule"
    )
    lines.append("")

    lines.append(
        "High rank correlation and small score/rank changes indicate "
        "greater stability under the tested weighting specification. "
        "Material score or rank changes constitute sensitivity signals "
        "that require methodological consideration."
    )
    lines.append("")

    lines.append(
        "The analysis does not designate a preferred weighting "
        "specification, automatically change the production weights, "
        "remove any pillar, or reweight any indicator."
    )
    lines.append("")

    lines.append(
        "## Methodological limitation"
    )
    lines.append("")

    lines.append(
        "The tested perturbation range is deliberately bounded. "
        "The results therefore describe sensitivity within the "
        "specified experimental design and should not be interpreted "
        "as proof of robustness for all possible weighting schemes."
    )
    lines.append("")

    lines.append(
        "Weight sensitivity is one component of the broader JESI "
        "validation sequence. It must be considered together with "
        "pillar validity, indicator validity, redundancy/correlation, "
        "normalization sensitivity, aggregation sensitivity, historical "
        "validation, and the final methodological judgment."
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    print("=" * 78)
    print("JESI WEIGHT SENSITIVITY ANALYSIS")
    print("=" * 78)

    # ---------------------------------------------------------------
    # Validate production weights.
    # ---------------------------------------------------------------

    validate_weights(
        BASELINE_WEIGHTS,
        "baseline",
    )

    print()
    print("Production baseline weights:")

    for pillar in PILLARS:
        print(
            f"  {pillar} "
            f"({PILLAR_NAMES[pillar]}): "
            f"{BASELINE_WEIGHTS[pillar]:.6f}"
        )

    # ---------------------------------------------------------------
    # Build weight specifications.
    # ---------------------------------------------------------------

    specifications = (
        build_weight_specifications()
    )

    print()
    print(
        "Weight specifications:"
    )

    for name, weights in specifications.items():

        print(
            f"  {name}: "
            + ", ".join(
                f"{pillar}={weights[pillar]:.6f}"
                for pillar in PILLARS
            )
        )

    # ---------------------------------------------------------------
    # Build analytical pillar panel.
    # ---------------------------------------------------------------

    print()
    print(
        "Loading current persisted pillar-score sources..."
    )

    panel = build_pillar_panel()

    print(
        f"  Raw analytical panel rows: {len(panel)}"
    )

    # ---------------------------------------------------------------
    # Validate final complete-case benchmark.
    # ---------------------------------------------------------------

    complete_panel = (
        validate_complete_case(
            panel
        )
    )

    print(
        "  Complete-case observations: "
        f"{len(complete_panel)}"
    )

    # ---------------------------------------------------------------
    # Calculate all weighting specifications.
    # ---------------------------------------------------------------

    country_year = (
        calculate_specifications(
            complete_panel,
            specifications,
        )
    )

    # ---------------------------------------------------------------
    # Validate calculations independently.
    # ---------------------------------------------------------------

    validate_results(
        country_year,
        specifications,
    )

    print()
    print(
        "Mathematical validation: PASSED"
    )

    # ---------------------------------------------------------------
    # Country summary.
    # ---------------------------------------------------------------

    country_summary = (
        build_country_summary(
            country_year
        )
    )

    # ---------------------------------------------------------------
    # Rank correlations.
    # ---------------------------------------------------------------

    rank_results = (
        calculate_rank_correlations(
            country_year
        )
    )

    # ---------------------------------------------------------------
    # Sensitivity summary.
    # ---------------------------------------------------------------

    sensitivity_summary = (
        build_sensitivity_summary(
            country_year
        )
    )

    # ---------------------------------------------------------------
    # Output directory.
    # ---------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Save country-year results.
    # ---------------------------------------------------------------

    country_year.to_csv(
        COUNTRY_YEAR_OUTPUT,
        index=False,
    )

    # ---------------------------------------------------------------
    # Save country summary.
    # ---------------------------------------------------------------

    country_summary.to_csv(
        COUNTRY_SUMMARY_OUTPUT,
        index=False,
    )

    # ---------------------------------------------------------------
    # Save rank correlations.
    # ---------------------------------------------------------------

    rank_results.to_csv(
        RANK_OUTPUT,
        index=False,
    )

    # ---------------------------------------------------------------
    # Save sensitivity summary.
    # ---------------------------------------------------------------

    sensitivity_summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
    )

    # ---------------------------------------------------------------
    # Save research report.
    # ---------------------------------------------------------------

    report = build_report(
        specifications,
        sensitivity_summary,
        rank_results,
    )

    REPORT_OUTPUT.write_text(
        report,
        encoding="utf-8",
    )

    # ---------------------------------------------------------------
    # Console output.
    # ---------------------------------------------------------------

    print()
    print("=" * 78)
    print("WEIGHT SENSITIVITY SUMMARY")
    print("=" * 78)

    print(
        sensitivity_summary.to_string(
            index=False
        )
    )

    print()
    print(
        "Rank correlations:"
    )

    print(
        rank_results.to_string(
            index=False
        )
    )

    print()
    print(
        "Output files:"
    )

    print(
        f"  - {COUNTRY_YEAR_OUTPUT}"
    )

    print(
        f"  - {COUNTRY_SUMMARY_OUTPUT}"
    )

    print(
        f"  - {RANK_OUTPUT}"
    )

    print(
        f"  - {SUMMARY_OUTPUT}"
    )

    print(
        f"  - {REPORT_OUTPUT}"
    )

    print()
    print(
        "Weight sensitivity analysis: PASSED"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()
