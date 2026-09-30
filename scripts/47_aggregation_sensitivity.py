"""
JAS Unified Economic Strength Index (JESI)
Aggregation Sensitivity Analysis

Research-validation layer only.

Purpose
-------
Evaluate whether JESI results are sensitive to the choice of
aggregation function while keeping:

- the same pillar scores
- the same complete-case observations
- the same production pillar weights
- the same normalization
- the same pillar construction
- the same missing-data treatment

The production JESI aggregation remains unchanged.

Production baseline:
    Weighted Geometric Mean

Alternative benchmark:
    Weighted Arithmetic Mean

This script does NOT:
- modify production JESI results
- modify production weights
- modify indicator normalization
- modify pillar construction
- impute missing observations
- remove indicators
- automatically select an aggregation method
- replace the production aggregation function

Analytical benchmark
--------------------
Countries:
- Bangladesh
- India
- Indonesia
- Malaysia
- Vietnam

Period:
- 2016-2023

Expected theoretical panel:
- 5 countries × 8 years = 40 observations

Expected complete-case panel:
- 34 observations

Outputs
-------
data/results/jesi_aggregation_sensitivity_country_year.csv
data/results/jesi_aggregation_sensitivity_country_summary.csv
data/results/jesi_aggregation_sensitivity_rank_correlations.csv
data/results/jesi_aggregation_sensitivity_summary.csv
data/results/jesi_aggregation_sensitivity_report.md
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
    OUTPUT_DIR
    / "jesi_aggregation_sensitivity_country_year.csv"
)

COUNTRY_SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "jesi_aggregation_sensitivity_country_summary.csv"
)

RANK_OUTPUT = (
    OUTPUT_DIR
    / "jesi_aggregation_sensitivity_rank_correlations.csv"
)

SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "jesi_aggregation_sensitivity_summary.csv"
)

REPORT_OUTPUT = (
    OUTPUT_DIR
    / "jesi_aggregation_sensitivity_report.md"
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
# VALIDATION
# ---------------------------------------------------------------------

def fail(message):
    """Raise a clear methodological validation error."""

    raise ValueError(message)


def validate_weights(weights):
    """Validate the fixed production JESI weights."""

    if set(weights) != set(PILLARS):
        fail(
            "Weight specification must contain exactly "
            f"{PILLARS}."
        )

    values = np.array(
        [weights[pillar] for pillar in PILLARS],
        dtype=float,
    )

    if not np.isfinite(values).all():
        fail("Non-finite weight detected.")

    if (values < 0).any():
        fail("Negative weight detected.")

    if not np.isclose(
        values.sum(),
        1.0,
        atol=1e-12,
    ):
        fail(
            "Production weights do not sum to 1.0."
        )


# ---------------------------------------------------------------------
# LOAD PILLAR SOURCE
# ---------------------------------------------------------------------

def load_pillar_source(pillar):
    """
    Load one persisted pillar source.

    No imputation or interpolation is performed.
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

    required = {
        "country",
        "year",
        *PILLAR_SCORE_COLUMNS[pillar],
    }

    if "country_code" in df.columns:
        required.add("country_code")

    missing = required - set(df.columns)

    if missing:
        fail(
            f"Pillar {pillar} source is missing columns: "
            f"{sorted(missing)}"
        )

    # ---------------------------------------------------------------
    # Year
    # ---------------------------------------------------------------

    year = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    if year.isna().any():
        fail(
            f"Pillar {pillar}: invalid year values detected."
        )

    df["year"] = year.astype(int)

    # ---------------------------------------------------------------
    # Country
    # ---------------------------------------------------------------

    if df["country"].isna().any():
        fail(
            f"Pillar {pillar}: missing country values detected."
        )

    # ---------------------------------------------------------------
    # Country code
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
            df["country"].map(country_to_code)
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
                f"Pillar {pillar}: unable to map countries: "
                f"{unknown}"
            )

    else:

        if df["country_code"].isna().any():
            fail(
                f"Pillar {pillar}: missing country_code values."
            )

        df["country_code"] = (
            df["country_code"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    canonical_names = {
        "BGD": "Bangladesh",
        "IND": "India",
        "IDN": "Indonesia",
        "MYS": "Malaysia",
        "VNM": "Vietnam",
    }

    unknown_codes = (
        set(df["country_code"].dropna())
        - set(canonical_names)
    )

    if unknown_codes:
        fail(
            f"Pillar {pillar}: unexpected country codes: "
            f"{sorted(unknown_codes)}"
        )

    df["country"] = (
        df["country_code"].map(canonical_names)
    )

    # ---------------------------------------------------------------
    # Indicator scores
    # ---------------------------------------------------------------

    for column in PILLAR_SCORE_COLUMNS[pillar]:

        numeric = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        invalid = (
            df[column].notna()
            & numeric.isna()
        )

        if invalid.any():
            fail(
                f"Pillar {pillar}: non-numeric values "
                f"in {column}."
            )

        df[column] = numeric

    # ---------------------------------------------------------------
    # Country-year uniqueness
    # ---------------------------------------------------------------

    duplicates = df.duplicated(
        subset=[
            "country_code",
            "year",
        ],
        keep=False,
    )

    if duplicates.any():
        records = (
            df.loc[
                duplicates,
                [
                    "country_code",
                    "year",
                ],
            ]
            .drop_duplicates()
            .to_dict("records")
        )

        fail(
            f"Pillar {pillar}: duplicate country-year "
            f"observations: {records}"
        )

    return df


# ---------------------------------------------------------------------
# BUILD PILLAR PANEL
# ---------------------------------------------------------------------

def build_pillar_panel():
    """
    Construct the five-pillar country-year panel.

    A pillar score is calculated only when every required
    indicator score for that pillar is present.

    Missing observations remain missing.
    """

    panels = []

    for pillar in PILLARS:

        source = load_pillar_source(pillar)

        columns = PILLAR_SCORE_COLUMNS[pillar]

        source = source[
            [
                "country_code",
                "country",
                "year",
                *columns,
            ]
        ].copy()

        complete = (
            source[columns]
            .notna()
            .all(axis=1)
        )

        source[pillar] = (
            source[columns]
            .mean(
                axis=1,
                skipna=False,
            )
        )

        source.loc[
            ~complete,
            pillar,
        ] = np.nan

        panels.append(
            source[
                [
                    "country_code",
                    "country",
                    "year",
                    pillar,
                ]
            ]
        )

    panel = panels[0].copy()

    for next_panel in panels[1:]:

        panel = pd.merge(
            panel,
            next_panel,
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
# COMPLETE-CASE BENCHMARK
# ---------------------------------------------------------------------

def validate_complete_case(panel):
    """
    Restrict analysis to the verified five-country,
    2016-2023 complete-case benchmark.

    No missing values are imputed.
    """

    panel = panel.copy()

    panel = panel[
        panel["country_code"].isin(COUNTRIES)
    ]

    panel = panel[
        panel["year"].isin(FINAL_YEARS)
    ]

    expected = (
        len(COUNTRIES)
        * len(FINAL_YEARS)
    )

    theoretical = panel[
        [
            "country_code",
            "year",
        ]
    ].drop_duplicates()

    if len(theoretical) != expected:
        fail(
            "Theoretical benchmark does not contain "
            f"{expected} country-year identities. "
            f"Found {len(theoretical)}."
        )

    complete = panel[
        PILLARS
    ].notna().all(axis=1)

    complete_panel = panel.loc[
        complete
    ].copy()

    if len(complete_panel) != 34:
        fail(
            "Expected complete-case benchmark of 34 "
            f"observations, found {len(complete_panel)}."
        )

    if complete_panel[PILLARS].isna().any().any():
        fail(
            "Missing pillar scores remain in the "
            "complete-case analytical panel."
        )

    return complete_panel.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)


# ---------------------------------------------------------------------
# AGGREGATION FUNCTIONS
# ---------------------------------------------------------------------

def weighted_geometric_mean(
    df,
    weights,
):
    """
    Production JESI aggregation.

    JESI = 100 × Π(PillarScore ^ Weight)
    """

    values = df[PILLARS].to_numpy(
        dtype=float
    )

    if not np.isfinite(values).all():
        fail(
            "Non-finite pillar score detected."
        )

    if (
        values < 0
    ).any() or (
        values > 1
    ).any():
        fail(
            "Pillar scores outside [0, 1] detected."
        )

    log_value = np.zeros(
        len(df),
        dtype=float,
    )

    zero_mask = np.zeros(
        len(df),
        dtype=bool,
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

        zero_mask |= score == 0

        positive = score > 0

        log_value[positive] += (
            weight
            * np.log(score[positive])
        )

    result = np.exp(log_value)

    result[zero_mask] = 0.0

    return 100.0 * result


def weighted_arithmetic_mean(
    df,
    weights,
):
    """
    Alternative aggregation benchmark.

    JESI = 100 × Σ(PillarScore × Weight)
    """

    values = df[PILLARS].to_numpy(
        dtype=float
    )

    if not np.isfinite(values).all():
        fail(
            "Non-finite pillar score detected."
        )

    if (
        values < 0
    ).any() or (
        values > 1
    ).any():
        fail(
            "Pillar scores outside [0, 1] detected."
        )

    weighted_sum = np.zeros(
        len(df),
        dtype=float,
    )

    for pillar in PILLARS:

        weighted_sum += (
            df[pillar].to_numpy(
                dtype=float
            )
            * float(weights[pillar])
        )

    return 100.0 * weighted_sum


# ---------------------------------------------------------------------
# CALCULATE AGGREGATION SPECIFICATIONS
# ---------------------------------------------------------------------

def calculate_aggregation_results(
    panel,
    weights,
):
    """
    Calculate both production and alternative aggregation
    results from exactly the same pillar-score panel.
    """

    result = panel[
        [
            "country_code",
            "country",
            "year",
            *PILLARS,
        ]
    ].copy()

    result["production_geometric"] = (
        weighted_geometric_mean(
            result,
            weights,
        )
    )

    result["alternative_arithmetic"] = (
        weighted_arithmetic_mean(
            result,
            weights,
        )
    )

    result["absolute_difference"] = (
        result["alternative_arithmetic"]
        - result["production_geometric"]
    ).abs()

    result["signed_difference"] = (
        result["alternative_arithmetic"]
        - result["production_geometric"]
    )

    return result


# ---------------------------------------------------------------------
# COUNTRY SUMMARY
# ---------------------------------------------------------------------

def build_country_summary(
    country_year,
):
    """
    Calculate country-level mean JESI under both
    aggregation functions.
    """

    grouped = (
        country_year
        .groupby(
            [
                "country_code",
                "country",
            ],
            as_index=False,
        )
        .agg(
            production_geometric_mean=(
                "production_geometric",
                "mean",
            ),
            alternative_arithmetic_mean=(
                "alternative_arithmetic",
                "mean",
            ),
            mean_absolute_difference=(
                "absolute_difference",
                "mean",
            ),
            max_absolute_difference=(
                "absolute_difference",
                "max",
            ),
            mean_signed_difference=(
                "signed_difference",
                "mean",
            ),
        )
    )

    grouped["production_rank"] = (
        grouped[
            "production_geometric_mean"
        ]
        .rank(
            method="min",
            ascending=False,
        )
    )

    grouped["alternative_rank"] = (
        grouped[
            "alternative_arithmetic_mean"
        ]
        .rank(
            method="min",
            ascending=False,
        )
    )

    grouped["absolute_rank_change"] = (
        grouped["alternative_rank"]
        - grouped["production_rank"]
    ).abs()

    return grouped


# ---------------------------------------------------------------------
# RANK CORRELATIONS
# ---------------------------------------------------------------------

def build_rank_correlations(
    country_year,
):
    """
    Compare rankings produced by the two aggregation functions
    at country-year and country-mean levels.
    """

    rows = []

    # ---------------------------------------------------------------
    # Country-year level
    # ---------------------------------------------------------------

    if len(country_year) >= 2:

        rho, p_value = spearmanr(
            country_year[
                "production_geometric"
            ],
            country_year[
                "alternative_arithmetic"
            ],
        )

    else:

        rho = np.nan
        p_value = np.nan

    rows.append(
        {
            "analysis_level": "country_year",
            "pairwise_n": len(country_year),
            "spearman_rho": rho,
            "spearman_p_value": p_value,
        }
    )

    # ---------------------------------------------------------------
    # Country-mean level
    # ---------------------------------------------------------------

    country_means = (
        country_year
        .groupby(
            [
                "country_code",
                "country",
            ],
        )[
            [
                "production_geometric",
                "alternative_arithmetic",
            ]
        ]
        .mean()
        .dropna()
    )

    if len(country_means) >= 2:

        rho, p_value = spearmanr(
            country_means[
                "production_geometric"
            ],
            country_means[
                "alternative_arithmetic"
            ],
        )

    else:

        rho = np.nan
        p_value = np.nan

    rows.append(
        {
            "analysis_level": "country_mean",
            "pairwise_n": len(country_means),
            "spearman_rho": rho,
            "spearman_p_value": p_value,
        }
    )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# SENSITIVITY SUMMARY
# ---------------------------------------------------------------------

def build_sensitivity_summary(
    country_year,
    country_summary,
):
    """
    Produce the main aggregation-sensitivity diagnostics.
    """

    production = (
        country_year[
            "production_geometric"
        ]
    )

    alternative = (
        country_year[
            "alternative_arithmetic"
        ]
    )

    rank_changes = (
        country_summary[
            "absolute_rank_change"
        ]
    )

    country_rank_correlation = (
        spearmanr(
            country_summary[
                "production_geometric_mean"
            ],
            country_summary[
                "alternative_arithmetic_mean"
            ],
        ).statistic
        if len(country_summary) >= 2
        else np.nan
    )

    return pd.DataFrame(
        [
            {
                "production_aggregation": (
                    "weighted_geometric_mean"
                ),
                "alternative_aggregation": (
                    "weighted_arithmetic_mean"
                ),
                "country_year_n": len(
                    country_year
                ),
                "country_n": len(
                    country_summary
                ),
                "mean_absolute_jesi_difference": (
                    (
                        alternative
                        - production
                    )
                    .abs()
                    .mean()
                ),
                "max_absolute_jesi_difference": (
                    (
                        alternative
                        - production
                    )
                    .abs()
                    .max()
                ),
                "mean_signed_jesi_difference": (
                    alternative
                    - production
                ).mean(),
                "max_absolute_country_rank_change": (
                    rank_changes.max()
                ),
                "countries_with_rank_change": int(
                    (rank_changes > 0).sum()
                ),
                "country_mean_spearman": (
                    country_rank_correlation
                ),
            }
        ]
    )


# ---------------------------------------------------------------------
# MATHEMATICAL VALIDATION
# ---------------------------------------------------------------------

def validate_calculations(
    country_year,
    weights,
):
    """
    Independently recalculate both aggregation functions
    and verify exact agreement.
    """

    expected_geometric = (
        weighted_geometric_mean(
            country_year,
            weights,
        )
    )

    expected_arithmetic = (
        weighted_arithmetic_mean(
            country_year,
            weights,
        )
    )

    geometric_difference = (
        expected_geometric
        - country_year[
            "production_geometric"
        ].to_numpy(
            dtype=float
        )
    )

    arithmetic_difference = (
        expected_arithmetic
        - country_year[
            "alternative_arithmetic"
        ].to_numpy(
            dtype=float
        )
    )

    geometric_max_error = np.max(
        np.abs(
            geometric_difference
        )
    )

    arithmetic_max_error = np.max(
        np.abs(
            arithmetic_difference
        )
    )

    if geometric_max_error > 1e-10:
        fail(
            "Weighted geometric aggregation mathematical "
            "validation failed. "
            f"Maximum error = {geometric_max_error}"
        )

    if arithmetic_max_error > 1e-10:
        fail(
            "Weighted arithmetic aggregation mathematical "
            "validation failed. "
            f"Maximum error = {arithmetic_max_error}"
        )


# ---------------------------------------------------------------------
# RESEARCH REPORT
# ---------------------------------------------------------------------

def build_report(
    country_year,
    country_summary,
    rank_results,
    sensitivity_summary,
):
    """
    Build an audit-ready research report.

    The report describes evidence without selecting a preferred
    aggregation function.
    """

    lines = []

    lines.append(
        "# JESI Aggregation Sensitivity Analysis"
    )
    lines.append("")

    lines.append(
        "## Research-validation status"
    )
    lines.append("")

    lines.append(
        "This analysis is a research-validation layer only. "
        "It evaluates whether JESI results are sensitive to the "
        "choice of aggregation function while preserving the "
        "production pillar scores, production weights, normalization, "
        "pillar construction, and missing-data treatment."
    )
    lines.append("")

    lines.append(
        "The production JESI methodology is not modified by this "
        "analysis."
    )
    lines.append("")

    lines.append(
        "## Production aggregation"
    )
    lines.append("")

    lines.append(
        "The current production JESI aggregation is the weighted "
        "geometric mean:"
    )
    lines.append("")

    lines.append(
        "JESI = 100 × Π(Pillar Score ^ Pillar Weight)"
    )
    lines.append("")

    lines.append(
        "Production pillar weights:"
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
        "## Alternative aggregation benchmark"
    )
    lines.append("")

    lines.append(
        "The alternative benchmark is the weighted arithmetic mean:"
    )
    lines.append("")

    lines.append(
        "JESI_alt = 100 × Σ(Pillar Score × Pillar Weight)"
    )
    lines.append("")

    lines.append(
        "The same production pillar weights are used for the "
        "alternative aggregation so that the experiment isolates "
        "aggregation-function sensitivity rather than weight "
        "sensitivity."
    )
    lines.append("")

    lines.append(
        "## Analytical benchmark"
    )
    lines.append("")

    lines.extend(
        [
            "- Countries: Bangladesh, India, Indonesia, Malaysia, Vietnam",
            "- Comparison period: 2016-2023",
            "- Theoretical country-year observations: 40",
            "- Complete-case observations: 34",
            "- Missing-data treatment: no imputation",
            "",
        ]
    )

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
        "## Country-level results"
    )
    lines.append("")

    lines.append(
        country_summary.to_markdown(
            index=False,
            floatfmt=".6f",
        )
    )
    lines.append("")

    lines.append(
        "## Interpretation"
    )
    lines.append("")

    lines.append(
        "The aggregation sensitivity results describe how much "
        "JESI changes when the production weighted geometric "
        "aggregation is replaced by the specified weighted "
        "arithmetic benchmark while all underlying pillar scores "
        "and production weights remain unchanged."
    )
    lines.append("")

    lines.append(
        "High rank correlation and small score differences indicate "
        "greater stability between the tested aggregation functions. "
        "Material score or rank differences constitute sensitivity "
        "signals requiring methodological consideration."
    )
    lines.append("")

    lines.append(
        "This analysis does not designate a preferred aggregation "
        "function and does not automatically change the production "
        "JESI methodology."
    )
    lines.append("")

    lines.append(
        "## Methodological limitation"
    )
    lines.append("")

    lines.append(
        "Only the specified alternative aggregation benchmark is "
        "tested here. Therefore, the results should be interpreted "
        "as sensitivity evidence within this experimental design "
        "rather than proof of robustness to every possible "
        "aggregation function."
    )
    lines.append("")

    lines.append(
        "Aggregation sensitivity is one component of the broader "
        "JESI validation sequence and must be considered together "
        "with pillar validity, indicator validity, redundancy/"
        "correlation, normalization sensitivity, weight sensitivity, "
        "historical validation, and the final methodological judgment."
    )
    lines.append("")

    lines.append(
        "## Mathematical validation"
    )
    lines.append("")

    lines.append(
        "Both aggregation functions were independently recalculated "
        "and compared with the persisted analytical results using "
        "a numerical tolerance of 1e-10."
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    print("=" * 78)
    print("JESI AGGREGATION SENSITIVITY ANALYSIS")
    print("=" * 78)

    # ---------------------------------------------------------------
    # Validate production weights.
    # ---------------------------------------------------------------

    validate_weights(
        BASELINE_WEIGHTS
    )

    print()
    print("Production weights validated.")

    # ---------------------------------------------------------------
    # Build pillar panel.
    # ---------------------------------------------------------------

    print()
    print(
        "Loading persisted pillar-score sources..."
    )

    panel = build_pillar_panel()

    print(
        f"Raw analytical panel rows: {len(panel)}"
    )

    # ---------------------------------------------------------------
    # Complete-case benchmark.
    # ---------------------------------------------------------------

    complete_panel = (
        validate_complete_case(
            panel
        )
    )

    print(
        "Complete-case observations: "
        f"{len(complete_panel)}"
    )

    # ---------------------------------------------------------------
    # Calculate aggregation alternatives.
    # ---------------------------------------------------------------

    country_year = (
        calculate_aggregation_results(
            complete_panel,
            BASELINE_WEIGHTS,
        )
    )

    # ---------------------------------------------------------------
    # Mathematical validation.
    # ---------------------------------------------------------------

    validate_calculations(
        country_year,
        BASELINE_WEIGHTS,
    )

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
        build_rank_correlations(
            country_year
        )
    )

    # ---------------------------------------------------------------
    # Sensitivity summary.
    # ---------------------------------------------------------------

    sensitivity_summary = (
        build_sensitivity_summary(
            country_year,
            country_summary,
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
    # Persist outputs.
    # ---------------------------------------------------------------

    country_year.to_csv(
        COUNTRY_YEAR_OUTPUT,
        index=False,
    )

    country_summary.to_csv(
        COUNTRY_SUMMARY_OUTPUT,
        index=False,
    )

    rank_results.to_csv(
        RANK_OUTPUT,
        index=False,
    )

    sensitivity_summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
    )

    report = build_report(
        country_year,
        country_summary,
        rank_results,
        sensitivity_summary,
    )

    REPORT_OUTPUT.write_text(
        report,
        encoding="utf-8",
    )

    # ---------------------------------------------------------------
    # Console summary.
    # ---------------------------------------------------------------

    print()
    print("=" * 78)
    print("AGGREGATION SENSITIVITY SUMMARY")
    print("=" * 78)

    print(
        sensitivity_summary.to_string(
            index=False
        )
    )

    print()
    print("Rank correlations:")

    print(
        rank_results.to_string(
            index=False
        )
    )

    print()
    print("Output files:")

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
        "Aggregation sensitivity analysis: PASSED"
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
