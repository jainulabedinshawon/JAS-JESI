"""
JAS Unified Economic Strength Index (JESI)
Normalization Sensitivity Analysis
Master Version 1.0

Purpose
-------
Evaluate whether JESI results are materially sensitive to
alternative normalization specifications without modifying
the production JESI pipeline.

Design
------
1. Reconstructs indicator scores from the persisted raw
   indicator values.
2. Preserves the current production specification as BASELINE.
3. Tests alternative monotonic normalization methods:
       - full-sample min-max
       - winsorized min-max (5th-95th percentile)
       - pooled percentile rank
4. Separately tests the nonlinear Resilience reference-zone
   specification:
       - baseline P10-P90
       - alternative P5-P95
       - alternative P20-P80
5. Keeps pillar aggregation and JESI strategic weights fixed.
6. Uses the same 2016-2023 complete-case benchmark panel
   used by the final JESI validation.
7. Does NOT modify any production JESI output.

Important
---------
This is a sensitivity-analysis module, not a replacement
for the production normalization/scoring pipeline.

The baseline specification is reproduced from the current
repository implementation.

Production files are never overwritten.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------
# Benchmark definition
# ---------------------------------------------------------------------

COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
    "VNM": "Vietnam",
}

FINAL_YEARS = set(range(2016, 2024))

# Production benchmark periods
GROWTH_YEARS = set(range(2015, 2025))
PRODUCTIVITY_YEARS = set(range(2016, 2024))
CONNECTIVITY_YEARS = set(range(2015, 2025))
RESILIENCE_YEARS = set(range(2015, 2025))
AUTONOMY_YEARS = set(range(2015, 2025))


# ---------------------------------------------------------------------
# Production input files
# ---------------------------------------------------------------------

GROWTH_FILE = (
    ROOT
    / "data"
    / "processed"
    / "growth_pillar_scores_2015_2024.csv"
)

P1_FILE = (
    ROOT
    / "data"
    / "processed"
    / "productivity_p1_scores_2016_2023.csv"
)

P2_FILE = (
    ROOT
    / "data"
    / "processed"
    / "productivity_p2_scores_2016_2023.csv"
)

CONNECTIVITY_FILE = (
    ROOT
    / "data"
    / "processed"
    / "connectivity_indicator_scores_2015_2024.csv"
)

RESILIENCE_FILE = (
    ROOT
    / "data"
    / "processed"
    / "resilience_pillar_scores_2015_2024.csv"
)

AUTONOMY_FILE = (
    ROOT
    / "data"
    / "processed"
    / "autonomy_indicator_scores_2015_2024.csv"
)


# ---------------------------------------------------------------------
# Output files
# ---------------------------------------------------------------------

OUTPUT_DIR = ROOT / "data" / "results"

COUNTRY_YEAR_OUTPUT = (
    OUTPUT_DIR
    / "jesi_normalization_sensitivity_country_year.csv"
)

COUNTRY_SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "jesi_normalization_sensitivity_country_summary.csv"
)

RANK_OUTPUT = (
    OUTPUT_DIR
    / "jesi_normalization_sensitivity_rank_correlations.csv"
)

SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "jesi_normalization_sensitivity_summary.csv"
)

REPORT_OUTPUT = (
    OUTPUT_DIR
    / "jesi_normalization_sensitivity_report.md"
)


# ---------------------------------------------------------------------
# JESI strategic weights
# ---------------------------------------------------------------------

JESI_WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def fail(message: str) -> None:
    """Raise a clear analysis failure."""
    raise RuntimeError(message)


def require_file(path: Path) -> None:
    """Require an input file to exist."""
    if not path.exists():
        fail(f"Required input file not found: {path}")


def standardize_country_code(value):
    """Map country names/codes to JESI ISO3 codes."""

    if pd.isna(value):
        return np.nan

    text = str(value).strip().lower()

    mapping = {
        "bangladesh": "BGD",
        "bgd": "BGD",
        "india": "IND",
        "ind": "IND",
        "indonesia": "IDN",
        "idn": "IDN",
        "malaysia": "MYS",
        "mys": "MYS",
        "vietnam": "VNM",
        "viet nam": "VNM",
        "viet_nam": "VNM",
        "vnm": "VNM",
    }

    return mapping.get(text, np.nan)


def validate_country_year(
    df: pd.DataFrame,
    name: str,
    years,
) -> None:
    """Validate country/year coverage."""

    if df.empty:
        fail(f"{name} dataset is empty.")

    actual_countries = set(
        df["country_code"]
        .dropna()
        .astype(str)
    )

    unexpected = actual_countries - set(COUNTRIES)

    if unexpected:
        fail(
            f"{name} contains unexpected countries: "
            f"{sorted(unexpected)}"
        )

    actual_years = set(
        pd.to_numeric(
            df["year"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
    )

    unexpected_years = actual_years - set(years)

    if unexpected_years:
        fail(
            f"{name} contains unexpected years: "
            f"{sorted(unexpected_years)}"
        )

    duplicates = df.duplicated(
        subset=["country_code", "year"],
        keep=False,
    )

    if duplicates.any():
        fail(
            f"{name} contains duplicate country-year "
            "observations."
        )


def numeric_series(
    df: pd.DataFrame,
    column: str,
    name: str,
) -> pd.Series:
    """Convert a required indicator column to numeric."""

    if column not in df.columns:
        fail(
            f"{name} is missing required column: {column}"
        )

    result = pd.to_numeric(
        df[column],
        errors="coerce",
    )

    if result.notna().sum() == 0:
        fail(
            f"{name}.{column} contains no valid numeric values."
        )

    return result


# ---------------------------------------------------------------------
# Normalization functions
# ---------------------------------------------------------------------

def minmax_positive(series: pd.Series) -> pd.Series:
    """Standard full-sample positive-direction min-max."""

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    minimum = numeric.min()
    maximum = numeric.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(
            np.nan,
            index=series.index,
        )

    if maximum == minimum:
        return pd.Series(
            1.0,
            index=series.index,
        )

    result = (
        (numeric - minimum)
        / (maximum - minimum)
    )

    return result.clip(0.0, 1.0)


def minmax_negative(series: pd.Series) -> pd.Series:
    """Standard full-sample negative-direction min-max."""

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    minimum = numeric.min()
    maximum = numeric.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(
            np.nan,
            index=series.index,
        )

    if maximum == minimum:
        return pd.Series(
            1.0,
            index=series.index,
        )

    result = (
        (maximum - numeric)
        / (maximum - minimum)
    )

    return result.clip(0.0, 1.0)


def winsorized_minmax_positive(
    series: pd.Series,
) -> pd.Series:
    """5th-95th percentile winsorized positive min-max."""

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    lower = numeric.quantile(0.05)
    upper = numeric.quantile(0.95)

    if upper == lower:
        return pd.Series(
            1.0,
            index=series.index,
        )

    clipped = numeric.clip(
        lower=lower,
        upper=upper,
    )

    result = (
        (clipped - lower)
        / (upper - lower)
    )

    return result.clip(0.0, 1.0)


def winsorized_minmax_negative(
    series: pd.Series,
) -> pd.Series:
    """5th-95th percentile winsorized negative min-max."""

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    lower = numeric.quantile(0.05)
    upper = numeric.quantile(0.95)

    if upper == lower:
        return pd.Series(
            1.0,
            index=series.index,
        )

    clipped = numeric.clip(
        lower=lower,
        upper=upper,
    )

    result = (
        (upper - clipped)
        / (upper - lower)
    )

    return result.clip(0.0, 1.0)


def percentile_score(
    series: pd.Series,
) -> pd.Series:
    """
    Pooled empirical percentile rank.

    Matches the production percentile-rank approach.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    result = numeric.rank(
        method="average",
        pct=True,
        na_option="keep",
    )

    return result.clip(
        lower=0.001,
        upper=1.0,
    )


