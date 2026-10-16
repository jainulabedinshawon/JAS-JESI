
"""
JAS Unified Economic Strength Index (JESI)
Normalization Sensitivity Analysis
Master Version 1.0 — Phase 3

IMPORTANT
---------
This script is an audit tool, not a production scoring pipeline.
It never overwrites production inputs or the final JESI results.

Production pillar scores are reconstructed from persisted scores
where available. Growth uses its persisted aggregate pillar score
because this input does not necessarily contain separate persisted
production scores for its underlying indicators.

The reconstructed baseline is reconciled against the stored final
JESI output. A mismatch is reported, never silently treated as a pass.
"""

from pathlib import Path
import warnings

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

YEARS = list(range(2016, 2024))
EXPECTED_PANEL = len(COUNTRIES) * len(YEARS)
EXPECTED_COMPLETE = 34
TOLERANCE = 1e-6

WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}

DATA = ROOT / "data" / "processed"
PRODUCTION_FILE = (
    ROOT / "data" / "results"
    / "jesi_country_year_2016_2023.csv"
)

INPUTS = {
    "growth": DATA / "growth_pillar_scores_2015_2024.csv",
    "p1": DATA / "productivity_p1_scores_2016_2023.csv",
    "p2": DATA / "productivity_p2_scores_2016_2023.csv",
    "connectivity": DATA / "connectivity_indicator_scores_2015_2024.csv",
    "resilience": DATA / "resilience_pillar_scores_2015_2024.csv",
    "autonomy": DATA / "autonomy_indicator_scores_2015_2024.csv",
}

OUT = ROOT / "artifacts" / "normalization_audit" / "phase_3"

OUTPUTS = {
    "country_year": OUT / "jesi_normalization_sensitivity_country_year.csv",
    "country_summary": OUT / "jesi_normalization_sensitivity_country_summary.csv",
    "rank": OUT / "jesi_normalization_sensitivity_rank_correlations.csv",
    "summary": OUT / "jesi_normalization_sensitivity_summary.csv",
    "report": OUT / "jesi_normalization_sensitivity_report.md",
    "reconciliation": OUT / "jesi_normalization_production_reconciliation.csv",
}

SPECIFICATIONS = [
    "baseline",
    "minmax",
    "winsorized_minmax",
    "percentile",
    "reference_p5_p95",
    "reference_p20_p80",
]


# ================================================================
# GENERAL UTILITIES
# ================================================================

def fail(message):
    raise RuntimeError(message)


def require_file(path):
    if not path.is_file():
        fail(f"Required input file not found: {path}")


def standardize_country(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip().lower()

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

    return mapping.get(value, np.nan)


def standardize_keys(df, name, country_column=None):
    df = df.copy()

    if country_column is None:
        candidates = [
            "country_code",
            "country",
            "Country",
            "country_name",
        ]
        country_column = next(
            (c for c in candidates if c in df.columns),
            None,
        )

    if country_column is None:
        fail(f"{name}: no recognizable country column.")

    if country_column != "country_code":
        df["country_code"] = df[country_column].apply(
            standardize_country
        )
    else:
        df["country_code"] = df["country_code"].apply(
            standardize_country
        )

    if "year" not in df.columns:
        fail(f"{name}: missing year column.")

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["country_code", "year"]).copy()
    df["year"] = df["year"].astype(int)

    df = df[
        df["country_code"].isin(COUNTRIES)
        & df["year"].isin(YEARS)
    ].copy()

    if df.duplicated(["country_code", "year"]).any():
        fail(f"{name}: duplicate country-year records detected.")

    return df


def numeric_column(df, column, name, required=True):
    if column not in df.columns:
        if required:
            fail(f"{name}: required column '{column}' is missing.")
        return pd.Series(np.nan, index=df.index, dtype=float)

    return pd.to_numeric(df[column], errors="coerce")


def merge_one_to_one(left, right, name):
    return left.merge(
        right,
        on=["country_code", "year"],
        how="outer",
        validate="one_to_one",
        suffixes=("", "_duplicate"),
    )


