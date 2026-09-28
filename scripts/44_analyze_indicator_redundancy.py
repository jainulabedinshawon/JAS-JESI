"""
JAS Unified Economic Strength Index (JESI)
Indicator Redundancy / Correlation Analysis

Research-validation layer only.

Purpose
-------
This module evaluates within-pillar relationships among the current
indicator-level values persisted in the JESI repository.

It does NOT:
- modify JESI calculations
- modify JESI weights
- modify normalization
- modify final JESI scores
- impute missing observations
- interpolate missing observations
- fabricate or replace data

Primary analysis
---------------
The primary redundancy analysis uses the currently persisted
indicator-level score representations so that indicators from all
five pillars are evaluated on a consistent analytical representation.

Statistics
----------
- Pearson correlation
- Spearman correlation
- Pairwise usable observation count (N)
- Indicator-level missingness
- Descriptive correlation bands
- Methodological review flags
- Pillar-level summaries

Outputs
-------
data/results/jesi_indicator_redundancy_pairwise.csv
data/results/jesi_indicator_redundancy_missingness.csv
data/results/jesi_indicator_redundancy_pillar_summary.csv
data/results/jesi_indicator_redundancy_report.md
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


# -------------------------------------------------------------------
# PATHS
# -------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT / "data/results"


# -------------------------------------------------------------------
# CURRENT REPOSITORY INDICATOR DEFINITIONS
#
# These mappings were aligned to the currently persisted repository
# files and their actual column names.
# -------------------------------------------------------------------

PILLAR_SOURCES = {
    "G": {
        "file": (
            "data/processed/"
            "growth_pillar_scores_2015_2024.csv"
        ),
        "country_column": "country",
        "country_code_column": "country_code",
        "year_column": "year",
        "indicators": {
            "real_gdp_growth": "real_gdp_growth_percentile",
            "gni_per_capita_growth": (
                "gni_per_capita_growth_percentile"
            ),
        },
    },
    "P": {
        "file": (
            "data/processed/"
            "productivity_pillar_scores_2016_2023.csv"
        ),
        "country_column": "country",
        "country_code_column": "country_code",
        "year_column": "year",
        "indicators": {
            "productivity_p1": "productivity_p1_score",
            "productivity_p2": "productivity_p2_score",
        },
    },
    "C": {
        "file": (
            "data/processed/"
            "connectivity_indicator_scores_2015_2024.csv"
        ),
        "country_column": "country",
        "country_code_column": "country_code",
        "year_column": "year",
        "indicators": {
            "trade_openness": "connectivity_trade_score",
            "fdi_inflows": "connectivity_fdi_score",
            "internet_use": "connectivity_internet_score",
        },
    },
    "R": {
        "file": (
            "data/processed/"
            "resilience_pillar_scores_2015_2024.csv"
        ),
        "country_column": "country",
        "country_code_column": None,
        "year_column": "year",
        "indicators": {
            "fx_reserves": "R1_fx_reserves_score",
            "government_debt": "R2_debt_score",
            "current_account": "R3_current_account_score",
        },
    },
    "A": {
        "file": (
            "data/processed/"
            "autonomy_indicator_scores_2015_2024.csv"
        ),
        "country_column": "country",
        "country_code_column": "country_code",
        "year_column": "year",
        "indicators": {
            "economic_complexity": "eci_score",
            "high_tech_exports": "high_tech_exports_score",
            "import_product_concentration": (
                "import_product_concentration_score"
            ),
        },
    },
}


PILLAR_NAMES = {
    "G": "Growth",
    "P": "Productivity",
    "C": "Connectivity",
    "R": "Resilience",
    "A": "Strategic Autonomy",
}


# -------------------------------------------------------------------
# DESCRIPTIVE CORRELATION BANDS
# -------------------------------------------------------------------

def correlation_band(value):
    """
    Assign a descriptive band based on absolute correlation.

    These bands are descriptive screening categories only.
    They do not establish that an indicator is redundant.
    """

    if pd.isna(value):
        return "Not estimable"

    absolute_value = abs(float(value))

    if absolute_value < 0.30:
        return "Low"

    if absolute_value < 0.50:
        return "Moderate"

    if absolute_value < 0.70:
        return "High"

    if absolute_value < 0.90:
        return "Very high"

    return "Extremely high"


def methodological_flag(
    pearson_value,
    spearman_value,
):
    """
    Produce a conservative methodological screening flag.

    The flag identifies pairs that warrant substantive review.
    It does NOT declare the indicators redundant.
    """

    values = [
        abs(float(x))
        for x in [
            pearson_value,
            spearman_value,
        ]
        if pd.notna(x)
    ]

    if not values:
        return "INSUFFICIENT_DATA"

    maximum = max(values)

    if maximum >= 0.90:
        return "REVIEW_EXTREMELY_HIGH_CORRELATION"

    if maximum >= 0.70:
        return "REVIEW_HIGH_CORRELATION"

    return "NO_HIGH_CORRELATION_FLAG"


# -------------------------------------------------------------------
# INPUT VALIDATION
# -------------------------------------------------------------------

def load_and_validate_source(
    pillar,
    specification,
):
    """
    Load one pillar's current persisted indicator-score dataset
    and validate its structure without altering observations.
    """

    relative_file = specification["file"]
    path = ROOT / relative_file

    if not path.exists():
        raise FileNotFoundError(
            f"Missing required indicator source for pillar {pillar}: "
            f"{relative_file}"
        )

    df = pd.read_csv(path)

    required_columns = {
        specification["country_column"],
        specification["year_column"],
        *specification["indicators"].values(),
    }

    if specification["country_code_column"] is not None:
        required_columns.add(
            specification["country_code_column"]
        )

    missing_columns = (
        required_columns - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Pillar {pillar} source is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if df.empty:
        raise ValueError(
            f"Pillar {pillar} source is empty: {relative_file}"
        )

    # ---------------------------------------------------------------
    # Validate country/year uniqueness.
    # ---------------------------------------------------------------

    key_columns = [
        specification["country_column"],
        specification["year_column"],
    ]

    duplicates = df[
        df.duplicated(
            subset=key_columns,
            keep=False,
        )
    ]

    if not duplicates.empty:
        raise ValueError(
            f"Duplicate country-year observations found in "
            f"pillar {pillar} source: {relative_file}"
        )

    # ---------------------------------------------------------------
    # Validate numeric indicator columns.
    # ---------------------------------------------------------------

    for indicator_name, column in specification[
        "indicators"
    ].items():

        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        non_numeric = (
            df[column].notna()
            & numeric_values.isna()
        )

        if non_numeric.any():
            raise ValueError(
                f"Non-numeric values found in pillar {pillar}, "
                f"indicator {indicator_name}, column {column}."
            )

        df[column] = numeric_values

    return df


# -------------------------------------------------------------------
# BUILD PILLAR DATASET
# -------------------------------------------------------------------

def build_pillar_dataset(
    pillar,
    specification,
):
    """
    Create a standardized indicator-level dataset.

    Missing observations remain missing.
    No imputation or interpolation is performed.
    """

    df = load_and_validate_source(
        pillar,
        specification,
    )

    rename_map = {}

    for indicator_name, column in specification[
        "indicators"
    ].items():
        rename_map[column] = indicator_name

    standardized = df[
        [
            specification["country_column"],
            specification["year_column"],
            *specification["indicators"].values(),
        ]
    ].rename(
        columns=rename_map
    )

    standardized = standardized.rename(
        columns={
            specification["country_column"]: "country",
            specification["year_column"]: "year",
        }
    )

    standardized["pillar"] = pillar

    return standardized


# -------------------------------------------------------------------
# PAIRWISE CORRELATION
# -------------------------------------------------------------------

def calculate_pairwise_statistics(
    df,
    pillar,
    indicator_a,
    indicator_b,
):
    """
    Calculate Pearson and Spearman correlations using pairwise
    complete observations only.

    No missing-value imputation is performed.
    """

    pair = df[
        [
            indicator_a,
            indicator_b,
        ]
    ].dropna(
        how="any"
    )

    n = len(pair)

    if n < 3:
        return {
            "pillar": pillar,
            "pillar_name": PILLAR_NAMES[pillar],
            "indicator_a": indicator_a,
            "indicator_b": indicator_b,
            "pairwise_n": n,
            "pearson_r": np.nan,
            "pearson_p_value": np.nan,
            "spearman_rho": np.nan,
            "spearman_p_value": np.nan,
            "pearson_band": "Not estimable",
            "spearman_band": "Not estimable",
            "methodological_flag": "INSUFFICIENT_DATA",
        }

    x = pair[indicator_a].to_numpy(
        dtype=float
    )

    y = pair[indicator_b].to_numpy(
        dtype=float
    )

    # ---------------------------------------------------------------
    # Constant-series protection.
    # ---------------------------------------------------------------

    if (
        np.isclose(np.nanstd(x), 0.0)
        or np.isclose(np.nanstd(y), 0.0)
    ):
        return {
            "pillar": pillar,
            "pillar_name": PILLAR_NAMES[pillar],
            "indicator_a": indicator_a,
            "indicator_b": indicator_b,
            "pairwise_n": n,
            "pearson_r": np.nan,
            "pearson_p_value": np.nan,
            "spearman_rho": np.nan,
            "spearman_p_value": np.nan,
            "pearson_band": "Not estimable",
            "spearman_band": "Not estimable",
            "methodological_flag": (
                "CONSTANT_SERIES_NOT_ESTIMABLE"
            ),
        }

    pearson_result = pearsonr(
        x,
        y,
    )

    spearman_result = spearmanr(
        x,
        y,
    )

    pearson_r = float(
        pearson_result.statistic
    )

    pearson_p = float(
        pearson_result.pvalue
    )

    spearman_rho = float(
        spearman_result.statistic
    )

    spearman_p = float(
        spearman_result.pvalue
    )

    return {
        "pillar": pillar,
        "pillar_name": PILLAR_NAMES[pillar],
        "indicator_a": indicator_a,
        "indicator_b": indicator_b,
        "pairwise_n": n,
        "pearson_r": pearson_r,
        "pearson_p_value": pearson_p,
        "spearman_rho": spearman_rho,
        "spearman_p_value": spearman_p,
        "pearson_band": correlation_band(
            pearson_r
        ),
        "spearman_band": correlation_band(
            spearman_rho
        ),
        "methodological_flag": methodological_flag(
            pearson_r,
            spearman_rho,
        ),
    }


# -------------------------------------------------------------------
# MISSINGNESS
# -------------------------------------------------------------------

def calculate_missingness(
    df,
    pillar,
    indicator_columns,
):
    """
    Calculate indicator-level missingness without filling values.
    """

    rows = []

    total_rows = len(df)

    for indicator in indicator_columns:

        missing_count = int(
            df[indicator].isna().sum()
        )

        observed_count = (
            total_rows - missing_count
        )

        missing_pct = (
            100.0 * missing_count / total_rows
            if total_rows
            else np.nan
        )

        rows.append(
            {
                "pillar": pillar,
                "pillar_name": PILLAR_NAMES[pillar],
                "indicator": indicator,
                "total_rows": total_rows,
                "observed_n": observed_count,
                "missing_n": missing_count,
                "missing_pct": missing_pct,
            }
        )

    return rows


# -------------------------------------------------------------------
# PILLAR SUMMARY
# -------------------------------------------------------------------

def build_pillar_summary(
    pairwise_df,
    missingness_df,
):
    """
    Produce pillar-level descriptive summaries.

    A high-correlation pair is flagged for review, but this summary
    does not automatically remove or down-weight any indicator.
    """

    rows = []

    for pillar in PILLAR_NAMES:

        pair_subset = pairwise_df[
            pairwise_df["pillar"] == pillar
        ]

        missing_subset = missingness_df[
            missingness_df["pillar"] == pillar
        ]

        if pair_subset.empty:
            rows.append(
                {
                    "pillar": pillar,
                    "pillar_name": PILLAR_NAMES[pillar],
                    "indicator_count": 0,
                    "pair_count": 0,
                    "high_correlation_pair_count": 0,
                    "extremely_high_correlation_pair_count": 0,
                    "maximum_absolute_pearson": np.nan,
                    "maximum_absolute_spearman": np.nan,
                    "maximum_missing_pct": np.nan,
                    "pillar_methodological_flag": (
                        "NO_PAIRWISE_COMPARISONS"
                    ),
                }
            )
            continue

        abs_pearson = (
            pair_subset["pearson_r"]
            .abs()
            .dropna()
        )

        abs_spearman = (
            pair_subset["spearman_rho"]
            .abs()
            .dropna()
        )

        high_mask = (
            pair_subset[
                [
                    "pearson_r",
                    "spearman_rho",
                ]
            ]
            .abs()
            .max(axis=1)
            >= 0.70
        )

        extreme_mask = (
            pair_subset[
                [
                    "pearson_r",
                    "spearman_rho",
                ]
            ]
            .abs()
            .max(axis=1)
            >= 0.90
        )

        maximum_missing = (
            missing_subset["missing_pct"].max()
            if not missing_subset.empty
            else np.nan
        )

        if extreme_mask.any():
            pillar_flag = (
                "REVIEW_EXTREMELY_HIGH_CORRELATION"
            )
        elif high_mask.any():
            pillar_flag = (
                "REVIEW_HIGH_CORRELATION"
            )
        else:
            pillar_flag = (
                "NO_HIGH_CORRELATION_FLAG"
            )

        rows.append(
            {
                "pillar": pillar,
                "pillar_name": PILLAR_NAMES[pillar],
                "indicator_count": (
                    pair_subset["indicator_a"]
                    .nunique()
                    + 1
                ),
                "pair_count": len(pair_subset),
                "high_correlation_pair_count": int(
                    high_mask.sum()
                ),
                "extremely_high_correlation_pair_count": int(
                    extreme_mask.sum()
                ),
                "maximum_absolute_pearson": (
                    abs_pearson.max()
                    if not abs_pearson.empty
                    else np.nan
                ),
                "maximum_absolute_spearman": (
                    abs_spearman.max()
                    if not abs_spearman.empty
                    else np.nan
                ),
                "maximum_missing_pct": maximum_missing,
                "pillar_methodological_flag": pillar_flag,
            }
        )

    return pd.DataFrame(rows)


# -------------------------------------------------------------------
# MARKDOWN REPORT
# -------------------------------------------------------------------

def build_markdown_report(
    pairwise_df,
    missingness_df,
    pillar_summary_df,
):
    """
    Build an audit-ready methodological report.
    """

    lines = []

    lines.append(
        "# JESI Indicator Redundancy / Correlation Analysis"
    )
    lines.append("")
    lines.append(
        "## Purpose"
    )
    lines.append("")
    lines.append(
        "This report evaluates within-pillar relationships among "
        "the indicator-level values currently persisted in the "
        "JESI repository."
    )
    lines.append("")
    lines.append(
        "The analysis is a research-validation layer only. "
        "It does not modify JESI weights, normalization, "
        "aggregation, or final scores."
    )
    lines.append("")

    lines.append(
        "## Missing-data policy"
    )
    lines.append("")
    lines.append(
        "Pairwise correlations use pairwise complete observations "
        "only. Missing observations are retained as missing. "
        "No imputation, interpolation, replacement, or fabrication "
        "is performed."
    )
    lines.append("")

    lines.append(
        "## Correlation interpretation"
    )
    lines.append("")
    lines.append(
        "The correlation bands are descriptive screening categories, "
        "not proof of conceptual redundancy."
    )
    lines.append("")
    lines.append(
        "| Absolute correlation | Descriptive band |"
    )
    lines.append(
        "|---:|---|"
    )
    lines.append(
        "| < 0.30 | Low |"
    )
    lines.append(
        "| 0.30–<0.50 | Moderate |"
    )
    lines.append(
        "| 0.50–<0.70 | High |"
    )
    lines.append(
        "| 0.70–<0.90 | Very high |"
    )
    lines.append(
        "| ≥ 0.90 | Extremely high |"
    )
    lines.append("")

    lines.append(
        "## Pillar summary"
    )
    lines.append("")
    lines.append(
        pillar_summary_df.to_markdown(
            index=False,
        )
    )
    lines.append("")

    lines.append(
        "## Pairwise results"
    )
    lines.append("")
    lines.append(
        pairwise_df.to_markdown(
            index=False,
        )
    )
    lines.append("")

    lines.append(
        "## Indicator missingness"
    )
    lines.append("")
    lines.append(
        missingness_df.to_markdown(
            index=False,
        )
    )
    lines.append("")

    lines.append(
        "## Methodological interpretation"
    )
    lines.append("")
    lines.append(
        "High or extremely high correlation is treated as a "
        "review signal rather than an automatic instruction to "
        "remove, reweight, or replace an indicator."
    )
    lines.append("")
    lines.append(
        "Any subsequent methodological decision must consider "
        "conceptual validity, theoretical distinctness, data "
        "quality, and sensitivity analysis together with the "
        "correlation evidence."
    )
    lines.append("")

    return "\n".join(lines)


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

def main():
    print("=" * 78)
    print("JAS Unified Economic Strength Index (JESI)")
    print("Indicator Redundancy / Correlation Analysis")
    print("=" * 78)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pillar_data = {}

    # ---------------------------------------------------------------
    # 1. Load and validate every current pillar source.
    # ---------------------------------------------------------------

    for pillar, specification in PILLAR_SOURCES.items():

        print()
        print(
            f"Loading pillar {pillar}: "
            f"{PILLAR_NAMES[pillar]}"
        )

        df = build_pillar_dataset(
            pillar,
            specification,
        )

        pillar_data[pillar] = df

        print(
            f"  Source: {specification['file']}"
        )
        print(
            f"  Rows: {len(df)}"
        )
        print(
            f"  Indicators: "
            f"{list(specification['indicators'].keys())}"
        )

    # ---------------------------------------------------------------
    # 2. Pairwise correlations.
    # ---------------------------------------------------------------

    pairwise_rows = []

    for pillar, df in pillar_data.items():

        indicators = list(
            PILLAR_SOURCES[pillar]["indicators"].keys()
        )

        for index_a in range(
            len(indicators)
        ):

            for index_b in range(
                index_a + 1,
                len(indicators),
            ):

                indicator_a = indicators[index_a]
                indicator_b = indicators[index_b]

                result = calculate_pairwise_statistics(
                    df,
                    pillar,
                    indicator_a,
                    indicator_b,
                )

                pairwise_rows.append(
                    result
                )

    pairwise_df = pd.DataFrame(
        pairwise_rows
    )

    # ---------------------------------------------------------------
    # 3. Missingness.
    # ---------------------------------------------------------------

    missingness_rows = []

    for pillar, df in pillar_data.items():

        indicators = list(
            PILLAR_SOURCES[pillar]["indicators"].keys()
        )

        missingness_rows.extend(
            calculate_missingness(
                df,
                pillar,
                indicators,
            )
        )

    missingness_df = pd.DataFrame(
        missingness_rows
    )

    # ---------------------------------------------------------------
    # 4. Pillar summary.
    # ---------------------------------------------------------------

    pillar_summary_df = build_pillar_summary(
        pairwise_df,
        missingness_df,
    )

    # ---------------------------------------------------------------
    # 5. Add source metadata.
    # ---------------------------------------------------------------

    pairwise_df["analysis_level"] = (
        "persisted_indicator_score"
    )

    missingness_df["analysis_level"] = (
        "persisted_indicator_score"
    )

    pillar_summary_df["analysis_level"] = (
        "persisted_indicator_score"
    )

    # ---------------------------------------------------------------
    # 6. Save CSV outputs.
    # ---------------------------------------------------------------

    pairwise_path = (
        OUTPUT_DIR
        / "jesi_indicator_redundancy_pairwise.csv"
    )

    missingness_path = (
        OUTPUT_DIR
        / "jesi_indicator_redundancy_missingness.csv"
    )

    pillar_summary_path = (
        OUTPUT_DIR
        / "jesi_indicator_redundancy_pillar_summary.csv"
    )

    report_path = (
        OUTPUT_DIR
        / "jesi_indicator_redundancy_report.md"
    )

    pairwise_df.to_csv(
        pairwise_path,
        index=False,
    )

    missingness_df.to_csv(
        missingness_path,
        index=False,
    )

    pillar_summary_df.to_csv(
        pillar_summary_path,
        index=False,
    )

    # ---------------------------------------------------------------
    # 7. Markdown report.
    # ---------------------------------------------------------------

    report = build_markdown_report(
        pairwise_df,
        missingness_df,
        pillar_summary_df,
    )

    report_path.write_text(
        report,
        encoding="utf-8",
    )

    # ---------------------------------------------------------------
    # 8. Console summary.
    # ---------------------------------------------------------------

    print()
    print("=" * 78)
    print("PILLAR SUMMARY")
    print("=" * 78)

    print(
        pillar_summary_df.to_string(
            index=False
        )
    )

    print()
    print("=" * 78)
    print("PAIRWISE CORRELATION RESULTS")
    print("=" * 78)

    print(
        pairwise_df.to_string(
            index=False
        )
    )

    print()
    print("=" * 78)
    print("MISSINGNESS")
    print("=" * 78)

    print(
        missingness_df.to_string(
            index=False
        )
    )

    print()
    print("=" * 78)
    print("OUTPUT FILES")
    print("=" * 78)

    print(
        pairwise_path
    )

    print(
        missingness_path
    )

    print(
        pillar_summary_path
    )

    print(
        report_path
    )

    print()
    print(
        "Indicator redundancy analysis: PASSED"
    )


if __name__ == "__main__":
    main()