def reference_zone_score(
    series: pd.Series,
    lower: float,
    upper: float,
) -> pd.Series:
    """
    Smooth nonlinear reference-zone score.

    Matches the production JESI resilience formulation:
    score = 1 inside the zone and exponential penalty
    outside the zone.

    lambda = ln(2)
    """

    if upper <= lower:
        fail(
            "Reference-zone upper bound must exceed lower bound."
        )

    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    width = upper - lower
    lam = np.log(2.0)

    below = (
        np.maximum(
            lower - values,
            0.0,
        )
        / width
    )

    above = (
        np.maximum(
            values - upper,
            0.0,
        )
        / width
    )

    distance = below + above

    result = np.exp(
        -lam * distance
    )

    return result.clip(
        lower=0.0,
        upper=1.0,
    )


def reference_zone_from_quantiles(
    series: pd.Series,
    lower_q: float,
    upper_q: float,
) -> pd.Series:
    """Construct a reference-zone score from empirical quantiles."""

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    lower = numeric.quantile(
        lower_q
    )

    upper = numeric.quantile(
        upper_q
    )

    return reference_zone_score(
        numeric,
        lower=lower,
        upper=upper,
    )


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------

def load_growth() -> pd.DataFrame:
    require_file(GROWTH_FILE)

    df = pd.read_csv(GROWTH_FILE)

    required = [
        "country_code",
        "year",
        "real_gdp_growth",
        "gni_per_capita_growth",
    ]

    for column in required:
        if column not in df.columns:
            fail(
                f"Growth file missing column: {column}"
            )

    df["country_code"] = (
        df["country_code"]
        .apply(standardize_country_code)
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df = df[
        df["country_code"].isin(COUNTRIES)
        & df["year"].isin(GROWTH_YEARS)
    ].copy()

    df["year"] = df["year"].astype(int)

    for column in [
        "real_gdp_growth",
        "gni_per_capita_growth",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    validate_country_year(
        df,
        "Growth",
        GROWTH_YEARS,
    )

    return df[
        [
            "country_code",
            "year",
            "real_gdp_growth",
            "gni_per_capita_growth",
        ]
    ].copy()


def load_productivity() -> pd.DataFrame:
    require_file(P1_FILE)
    require_file(P2_FILE)

    p1 = pd.read_csv(P1_FILE)
    p2 = pd.read_csv(P2_FILE)

    for column in [
        "country_code",
        "year",
        "gdp_per_person_employed",
    ]:
        if column not in p1.columns:
            fail(
                f"P1 file missing column: {column}"
            )

    for column in [
        "country_code",
        "year",
        "tfp_growth",
    ]:
        if column not in p2.columns:
            fail(
                f"P2 file missing column: {column}"
            )

    p1["country_code"] = (
        p1["country_code"]
        .apply(standardize_country_code)
    )

    p2["country_code"] = (
        p2["country_code"]
        .apply(standardize_country_code)
    )

    p1["year"] = pd.to_numeric(
        p1["year"],
        errors="coerce",
    )

    p2["year"] = pd.to_numeric(
        p2["year"],
        errors="coerce",
    )

    p1 = p1[
        p1["country_code"].isin(COUNTRIES)
        & p1["year"].isin(PRODUCTIVITY_YEARS)
    ].copy()

    p2 = p2[
        p2["country_code"].isin(COUNTRIES)
        & p2["year"].isin(PRODUCTIVITY_YEARS)
    ].copy()

    p1["year"] = p1["year"].astype(int)
    p2["year"] = p2["year"].astype(int)

    p1["gdp_per_person_employed"] = pd.to_numeric(
        p1["gdp_per_person_employed"],
        errors="coerce",
    )

    p2["tfp_growth"] = pd.to_numeric(
        p2["tfp_growth"],
        errors="coerce",
    )

    validate_country_year(
        p1,
        "Productivity P1",
        PRODUCTIVITY_YEARS,
    )

    validate_country_year(
        p2,
        "Productivity P2",
        PRODUCTIVITY_YEARS,
    )

    merged = pd.merge(
        p1[
            [
                "country_code",
                "year",
                "gdp_per_person_employed",
            ]
        ],
        p2[
            [
                "country_code",
                "year",
                "tfp_growth",
            ]
        ],
        on=[
            "country_code",
            "year",
        ],
        how="outer",
        validate="one_to_one",
    )

    return merged


def load_connectivity() -> pd.DataFrame:
    require_file(CONNECTIVITY_FILE)

    df = pd.read_csv(
        CONNECTIVITY_FILE
    )

    required = [
        "country_code",
        "year",
        "trade_openness",
        "fdi_inflows",
        "internet_use",
    ]

    for column in required:
        if column not in df.columns:
            fail(
                f"Connectivity file missing column: {column}"
            )

    df["country_code"] = (
        df["country_code"]
        .apply(standardize_country_code)
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df = df[
        df["country_code"].isin(COUNTRIES)
        & df["year"].isin(CONNECTIVITY_YEARS)
    ].copy()

    df["year"] = df["year"].astype(int)

    for column in [
        "trade_openness",
        "fdi_inflows",
        "internet_use",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    validate_country_year(
        df,
        "Connectivity",
        CONNECTIVITY_YEARS,
    )

    return df[
        [
            "country_code",
            "year",
            "trade_openness",
            "fdi_inflows",
            "internet_use",
        ]
    ].copy()


def load_resilience() -> pd.DataFrame:
    require_file(RESILIENCE_FILE)

    df = pd.read_csv(
        RESILIENCE_FILE
    )

    required = [
        "country",
        "year",
        "fx_reserves_months",
        "government_debt_gdp",
        "current_account_gdp",
    ]

    for column in required:
        if column not in df.columns:
            fail(
                f"Resilience file missing column: {column}"
            )

    df["country_code"] = (
        df["country"]
        .apply(standardize_country_code)
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df = df[
        df["country_code"].isin(COUNTRIES)
        & df["year"].isin(RESILIENCE_YEARS)
    ].copy()

    df["year"] = df["year"].astype(int)

    for column in [
        "fx_reserves_months",
        "government_debt_gdp",
        "current_account_gdp",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    validate_country_year(
        df,
        "Resilience",
        RESILIENCE_YEARS,
    )

    return df[
        [
            "country_code",
            "year",
            "fx_reserves_months",
            "government_debt_gdp",
            "current_account_gdp",
        ]
    ].copy()


def load_autonomy() -> pd.DataFrame:
    require_file(AUTONOMY_FILE)

    df = pd.read_csv(
        AUTONOMY_FILE
    )

    required = [
        "country_code",
        "year",
        "eci",
        "high_tech_exports",
        "import_product_concentration",
    ]

    for column in required:
        if column not in df.columns:
            fail(
                f"Autonomy file missing column: {column}"
            )

    df["country_code"] = (
        df["country_code"]
        .apply(standardize_country_code)
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df = df[
        df["country_code"].isin(COUNTRIES)
        & df["year"].isin(AUTONOMY_YEARS)
    ].copy()

    df["year"] = df["year"].astype(int)

    for column in [
        "eci",
        "high_tech_exports",
        "import_product_concentration",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    validate_country_year(
        df.dropna(
            subset=["country_code", "year"]
        ),
        "Strategic Autonomy",
        AUTONOMY_YEARS,
    )

    return df[
        [
            "country_code",
            "year",
            "eci",
            "high_tech_exports",
            "import_product_concentration",
        ]
    ].copy()


# ---------------------------------------------------------------------
# Score construction
# ---------------------------------------------------------------------

def build_indicator_scores():
    """Build all baseline and alternative indicator scores."""

    growth = load_growth()
    productivity = load_productivity()
    connectivity = load_connectivity()
    resilience = load_resilience()
    autonomy = load_autonomy()

    # ---------------------------------------------------------------
    # Growth
    #
    # Production baseline = pooled percentile.
    # ---------------------------------------------------------------

    growth_scores = growth[
        [
            "country_code",
            "year",
        ]
    ].copy()

    growth_scores["G_real_gdp_baseline"] = (
        percentile_score(
            growth["real_gdp_growth"]
        )
    )

    growth_scores["G_gni_baseline"] = (
        percentile_score(
            growth["gni_per_capita_growth"]
        )
    )

    for method in [
        "minmax",
        "winsorized_minmax",
        "percentile",
    ]:
        if method == "minmax":
            gdp = minmax_positive(
                growth["real_gdp_growth"]
            )
            gni = minmax_positive(
                growth["gni_per_capita_growth"]
            )

        elif method == "winsorized_minmax":
            gdp = winsorized_minmax_positive(
                growth["real_gdp_growth"]
            )
            gni = winsorized_minmax_positive(
                growth["gni_per_capita_growth"]
            )

        else:
            gdp = percentile_score(
                growth["real_gdp_growth"]
            )
            gni = percentile_score(
                growth["gni_per_capita_growth"]
            )

        growth_scores[
            f"G_real_gdp_{method}"
        ] = gdp

        growth_scores[
            f"G_gni_{method}"
        ] = gni

    # ---------------------------------------------------------------
    # Productivity
    # ---------------------------------------------------------------

    productivity_scores = productivity[
        [
            "country_code",
            "year",
        ]
    ].copy()

    productivity_scores[
        "P_p1_baseline"
    ] = percentile_score(
        productivity[
            "gdp_per_person_employed"
        ]
    )

    productivity_scores[
        "P_p2_baseline"
    ] = percentile_score(
        productivity[
            "tfp_growth"
        ]
    )

    for method in [
        "minmax",
        "winsorized_minmax",
        "percentile",
    ]:
        if method == "minmax":
            p1 = minmax_positive(
                productivity[
                    "gdp_per_person_employed"
                ]
            )
            p2 = minmax_positive(
                productivity[
                    "tfp_growth"
                ]
            )

        elif method == "winsorized_minmax":
            p1 = winsorized_minmax_positive(
                productivity[
                    "gdp_per_person_employed"
                ]
            )
            p2 = winsorized_minmax_positive(
                productivity[
                    "tfp_growth"
                ]
            )

        else:
            p1 = percentile_score(
                productivity[
                    "gdp_per_person_employed"
                ]
            )
            p2 = percentile_score(
                productivity[
                    "tfp_growth"
                ]
            )

        productivity_scores[
            f"P_p1_{method}"
        ] = p1

        productivity_scores[
            f"P_p2_{method}"
        ] = p2

    # ---------------------------------------------------------------
    # Connectivity
    # ---------------------------------------------------------------

    connectivity_scores = connectivity[
        [
            "country_code",
            "year",
        ]
    ].copy()

    connectivity_indicators = [
        "trade_openness",
        "fdi_inflows",
        "internet_use",
    ]

    for indicator in connectivity_indicators:
        connectivity_scores[
            f"C_{indicator}_baseline"
        ] = percentile_score(
            connectivity[indicator]
        )

    for method in [
        "minmax",
        "winsorized_minmax",
        "percentile",
    ]:
        for indicator in connectivity_indicators:

            if method == "minmax":
                score = minmax_positive(
                    connectivity[indicator]
                )

            elif method == "winsorized_minmax":
                score = winsorized_minmax_positive(
                    connectivity[indicator]
                )

            else:
                score = percentile_score(
                    connectivity[indicator]
                )

            connectivity_scores[
                f"C_{indicator}_{method}"
            ] = score

    # ---------------------------------------------------------------
    # Resilience
    #
    # R1 baseline = full-sample min-max.
    # R2/R3 baseline = P10-P90 nonlinear reference zone.
    #
    # Alternative monotonic normalization specifications are NOT
    # forced onto R2/R3 because those indicators are explicitly
    # target/reference-zone indicators in the methodology.
    # ---------------------------------------------------------------

    resilience_scores = resilience[
        [
            "country_code",
            "year",
        ]
    ].copy()

    resilience_scores[
        "R_fx_baseline"
    ] = minmax_positive(
        resilience[
            "fx_reserves_months"
        ]
    )

    resilience_scores[
        "R_debt_baseline"
    ] = reference_zone_from_quantiles(
        resilience[
            "government_debt_gdp"
        ],
        0.10,
        0.90,
    )

    resilience_scores[
        "R_ca_baseline"
    ] = reference_zone_from_quantiles(
        resilience[
            "current_account_gdp"
        ],
        0.10,
        0.90,
    )

    # Reference-zone sensitivity.
    for label, lower_q, upper_q in [
        (
            "reference_p5_p95",
            0.05,
            0.95,
        ),
        (
            "reference_p20_p80",
            0.20,
            0.80,
        ),
    ]:
        resilience_scores[
            f"R_debt_{label}"
        ] = reference_zone_from_quantiles(
            resilience[
                "government_debt_gdp"
            ],
            lower_q,
            upper_q,
        )

        resilience_scores[
            f"R_ca_{label}"
        ] = reference_zone_from_quantiles(
            resilience[
                "current_account_gdp"
            ],
            lower_q,
            upper_q,
        )

    # R1 alternative normalization.
    for method in [
        "minmax",
        "winsorized_minmax",
        "percentile",
    ]:
        if method == "minmax":
            score = minmax_positive(
                resilience[
                    "fx_reserves_months"
                ]
            )

        elif method == "winsorized_minmax":
            score = winsorized_minmax_positive(
                resilience[
                    "fx_reserves_months"
                ]
            )

        else:
            score = percentile_score(
                resilience[
                    "fx_reserves_months"
                ]
            )

        resilience_scores[
            f"R_fx_{method}"
        ] = score

    # ---------------------------------------------------------------
    # Strategic Autonomy
    #
    # Production baseline = P10-P90 min-max reference bounds.
    # ECI and high-tech exports are positive direction.
    # Import concentration is negative direction.
    # ---------------------------------------------------------------

    autonomy_scores = autonomy[
        [
            "country_code",
            "year",
        ]
    ].copy()

    complete_autonomy = autonomy[
        [
            "eci",
            "high_tech_exports",
            "import_product_concentration",
        ]
    ].notna().all(axis=1)

    # Baseline P10-P90 reference bounds are calculated only from
    # complete official-source observations, matching production.
    eci_complete = autonomy.loc[
        complete_autonomy,
        "eci",
    ]

    hightech_complete = autonomy.loc[
        complete_autonomy,
        "high_tech_exports",
    ]

    concentration_complete = autonomy.loc[
        complete_autonomy,
        "import_product_concentration",
    ]

    eci_lower = eci_complete.quantile(0.10)
    eci_upper = eci_complete.quantile(0.90)

    hightech_lower = hightech_complete.quantile(0.10)
    hightech_upper = hightech_complete.quantile(0.90)

    concentration_lower = concentration_complete.quantile(0.10)
    concentration_upper = concentration_complete.quantile(0.90)

    autonomy_scores[
        "A_eci_baseline"
    ] = np.nan

    autonomy_scores[
        "A_hightech_baseline"
    ] = np.nan

    autonomy_scores[
        "A_concentration_baseline"
    ] = np.nan

    valid = complete_autonomy

    autonomy_scores.loc[
        valid,
        "A_eci_baseline",
    ] = minmax_positive(
        eci_complete
    ).to_numpy()

    autonomy_scores.loc[
        valid,
        "A_hightech_baseline",
    ] = minmax_positive(
        hightech_complete
    ).to_numpy()

    autonomy_scores.loc[
        valid,
        "A_concentration_baseline",
    ] = minmax_negative(
        concentration_complete
    ).to_numpy()

    for method in [
        "minmax",
        "winsorized_minmax",
        "percentile",
    ]:
        autonomy_scores[
            f"A_eci_{method}"
        ] = np.nan

        autonomy_scores[
            f"A_hightech_{method}"
        ] = np.nan

        autonomy_scores[
            f"A_concentration_{method}"
        ] = np.nan

        if method == "minmax":
            eci_score = minmax_positive(
                eci_complete
            )
            hightech_score = minmax_positive(
                hightech_complete
            )
            concentration_score = minmax_negative(
                concentration_complete
            )

        elif method == "winsorized_minmax":
            eci_score = winsorized_minmax_positive(
                eci_complete
            )
            hightech_score = winsorized_minmax_positive(
                hightech_complete
            )
            concentration_score = winsorized_minmax_negative(
                concentration_complete
            )

        else:
            eci_score = percentile_score(
                eci_complete
            )
            hightech_score = percentile_score(
                hightech_complete
            )
            concentration_score = percentile_score(
                -concentration_complete
            )

        autonomy_scores.loc[
            valid,
            f"A_eci_{method}",
        ] = eci_score.to_numpy()

        autonomy_scores.loc[
            valid,
            f"A_hightech_{method}",
        ] = hightech_score.to_numpy()

        autonomy_scores.loc[
            valid,
            f"A_concentration_{method}",
        ] = concentration_score.to_numpy()

    # ---------------------------------------------------------------
    # Merge all indicator score tables
    # ---------------------------------------------------------------

    result = growth_scores.merge(
        productivity_scores,
        on=[
            "country_code",
            "year",
        ],
        how="outer",
    )

    result = result.merge(
        connectivity_scores,
        on=[
            "country_code",
            "year",
        ],
        how="outer",
    )

    result = result.merge(
        resilience_scores,
        on=[
            "country_code",
            "year",
        ],
        how="outer",
    )

    result = result.merge(
        autonomy_scores,
        on=[
            "country_code",
            "year",
        ],
        how="outer",
    )

    result["country"] = (
        result["country_code"]
        .map(COUNTRIES)
    )

    return result


# ---------------------------------------------------------------------
# Pillar/JESI construction
# ---------------------------------------------------------------------

def arithmetic_mean(
    frame: pd.DataFrame,
    columns,
) -> pd.Series:
    """Equal-weight arithmetic pillar aggregation."""

    return frame[
        columns
    ].mean(
        axis=1,
        skipna=False,
    )


def geometric_jesi(
    frame: pd.DataFrame,
) -> pd.Series:
    """Master JESI geometric aggregation."""

    safe = frame[
        [
            "G",
            "P",
            "C",
            "R",
            "A",
        ]
    ].clip(
        lower=1e-12,
        upper=1.0,
    )

    return (
        100.0
        * safe["G"].pow(
            JESI_WEIGHTS["G"]
        )
        * safe["P"].pow(
            JESI_WEIGHTS["P"]
        )
        * safe["C"].pow(
            JESI_WEIGHTS["C"]
        )
        * safe["R"].pow(
            JESI_WEIGHTS["R"]
        )
        * safe["A"].pow(
            JESI_WEIGHTS["A"]
        )
    )


def build_specification(
    scores: pd.DataFrame,
    name: str,
) -> pd.DataFrame:
    """
    Construct one normalization specification.

    Monotonic indicator specifications:
        baseline
        minmax
        winsorized_minmax
        percentile

    Nonlinear Resilience specifications:
        baseline
        reference_p5_p95
        reference_p20_p80
    """

    df = scores[
        [
            "country_code",
            "country",
            "year",
        ]
    ].copy()

    # ---------------------------------------------------------------
    # Select Growth
    # ---------------------------------------------------------------

    if name == "baseline":
        g_cols = [
            "G_real_gdp_baseline",
            "G_gni_baseline",
        ]

    else:
        g_cols = [
            f"G_real_gdp_{name}",
            f"G_gni_{name}",
        ]

    df["G"] = arithmetic_mean(
        scores,
        g_cols,
    )

    # ---------------------------------------------------------------
    # Productivity
    # ---------------------------------------------------------------

    if name == "baseline":
        p_cols = [
            "P_p1_baseline",
            "P_p2_baseline",
        ]
    else:
        p_cols = [
            f"P_p1_{name}",
            f"P_p2_{name}",
        ]

    df["P"] = arithmetic_mean(
        scores,
        p_cols,
    )

    # ---------------------------------------------------------------
    # Connectivity
    # ---------------------------------------------------------------

    connectivity_names = [
        "trade_openness",
        "fdi_inflows",
        "internet_use",
    ]

    if name == "baseline":
        c_cols = [
            f"C_{item}_baseline"
            for item in connectivity_names
        ]
    else:
        c_cols = [
            f"C_{item}_{name}"
            for item in connectivity_names
        ]

    df["C"] = arithmetic_mean(
        scores,
        c_cols,
    )

    # ---------------------------------------------------------------
    # Resilience
    # ---------------------------------------------------------------

    if name in {
        "baseline",
        "minmax",
        "winsorized_minmax",
        "percentile",
    }:
        # Monotonic sensitivity applies only to R1.
        # R2/R3 retain their theoretically justified
        # nonlinear baseline reference-zone treatment.
        r_cols = [
            f"R_fx_{name}",
            "R_debt_baseline",
            "R_ca_baseline",
        ]

    elif name == "reference_p5_p95":
        r_cols = [
            "R_fx_baseline",
            "R_debt_reference_p5_p95",
            "R_ca_reference_p5_p95",
        ]

    elif name == "reference_p20_p80":
        r_cols = [
            "R_fx_baseline",
            "R_debt_reference_p20_p80",
            "R_ca_reference_p20_p80",
        ]

    else:
        fail(
            f"Unknown normalization specification: {name}"
        )

    df["R"] = arithmetic_mean(
        scores,
        r_cols,
    )

    # ---------------------------------------------------------------
    # Strategic Autonomy
    # ---------------------------------------------------------------

    if name == "baseline":
        a_cols = [
            "A_eci_baseline",
            "A_hightech_baseline",
            "A_concentration_baseline",
        ]
    else:
        a_cols = [
            f"A_eci_{name}",
            f"A_hightech_{name}",
            f"A_concentration_{name}",
        ]

    df["A"] = arithmetic_mean(
        scores,
        a_cols,
    )

    # ---------------------------------------------------------------
    # JESI
    # ---------------------------------------------------------------

    df["JESI"] = geometric_jesi(
        df
    )

    df["specification"] = name

    return df[
        [
            "country_code",
            "country",
            "year",
            "G",
            "P",
            "C",
            "R",
            "A",
            "JESI",
            "specification",
        ]
    ]


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def validate_complete_case(
    df: pd.DataFrame,
    specification: str,
) -> pd.DataFrame:
    """
    Restrict to the final 2016-2023 complete-case panel.

    Expected theoretical panel:
        5 countries × 8 years = 40

    Expected complete-case panel:
        34 observations

    Expected exclusions:
        6 observations
    """

    final = df[
        df["year"].isin(FINAL_YEARS)
        & df["country_code"].isin(COUNTRIES)
    ].copy()

    theoretical = (
        len(COUNTRIES)
        * len(FINAL_YEARS)
    )

    if len(
        final[
            [
                "country_code",
                "year",
            ]
        ].drop_duplicates()
    ) != theoretical:
        fail(
            f"{specification}: final panel does not contain "
            f"theoretical {theoretical} country-year combinations."
        )

    complete = final[
        [
            "G",
            "P",
            "C",
            "R",
            "A",
            "JESI",
        ]
    ].notna().all(axis=1)

    scored = final.loc[
        complete
    ].copy()

    if len(scored) != 34:
        fail(
            f"{specification}: expected 34 complete-case "
            f"observations, found {len(scored)}."
        )

    if (
        scored[
            [
                "G",
                "P",
                "C",
                "R",
                "A",
            ]
        ]
        .lt(0)
        .any()
        .any()
    ):
        fail(
            f"{specification}: negative pillar scores detected."
        )

    if (
        scored[
            [
                "G",
                "P",
                "C",
                "R",
                "A",
            ]
        ]
        .gt(1)
        .any()
        .any()
    ):
        fail(
            f"{specification}: pillar scores above 1 detected."
        )

    return scored


# ---------------------------------------------------------------------
# Rank analysis
# ---------------------------------------------------------------------

def rank_correlation(
    baseline: pd.DataFrame,
    alternative: pd.DataFrame,
    level: str,
    specification: str,
) -> dict:
    """Calculate Spearman rank correlation."""

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
        suffixes=(
            "_baseline",
            "_alternative",
        ),
        how="inner",
    )

    if level == "country_year":
        x = merged["JESI_baseline"]
        y = merged["JESI_alternative"]

        n = len(merged)

    else:
        x_country = (
            merged.groupby(
                "country_code"
            )["JESI_baseline"]
            .mean()
        )

        y_country = (
            merged.groupby(
                "country_code"
            )["JESI_alternative"]
            .mean()
        )

        joined = pd.concat(
            [
                x_country.rename(
                    "baseline"
                ),
                y_country.rename(
                    "alternative"
                ),
            ],
            axis=1,
            join="inner",
        ).dropna()

        x = joined["baseline"]
        y = joined["alternative"]

        n = len(joined)

    if n < 2:
        rho = np.nan
        p_value = np.nan
    else:
        rho, p_value = spearmanr(
            x,
            y,
        )

    return {
        "specification": specification,
        "analysis_level": level,
        "pairwise_n": n,
        "spearman_rho": rho,
        "spearman_p_value": p_value,
    }


# ---------------------------------------------------------------------
# Country summary
# ---------------------------------------------------------------------

def build_country_summary(
    all_specs: pd.DataFrame,
) -> pd.DataFrame:
    """Build country-level mean JESI and ranking for every specification."""

    summary = (
        all_specs
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
    ).reset_index(drop=True)


# ---------------------------------------------------------------------
# Summary diagnostics
# ---------------------------------------------------------------------

def build_sensitivity_summary(
    baseline: pd.DataFrame,
    alternatives: dict,
) -> pd.DataFrame:
    """Calculate score/rank stability diagnostics."""

    rows = []

    for specification, alternative in alternatives.items():

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
            suffixes=(
                "_baseline",
                "_alternative",
            ),
            how="inner",
        )

        absolute_difference = (
            merged["JESI_alternative"]
            - merged["JESI_baseline"]
        ).abs()

        country_base = (
            merged.groupby(
                "country_code"
            )["JESI_baseline"]
            .mean()
        )

        country_alt = (
            merged.groupby(
                "country_code"
            )["JESI_alternative"]
            .mean()
        )

        country_rank_base = (
            country_base.rank(
                method="min",
                ascending=False,
            )
        )

        country_rank_alt = (
            country_alt.rank(
                method="min",
                ascending=False,
            )
        )

        rank_change = (
            country_rank_alt
            - country_rank_base
        ).abs()

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
                        country_alt
                        - country_base
                    )
                    .abs()
                    .mean()
                ),
                "max_country_rank_change": (
                    rank_change.max()
                ),
                "countries_with_rank_change": int(
                    (
                        rank_change > 0
                    ).sum()
                ),
                "country_rank_spearman": (
                    spearmanr(
                        country_base,
                        country_alt,
                    ).statistic
                ),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# Research report
# ---------------------------------------------------------------------

def build_report(
    sensitivity_summary: pd.DataFrame,
    rank_results: pd.DataFrame,
    baseline: pd.DataFrame,
) -> str:
    """Create a reproducible Markdown research report."""

    baseline_country = (
        baseline
        .groupby(
            [
                "country_code",
                "country",
            ],
            as_index=False,
        )["JESI"]
        .mean()
        .sort_values(
            "JESI",
            ascending=False,
        )
    )

    lines = []

    lines.append(
        "# JESI Normalization Sensitivity Analysis"
    )
    lines.append("")
    lines.append(
        "## Purpose"
    )
    lines.append(
        "This analysis evaluates whether the JESI results are "
        "materially sensitive to alternative normalization "
        "specifications while preserving the production JESI "
        "pillar definitions, strategic weights, missing-data "
        "rules, and geometric final aggregation."
    )
    lines.append("")
    lines.append(
        "## Benchmark"
    )
    lines.append(
        "- Countries: Bangladesh, India, Indonesia, Malaysia, Vietnam"
    )
    lines.append(
        "- Final comparison period: 2016–2023"
    )
    lines.append(
        "- Theoretical observations: 40"
    )
    lines.append(
        "- Complete-case observations: 34"
    )
    lines.append(
        "- Imputation: none"
    )
    lines.append("")
    lines.append(
        "## Baseline"
    )
    lines.append(
        "- Growth, Productivity and Connectivity: pooled "
        "percentile-rank scoring"
    )
    lines.append(
        "- Resilience R1: full-sample min-max"
    )
    lines.append(
        "- Resilience R2/R3: nonlinear P10-P90 reference-zone scoring"
    )
    lines.append(
        "- Strategic Autonomy: P10-P90 reference-bound min-max scoring"
    )
    lines.append(
        "- Pillar aggregation: equal-weight arithmetic mean"
    )
    lines.append(
        "- JESI aggregation: weighted geometric formulation"
    )
    lines.append("")
    lines.append(
        "## Alternative specifications"
    )
    lines.append(
        "- Full-sample min-max for monotonic indicators"
    )
    lines.append(
        "- 5th-95th percentile winsorized min-max for monotonic indicators"
    )
    lines.append(
        "- Pooled percentile-rank scoring"
    )
    lines.append(
        "- Resilience reference-zone sensitivity using P5-P95"
    )
    lines.append(
        "- Resilience reference-zone sensitivity using P20-P80"
    )
    lines.append("")
    lines.append(
        "R2 Government Debt and R3 Current Account are not "
        "mechanically forced into monotonic normalization because "
        "the current JESI methodology explicitly treats them as "
        "reference-zone indicators."
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
        "## Baseline country mean JESI"
    )
    lines.append("")
    lines.append(
        baseline_country.to_markdown(
            index=False,
            floatfmt=".6f",
        )
    )
    lines.append("")
    lines.append(
        "## Methodological interpretation rule"
    )
    lines.append("")
    lines.append(
        "High rank correlation and small score/rank changes "
        "support robustness to the tested normalization "
        "specifications. Material rank changes or large score "
        "changes constitute sensitivity signals requiring "
        "methodological review. No indicator is automatically "
        "removed, reweighted, or replaced by this analysis."
    )
    lines.append("")
    lines.append(
        "## Important limitation"
    )
    lines.append("")
    lines.append(
        "This test evaluates normalization sensitivity using "
        "the raw indicator values persisted in the JESI repository. "
        "It does not constitute a new production normalization "
        "specification and does not alter the Master Version 1.0 "
        "JESI results."
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:
    print("=" * 78)
    print("JESI NORMALIZATION SENSITIVITY ANALYSIS")
    print("=" * 78)

    scores = build_indicator_scores()

    specifications = [
        "baseline",
        "minmax",
        "winsorized_minmax",
        "percentile",
        "reference_p5_p95",
        "reference_p20_p80",
    ]

    complete_specs = {}

    for specification in specifications:
        print(
            f"Building specification: {specification}"
        )

        built = build_specification(
            scores,
            specification,
        )

        complete = validate_complete_case(
            built,
            specification,
        )

        complete_specs[
            specification
        ] = complete

        print(
            f"  Complete-case observations: {len(complete)}"
        )

    baseline = complete_specs[
        "baseline"
    ]

    alternatives = {
        key: value
        for key, value in complete_specs.items()
        if key != "baseline"
    }

    # ---------------------------------------------------------------
    # Combine country-year results
    # ---------------------------------------------------------------

    country_year = pd.concat(
        complete_specs.values(),
        ignore_index=True,
    )

    country_year = country_year.sort_values(
        [
            "specification",
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)

    # ---------------------------------------------------------------
    # Country summary
    # ---------------------------------------------------------------

    country_summary = build_country_summary(
        country_year
    )

    # ---------------------------------------------------------------
    # Rank correlations
    # ---------------------------------------------------------------

    rank_rows = []

    for specification in alternatives:

        for level in [
            "country_year",
            "country_mean",
        ]:
            rank_rows.append(
                rank_correlation(
                    baseline,
                    alternatives[
                        specification
                    ],
                    level,
                    specification,
                )
            )

    rank_results = pd.DataFrame(
        rank_rows
    )

    # ---------------------------------------------------------------
    # Sensitivity summary
    # ---------------------------------------------------------------

    sensitivity_summary = (
        build_sensitivity_summary(
            baseline,
            alternatives,
        )
    )

    # ---------------------------------------------------------------
    # Mathematical validation
    # ---------------------------------------------------------------

    for specification, df in complete_specs.items():

        recalculated = geometric_jesi(
            df
        )

        difference = (
            recalculated
            - df["JESI"]
        ).abs().max()

        if difference > 1e-10:
            fail(
                f"{specification}: JESI formula "
                f"validation failed. Max difference={difference}"
            )

    # ---------------------------------------------------------------
    # Output directory
    # ---------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Save outputs
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
        sensitivity_summary,
        rank_results,
        baseline,
    )

    REPORT_OUTPUT.write_text(
        report,
        encoding="utf-8",
    )

    # ---------------------------------------------------------------
    # Console summary
    # ---------------------------------------------------------------

    print()
    print("=" * 78)
    print("NORMALIZATION SENSITIVITY SUMMARY")
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
        "Normalization sensitivity analysis: PASSED"
    )

    print("=" * 78)


if __name__ == "__main__":
    main()