# ================================================================
# NORMALIZATION METHODS
# ================================================================

def minmax_positive(series):
    x = pd.to_numeric(series, errors="coerce")
    lo, hi = x.min(), x.max()

    if pd.isna(lo) or pd.isna(hi):
        return pd.Series(np.nan, index=x.index)

    if np.isclose(lo, hi):
        return pd.Series(np.where(x.notna(), 1.0, np.nan), index=x.index)

    return ((x - lo) / (hi - lo)).clip(0, 1)


def minmax_negative(series):
    x = pd.to_numeric(series, errors="coerce")
    lo, hi = x.min(), x.max()

    if pd.isna(lo) or pd.isna(hi):
        return pd.Series(np.nan, index=x.index)

    if np.isclose(lo, hi):
        return pd.Series(np.where(x.notna(), 1.0, np.nan), index=x.index)

    return ((hi - x) / (hi - lo)).clip(0, 1)


def winsor_positive(series):
    x = pd.to_numeric(series, errors="coerce")
    lo, hi = x.quantile(0.05), x.quantile(0.95)

    if pd.isna(lo) or pd.isna(hi):
        return pd.Series(np.nan, index=x.index)

    if np.isclose(lo, hi):
        return pd.Series(np.where(x.notna(), 1.0, np.nan), index=x.index)

    return ((x.clip(lo, hi) - lo) / (hi - lo)).clip(0, 1)


def winsor_negative(series):
    x = pd.to_numeric(series, errors="coerce")
    lo, hi = x.quantile(0.05), x.quantile(0.95)

    if pd.isna(lo) or pd.isna(hi):
        return pd.Series(np.nan, index=x.index)

    if np.isclose(lo, hi):
        return pd.Series(np.where(x.notna(), 1.0, np.nan), index=x.index)

    return ((hi - x.clip(lo, hi)) / (hi - lo)).clip(0, 1)


def percentile_score(series):
    x = pd.to_numeric(series, errors="coerce")
    return x.rank(method="average", pct=True).clip(0.001, 1.0)


def reference_score(series, lower, upper):
    if not np.isfinite(lower) or not np.isfinite(upper) or upper <= lower:
        fail("Invalid nonlinear reference-zone bounds.")

    x = pd.to_numeric(series, errors="coerce")
    width = upper - lower
    distance = (
        (lower - x).clip(lower=0) / width
        + (x - upper).clip(lower=0) / width
    )
    return np.exp(-np.log(2.0) * distance).clip(0, 1)


def reference_quantiles(series, low_q, high_q):
    x = pd.to_numeric(series, errors="coerce")
    lower = x.quantile(low_q)
    upper = x.quantile(high_q)
    return reference_score(x, lower, upper)


def normalize(series, method, direction="positive"):
    if method == "minmax":
        return (
            minmax_positive(series)
            if direction == "positive"
            else minmax_negative(series)
        )

    if method == "winsorized_minmax":
        return (
            winsor_positive(series)
            if direction == "positive"
            else winsor_negative(series)
        )

    if method == "percentile":
        if direction == "negative":
            return percentile_score(-pd.to_numeric(series, errors="coerce"))
        return percentile_score(series)

    fail(f"Unknown monotonic normalization: {method}")


# ================================================================
# LOAD PERSISTED PRODUCTION INPUTS
# ================================================================

