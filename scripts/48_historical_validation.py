"""
JAS Unified Economic Strength Index (JESI)
Script 48 — Historical Validation

Purpose
-------
Research-validation layer for historical validation of JESI.

This script:
1. Reconstructs the production JESI series from the existing pillar scores.
2. Uses the production weights and weighted geometric aggregation.
3. Restricts the historical validation sample to the complete-case panel.
4. Tests historical event windows.
5. Decomposes JESI changes into pillar contributions.
6. Compares JESI with independent World Bank outcomes:
   - Unemployment, total (% of total labor force)
   - Inflation, consumer prices (annual %)
7. Calculates both level and first-difference Spearman correlations.
8. Produces reproducible research-validation outputs.

Methodological safeguards
-------------------------
- No imputation.
- No interpolation.
- No fabricated observations.
- No automatic removal of indicators.
- No reweighting.
- No production-methodology change.
- No production JESI overwrite.
- Complete-case observations only.
- Historical validation is diagnostic/research-validation only.

Production aggregation
-----------------------
JESI = 100 × G^0.20 × P^0.25 × C^0.20 × R^0.20 × A^0.15

Historical period
-----------------
2016–2023

Countries
---------
Bangladesh (BGD)
India (IND)
Indonesia (IDN)
Malaysia (MYS)
Vietnam (VNM)

Event windows
------------
2019 → 2020
2020 → 2021
2021 → 2022
2022 → 2023
"""

from pathlib import Path
import time

import numpy as np
import pandas as pd
import requests
from scipy.stats import spearmanr


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

RESULTS_DIR = BASE_DIR / "data" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2016
END_YEAR = 2023

COUNTRY_MAP = {
    "Bangladesh": "BGD",
    "India": "IND",
    "Indonesia": "IDN",
    "Malaysia": "MYS",
    "Vietnam": "VNM",
    "Viet Nam": "VNM",
}

COUNTRIES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
    "VNM": "Vietnam",
}

COUNTRY_CODES = list(COUNTRIES.keys())

# Production JESI weights — DO NOT CHANGE
JESI_WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}

PILLAR_FILES = {
    "G": BASE_DIR / "data" / "processed" / "growth_pillar_scores_2015_2024.csv",
    "P": BASE_DIR / "data" / "processed" / "productivity_pillar_scores_2016_2023.csv",
    "C": BASE_DIR / "data" / "processed" / "connectivity_indicator_scores_2015_2024.csv",
    "R": BASE_DIR / "data" / "processed" / "resilience_pillar_scores_2015_2024.csv",
    "A": BASE_DIR / "data" / "processed" / "autonomy_indicator_scores_2015_2024.csv",
}

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

EXTERNAL_INDICATORS = {
    "unemployment": {
        "code": "SL.UEM.TOTL.ZS",
        "label": "Unemployment, total (% of total labor force)",
    },
    "inflation": {
        "code": "FP.CPI.TOTL.ZG",
        "label": "Inflation, consumer prices (annual %)",
    },
}

EVENT_WINDOWS = [
    (2019, 2020),
    (2020, 2021),
    (2021, 2022),
    (2022, 2023),
]

EXPECTED_THEORETICAL_ROWS = 5 * 8
EXPECTED_COMPLETE_CASE_ROWS = 34

# Numerical validation tolerance
CALC_TOLERANCE = 1e-10

# World Bank request settings
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"

WORLD_BANK_MAX_RETRIES = 4
WORLD_BANK_CONNECT_TIMEOUT = 20
WORLD_BANK_READ_TIMEOUT = 90
WORLD_BANK_BACKOFF_SECONDS = 5
WORLD_BANK_COUNTRY_PAUSE_SECONDS = 1

WORLD_BANK_HEADERS = {
    "User-Agent": (
        "JAS-JESI-Historical-Validation/1.0 "
        "(research-validation; reproducible-analysis)"
    )
}


# ============================================================
# OUTPUT PATHS
# ============================================================

OUTPUT_COUNTRY_YEAR = (
    RESULTS_DIR / "jesi_historical_validation_country_year.csv"
)

OUTPUT_EVENT_WINDOWS = (
    RESULTS_DIR / "jesi_historical_validation_event_windows.csv"
)

