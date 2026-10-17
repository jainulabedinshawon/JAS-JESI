#!/usr/bin/env python3
"""
JAS Unified Economic Strength Index (JESI)
Normalization Sensitivity Analysis
Master Version 1.0 — Phase 3 Audit

Purpose
-------
1. Use persisted production pillar scores as the authoritative baseline.
2. Compare baseline pillar scores and JESI with production outputs.
3. Evaluate three alternative monotonic normalization methods.
4. Evaluate Resilience reference-zone alternatives.
5. Report country-year coverage, numerical differences and ranking
   stability.
6. Keep every audit output isolated from production outputs.

Production methodology is not modified.
No imputation is performed.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


# ================================================================
# CONFIGURATION
# ================================================================

ROOT = Path(__file__).resolve().parents[1]

COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
    "VNM": "Vietnam",
}

FINAL_YEARS = set(range(2016, 2024))
DISTRIBUTION_YEARS = set(range(2015, 2025))

EXPECTED_PANEL_SIZE = 40
EXPECTED_COMPLETE_CASES = 34

WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}

PILLARS = ["G", "P", "C", "R", "A"]
NUMERIC_OUTPUTS = PILLARS + ["JESI"]

TOLERANCE = 1e-7

DEBT_LOWER = 29.287000
DEBT_UPPER = 77.458300

CURRENT_ACCOUNT_LOWER = -2.427516
CURRENT_ACCOUNT_UPPER = 3.881556

OUTPUT_DIR = (
    ROOT
    / "artifacts"
    / "normalization_audit"
    / "phase_3"
)

COUNTRY_YEAR_OUTPUT = (
    OUTPUT_DIR / "jesi_normalization_sensitivity_country_year.csv"
)

COUNTRY_SUMMARY_OUTPUT = (
    OUTPUT_DIR / "jesi_normalization_sensitivity_country_summary.csv"
)

RANK_OUTPUT = (
    OUTPUT_DIR / "jesi_normalization_sensitivity_rank_correlations.csv"
)

SUMMARY_OUTPUT = (
    OUTPUT_DIR / "jesi_normalization_sensitivity_summary.csv"
)

REPORT_OUTPUT = (
    OUTPUT_DIR / "jesi_normalization_sensitivity_report.md"
)

# Production outputs are READ ONLY.
PRODUCTION_JESI_FILE = (
    ROOT / "data" / "results" / "jesi_country_year_2016_2023.csv"
)

GROWTH_FILE = (
    ROOT / "data" / "processed"
    / "growth_pillar_scores_2015_2024.csv"
)

PRODUCTIVITY_P1_FILE = (
    ROOT / "data" / "processed"
    / "productivity_p1_scores_2016_2023.csv"
)

PRODUCTIVITY_P2_FILE = (
    ROOT / "data" / "processed"
    / "productivity_p2_scores_2016_2023.csv"
)

CONNECTIVITY_FILE = (
    ROOT / "data" / "processed"
    / "connectivity_indicator_scores_2015_2024.csv"
)

RESILIENCE_FILE = (
    ROOT / "data" / "processed"
    / "resilience_pillar_scores_2015_2024.csv"
)

AUTONOMY_FILE = (
    ROOT / "data" / "processed"
    / "autonomy_indicator_scores_2015_2024.csv"
)

PRODUCTIVITY_PILLAR_FILE = (
    ROOT / "data" / "processed"
    / "productivity_pillar_scores_2016_2023.csv"
)

CONNECTIVITY_PILLAR_FILE = (
    ROOT / "data" / "processed"
    / "connectivity_pillar_scores_2015_2024.csv"
)

AUTONOMY_PILLAR_FILE = (
    ROOT / "data" / "processed"
    / "strategic_autonomy_pillar_2015_2024.csv"
)


SPECIFICATIONS = [
    "baseline",
    "minmax",
    "winsorized_minmax",
    "percentile",
    "reference_p5_p95",
    "reference_p20_p80",
]


# ================================================================
# GENERAL VALIDATION
# ================================================================

def fail(message):
    raise RuntimeError(message)


def require_file(path):
    if not path.is_file():
        fail(f"Required input file not found: {path}")


def read_csv(path):
    require_file(path)
    return pd.read_csv(path)


def country_code(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip().lower()
    text = text.replace("_", " ").replace("-", " ")

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
        "vnm": "VNM",
    }

    return mapping.get(text, np.nan)


def standardize_keys(df, name, country_column="country_code"):
    df = df.copy()

    if country_column not in df.columns:
        fail(f"{name}: missing country column {country_column!r}.")

    if "year" not in df.columns:
        fail(f"{name}: missing year column.")

    df["country_code"] = df[country_column].apply(country_code)

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    if df["year"].isna().any():
        fail(f"{name}: invalid or missing year values.")

    if not np.isfinite(df["year"].to_numpy(dtype=float)).all():
        fail(f"{name}: non-finite year values.")

    if not df["year"].mod(1).eq(0).all():
        fail(f"{name}: non-integer year values.")

    df["year"] = df["year"].astype(int)

    df = df[
        df["country_code"].isin(COUNTRIES)
    ].copy()

    duplicates = df.duplicated(
        ["country_code", "year"],
        keep=False,
    )

    if duplicates.any():
        sample = df.loc[
            duplicates,
            ["country_code", "year"],
        ].to_string(index=False)

        fail(f"{name}: duplicate country-year keys:\n{sample}")

    return df


def numeric_column(df, column, name):
    if column not in df.columns:
        fail(f"{name}: required column {column!r} is missing.")

    result = pd.to_numeric(
        df[column],
        errors="coerce",
    )

    invalid = df[column].notna() & result.isna()

    if invalid.any():
        fail(f"{name}.{column}: non-numeric values found.")

    result = result.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    return result


def validate_weights():
    if not np.isclose(sum(WEIGHTS.values()), 1.0):
        fail("JESI weights do not sum to 1.")

    if WEIGHTS != {
        "G": 0.20,
        "P": 0.25,
        "C": 0.20,
        "R": 0.20,
        "A": 0.15,
    }:
        fail("Unexpected change to Master Version 1.0 weights.")


def expected_panel():
    return pd.DataFrame(
        [
            {
                "country_code": code,
                "country": name,
                "year": year,
            }
            for code, name in COUNTRIES.items()
            for year in sorted(FINAL_YEARS)
        ]
    )


# ================================================================
# NORMALIZATION FUNCTIONS
# ================================================================

def percentile_score(series):
    """
    Average-rank percentile scoring, matching the pandas ranking
    convention used by the Growth and Productivity scoring scripts.
    """
    values = pd.to_numeric(series, errors="coerce")

    return values.rank(
        method="average",
        pct=True,
        na_option="keep",
    ).clip(lower=0.001, upper=1.0)


def minmax_positive(series):
    values = pd.to_numeric(series, errors="coerce")
    low = values.min()
    high = values.max()

    if pd.isna(low) or pd.isna(high):
        return pd.Series(np.nan, index=series.index)

    if np.isclose(high, low):
        return pd.Series(1.0, index=series.index)

    return ((values - low) / (high - low)).clip(0.0, 1.0)


def minmax_negative(series):
    values = pd.to_numeric(series, errors="coerce")
    low = values.min()
    high = values.max()

    if pd.isna(low) or pd.isna(high):
        return pd.Series(np.nan, index=series.index)

    if np.isclose(high, low):
        return pd.Series(1.0, index=series.index)

    return ((high - values) / (high - low)).clip(0.0, 1.0)


def winsorized_minmax_positive(series):
    values = pd.to_numeric(series, errors="coerce")
    low = values.quantile(0.05)
    high = values.quantile(0.95)

    if pd.isna(low) or pd.isna(high):
        return pd.Series(np.nan, index=series.index)

    if np.isclose(high, low):
        return pd.Series(1.0, index=series.index)

    clipped = values.clip(lower=low, upper=high)

    return ((clipped - low) / (high - low)).clip(0.0, 1.0)


def winsorized_minmax_negative(series):
    values = pd.to_numeric(series, errors="coerce")
    low = values.quantile(0.05)
    high = values.quantile(0.95)

    if pd.isna(low) or pd.isna(high):
        return pd.Series(np.nan, index=series.index)

    if np.isclose(high, low):
        return pd.Series(1.0, index=series.index)

    clipped = values.clip(lower=low, upper=high)

    return ((high - clipped) / (high - low)).clip(0.0, 1.0)


def normalize_monotonic(series, method, direction="positive"):
    if direction not in {"positive", "negative"}:
        fail(f"Unknown indicator direction: {direction}")

    if method == "percentile":
        scored = percentile_score(series)

        if direction == "negative":
            valid = pd.to_numeric(series, errors="coerce").notna()
            scored.loc[valid] = (
                1.0
                - percentile_score(series.loc[valid])
                + 1.0 / max(int(valid.sum()), 1)
            ).clip(0.001, 1.0)

        return scored

    if method == "minmax":
        return (
            minmax_positive(series)
            if direction == "positive"
            else minmax_negative(series)
        )

    if method == "winsorized_minmax":
        return (
            winsorized_minmax_positive(series)
            if direction == "positive"
            else winsorized_minmax_negative(series)
        )

    fail(f"Unknown monotonic normalization: {method}")


def reference_zone_score(series, lower, upper):
    """
    JESI nonlinear reference-zone scoring:
    1 inside the zone; exponential penalty outside it.
    """
    if not lower < upper:
        fail("Reference-zone lower bound must be below upper bound.")

    values = pd.to_numeric(series, errors="coerce")
    width = upper - lower
    lam = np.log(2.0)

    distance_below = (lower - values).clip(lower=0.0) / width
    distance_above = (values - upper).clip(lower=0.0) / width

    distance = distance_below + distance_above

    return np.exp(-lam * distance).clip(0.0, 1.0)


def weighted_geometric_jesi(df, allow_zero=False):
    values = df[PILLARS].to_numpy(dtype=float)

    if not np.isfinite(values).all():
        fail("Pillar values contain missing or non-finite values.")

    lower_bound_invalid = (
        (values < 0.0).any()
        if allow_zero
        else (values <= 0.0).any()
    )

    if lower_bound_invalid or (values > 1.0).any():
        allowed = "[0, 1]" if allow_zero else "(0, 1]"
        fail(f"Pillar scores must be within {allowed}.")

    # Preserve the production weighted-geometric formulation.
    with np.errstate(divide="ignore", invalid="ignore"):
        result = (
            100.0
            * np.power(df["G"], WEIGHTS["G"])
            * np.power(df["P"], WEIGHTS["P"])
            * np.power(df["C"], WEIGHTS["C"])
            * np.power(df["R"], WEIGHTS["R"])
            * np.power(df["A"], WEIGHTS["A"])
        )

    return result


def arithmetic_mean(df, columns):
    if not columns:
        fail("Cannot aggregate an empty indicator list.")

    return df[columns].mean(axis=1, skipna=False)


# ================================================================
# LOAD AUTHORITATIVE PRODUCTION BASELINE
# ================================================================

def load_pillar_file(path, score_column, pillar, country_column="country_code"):
    df = read_csv(path)

    if score_column not in df.columns:
        fail(
            f"{path.name}: expected production score column "
            f"{score_column!r} was not found."
        )

    if country_column not in df.columns:
        # Resilience production output uses country names.
        if "country" in df.columns:
            country_column = "country"
        else:
            fail(f"{path.name}: no usable country column.")

    df = standardize_keys(
        df,
        path.name,
        country_column=country_column,
    )

    result = df[
        ["country_code", "year"]
    ].copy()

    result[pillar] = numeric_column(
        df,
        score_column,
        path.name,
    ).to_numpy()

    return result


def load_production_baseline():
    """
    The persisted pillar outputs are authoritative for the baseline.
    This prevents a reconstructed approximation from being mislabeled
    as production-equivalent.
    """
    growth = load_pillar_file(
        GROWTH_FILE,
        "growth_score",
        "G",
    )

    productivity = load_pillar_file(
        PRODUCTIVITY_PILLAR_FILE,
        "productivity_score",
        "P",
    )

    connectivity = load_pillar_file(
        CONNECTIVITY_PILLAR_FILE,
        "connectivity_score",
        "C",
    )

    resilience = load_pillar_file(
        RESILIENCE_FILE,
        "resilience_score",
        "R",
        country_column="country",
    )

    autonomy = load_pillar_file(
        AUTONOMY_PILLAR_FILE,
        "strategic_autonomy_arithmetic",
        "A",
    )

    baseline = expected_panel()

    for pillar_df in [
        growth,
        productivity,
        connectivity,
        resilience,
        autonomy,
    ]:
        baseline = baseline.merge(
            pillar_df,
            on=["country_code", "year"],
            how="left",
            validate="one_to_one",
        )

    baseline["JESI"] = np.nan

    complete = baseline[PILLARS].notna().all(axis=1)

    if complete.sum() != EXPECTED_COMPLETE_CASES:
        fail(
            "Production pillar files do not yield the expected "
            f"{EXPECTED_COMPLETE_CASES} complete cases; "
            f"found {int(complete.sum())}. No imputation was performed."
        )

    baseline.loc[complete, "JESI"] = weighted_geometric_jesi(
        baseline.loc[complete],
        allow_zero=False,
    )

    return baseline


def compare_with_production_csv(baseline):
    production = read_csv(PRODUCTION_JESI_FILE)

    required = {
        "country_code",
        "year",
        *PILLARS,
        "JESI",
    }

    missing = required - set(production.columns)

    if missing:
        fail(
            "Production JESI CSV is missing required columns: "
            f"{sorted(missing)}"
        )

    production = standardize_keys(
        production,
        PRODUCTION_JESI_FILE.name,
    )

    for column in NUMERIC_OUTPUTS:
        production[column] = numeric_column(
            production,
            column,
            PRODUCTION_JESI_FILE.name,
        )

    production = production[
        production["year"].isin(FINAL_YEARS)
    ].copy()

    production_complete = production[
        NUMERIC_OUTPUTS
    ].notna().all(axis=1)

    production_complete = production.loc[
        production_complete
    ].copy()

    baseline_complete = baseline[
        baseline[NUMERIC_OUTPUTS].notna().all(axis=1)
    ].copy()

    merged = baseline_complete.merge(
        production_complete,
        on=["country_code", "year"],
        how="outer",
        suffixes=("_reconstructed", "_production"),
        indicator=True,
        validate="one_to_one",
    )

    if not merged["_merge"].eq("both").all():
        counts = merged["_merge"].value_counts().to_dict()
        fail(
            "Production/baseline country-year key mismatch: "
            f"{counts}"
        )

    rows = []

    for column in NUMERIC_OUTPUTS:
        reconstructed = merged[f"{column}_reconstructed"]
        persisted = merged[f"{column}_production"]

        diff = (reconstructed - persisted).abs()

        rows.append(
            {
                "field": column,
                "n": int(diff.notna().sum()),
                "max_absolute_difference": float(diff.max()),
                "mean_absolute_difference": float(diff.mean()),
                "within_tolerance": bool(
                    (diff <= TOLERANCE).all()
                ),
            }
        )

    differences = pd.DataFrame(rows)

    if not differences["within_tolerance"].all():
        failed = differences.loc[
            ~differences["within_tolerance"]
        ].to_dict("records")

        fail(
            "Production equivalence check FAILED. "
            "Do not interpret the reconstructed baseline as verified. "
            f"Differences: {failed}"
        )

    return differences


# ================================================================
# LOAD RAW INDICATORS FOR ALTERNATIVE SPECIFICATIONS
# ================================================================

def load_indicator_table(path, name, columns, country_column="country_code"):
    df = read_csv(path)

    if country_column not in df.columns and "country" in df.columns:
        country_column = "country"

    df = standardize_keys(
        df,
        name,
        country_column=country_column,
    )

    for column in columns:
        df[column] = numeric_column(df, column, name)

    return df[
        ["country_code", "year", *columns]
    ].copy()


def load_raw_indicators():
    growth = load_indicator_table(
        GROWTH_FILE,
        "Growth",
        ["real_gdp_growth", "gni_per_capita_growth"],
    )

    p1 = load_indicator_table(
        PRODUCTIVITY_P1_FILE,
        "Productivity P1",
        ["gdp_per_person_employed"],
    )

    p2 = load_indicator_table(
        PRODUCTIVITY_P2_FILE,
        "Productivity P2",
        ["tfp_growth"],
    )

    connectivity = load_indicator_table(
        CONNECTIVITY_FILE,
        "Connectivity",
        ["trade_openness", "fdi_inflows", "internet_use"],
    )

    resilience = load_indicator_table(
        RESILIENCE_FILE,
        "Resilience",
        [
            "fx_reserves_months",
            "government_debt_gdp",
            "current_account_gdp",
        ],
        country_column="country",
    )

    autonomy = load_indicator_table(
        AUTONOMY_FILE,
        "Strategic Autonomy",
        ["eci", "high_tech_exports", "import_product_concentration"],
    )

    # Merge raw indicators by country-code/year, never country-name text.
    frames = [
        growth,
        p1,
        p2,
        connectivity,
        resilience,
        autonomy,
    ]

    merged = frames[0]

    for frame in frames[1:]:
        merged = merged.merge(
            frame,
            on=["country_code", "year"],
            how="outer",
            validate="one_to_one",
        )

    merged["country"] = merged["country_code"].map(COUNTRIES)

    return merged


# ================================================================
# BUILD ALTERNATIVE SCORES
# ================================================================

def score_alternative_indicators(raw, method):
    scored = raw[
        ["country_code", "country", "year"]
    ].copy()

    # Growth: two positively directed indicators.
    scored["G1"] = normalize_monotonic(
        raw["real_gdp_growth"], method
    )
    scored["G2"] = normalize_monotonic(
        raw["gni_per_capita_growth"], method
    )
    scored["G"] = arithmetic_mean(scored, ["G1", "G2"])

    # Productivity: two positively directed indicators.
    scored["P1"] = normalize_monotonic(
        raw["gdp_per_person_employed"], method
    )
    scored["P2"] = normalize_monotonic(
        raw["tfp_growth"], method
    )
    scored["P"] = arithmetic_mean(scored, ["P1", "P2"])

    # Connectivity: three positively directed indicators.
    scored["C1"] = normalize_monotonic(
        raw["trade_openness"], method
    )
    scored["C2"] = normalize_monotonic(
        raw["fdi_inflows"], method
    )
    scored["C3"] = normalize_monotonic(
        raw["internet_use"], method
    )
    scored["C"] = arithmetic_mean(scored, ["C1", "C2", "C3"])

    # Resilience:
    # R1 is positively directed; R2/R3 retain nonlinear
    # reference-zone scoring except in the dedicated zone tests.
    scored["R1"] = normalize_monotonic(
        raw["fx_reserves_months"], method
    )

    scored["R2"] = reference_zone_score(
        raw["government_debt_gdp"],
        DEBT_LOWER,
        DEBT_UPPER,
    )

    scored["R3"] = reference_zone_score(
        raw["current_account_gdp"],
        CURRENT_ACCOUNT_LOWER,
        CURRENT_ACCOUNT_UPPER,
    )

    scored["R"] = arithmetic_mean(
        scored,
        ["R1", "R2", "R3"],
    )

    # Strategic Autonomy: ECI and high-tech exports positive;
    # import concentration negative.
    scored["A1"] = normalize_monotonic(
        raw["eci"], method
    )
    scored["A2"] = normalize_monotonic(
        raw["high_tech_exports"], method
    )
    scored["A3"] = normalize_monotonic(
        raw["import_product_concentration"],
        method,
        direction="negative",
    )

    scored["A"] = arithmetic_mean(
        scored,
        ["A1", "A2", "A3"],
    )

    return scored


def apply_reference_zone_alternative(raw, name):
    scored = raw[
        ["country_code", "country", "year"]
    ].copy()

    # Other pillars retain their current production baseline.
    baseline = load_production_baseline()

    scored = scored.merge(
        baseline[
            ["country_code", "year", "G", "P", "C", "R", "A"]
        ],
        on=["country_code", "year"],
        how="left",
        validate="one_to_one",
    )

    # Recompute only Resilience R2/R3 bounds.
    if name == "reference_p5_p95":
        lower_q, upper_q = 0.05, 0.95
    elif name == "reference_p20_p80":
        lower_q, upper_q = 0.20, 0.80
    else:
        fail(f"Invalid reference-zone specification: {name}")

    debt = raw["government_debt_gdp"]
    current_account = raw["current_account_gdp"]

    debt_lower = debt.quantile(lower_q)
    debt_upper = debt.quantile(upper_q)

    ca_lower = current_account.quantile(lower_q)
    ca_upper = current_account.quantile(upper_q)

    debt_score = reference_zone_score(
        debt,
        debt_lower,
        debt_upper,
    )

    ca_score = reference_zone_score(
        current_account,
        ca_lower,
        ca_upper,
    )

    # Use the same R1 production score and replace only R2/R3.
    resilience_source = read_csv(RESILIENCE_FILE)
    resilience_source = standardize_keys(
        resilience_source,
        "Resilience production file",
        country_column="country",
    )

    if "R1_fx_reserves_score" not in resilience_source.columns:
        fail("Resilience file missing R1_fx_reserves_score.")

    resilience_source["R1_fx_reserves_score"] = numeric_column(
        resilience_source,
        "R1_fx_reserves_score",
        "Resilience",
    )

    r1 = resilience_source[
        ["country_code", "year", "R1_fx_reserves_score"]
    ].rename(columns={"R1_fx_reserves_score": "R1"})

    zone_data = raw[
        ["country_code", "year"]
    ].copy()

    zone_data["R2"] = debt_score.to_numpy()
    zone_data["R3"] = ca_score.to_numpy()

    zone_data = zone_data.merge(
        r1,
        on=["country_code", "year"],
        how="left",
        validate="one_to_one",
    )

    zone_data["R_new"] = arithmetic_mean(
        zone_data,
        ["R1", "R2", "R3"],
    )

    scored = scored.drop(columns=["R"]).merge(
        zone_data[
            ["country_code", "year", "R_new"]
        ],
        on=["country_code", "year"],
        how="left",
        validate="one_to_one",
    )

    scored = scored.rename(columns={"R_new": "R"})

    return scored


def build_specification(raw, baseline, name):
    if name == "baseline":
        result = baseline.copy()

    elif name in {
        "minmax",
        "winsorized_minmax",
        "percentile",
    }:
        result = score_alternative_indicators(
            raw,
            name,
        )

    elif name in {
        "reference_p5_p95",
        "reference_p20_p80",
    }:
        result = apply_reference_zone_alternative(
            raw,
            name,
        )

    else:
        fail(f"Unknown specification: {name}")

    result = result[
        result["year"].isin(FINAL_YEARS)
        & result["country_code"].isin(COUNTRIES)
    ].copy()

    result["specification"] = name

    result = result.sort_values(
        ["country_code", "year"]
    ).reset_index(drop=True)

      # Calculate JESI only for complete country-year cases.
    # Never impute missing pillar scores.
    if name != "baseline":
        result["JESI"] = np.nan
        complete_mask = result[PILLARS].notna().all(axis=1)

        if complete_mask.any():
            result.loc[complete_mask, "JESI"] = (
                weighted_geometric_jesi(
                    result.loc[complete_mask],
                    allow_zero=True,
                )
            )

    return result


# ================================================================
# PANEL / EQUIVALENCE VALIDATION
# ================================================================

def validate_complete_case_panel(frame, name):
    theoretical = expected_panel()

    keys = frame[
        ["country_code", "year"]
    ].drop_duplicates()

    if len(keys) != EXPECTED_PANEL_SIZE:
        fail(
            f"{name}: expected {EXPECTED_PANEL_SIZE} theoretical "
            f"country-year keys, found {len(keys)}."
        )

    if len(keys.merge(
        theoretical[["country_code", "year"]],
        on=["country_code", "year"],
        how="inner",
    )) != EXPECTED_PANEL_SIZE:
        fail(f"{name}: unexpected country-year panel coverage.")

    complete_mask = frame[PILLARS].notna().all(axis=1)
    complete = frame.loc[complete_mask].copy()

    if len(complete) != EXPECTED_COMPLETE_CASES:
        fail(
            f"{name}: expected {EXPECTED_COMPLETE_CASES} complete "
            f"cases, found {len(complete)}. No imputation permitted."
        )

    if complete.duplicated(["country_code", "year"]).any():
        fail(f"{name}: duplicate complete-case country-year keys.")

    return complete


# ================================================================
# RANKING / SENSITIVITY SUMMARIES
# ================================================================

def rank_correlations(all_results):
    rows = []

    baseline = all_results[
        all_results["specification"] == "baseline"
    ][["country_code", "year", "JESI"]].rename(
        columns={"JESI": "JESI_baseline"}
    )

    for specification in SPECIFICATIONS:
        if specification == "baseline":
            continue

        alternative = all_results[
            all_results["specification"] == specification
        ][["country_code", "year", "JESI"]].rename(
            columns={"JESI": "JESI_alternative"}
        )

        joined = baseline.merge(
            alternative,
            on=["country_code", "year"],
            how="inner",
            validate="one_to_one",
        ).dropna()

        rho = (
            float(
                spearmanr(
                    joined["JESI_baseline"],
                    joined["JESI_alternative"],
                ).statistic
            )
            if len(joined) >= 2
            else np.nan
        )

        rows.append(
            {
                "specification": specification,
                "analysis_level": "country_year",
                "pairwise_n": len(joined),
                "spearman_rho": rho,
            }
        )

        base_country = (
            joined.groupby("country_code")["JESI_baseline"].mean()
        )

        alt_country = (
            joined.groupby("country_code")["JESI_alternative"].mean()
        )

        country_join = pd.concat(
            [
                base_country.rename("baseline"),
                alt_country.rename("alternative"),
            ],
            axis=1,
            join="inner",
        ).dropna()

        country_rho = (
            float(
                spearmanr(
                    country_join["baseline"],
                    country_join["alternative"],
                ).statistic
            )
            if len(country_join) >= 2
            else np.nan
        )

        rows.append(
            {
                "specification": specification,
                "analysis_level": "country_mean",
                "pairwise_n": len(country_join),
                "spearman_rho": country_rho,
            }
        )

    return pd.DataFrame(rows)


def build_country_summary(all_results):
    summary = (
        all_results
        .groupby(
            ["specification", "country_code", "country"],
            as_index=False,
        )
        .agg(
            mean_jesi=("JESI", "mean"),
            observations=("JESI", "count"),
        )
    )

    summary["rank"] = (
        summary.groupby("specification")["mean_jesi"]
        .rank(method="min", ascending=False)
    )

    summary["rank"] = summary["rank"].astype("Int64")

    return summary.sort_values(
        ["specification", "rank", "country_code"]
    ).reset_index(drop=True)


def build_sensitivity_summary(all_results):
    baseline = all_results[
        all_results["specification"] == "baseline"
    ][["country_code", "year", *PILLARS, "JESI"]]

    rows = []

    for specification in SPECIFICATIONS:
        if specification == "baseline":
            continue

        alternative = all_results[
            all_results["specification"] == specification
        ][["country_code", "year", *PILLARS, "JESI"]]

        joined = baseline.merge(
            alternative,
            on=["country_code", "year"],
            how="inner",
            suffixes=("_baseline", "_alternative"),
            validate="one_to_one",
        )

        row = {
            "specification": specification,
            "country_year_n": len(joined),
        }

        for column in NUMERIC_OUTPUTS:
            difference = (
                joined[f"{column}_alternative"]
                - joined[f"{column}_baseline"]
            ).abs()

            row[f"{column}_mean_absolute_difference"] = (
                float(difference.mean())
            )
            row[f"{column}_max_absolute_difference"] = (
                float(difference.max())
            )

        baseline_country = (
            joined.groupby("country_code")["JESI_baseline"].mean()
        )
        alternative_country = (
            joined.groupby("country_code")["JESI_alternative"].mean()
        )

        base_rank = baseline_country.rank(
            method="min",
            ascending=False,
        )
        alt_rank = alternative_country.rank(
            method="min",
            ascending=False,
        )

        rank_diff = (alt_rank - base_rank).abs()

        row["countries_with_rank_change"] = int(
            (rank_diff > 0).sum()
        )
        row["max_country_rank_change"] = float(rank_diff.max())

        rows.append(row)

    return pd.DataFrame(rows)


# ================================================================
# REPORT
# ================================================================

def build_report(
    equivalence,
    sensitivity_summary,
    rank_results,
    country_summary,
    baseline,
):
    baseline_country = country_summary[
        country_summary["specification"] == "baseline"
    ].sort_values("rank")

    lines = [
        "# JESI Normalization Sensitivity Analysis",
        "",
        "## Audit scope",
        "",
        "- JESI Master Version 1.0.",
        "- Five benchmark countries: Bangladesh, India, Indonesia, Malaysia, Vietnam.",
        "- Final comparison period: 2016–2023.",
        "- Theoretical panel: 40 country-year observations.",
        "- Expected complete cases: 34.",
        "- Missing-data treatment: complete cases only; no imputation.",
        "- Production formulas, pillar weights, and production outputs are unchanged.",
        "",
        "## Production-baseline equivalence",
        "",
        "The following table compares reconstructed JESI values based on the "
        "persisted production pillar scores against the persisted production "
        "JESI CSV. This comparison was computed at runtime.",
        "",
        equivalence.to_markdown(index=False, floatfmt=".10f"),
        "",
        "## Baseline country mean JESI",
        "",
        baseline_country.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Sensitivity summary",
        "",
        sensitivity_summary.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Rank correlations",
        "",
        rank_results.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Interpretation and limitations",
        "",
        "The baseline uses persisted production pillar scores. Alternative "
        "specifications are research-only and do not replace the Master "
        "Version 1.0 production specification.",
        "",
        "Pooled percentile scoring and min-max scoring can produce different "
        "pillar scores and rankings. Resilience P5–P95 and P20–P80 variants "
        "change the reference-zone bounds for government debt and current "
        "account balance only.",
        "",
        "Country-level rank correlations use only five country means and "
        "should be interpreted descriptively, not as strong inferential evidence.",
        "",
        "The audit does not establish universal validity of JESI. It evaluates "
        "reproducibility and sensitivity under the tested specifications only.",
        "",
        "No production output was written or modified by this script.",
        "",
    ]

    return "\n".join(lines)


# ================================================================
# MAIN
# ================================================================

def main():
    print("=" * 72)
    print("JESI NORMALIZATION SENSITIVITY — PHASE 3")
    print("=" * 72)

    validate_weights()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/7] Loading authoritative production pillar scores...")
    baseline = load_production_baseline()

    print("[2/7] Checking baseline against production JESI output...")
    equivalence = compare_with_production_csv(baseline)

    print("[3/7] Loading persisted raw indicator values...")
    raw = load_raw_indicators()

    print("[4/7] Building baseline and alternative specifications...")
    results = []

    for specification in SPECIFICATIONS:
        print(f"  - {specification}")

        frame = build_specification(
            raw,
            baseline,
            specification,
        )

        complete = validate_complete_case_panel(
            frame,
            specification,
        )

        results.append(complete)

    all_results = pd.concat(
        results,
        ignore_index=True,
    )

    print("[5/7] Calculating sensitivity and ranking diagnostics...")
    sensitivity_summary = build_sensitivity_summary(all_results)
    correlations = rank_correlations(all_results)
    country_summary = build_country_summary(all_results)

    print("[6/7] Writing isolated audit outputs...")
    all_results.to_csv(COUNTRY_YEAR_OUTPUT, index=False)
    country_summary.to_csv(COUNTRY_SUMMARY_OUTPUT, index=False)
    correlations.to_csv(RANK_OUTPUT, index=False)
    sensitivity_summary.to_csv(SUMMARY_OUTPUT, index=False)

    report = build_report(
        equivalence,
        sensitivity_summary,
        correlations,
        country_summary,
        baseline,
    )

    REPORT_OUTPUT.write_text(
        report,
        encoding="utf-8",
    )

    print("[7/7] Audit finished.")
    print()
    print("Production equivalence:")
    print(equivalence.to_string(index=False))
    print()
    print("Audit outputs:")
    print(f"  {COUNTRY_YEAR_OUTPUT}")
    print(f"  {COUNTRY_SUMMARY_OUTPUT}")
    print(f"  {RANK_OUTPUT}")
    print(f"  {SUMMARY_OUTPUT}")
    print(f"  {REPORT_OUTPUT}")
    print()
    print("STATUS: COMPLETED")
    print("This status does not mean all alternative methods are robust.")
    print("Review the equivalence and sensitivity outputs before publication.")
    print("=" * 72)


if __name__ == "__main__":
    main()