def load_inputs():
    for path in INPUTS.values():
        require_file(path)

    tables = {}

    # Growth: stored aggregate score plus raw indicators for alternatives.
    g = pd.read_csv(INPUTS["growth"])
    g = standardize_keys(g, "Growth")

    for c in ["growth_score", "real_gdp_growth", "gni_per_capita_growth"]:
        g[c] = numeric_column(g, c, "Growth", required=(c == "growth_score"))

    tables["growth"] = g[
        ["country_code", "year", "growth_score",
         "real_gdp_growth", "gni_per_capita_growth"]
    ].copy()

    # Productivity.
    p1 = pd.read_csv(INPUTS["p1"])
    p2 = pd.read_csv(INPUTS["p2"])
    p1 = standardize_keys(p1, "Productivity P1")
    p2 = standardize_keys(p2, "Productivity P2")

    for c in ["productivity_p1_score", "gdp_per_person_employed"]:
        p1[c] = numeric_column(
            p1, c, "Productivity P1",
            required=(c == "productivity_p1_score"),
        )

    for c in ["productivity_p2_score", "tfp_growth"]:
        p2[c] = numeric_column(
            p2, c, "Productivity P2",
            required=(c == "productivity_p2_score"),
        )

    tables["productivity"] = p1[
        ["country_code", "year", "productivity_p1_score",
         "gdp_per_person_employed"]
    ].merge(
        p2[
            ["country_code", "year", "productivity_p2_score", "tfp_growth"]
        ],
        on=["country_code", "year"],
        how="outer",
        validate="one_to_one",
    )

    # Connectivity.
    c = pd.read_csv(INPUTS["connectivity"])
    c = standardize_keys(c, "Connectivity")

    connectivity_columns = {
        "connectivity_trade_score": "trade_openness",
        "connectivity_fdi_score": "fdi_inflows",
        "connectivity_internet_score": "internet_use",
    }

    for score_col, raw_col in connectivity_columns.items():
        c[score_col] = numeric_column(c, score_col, "Connectivity")
        c[raw_col] = numeric_column(c, raw_col, "Connectivity")

    tables["connectivity"] = c[
        ["country_code", "year"]
        + list(connectivity_columns.keys())
        + list(connectivity_columns.values())
    ].copy()

    # Resilience: support country or country_code.
    r = pd.read_csv(INPUTS["resilience"])
    r = standardize_keys(r, "Resilience")

    resilience_columns = {
        "R1_fx_reserves_score": "fx_reserves_months",
        "R2_debt_score": "government_debt_gdp",
        "R3_current_account_score": "current_account_gdp",
    }

    for score_col, raw_col in resilience_columns.items():
        r[score_col] = numeric_column(r, score_col, "Resilience")
        r[raw_col] = numeric_column(r, raw_col, "Resilience")

    if "resilience_score" not in r.columns:
        fail("Resilience: missing persisted resilience_score.")

    r["resilience_score"] = numeric_column(
        r, "resilience_score", "Resilience"
    )

    # The saved resilience_score is expected to be on 0-1 scale.
    # If the file only supplies a 0-100 version, fail rather than guess.
    if r["resilience_score"].dropna().gt(1.0).any():
        fail(
            "Resilience resilience_score exceeds 1.0. "
            "Check the input scale; do not silently rescale production data."
        )

    tables["resilience"] = r[
        ["country_code", "year", "resilience_score"]
        + list(resilience_columns.keys())
        + list(resilience_columns.values())
    ].copy()

    # Strategic autonomy.
    a = pd.read_csv(INPUTS["autonomy"])
    a = standardize_keys(a, "Strategic Autonomy")

    autonomy_columns = {
        "eci_score": "eci",
        "high_tech_exports_score": "high_tech_exports",
        "import_product_concentration_score": "import_product_concentration",
    }

    for score_col, raw_col in autonomy_columns.items():
        a[score_col] = numeric_column(a, score_col, "Strategic Autonomy")
        a[raw_col] = numeric_column(a, raw_col, "Strategic Autonomy")

    tables["autonomy"] = a[
        ["country_code", "year"]
        + list(autonomy_columns.keys())
        + list(autonomy_columns.values())
    ].copy()

    return tables


# ================================================================
# BUILD BASELINE AND ALTERNATIVE SCORES
# ================================================================