OUTPUT_PILLAR_CONTRIBUTIONS = (
    RESULTS_DIR / "jesi_historical_validation_pillar_contributions.csv"
)

OUTPUT_CORRELATIONS = (
    RESULTS_DIR / "jesi_historical_validation_correlations.csv"
)

OUTPUT_SUMMARY = (
    RESULTS_DIR / "jesi_historical_validation_summary.csv"
)

OUTPUT_REPORT = (
    RESULTS_DIR / "jesi_historical_validation_report.md"
)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def standardize_country(value):
    """Convert country names/codes to ISO-like three-letter codes."""
    if pd.isna(value):
        return np.nan

    text = str(value).strip()

    if text in COUNTRY_CODES:
        return text

    if text in COUNTRY_MAP:
        return COUNTRY_MAP[text]

    normalized = text.lower()

    for name, code in COUNTRY_MAP.items():
        if normalized == name.lower():
            return code

    return np.nan


def validate_weights():
    """Validate that production JESI weights sum to one."""
    total = sum(JESI_WEIGHTS.values())

    if not np.isclose(total, 1.0, atol=CALC_TOLERANCE):
        raise ValueError(
            f"JESI weights must sum to 1.0; received {total:.15f}"
        )

    print("Production weights validated.")


def identify_country_column(df):
    """Find country identifier column."""
    candidates = [
        "country_code",
        "country",
        "Country",
        "COUNTRY",
        "economy",
        "Economy",
    ]

    for column in candidates:
        if column in df.columns:
            return column

    raise ValueError(
        "No supported country identifier column found. "
        f"Available columns: {list(df.columns)}"
    )


def identify_year_column(df):
    """Find year column."""
    candidates = [
        "year",
        "Year",
        "YEAR",
        "date",
    ]

    for column in candidates:
        if column in df.columns:
            return column

    raise ValueError(
        "No supported year column found. "
        f"Available columns: {list(df.columns)}"
    )