def build_score_table(tables):
    # Start from the full theoretical 5 x 8 panel.
    result = pd.MultiIndex.from_product(
        [list(COUNTRIES), YEARS],
        names=["country_code", "year"],
    ).to_frame(index=False)

    for table in tables.values():
        result = result.merge(
            table,
            on=["country_code", "year"],
            how="left",
            validate="one_to_one",
        )

    result["country"] = result["country_code"].map(COUNTRIES)

    # Production-based baseline indicator scores.
    # Growth only provides a persisted aggregate score.
    result["G_baseline"] = result["growth_score"]

    result["P_baseline"] = result[
        ["productivity_p1_score", "productivity_p2_score"]
    ].mean(axis=1, skipna=False)

    result["C_baseline"] = result[
        [
            "connectivity_trade_score",
            "connectivity_fdi_score",
            "connectivity_internet_score",
        ]
    ].mean(axis=1, skipna=False)

    result["R_baseline"] = result["resilience_score"]

    result["A_baseline"] = result[
        [
            "eci_score",
            "high_tech_exports_score",
            "import_product_concentration_score",
        ]
    ].mean(axis=1, skipna=False)

    # Raw-indicator normalization alternatives.
    # These alternatives are diagnostic, not production replacements.
    raw_groups = {
        "G": [
            ("real_gdp_growth", "positive"),
            ("gni_per_capita_growth", "positive"),
        ],
        "P": [
            ("gdp_per_person_employed", "positive"),
            ("tfp_growth", "positive"),
        ],
        "C": [
            ("trade_openness", "positive"),
            ("fdi_inflows", "positive"),
            ("internet_use", "positive"),
        ],
        "A": [
            ("eci", "positive"),
            ("high_tech_exports", "positive"),
            ("import_product_concentration", "negative"),
        ],
    }

    methods = ["minmax", "winsorized_minmax", "percentile"]

    for pillar, indicators in raw_groups.items():
        for method in methods:
            scores = []

            for raw_col, direction in indicators:
                scores.append(
                    normalize(
                        result[raw_col],
                        method,
                        direction,
                    )
                )

            result[f"{pillar}_{method}"] = pd.concat(
                scores, axis=1
            ).mean(axis=1, skipna=False)

    # Resilience R1 alternatives; R2/R3 retain stored baseline scores.
    for method in methods:
        r1 = normalize(
            result["fx_reserves_months"],
            method,
            "positive",
        )

        result[f"R_{method}"] = pd.concat(
            [
                r1,
                result["R2_debt_score"],
                result["R3_current_account_score"],
            ],
            axis=1,
        ).mean(axis=1, skipna=False)

    # Reference-zone alternatives affect only R2/R3.
    # Baseline uses persisted R2/R3 component scores.
    for label, low_q, high_q in [
        ("reference_p5_p95", 0.05, 0.95),
        ("reference_p20_p80", 0.20, 0.80),
    ]:
        debt = reference_quantiles(
            result["government_debt_gdp"], low_q, high_q
        )
        current_account = reference_quantiles(
            result["current_account_gdp"], low_q, high_q
        )

        result[f"R_{label}"] = pd.concat(
            [
                result["R1_fx_reserves_score"],
                debt,
                current_account,
            ],
            axis=1,
        ).mean(axis=1, skipna=False)

    return result


# ================================================================
# JESI FORMULA
# ================================================================

def calculate_jesi(frame, pillar_columns):
    pillars = frame[pillar_columns].copy()

    if pillars.lt(0).any().any() or pillars.gt(1).any().any():
        fail("Pillar scores outside [0, 1] detected.")

    safe = pillars.clip(lower=1e-12, upper=1.0)

    return 100.0 * (
        safe["G"].pow(WEIGHTS["G"])
        * safe["P"].pow(WEIGHTS["P"])
        * safe["C"].pow(WEIGHTS["C"])
        * safe["R"].pow(WEIGHTS["R"])
        * safe["A"].pow(WEIGHTS["A"])
    )