def load_pillar(pillar_name, path, score_columns):
    """Load and construct pillar-level scores."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required pillar file not found: {path}"
        )

    df = pd.read_csv(path)

    country_column = identify_country_column(df)
    year_column = identify_year_column(df)

    missing_columns = [
        column
        for column in score_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{pillar_name} pillar missing required score columns: "
            f"{missing_columns}"
        )

    result = pd.DataFrame()

    result["country_code"] = df[country_column].map(
        standardize_country
    )

    result["year"] = pd.to_numeric(
        df[year_column],
        errors="coerce",
    )

    # Indicator-level mean without skipna:
    # if any required indicator is missing, the pillar score is missing.
    result[f"{pillar_name}_score"] = df[score_columns].mean(
        axis=1,
        skipna=False,
    )

    result = result[
        result["country_code"].isin(COUNTRY_CODES)
    ].copy()

    result = result[
        result["year"].between(START_YEAR, END_YEAR)
    ].copy()

    result["year"] = result["year"].astype(int)

    result = result[
        ["country_code", "year", f"{pillar_name}_score"]
    ]

    # Prevent accidental duplicate country-year records.
    duplicates = result.duplicated(
        subset=["country_code", "year"],
        keep=False,
    )

    if duplicates.any():
        duplicate_rows = result.loc[duplicates].sort_values(
            ["country_code", "year"]
        )

        raise ValueError(
            f"{pillar_name} pillar contains duplicate "
            "country-year observations:\n"
            f"{duplicate_rows.to_string(index=False)}"
        )

    return result


# ============================================================
# BUILD HISTORICAL PILLAR PANEL
# ============================================================

def build_historical_panel():
    """Merge all pillar scores into the historical validation panel."""

    panel = None

    for pillar_name in ["G", "P", "C", "R", "A"]:
        pillar_df = load_pillar(
            pillar_name,
            PILLAR_FILES[pillar_name],
            PILLAR_SCORE_COLUMNS[pillar_name],
        )

        if panel is None:
            panel = pillar_df
        else:
            panel = panel.merge(
                pillar_df,
                on=["country_code", "year"],
                how="outer",
                validate="one_to_one",
            )

    theoretical_rows = len(panel)

    print(
        "Historical theoretical panel rows: "
        f"{theoretical_rows}"
    )

    if theoretical_rows != EXPECTED_THEORETICAL_ROWS:
        raise ValueError(
            "Unexpected theoretical historical panel size: "
            f"{theoretical_rows}. "
            f"Expected {EXPECTED_THEORETICAL_ROWS}."
        )

    panel = panel.sort_values(
        ["country_code", "year"]
    ).reset_index(drop=True)

    pillar_columns = [
        "G_score",
        "P_score",
        "C_score",
        "R_score",
        "A_score",
    ]

    # Complete-case rule:
    # no imputation, interpolation, or fabricated observations.
    complete_case = panel[pillar_columns].notna().all(axis=1)

    complete_panel = panel.loc[complete_case].copy()

    complete_rows = len(complete_panel)

    print(
        "Historical complete-case rows: "
        f"{complete_rows}"
    )

    if complete_rows != EXPECTED_COMPLETE_CASE_ROWS:
        raise ValueError(
            "Unexpected historical complete-case size: "
            f"{complete_rows}. "
            f"Expected {EXPECTED_COMPLETE_CASE_ROWS}."
        )

    return panel, complete_panel


# ============================================================
# JESI CONSTRUCTION
# ============================================================

def calculate_jesi(row):
    """
    Calculate production JESI using weighted geometric aggregation.

    JESI = 100 × G^0.20 × P^0.25 × C^0.20 × R^0.20 × A^0.15
    """

    pillar_values = {
        "G": row["G_score"],
        "P": row["P_score"],
        "C": row["C_score"],
        "R": row["R_score"],
        "A": row["A_score"],
    }

    for pillar, value in pillar_values.items():
        if pd.isna(value):
            return np.nan

        if value <= 0:
            raise ValueError(
                f"{pillar} score must be > 0 for geometric aggregation. "
                f"Received {value}."
            )

        if value > 1:
            raise ValueError(
                f"{pillar} score must be <= 1. "
                f"Received {value}."
            )

    log_index = 0.0

    for pillar, weight in JESI_WEIGHTS.items():
        log_index += weight * np.log(
            pillar_values[pillar]
        )

    return 100.0 * np.exp(log_index)


def construct_jesi(panel):
    """Construct historical JESI series."""
    result = panel.copy()

    result["JESI"] = result.apply(
        calculate_jesi,
        axis=1,
    )

    if result["JESI"].isna().any():
        raise ValueError(
            "Historical JESI contains unexpected missing values."
        )

    if not np.isfinite(result["JESI"]).all():
        raise ValueError(
            "Historical JESI contains non-finite values."
        )

    print("Historical JESI series constructed.")

    return result


# ============================================================
# PILLAR CONTRIBUTION DECOMPOSITION
# ============================================================

def construct_pillar_contributions(panel):
    """
    Decompose change in log(JESI) into weighted pillar contributions.

    Δln(JESI) = Σ weight_i × Δln(Pillar_i)
    """

    rows = []

    for country_code, group in panel.groupby(
        "country_code",
        sort=True,
    ):
        group = group.sort_values("year").reset_index(drop=True)

        for i in range(1, len(group)):
            previous = group.iloc[i - 1]
            current = group.iloc[i]

            previous_jesi = previous["JESI"]
            current_jesi = current["JESI"]

            delta_log_jesi = np.log(
                current_jesi / previous_jesi
            )

            contribution_values = {}

            contribution_sum = 0.0

            for pillar, weight in JESI_WEIGHTS.items():
                previous_value = previous[
                    f"{pillar}_score"
                ]

                current_value = current[
                    f"{pillar}_score"
                ]

                delta_log_pillar = np.log(
                    current_value / previous_value
                )

                contribution = (
                    weight * delta_log_pillar
                )

                contribution_values[
                    f"{pillar}_contribution"
                ] = contribution

                contribution_sum += contribution

            residual = (
                delta_log_jesi - contribution_sum
            )

            if abs(residual) > CALC_TOLERANCE:
                raise ValueError(
                    "Pillar contribution decomposition failed "
                    f"for {country_code}, "
                    f"{int(previous['year'])}->{int(current['year'])}. "
                    f"Residual={residual:.15e}"
                )

            rows.append(
                {
                    "country_code": country_code,
                    "country": COUNTRIES[country_code],
                    "from_year": int(previous["year"]),
                    "to_year": int(current["year"]),
                    "JESI_previous": previous_jesi,
                    "JESI_current": current_jesi,
                    "delta_log_JESI": delta_log_jesi,
                    **contribution_values,
                    "contribution_sum": contribution_sum,
                    "decomposition_residual": residual,
                }
            )

    result = pd.DataFrame(rows)

    print("Pillar contribution decomposition: PASSED")

    return result


# ============================================================
# EVENT-WINDOW ANALYSIS
# ============================================================

def construct_event_windows(panel):
    """Construct specified historical event-window comparisons."""

    rows = []

    for from_year, to_year in EVENT_WINDOWS:
        for country_code in COUNTRY_CODES:
            previous = panel[
                (
                    panel["country_code"]
                    == country_code
                )
                & (
                    panel["year"]
                    == from_year
                )
            ]

            current = panel[
                (
                    panel["country_code"]
                    == country_code
                )
                & (
                    panel["year"]
                    == to_year
                )
            ]

            if previous.empty or current.empty:
                continue

            previous = previous.iloc[0]
            current = current.iloc[0]

            if (
                previous[
                    [
                        "G_score",
                        "P_score",
                        "C_score",
                        "R_score",
                        "A_score",
                    ]
                ].isna().any()
                or
                current[
                    [
                        "G_score",
                        "P_score",
                        "C_score",
                        "R_score",
                        "A_score",
                    ]
                ].isna().any()
            ):
                continue

            row = {
                "country_code": country_code,
                "country": COUNTRIES[country_code],
                "from_year": from_year,
                "to_year": to_year,
                "JESI_previous": previous["JESI"],
                "JESI_current": current["JESI"],
                "JESI_change": (
                    current["JESI"]
                    - previous["JESI"]
                ),
                "JESI_percent_change": (
                    (
                        current["JESI"]
                        / previous["JESI"]
                    )
                    - 1.0
                )
                * 100.0,
            }

            for pillar in ["G", "P", "C", "R", "A"]:
                previous_value = previous[
                    f"{pillar}_score"
                ]

                current_value = current[
                    f"{pillar}_score"
                ]

                row[f"{pillar}_change"] = (
                    current_value
                    - previous_value
                )

                row[f"{pillar}_percent_change"] = (
                    (
                        current_value
                        / previous_value
                    )
                    - 1.0
                ) * 100.0

            rows.append(row)

    result = pd.DataFrame(rows)

    print(
        "Historical event-window analysis constructed."
    )

    return result


# ============================================================
# ROBUST WORLD BANK API FETCH
# ============================================================

def fetch_world_bank_json(url, params):
    """
    Fetch World Bank JSON with retry handling.

    This function handles:
    - connection timeouts
    - read timeouts
    - connection errors
    - transient HTTP errors
    - malformed/invalid JSON responses
    """

    last_error = None

    for attempt in range(
        1,
        WORLD_BANK_MAX_RETRIES + 1,
    ):
        try:
            print(
                f"World Bank request attempt "
                f"{attempt}/{WORLD_BANK_MAX_RETRIES}: "
                f"{url}"
            )

            response = requests.get(
                url,
                params=params,
                headers=WORLD_BANK_HEADERS,
                timeout=(
                    WORLD_BANK_CONNECT_TIMEOUT,
                    WORLD_BANK_READ_TIMEOUT,
                ),
            )

            response.raise_for_status()

            payload = response.json()

            if not isinstance(payload, list):
                raise ValueError(
                    "World Bank response is not a JSON list."
                )

            return payload

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            ValueError,
        ) as exc:

            last_error = exc

            print(
                "World Bank request failed: "
                f"{type(exc).__name__}: {exc}"
            )

            if attempt < WORLD_BANK_MAX_RETRIES:
                delay = min(
                    WORLD_BANK_BACKOFF_SECONDS
                    * (2 ** (attempt - 1)),
                    30,
                )

                print(
                    f"Retrying after {delay} seconds..."
                )

                time.sleep(delay)

    raise RuntimeError(
        "World Bank API request failed after "
        f"{WORLD_BANK_MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )


def fetch_world_bank_indicator(
    indicator_code,
    indicator_label,
):
    """
    Fetch one World Bank indicator country-by-country.

    Country-by-country requests are deliberately used instead
    of one large multi-country request to reduce API timeout risk.
    """

    rows = []

    for country_code in COUNTRY_CODES:

        print(
            f"Fetching World Bank indicator "
            f"{indicator_code} for "
            f"{country_code} "
            f"({indicator_label})..."
        )

        url = (
            f"{WORLD_BANK_BASE_URL}/country/"
            f"{country_code}/indicator/"
            f"{indicator_code}"
        )

        params = {
            "format": "json",
            "date": f"{START_YEAR}:{END_YEAR}",
            "per_page": 100,
        }

        payload = fetch_world_bank_json(
            url,
            params,
        )

        if len(payload) < 2:
            raise RuntimeError(
                "World Bank response does not contain "
                f"data for {country_code}, "
                f"indicator {indicator_code}."
            )

        records = payload[1]

        if records is None:
            raise RuntimeError(
                "World Bank returned no records for "
                f"{country_code}, "
                f"indicator {indicator_code}."
            )

        for record in records:
            year = pd.to_numeric(
                record.get("date"),
                errors="coerce",
            )

            value = record.get("value")

            if pd.isna(year):
                continue

            year = int(year)

            if (
                year < START_YEAR
                or year > END_YEAR
            ):
                continue

            rows.append(
                {
                    "country_code": country_code,
                    "year": year,
                    "value": (
                        pd.to_numeric(
                            value,
                            errors="coerce",
                        )
                    ),
                }
            )

        # Small pause between countries to reduce
        # rate-limit / transient connection risk.
        time.sleep(
            WORLD_BANK_COUNTRY_PAUSE_SECONDS
        )

    result = pd.DataFrame(rows)

    if result.empty:
        raise RuntimeError(
            "World Bank returned no usable observations "
            f"for indicator {indicator_code}."
        )

    result = result.drop_duplicates(
        subset=["country_code", "year"],
        keep="first",
    )

    return result


def fetch_external_outcomes():
    """Fetch all independent World Bank validation outcomes."""

    print(
        "Fetching independent World Bank "
        "external outcomes..."
    )

    result = None

    for outcome_name, metadata in EXTERNAL_INDICATORS.items():

        indicator_df = fetch_world_bank_indicator(
            metadata["code"],
            metadata["label"],
        )

        indicator_df = indicator_df.rename(
            columns={
                "value": outcome_name,
            }
        )

        if result is None:
            result = indicator_df
        else:
            result = result.merge(
                indicator_df,
                on=["country_code", "year"],
                how="outer",
                validate="one_to_one",
            )

    return result


# ============================================================
# CORRELATION ANALYSIS
# ============================================================

def safe_spearman(x, y):
    """Calculate Spearman correlation safely."""

    data = pd.DataFrame(
        {
            "x": x,
            "y": y,
        }
    ).dropna()

    n = len(data)

    if n < 3:
        return np.nan, n

    rho, _ = spearmanr(
        data["x"],
        data["y"],
    )

    return float(rho), n


def construct_correlations(
    historical_panel,
    external_outcomes,
):
    """
    Calculate:
    - country-year level Spearman correlations
    - country-year first-difference Spearman correlations
    - country-mean level Spearman correlations
    """

    merged = historical_panel.merge(
        external_outcomes,
        on=["country_code", "year"],
        how="left",
        validate="one_to_one",
    )

    rows = []

    outcomes = [
        "unemployment",
        "inflation",
    ]

    # --------------------------------------------------------
    # Country-year level correlations
    # --------------------------------------------------------

    for outcome in outcomes:

        rho, n = safe_spearman(
            merged["JESI"],
            merged[outcome],
        )

        rows.append(
            {
                "analysis_type": "country_year_level",
                "outcome": outcome,
                "correlation": rho,
                "n": n,
            }
        )

    # --------------------------------------------------------
    # First-difference correlations
    # --------------------------------------------------------

    diff = merged.sort_values(
        ["country_code", "year"]
    ).copy()

    diff["JESI_diff"] = diff.groupby(
        "country_code"
    )["JESI"].diff()

    for outcome in outcomes:
        diff[f"{outcome}_diff"] = diff.groupby(
            "country_code"
        )[outcome].diff()

        rho, n = safe_spearman(
            diff["JESI_diff"],
            diff[f"{outcome}_diff"],
        )

        rows.append(
            {
                "analysis_type": "country_year_first_difference",
                "outcome": outcome,
                "correlation": rho,
                "n": n,
            }
        )

    # --------------------------------------------------------
    # Country-mean level correlations
    # --------------------------------------------------------

    country_means = (
        merged.groupby(
            "country_code",
            as_index=False,
        )[
            [
                "JESI",
                "unemployment",
                "inflation",
            ]
        ]
        .mean(
            numeric_only=True
        )
    )

    for outcome in outcomes:

        rho, n = safe_spearman(
            country_means["JESI"],
            country_means[outcome],
        )

        rows.append(
            {
                "analysis_type": "country_mean_level",
                "outcome": outcome,
                "correlation": rho,
                "n": n,
            }
        )

    return pd.DataFrame(rows), merged


# ============================================================
# SUMMARY
# ============================================================

def construct_summary(
    theoretical_panel,
    complete_panel,
    event_windows,
    correlations,
):
    """Construct concise research-validation summary."""

    summary_rows = [
        {
            "metric": "theoretical_panel_rows",
            "value": len(theoretical_panel),
        },
        {
            "metric": "complete_case_rows",
            "value": len(complete_panel),
        },
        {
            "metric": "countries",
            "value": len(COUNTRY_CODES),
        },
        {
            "metric": "historical_start_year",
            "value": START_YEAR,
        },
        {
            "metric": "historical_end_year",
            "value": END_YEAR,
        },
        {
            "metric": "event_window_count",
            "value": len(event_windows),
        },
        {
            "metric": "jesi_aggregation",
            "value": "weighted_geometric",
        },
        {
            "metric": "missing_data_treatment",
            "value": "complete_case_only",
        },
        {
            "metric": "imputation_used",
            "value": False,
        },
        {
            "metric": "interpolation_used",
            "value": False,
        },
        {
            "metric": "fabricated_observations",
            "value": False,
        },
        {
            "metric": "production_jesi_modified",
            "value": False,
        },
    ]

    # Add selected correlations to summary.
    for _, row in correlations.iterrows():
        key = (
            f"{row['analysis_type']}_"
            f"{row['outcome']}_spearman"
        )

        summary_rows.append(
            {
                "metric": key,
                "value": row["correlation"],
            }
        )

        summary_rows.append(
            {
                "metric": (
                    f"{row['analysis_type']}_"
                    f"{row['outcome']}_n"
                ),
                "value": row["n"],
            }
        )

    return pd.DataFrame(summary_rows)


# ============================================================
# REPORT
# ============================================================

def write_report(
    theoretical_panel,
    complete_panel,
    event_windows,
    pillar_contributions,
    correlations,
):
    """Write the historical validation methodology report."""

    lines = []

    lines.append(
        "# JESI Historical Validation Report"
    )
    lines.append("")

    lines.append(
        "## 1. Purpose"
    )
    lines.append("")

    lines.append(
        "This report documents the historical validation layer "
        "for the JAS Unified Economic Strength Index (JESI). "
        "The analysis evaluates the behavior of the existing "
        "production JESI over 2016–2023 and compares the index "
        "with independent World Bank economic outcomes."
    )
    lines.append("")

    lines.append(
        "## 2. Production methodology preserved"
    )
    lines.append("")

    lines.append(
        "The production JESI aggregation was not modified."
    )
    lines.append("")

    lines.append(
        "Production aggregation:"
    )
    lines.append("")
    lines.append(
        "JESI = 100 × G^0.20 × P^0.25 × C^0.20 × "
        "R^0.20 × A^0.15"
    )
    lines.append("")

    lines.append(
        "The historical validation script is a "
        "research-validation layer only."
    )
    lines.append("")

    lines.append(
        "## 3. Sample"
    )
    lines.append("")

    lines.append(
        f"- Countries: {', '.join(COUNTRIES.values())}"
    )
    lines.append(
        f"- Period: {START_YEAR}–{END_YEAR}"
    )
    lines.append(
        f"- Theoretical panel rows: "
        f"{len(theoretical_panel)}"
    )
    lines.append(
        f"- Complete-case rows: "
        f"{len(complete_panel)}"
    )
    lines.append("")

    lines.append(
        "Missing observations were not imputed, "
        "interpolated, fabricated, or mechanically replaced."
    )
    lines.append("")

    lines.append(
        "## 4. Event-window validation"
    )
    lines.append("")

    lines.append(
        "The following historical transitions were evaluated:"
    )
    lines.append("")

    for from_year, to_year in EVENT_WINDOWS:
        lines.append(
            f"- {from_year} → {to_year}"
        )

    lines.append("")

    lines.append(
        "## 5. Pillar contribution decomposition"
    )
    lines.append("")

    lines.append(
        "JESI changes were decomposed using the log form:"
    )
    lines.append("")

    lines.append(
        "Δln(JESI) = Σ weight_i × Δln(Pillar_i)"
    )
    lines.append("")

    lines.append(
        "The decomposition was independently checked "
        f"with tolerance {CALC_TOLERANCE:.0e}."
    )
    lines.append("")

    lines.append(
        "## 6. Independent external outcomes"
    )
    lines.append("")

    for metadata in EXTERNAL_INDICATORS.values():
        lines.append(
            f"- {metadata['label']} "
            f"({metadata['code']})"
        )

    lines.append("")

    lines.append(
        "## 7. Correlation framework"
    )
    lines.append("")

    lines.append(
        "Spearman correlations were calculated for:"
    )
    lines.append("")

    lines.append(
        "1. Country-year levels"
    )
    lines.append(
        "2. Country-year first differences"
    )
    lines.append(
        "3. Country-mean levels"
    )
    lines.append("")

    lines.append(
        "These correlations are descriptive validation "
        "evidence and should not be interpreted as proof "
        "of causality."
    )
    lines.append("")

    lines.append(
        "## 8. Methodological safeguards"
    )
    lines.append("")

    safeguards = [
        "No imputation.",
        "No interpolation.",
        "No fabricated observations.",
        "No automatic indicator removal.",
        "No reweighting.",
        "No production JESI overwrite.",
        "No automatic aggregation-method selection.",
        "Complete-case historical validation only.",
    ]

    for safeguard in safeguards:
        lines.append(f"- {safeguard}")

    lines.append("")

    lines.append(
        "## 9. Important interpretation limits"
    )
    lines.append("")

    lines.append(
        "Historical validation provides empirical evidence "
        "about whether JESI behavior is associated with "
        "selected external economic outcomes over the "
        "observed sample. It does not establish causal "
        "relationships."
    )
    lines.append("")

    lines.append(
        "The sample contains five countries and a limited "
        "historical period. Therefore, correlation estimates "
        "should be interpreted as validation evidence within "
        "this sample rather than universal estimates."
    )
    lines.append("")

    lines.append(
        "Country-mean correlations have an especially small "
        "cross-sectional sample size."
    )
    lines.append("")

    lines.append(
        "## 10. Research status"
    )
    lines.append("")

    lines.append(
        "This analysis is part of the empirical validation "
        "sequence of JESI. It does not by itself constitute "
        "the final methodological judgment."
    )
    lines.append("")

    lines.append(
        "The broader methodological sequence remains:"
    )
    lines.append("")

    lines.append(
        "JESI Concept → Pillar validity → Indicator validity → "
        "Redundancy/Correlation → Normalization sensitivity → "
        "Weight sensitivity → Aggregation sensitivity → "
        "Historical validation → Final methodological judgment"
    )
    lines.append("")

    lines.append(
        "## 11. Correlation results"
    )
    lines.append("")

    if correlations.empty:
        lines.append(
            "No correlation results were available."
        )
    else:
        lines.append(
            correlations.to_markdown(index=False)
        )

    lines.append("")

    lines.append(
        "## 12. Event-window count"
    )
    lines.append("")

    lines.append(
        f"Constructed event-window observations: "
        f"{len(event_windows)}"
    )
    lines.append("")

    lines.append(
        "## 13. Pillar contribution observations"
    )
    lines.append("")

    lines.append(
        f"Constructed contribution observations: "
        f"{len(pillar_contributions)}"
    )
    lines.append("")

    OUTPUT_REPORT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("JESI HISTORICAL VALIDATION")
    print("=" * 70)

    validate_weights()

    # --------------------------------------------------------
    # 1. Build historical pillar panel
    # --------------------------------------------------------

    theoretical_panel, complete_panel = (
        build_historical_panel()
    )

    # --------------------------------------------------------
    # 2. Construct production JESI
    # --------------------------------------------------------

    complete_panel = construct_jesi(
        complete_panel
    )

    # --------------------------------------------------------
    # 3. Pillar contribution decomposition
    # --------------------------------------------------------

    pillar_contributions = (
        construct_pillar_contributions(
            complete_panel
        )
    )

    # --------------------------------------------------------
    # 4. Historical event windows
    # --------------------------------------------------------

    event_windows = construct_event_windows(
        complete_panel
    )

    # --------------------------------------------------------
    # 5. Independent World Bank outcomes
    # --------------------------------------------------------

    external_outcomes = fetch_external_outcomes()

    # --------------------------------------------------------
    # 6. Correlations
    # --------------------------------------------------------

    correlations, merged_panel = (
        construct_correlations(
            complete_panel,
            external_outcomes,
        )
    )

    # --------------------------------------------------------
    # 7. Summary
    # --------------------------------------------------------

    summary = construct_summary(
        theoretical_panel,
        complete_panel,
        event_windows,
        correlations,
    )

    # --------------------------------------------------------
    # 8. Write country-year output
    # --------------------------------------------------------

    country_year_output = merged_panel.copy()

    country_year_output["country"] = (
        country_year_output["country_code"]
        .map(COUNTRIES)
    )

    country_year_output = country_year_output[
        [
            "country_code",
            "country",
            "year",
            "G_score",
            "P_score",
            "C_score",
            "R_score",
            "A_score",
            "JESI",
            "unemployment",
            "inflation",
        ]
    ].sort_values(
        ["country_code", "year"]
    )

    country_year_output.to_csv(
        OUTPUT_COUNTRY_YEAR,
        index=False,
    )

    # --------------------------------------------------------
    # 9. Write event-window output
    # --------------------------------------------------------

    event_windows.to_csv(
        OUTPUT_EVENT_WINDOWS,
        index=False,
    )

    # --------------------------------------------------------
    # 10. Write pillar contribution output
    # --------------------------------------------------------

    pillar_contributions.to_csv(
        OUTPUT_PILLAR_CONTRIBUTIONS,
        index=False,
    )

    # --------------------------------------------------------
    # 11. Write correlation output
    # --------------------------------------------------------

    correlations.to_csv(
        OUTPUT_CORRELATIONS,
        index=False,
    )

    # --------------------------------------------------------
    # 12. Write summary output
    # --------------------------------------------------------

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
    )

    # --------------------------------------------------------
    # 13. Write report
    # --------------------------------------------------------

    write_report(
        theoretical_panel,
        complete_panel,
        event_windows,
        pillar_contributions,
        correlations,
    )

    # --------------------------------------------------------
    # 14. Final checks
    # --------------------------------------------------------

    required_outputs = [
        OUTPUT_COUNTRY_YEAR,
        OUTPUT_EVENT_WINDOWS,
        OUTPUT_PILLAR_CONTRIBUTIONS,
        OUTPUT_CORRELATIONS,
        OUTPUT_SUMMARY,
        OUTPUT_REPORT,
    ]

    for output in required_outputs:
        if not output.exists():
            raise FileNotFoundError(
                f"Expected output was not created: {output}"
            )

    print("")
    print("=" * 70)
    print("JESI HISTORICAL VALIDATION COMPLETED")
    print("=" * 70)

    print(
        f"Country-year observations: "
        f"{len(country_year_output)}"
    )

    print(
        f"Event-window observations: "
        f"{len(event_windows)}"
    )

    print(
        f"Pillar contribution observations: "
        f"{len(pillar_contributions)}"
    )

    print("")
    print("Correlation summary:")
    print(
        correlations.to_string(index=False)
    )

    print("")
    print("Output files:")

    for output in required_outputs:
        print(f"- {output.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