def build_specifications(scores):
    frames = {}

    for name in SPECIFICATIONS:
        df = scores[["country_code", "country", "year"]].copy()

        if name == "baseline":
            for pillar in ["G", "P", "C", "R", "A"]:
                df[pillar] = scores[f"{pillar}_baseline"]

        elif name in {"reference_p5_p95", "reference_p20_p80"}:
            for pillar in ["G", "P", "C", "A"]:
                df[pillar] = scores[f"{pillar}_baseline"]
            df["R"] = scores[f"R_{name}"]

        else:
            for pillar in ["G", "P", "C", "A"]:
                df[pillar] = scores[f"{pillar}_{name}"]
            df["R"] = scores[f"R_{name}"]

        df["JESI"] = calculate_jesi(
            df, ["G", "P", "C", "R", "A"]
        )
        df["specification"] = name
        frames[name] = df

    return frames


# ================================================================
# PRODUCTION RECONCILIATION
# ================================================================

def find_column(df, candidates):
    lower_map = {str(c).strip().lower(): c for c in df.columns}

    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    return None


def reconcile_production(baseline):
    require_file(PRODUCTION_FILE)

    production = pd.read_csv(PRODUCTION_FILE)
    production = standardize_keys(production, "Production JESI")

    jesi_column = find_column(
        production,
        [
            "JESI", "jesi_score", "jesi_100",
            "final_jesi", "jesi_final", "jesi_value",
        ],
    )

    if jesi_column is None:
        fail(
            "Production output has no recognized JESI score column. "
            f"Available columns: {list(production.columns)}"
        )

    production["production_JESI"] = pd.to_numeric(
        production[jesi_column], errors="coerce"
    )

    merged = baseline.merge(
        production[
            ["country_code", "year", "production_JESI"]
        ],
        on=["country_code", "year"],
        how="left",
        validate="one_to_one",
    )

    merged["absolute_difference"] = (
        merged["JESI"] - merged["production_JESI"]
    ).abs()

    merged["within_tolerance"] = (
        merged["absolute_difference"] <= TOLERANCE
    )

    rows = merged[
        [
            "country_code",
            "country",
            "year",
            "JESI",
            "production_JESI",
            "absolute_difference",
            "within_tolerance",
        ]
    ].copy()

    comparable = rows.dropna(
        subset=["JESI", "production_JESI"]
    )

    n_compared = len(comparable)
    n_match = int(comparable["within_tolerance"].sum())

    metrics = {
        "production_jesi_column": jesi_column,
        "comparison_n": n_compared,
        "matches_within_tolerance": n_match,
        "mismatches": n_compared - n_match,
        "mean_absolute_difference": (
            comparable["absolute_difference"].mean()
            if n_compared else np.nan
        ),
        "max_absolute_difference": (
            comparable["absolute_difference"].max()
            if n_compared else np.nan
        ),
        "reconciliation_passed": (
            n_compared > 0 and n_match == n_compared
        ),
    }

    return rows, metrics


# ================================================================
# ANALYSIS TABLES
# ================================================================

def validate_panel(frame, name):
    if len(frame) != EXPECTED_PANEL:
        fail(
            f"{name}: expected {EXPECTED_PANEL} panel rows, found {len(frame)}."
        )

    if frame.duplicated(["country_code", "year"]).any():
        fail(f"{name}: duplicate country-year observations.")

    complete = frame[["G", "P", "C", "R", "A", "JESI"]].notna().all(axis=1)
    n = int(complete.sum())

    if n != EXPECTED_COMPLETE:
        warnings.warn(
            f"{name}: expected {EXPECTED_COMPLETE} complete cases; found {n}. "
            "Inspect missingness before interpreting results.",
            RuntimeWarning,
        )

    return frame.loc[complete].copy()


def country_summary(all_results):
    out = (
        all_results.groupby(
            ["specification", "country_code", "country"],
            as_index=False,
        )
        .agg(
            mean_jesi=("JESI", "mean"),
            observations=("JESI", "count"),
        )
    )

    out["rank"] = out.groupby("specification")["mean_jesi"].rank(
        method="min", ascending=False
    )

    return out.sort_values(
        ["specification", "rank", "country_code"]
    ).reset_index(drop=True)


def calculate_rank_results(baseline, alternatives):
    rows = []

    for name, alternative in alternatives.items():
        merged = baseline[
            ["country_code", "year", "JESI"]
        ].merge(
            alternative[["country_code", "year", "JESI"]],
            on=["country_code", "year"],
            suffixes=("_baseline", "_alternative"),
            validate="one_to_one",
        )

        if len(merged) >= 2:
            rho = spearmanr(
                merged["JESI_baseline"],
                merged["JESI_alternative"],
            ).statistic
        else:
            rho = np.nan

        country = merged.groupby("country_code").agg(
            baseline=("JESI_baseline", "mean"),
            alternative=("JESI_alternative", "mean"),
        ).dropna()

        country_rho = (
            spearmanr(country["baseline"], country["alternative"]).statistic
            if len(country) >= 2 else np.nan
        )

        rows.extend([
            {
                "specification": name,
                "analysis_level": "country_year",
                "pairwise_n": len(merged),
                "spearman_rho": rho,
            },
            {
                "specification": name,
                "analysis_level": "country_mean",
                "pairwise_n": len(country),
                "spearman_rho": country_rho,
            },
        ])

    return pd.DataFrame(rows)


def sensitivity_summary(baseline, alternatives):
    rows = []

    for name, alternative in alternatives.items():
        merged = baseline[
            ["country_code", "year", "JESI"]
        ].merge(
            alternative[["country_code", "year", "JESI"]],
            on=["country_code", "year"],
            suffixes=("_baseline", "_alternative"),
            validate="one_to_one",
        )

        delta = (
            merged["JESI_alternative"] - merged["JESI_baseline"]
        ).abs()

        base_country = merged.groupby("country_code")[
            "JESI_baseline"
        ].mean()

        alt_country = merged.groupby("country_code")[
            "JESI_alternative"
        ].mean()

        rank_base = base_country.rank(method="min", ascending=False)
        rank_alt = alt_country.rank(method="min", ascending=False)
        rank_change = (rank_alt - rank_base).abs()

        rows.append({
            "specification": name,
            "country_year_n": len(merged),
            "mean_absolute_jesi_difference": delta.mean(),
            "max_absolute_jesi_difference": delta.max(),
            "mean_absolute_country_mean_difference": (
                alt_country - base_country
            ).abs().mean(),
            "max_country_rank_change": rank_change.max(),
            "countries_with_rank_change": int((rank_change > 0).sum()),
            "country_rank_spearman": (
                spearmanr(base_country, alt_country).statistic
                if len(base_country) >= 2 else np.nan
            ),
        })

    return pd.DataFrame(rows)


def build_report(summary, rank, reconciliation_metrics, complete_counts):
    lines = [
        "# JESI Normalization Sensitivity Analysis",
        "",
        "## Scope",
        "",
        "- JESI Master Version 1.0.",
        "- Countries: Bangladesh, India, Indonesia, Malaysia and Vietnam.",
        "- Comparison period: 2016–2023.",
        f"- Theoretical country-year panel: {EXPECTED_PANEL}.",
        f"- Expected complete-case benchmark: {EXPECTED_COMPLETE}.",
        "- Production files are read-only inputs to this audit.",
        "- No production score, weight, or formula is modified.",
        "",
        "## Baseline interpretation",
        "",
        "The baseline uses persisted production scores where available. "
        "The Growth input contains an aggregate production score; therefore "
        "the audit cannot claim to independently recover separate persisted "
        "Growth indicator scores from that file.",
        "",
        "The audit compares its reconstructed baseline JESI with the stored "
        "production JESI. A successful formula calculation alone does not "
        "prove production reproduction.",
        "",
        "## Complete-case counts",
        "",
        "| Specification | Complete observations |",
        "|---|---:|",
    ]

    for name, count in complete_counts.items():
        lines.append(f"| {name} | {count} |")

    lines += [
        "",
        "## Production reconciliation",
        "",
        f"- Production score column: `{reconciliation_metrics['production_jesi_column']}`",
        f"- Comparable rows: {reconciliation_metrics['comparison_n']}",
        f"- Matches within tolerance: {reconciliation_metrics['matches_within_tolerance']}",
        f"- Mismatches: {reconciliation_metrics['mismatches']}",
        f"- Mean absolute difference: {reconciliation_metrics['mean_absolute_difference']}",
        f"- Maximum absolute difference: {reconciliation_metrics['max_absolute_difference']}",
        f"- Reconciliation passed: {reconciliation_metrics['reconciliation_passed']}",
        "",
        "A mismatch means the audit baseline does not reproduce the stored "
        "production result. It does not, by itself, establish that the "
        "production pipeline is incorrect.",
        "",
        "## Sensitivity summary",
        "",
        summary.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Rank correlations",
        "",
        rank.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Interpretation",
        "",
        "These are sensitivity diagnostics, not authorization to change the "
        "production methodology. The strategic weights and weighted geometric "
        "aggregation remain fixed. Alternative results must not be substituted "
        "for Master Version 1.0 production scores without a separately approved "
        "methodological decision.",
        "",
    ]

    return "\n".join(lines)


# ================================================================
# MAIN
# ================================================================

def main():
    print("=" * 72)
    print("JESI NORMALIZATION SENSITIVITY AUDIT — PHASE 3")
    print("=" * 72)

    tables = load_inputs()
    scores = build_score_table(tables)
    built = build_specifications(scores)

    complete_specs = {}
    complete_counts = {}

    for name, frame in built.items():
        complete = validate_panel(frame, name)
        complete_specs[name] = complete
        complete_counts[name] = len(complete)
        print(f"{name}: {len(complete)} complete cases")

    baseline = complete_specs["baseline"]
    alternatives = {
        name: frame
        for name, frame in complete_specs.items()
        if name != "baseline"
    }

    # Production reconciliation uses the audit baseline against the
    # persisted final production JESI. It does not overwrite production.
    reconciliation, reconciliation_metrics = reconcile_production(
        baseline
    )

    all_results = pd.concat(
        complete_specs.values(),
        ignore_index=True,
    ).sort_values(
        ["specification", "country_code", "year"]
    ).reset_index(drop=True)

    c_summary = country_summary(all_results)
    ranks = calculate_rank_results(baseline, alternatives)
    summary = sensitivity_summary(baseline, alternatives)

    # Verify the declared geometric formula independently.
    for name, frame in complete_specs.items():
        recalculated = calculate_jesi(
            frame, ["G", "P", "C", "R", "A"]
        )
        difference = (recalculated - frame["JESI"]).abs().max()

        if pd.notna(difference) and difference > 1e-10:
            fail(
                f"{name}: geometric JESI formula check failed; "
                f"maximum difference={difference}"
            )

    OUT.mkdir(parents=True, exist_ok=True)

    all_results.to_csv(OUTPUTS["country_year"], index=False)
    c_summary.to_csv(OUTPUTS["country_summary"], index=False)
    ranks.to_csv(OUTPUTS["rank"], index=False)
    summary.to_csv(OUTPUTS["summary"], index=False)
    reconciliation.to_csv(OUTPUTS["reconciliation"], index=False)

    report = build_report(
        summary,
        ranks,
        reconciliation_metrics,
        complete_counts,
    )
    OUTPUTS["report"].write_text(report, encoding="utf-8")

    print("\nProduction reconciliation:")
    for key, value in reconciliation_metrics.items():
        print(f"  {key}: {value}")

    print("\nSensitivity summary:")
    print(summary.to_string(index=False))

    print("\nOutputs:")
    for path in OUTPUTS.values():
        print(f"  {path}")

    print("\nAudit computation completed.")
    if reconciliation_metrics["reconciliation_passed"]:
        print("Production reconciliation: PASSED within tolerance.")
    else:
        print(
            "Production reconciliation: NOT PASSED. "
            "Review the reconciliation CSV before interpreting the audit."
        )

    print("=" * 72)


if __name__ == "__main__":
    main()
