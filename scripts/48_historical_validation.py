"""
JAS Unified Economic Strength Index (JESI)
Historical Validation — Master Version 1.0

Research-validation layer only.

Purpose
-------
Evaluate whether the historical behavior of the production JESI
is consistent with:

1. observed year-to-year changes in the five JESI pillars;
2. pre-specified historical event windows;
3. independent external macroeconomic outcomes.

This script does NOT:
- modify production JESI results;
- modify production pillar weights;
- modify indicator normalization;
- modify pillar construction;
- impute missing observations;
- interpolate missing observations;
- fabricate observations;
- remove observations selectively;
- reweight pillars;
- automatically select a validation result;
- replace the production aggregation method.

Production aggregation
----------------------
JESI = 100 × G^0.20 × P^0.25 × C^0.20 × R^0.20 × A^0.15

Analytical sample
-----------------
Countries:
- Bangladesh
- India
- Indonesia
- Malaysia
- Vietnam

Historical analytical period:
- 2016-2023

The productivity pillar currently defines the common
historical intersection for this validation layer.

Historical event windows
------------------------
The event windows are pre-specified analytical windows.
They are descriptive validation windows, not causal identification.

- 2019 -> 2020
- 2020 -> 2021
- 2021 -> 2022
- 2022 -> 2023

Independent external outcomes
-----------------------------
World Bank World Development Indicators:

- Unemployment, total (% of total labor force)
  Indicator: SL.UEM.TOTL.ZS

- Inflation, consumer prices (annual %)
  Indicator: FP.CPI.TOTL.ZG

These external outcomes are NOT used in JESI construction.

Validation principle
--------------------
External outcome correlations are reported as evidence,
not as proof of causality.

No preferred direction, threshold, or automatic pass/fail rule
is imposed by this script.

Outputs
-------
data/results/jesi_historical_validation_country_year.csv
data/results/jesi_historical_validation_event_windows.csv
data/results/jesi_historical_validation_pillar_contributions.csv
data/results/jesi_historical_validation_correlations.csv
data/results/jesi_historical_validation_summary.csv
data/results/jesi_historical_validation_report.md
"""

from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.stats import spearmanr


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT / "data/results"

COUNTRY_YEAR_OUTPUT = (
    OUTPUT_DIR
    / "jesi_historical_validation_country_year.csv"
)

EVENT_OUTPUT = (
    OUTPUT_DIR
    / "jesi_historical_validation_event_windows.csv"
)

PILLAR_CONTRIBUTION_OUTPUT = (
    OUTPUT_DIR
    / "jesi_historical_validation_pillar_contributions.csv"
)

CORRELATION_OUTPUT = (
    OUTPUT_DIR
    / "jesi_historical_validation_correlations.csv"
)

SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "jesi_historical_validation_summary.csv"
)

REPORT_OUTPUT = (
    OUTPUT_DIR
    / "jesi_historical_validation_report.md"
)


# ---------------------------------------------------------------------
# ANALYTICAL BENCHMARK
# ---------------------------------------------------------------------

COUNTRIES = [
    "BGD",
    "IND",
    "IDN",
    "MYS",
    "VNM",
]

FINAL_YEARS = list(range(2016, 2024))


COUNTRY_NAMES = {
    "BGD": "Bangladesh",
    "IND": "India",
    "IDN": "Indonesia",
    "MYS": "Malaysia",
    "VNM": "Vietnam",
}


# ---------------------------------------------------------------------
# PRODUCTION JESI WEIGHTS
# ---------------------------------------------------------------------

WEIGHTS = {
    "G": 0.20,
    "P": 0.25,
    "C": 0.20,
    "R": 0.20,
    "A": 0.15,
}

PILLARS = [
    "G",
    "P",
    "C",
    "R",
    "A",
]

PILLAR_NAMES = {
    "G": "Growth",
    "P": "Productivity",
    "C": "Connectivity",
    "R": "Resilience",
    "A": "Strategic Autonomy",
}


# ---------------------------------------------------------------------
# PILLAR SOURCE FILES
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
# PILLAR SCORE COLUMNS
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
# INDEPENDENT EXTERNAL OUTCOMES
# ---------------------------------------------------------------------

EXTERNAL_INDICATORS = {
    "unemployment_rate": {
        "code": "SL.UEM.TOTL.ZS",
        "name": "Unemployment rate",
        "unit": "% of total labor force",
    },
    "inflation_rate": {
        "code": "FP.CPI.TOTL.ZG",
        "name": "Inflation, consumer prices",
        "unit": "annual %",
    },
}


# ---------------------------------------------------------------------
# PRE-SPECIFIED HISTORICAL WINDOWS
# ---------------------------------------------------------------------

EVENT_WINDOWS = [
    {
        "window": "2019_to_2020",
        "from_year": 2019,
        "to_year": 2020,
        "description": "Pre-shock to 2020 historical shock window",
    },
    {
        "window": "2020_to_2021",
        "from_year": 2020,
        "to_year": 2021,
        "description": "2020 shock to subsequent adjustment window",
    },
    {
        "window": "2021_to_2022",
        "from_year": 2021,
        "to_year": 2022,
        "description": "2021 to 2022 historical adjustment window",
    },
    {
        "window": "2022_to_2023",
        "from_year": 2022,
        "to_year": 2023,
        "description": "2022 to 2023 subsequent adjustment window",
    },
]


# ---------------------------------------------------------------------
# VALIDATION HELPERS
# ---------------------------------------------------------------------

def fail(message):
    """Raise a clear methodological validation error."""

    raise ValueError(message)


def validate_weights():
    """Validate the fixed production JESI weights."""

    if set(WEIGHTS) != set(PILLARS):
        fail(
            "JESI weights must contain exactly "
            f"{PILLARS}."
        )

    values = np.array(
        [WEIGHTS[pillar] for pillar in PILLARS],
        dtype=float,
    )

    if not np.isfinite(values).all():
        fail("Non-finite JESI weight detected.")

    if (values < 0).any():
        fail("Negative JESI weight detected.")

    if not np.isclose(
        values.sum(),
        1.0,
        atol=1e-12,
    ):
        fail(
            "JESI production weights do not sum to 1.0."
        )


# ---------------------------------------------------------------------
# COUNTRY STANDARDIZATION
# ---------------------------------------------------------------------

def standardize_country_code(df):
    """
    Standardize country identity without altering observations.
    """

    country_to_code = {
        "Bangladesh": "BGD",
        "India": "IND",
        "Indonesia": "IDN",
        "Malaysia": "MYS",
        "Vietnam": "VNM",
        "Viet Nam": "VNM",
    }

    if "country_code" not in df.columns:

        if "country" not in df.columns:
            fail(
                "Source does not contain country or country_code."
            )

        df["country_code"] = (
            df["country"].map(country_to_code)
        )

    else:

        df["country_code"] = (
            df["country_code"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        if "country" in df.columns:
            mapped = df["country"].map(
                country_to_code
            )

            unresolved = (
                mapped.notna()
                & (
                    df["country_code"]
                    != mapped
                )
            )

            if unresolved.any():
                fail(
                    "Country code and country name "
                    "identity conflict detected."
                )

    if df["country_code"].isna().any():
        unknown = (
            df.loc[
                df["country_code"].isna(),
                "country",
            ]
            .drop_duplicates()
            .tolist()
        )

        fail(
            f"Unable to map country identity: {unknown}"
        )

    unknown_codes = (
        set(df["country_code"].dropna())
        - set(COUNTRIES)
    )

    if unknown_codes:
        fail(
            "Unexpected country codes detected: "
            f"{sorted(unknown_codes)}"
        )

    df["country"] = (
        df["country_code"]
        .map(COUNTRY_NAMES)
    )

    return df


# ---------------------------------------------------------------------
# LOAD PILLAR SOURCE
# ---------------------------------------------------------------------

def load_pillar_source(pillar):
    """
    Load persisted pillar scores.

    No missing-value repair is performed.
    """

    relative_path = PILLAR_FILES[pillar]

    path = ROOT / relative_path

    if not path.exists():
        fail(
            f"Missing pillar source for {pillar}: "
            f"{relative_path}"
        )

    df = pd.read_csv(path)

    if df.empty:
        fail(
            f"Pillar source is empty: {relative_path}"
        )

    required = {
        "year",
        *PILLAR_SCORE_COLUMNS[pillar],
    }

    if "country" not in df.columns:
        required.add("country")

    missing = required - set(df.columns)

    if missing:
        fail(
            f"Pillar {pillar} missing columns: "
            f"{sorted(missing)}"
        )

    df = standardize_country_code(df)

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    if df["year"].isna().any():
        fail(
            f"Pillar {pillar}: invalid year detected."
        )

    df["year"] = df["year"].astype(int)

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
            .to_dict("records")
        )

        fail(
            f"Pillar {pillar}: duplicate country-year "
            f"observations: {duplicates}"
        )

    return df


# ---------------------------------------------------------------------
# BUILD PILLAR PANEL
# ---------------------------------------------------------------------

def build_pillar_panel():
    """
    Construct a common country-year panel from the five
    persisted pillar-score representations.

    A pillar score is present only when all of its component
    indicator scores are present.

    Missing observations remain missing.
    """

    panels = []

    for pillar in PILLARS:

        df = load_pillar_source(pillar)

        columns = PILLAR_SCORE_COLUMNS[pillar]

        df = df[
            [
                "country_code",
                "country",
                "year",
                *columns,
            ]
        ].copy()

        df = df[
            df["country_code"].isin(COUNTRIES)
        ]

        complete = (
            df[columns]
            .notna()
            .all(axis=1)
        )

        df[pillar] = (
            df[columns]
            .mean(
                axis=1,
                skipna=False,
            )
        )

        df.loc[
            ~complete,
            pillar,
        ] = np.nan

        panels.append(
            df[
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

    panel = panel[
        panel["country_code"].isin(COUNTRIES)
    ]

    panel = panel[
        panel["year"].isin(FINAL_YEARS)
    ]

    return panel.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)


# ---------------------------------------------------------------------
# COMPLETE-CASE VALIDATION
# ---------------------------------------------------------------------

def build_complete_case_panel(panel):
    """
    Preserve only naturally complete country-year observations.

    No imputation, interpolation, or fabricated observations.
    """

    theoretical_expected = (
        len(COUNTRIES)
        * len(FINAL_YEARS)
    )

    theoretical_identity = (
        panel[
            [
                "country_code",
                "year",
            ]
        ]
        .drop_duplicates()
    )

    if len(theoretical_identity) != theoretical_expected:
        fail(
            "Expected theoretical panel of "
            f"{theoretical_expected} country-year identities, "
            f"found {len(theoretical_identity)}."
        )

    complete_mask = (
        panel[PILLARS]
        .notna()
        .all(axis=1)
    )

    complete = panel.loc[
        complete_mask
    ].copy()

    if complete.empty:
        fail(
            "No complete country-year observations "
            "available for historical validation."
        )

    if complete[PILLARS].isna().any().any():
        fail(
            "Missing pillar scores remain in complete-case panel."
        )

    return complete.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)


# ---------------------------------------------------------------------
# PRODUCTION JESI
# ---------------------------------------------------------------------

def calculate_jesi(df):
    """
    Reproduce the production weighted-geometric JESI formula.
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
            "Pillar score outside [0, 1] detected."
        )

    if (
        values <= 0
    ).any():
        fail(
            "Zero pillar score detected. "
            "Log-based historical decomposition requires "
            "strictly positive pillar scores."
        )

    log_jesi = np.zeros(
        len(df),
        dtype=float,
    )

    for pillar in PILLARS:

        log_jesi += (
            WEIGHTS[pillar]
            * np.log(
                df[pillar].to_numpy(
                    dtype=float
                )
            )
        )

    return 100.0 * np.exp(log_jesi)


# ---------------------------------------------------------------------
# BUILD JESI HISTORICAL SERIES
# ---------------------------------------------------------------------

def build_jesi_series(panel):
    """
    Calculate production JESI for every naturally complete
    country-year observation.
    """

    result = panel[
        [
            "country_code",
            "country",
            "year",
            *PILLARS,
        ]
    ].copy()

    result["JESI"] = calculate_jesi(
        result
    )

    result = result.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)

    result["JESI_change"] = (
        result
        .groupby("country_code")["JESI"]
        .diff()
    )

    result["JESI_pct_change"] = (
        result
        .groupby("country_code")["JESI"]
        .pct_change()
        * 100.0
    )

    return result


# ---------------------------------------------------------------------
# PILLAR CONTRIBUTION DECOMPOSITION
# ---------------------------------------------------------------------

def build_pillar_contributions(jesi_series):
    """
    Decompose annual log-JESI changes into weighted pillar
    log-change contributions.

    Mathematical identity:

        Δln(JESI)
        =
        Σ weight_i × Δln(Pillar_i)

    The decomposition is descriptive and does not establish
    causality.
    """

    rows = []

    for country_code, group in (
        jesi_series
        .groupby("country_code")
    ):

        group = group.sort_values("year")

        for index in range(1, len(group)):

            previous = group.iloc[index - 1]
            current = group.iloc[index]

            if previous["year"] + 1 != current["year"]:
                continue

            row = {
                "country_code": country_code,
                "country": current["country"],
                "from_year": int(previous["year"]),
                "to_year": int(current["year"]),
                "JESI_previous": previous["JESI"],
                "JESI_current": current["JESI"],
                "JESI_change": (
                    current["JESI"]
                    - previous["JESI"]
                ),
                "log_JESI_change": (
                    np.log(current["JESI"])
                    - np.log(previous["JESI"])
                ),
            }

            contribution_sum = 0.0

            for pillar in PILLARS:

                previous_score = previous[pillar]
                current_score = current[pillar]

                contribution = (
                    WEIGHTS[pillar]
                    * (
                        np.log(current_score)
                        - np.log(previous_score)
                    )
                )

                row[
                    f"{pillar}_log_contribution"
                ] = contribution

                contribution_sum += contribution

            row[
                "decomposition_error"
            ] = (
                contribution_sum
                - row["log_JESI_change"]
            )

            rows.append(row)

    result = pd.DataFrame(rows)

    if result.empty:
        fail(
            "No annual pillar contribution observations "
            "could be constructed."
        )

    max_error = (
        result["decomposition_error"]
        .abs()
        .max()
    )

    if max_error > 1e-10:
        fail(
            "Pillar contribution decomposition failed. "
            f"Maximum error = {max_error}"
        )

    return result


# ---------------------------------------------------------------------
# HISTORICAL EVENT WINDOWS
# ---------------------------------------------------------------------

def build_event_windows(jesi_series):
    """
    Evaluate pre-specified year-to-year historical windows.

    These are descriptive historical comparisons only.
    No causal interpretation is imposed.
    """

    rows = []

    for event in EVENT_WINDOWS:

        from_year = event["from_year"]
        to_year = event["to_year"]

        for country_code in COUNTRIES:

            country_data = jesi_series[
                jesi_series["country_code"]
                == country_code
            ]

            previous = country_data[
                country_data["year"]
                == from_year
            ]

            current = country_data[
                country_data["year"]
                == to_year
            ]

            if previous.empty or current.empty:
                continue

            previous_row = previous.iloc[0]
            current_row = current.iloc[0]

            row = {
                "window": event["window"],
                "description": event["description"],
                "country_code": country_code,
                "country": COUNTRY_NAMES[country_code],
                "from_year": from_year,
                "to_year": to_year,
                "JESI_from": previous_row["JESI"],
                "JESI_to": current_row["JESI"],
                "JESI_change": (
                    current_row["JESI"]
                    - previous_row["JESI"]
                ),
                "JESI_pct_change": (
                    (
                        current_row["JESI"]
                        / previous_row["JESI"]
                    )
                    - 1.0
                )
                * 100.0,
            }

            for pillar in PILLARS:

                row[
                    f"{pillar}_change"
                ] = (
                    current_row[pillar]
                    - previous_row[pillar]
                )

            rows.append(row)

    result = pd.DataFrame(rows)

    if result.empty:
        fail(
            "Historical event-window analysis produced no rows."
        )

    return result


# ---------------------------------------------------------------------
# WORLD BANK API
# ---------------------------------------------------------------------

def fetch_world_bank_indicator(
    indicator_code,
    indicator_name,
):
    """
    Download one independent external outcome indicator
    from the World Bank WDI API.

    Only naturally returned observations are retained.
    No interpolation or imputation is performed.
    """

    countries = ";".join(COUNTRIES)

    url = (
        "https://api.worldbank.org/v2/country/"
        f"{countries}/indicator/{indicator_code}"
    )

    params = {
        "format": "json",
        "per_page": 1000,
        "date": "2015:2024",
    }

    response = requests.get(
        url,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, list) or len(payload) < 2:
        fail(
            f"World Bank API returned an unexpected "
            f"response for {indicator_code}."
        )

    records = payload[1]

    rows = []

    for record in records:

        country_code = record.get(
            "countryiso3code"
        )

        year_raw = record.get("date")
        value = record.get("value")

        if country_code not in COUNTRIES:
            continue

        if year_raw is None:
            continue

        year = int(year_raw)

        if year not in FINAL_YEARS:
            continue

        numeric_value = pd.to_numeric(
            value,
            errors="coerce",
        )

        if pd.isna(numeric_value):
            continue

        rows.append(
            {
                "country_code": country_code,
                "country": COUNTRY_NAMES[
                    country_code
                ],
                "year": year,
                "indicator_code": indicator_code,
                "indicator": indicator_name,
                "value": float(numeric_value),
            }
        )

    result = pd.DataFrame(rows)

    if result.empty:
        fail(
            f"No World Bank observations returned for "
            f"{indicator_code}."
        )

    duplicate_mask = result.duplicated(
        subset=[
            "country_code",
            "year",
        ],
        keep=False,
    )

    if duplicate_mask.any():
        fail(
            f"Duplicate World Bank observations detected "
            f"for {indicator_code}."
        )

    return result


def fetch_external_outcomes():
    """
    Retrieve the independent external validation outcomes.
    """

    frames = []

    for key, specification in EXTERNAL_INDICATORS.items():

        frame = fetch_world_bank_indicator(
            specification["code"],
            specification["name"],
        )

        frame["outcome_key"] = key
        frame["unit"] = specification["unit"]

        frames.append(frame)

    external = pd.concat(
        frames,
        ignore_index=True,
    )

    return external


# ---------------------------------------------------------------------
# MERGE EXTERNAL OUTCOMES
# ---------------------------------------------------------------------

def merge_external_outcomes(
    jesi_series,
    external,
):
    """
    Merge external outcomes with JESI historical observations.

    Missing external observations remain missing.
    """

    wide = external.pivot(
        index=[
            "country_code",
            "country",
            "year",
        ],
        columns="outcome_key",
        values="value",
    ).reset_index()

    result = pd.merge(
        jesi_series,
        wide,
        on=[
            "country_code",
            "country",
            "year",
        ],
        how="left",
        validate="one_to_one",
    )

    result = result.sort_values(
        [
            "country_code",
            "year",
        ]
    ).reset_index(drop=True)

    for column in EXTERNAL_INDICATORS:

        result[
            f"{column}_change"
        ] = (
            result
            .groupby("country_code")[column]
            .diff()
        )

    return result


# ---------------------------------------------------------------------
# SPEARMAN CORRELATION
# ---------------------------------------------------------------------

def safe_spearman(
    x,
    y,
):
    """
    Calculate Spearman correlation using naturally
    observed complete pairs only.
    """

    frame = pd.DataFrame(
        {
            "x": x,
            "y": y,
        }
    ).dropna()

    n = len(frame)

    if n < 3:
        return {
            "pairwise_n": n,
            "spearman_rho": np.nan,
            "spearman_p_value": np.nan,
        }

    if frame["x"].nunique() < 2:
        return {
            "pairwise_n": n,
            "spearman_rho": np.nan,
            "spearman_p_value": np.nan,
        }

    if frame["y"].nunique() < 2:
        return {
            "pairwise_n": n,
            "spearman_rho": np.nan,
            "spearman_p_value": np.nan,
        }

    rho, p_value = spearmanr(
        frame["x"],
        frame["y"],
    )

    return {
        "pairwise_n": n,
        "spearman_rho": rho,
        "spearman_p_value": p_value,
    }


# ---------------------------------------------------------------------
# CORRELATION ANALYSIS
# ---------------------------------------------------------------------

def build_correlations(validation_panel):
    """
    Compare JESI with independent external outcomes.

    Both levels and first differences are reported.

    The correlations are descriptive validation evidence,
    not causal estimates.
    """

    rows = []

    for outcome_key, specification in (
        EXTERNAL_INDICATORS.items()
    ):

        outcome_column = outcome_key
        outcome_change_column = (
            f"{outcome_key}_change"
        )

        # -------------------------------------------------------------
        # Level correlation
        # -------------------------------------------------------------

        level = safe_spearman(
            validation_panel["JESI"],
            validation_panel[outcome_column],
        )

        rows.append(
            {
                "outcome": specification["name"],
                "indicator_code": specification["code"],
                "analysis_type": "level",
                "jesi_variable": "JESI",
                "outcome_variable": outcome_column,
                **level,
            }
        )

        # -------------------------------------------------------------
        # First-difference correlation
        # -------------------------------------------------------------

        change = safe_spearman(
            validation_panel["JESI_change"],
            validation_panel[
                outcome_change_column
            ],
        )

        rows.append(
            {
                "outcome": specification["name"],
                "indicator_code": specification["code"],
                "analysis_type": "first_difference",
                "jesi_variable": "JESI_change",
                "outcome_variable": outcome_change_column,
                **change,
            }
        )

    # -------------------------------------------------------------
    # Country-mean external outcome levels
    # -------------------------------------------------------------

    country_means = (
        validation_panel
        .groupby(
            [
                "country_code",
                "country",
            ],
            as_index=False,
        )
        .agg(
            JESI_mean=("JESI", "mean"),
            unemployment_mean=(
                "unemployment_rate",
                "mean",
            ),
            inflation_mean=(
                "inflation_rate",
                "mean",
            ),
        )
    )

    for outcome_key, specification in (
        EXTERNAL_INDICATORS.items()
    ):

        column = (
            "unemployment_mean"
            if outcome_key
            == "unemployment_rate"
            else "inflation_mean"
        )

        level = safe_spearman(
            country_means["JESI_mean"],
            country_means[column],
        )

        rows.append(
            {
                "outcome": specification["name"],
                "indicator_code": specification["code"],
                "analysis_type": "country_mean_level",
                "jesi_variable": "JESI_mean",
                "outcome_variable": column,
                **level,
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------

def build_summary(
    jesi_series,
    event_windows,
    contribution_panel,
    correlations,
    validation_panel,
):
    """
    Produce an audit-oriented historical-validation summary.
    """

    total_theoretical = (
        len(COUNTRIES)
        * len(FINAL_YEARS)
    )

    complete_observations = len(
        jesi_series
    )

    annual_change_observations = (
        jesi_series["JESI_change"]
        .notna()
        .sum()
    )

    max_decomposition_error = (
        contribution_panel[
            "decomposition_error"
        ]
        .abs()
        .max()
    )

    external_pairs = (
        correlations[
            correlations["analysis_type"]
            == "first_difference"
        ]
    )

    return pd.DataFrame(
        [
            {
                "theoretical_country_year_observations": (
                    total_theoretical
                ),
                "complete_case_country_year_observations": (
                    complete_observations
                ),
                "annual_JESI_change_observations": (
                    annual_change_observations
                ),
                "historical_event_windows": (
                    len(EVENT_WINDOWS)
                ),
                "countries": len(COUNTRIES),
                "years_start": min(FINAL_YEARS),
                "years_end": max(FINAL_YEARS),
                "external_outcomes": len(
                    EXTERNAL_INDICATORS
                ),
                "external_first_difference_tests": len(
                    external_pairs
                ),
                "external_observed_pairs_total": int(
                    external_pairs[
                        "pairwise_n"
                    ].sum()
                ),
                "max_pillar_decomposition_error": (
                    max_decomposition_error
                ),
                "validation_scope": (
                    "historical descriptive validation"
                ),
                "causal_inference": False,
                "imputation_used": False,
                "interpolation_used": False,
                "fabrication_used": False,
                "production_method_modified": False,
            }
        ]
    )


# ---------------------------------------------------------------------
# RESEARCH REPORT
# ---------------------------------------------------------------------

def build_report(
    jesi_series,
    event_windows,
    contribution_panel,
    correlations,
    summary,
):
    """
    Create an audit-ready methodological report.
    """

    lines = []

    lines.append(
        "# JESI Historical Validation"
    )
    lines.append("")

    lines.append(
        "## Validation status"
    )
    lines.append("")

    lines.append(
        "This analysis is a research-validation layer for "
        "JAS Unified Economic Strength Index (JESI) Master Version 1.0."
    )
    lines.append("")

    lines.append(
        "It evaluates historical JESI behavior without modifying "
        "the production methodology."
    )
    lines.append("")

    lines.append(
        "No imputation, interpolation, fabricated observations, "
        "indicator removal, reweighting, or production-method "
        "replacement is performed."
    )
    lines.append("")

    lines.append(
        "## Production specification"
    )
    lines.append("")

    lines.append(
        "The historical series uses the production weighted "
        "geometric aggregation:"
    )
    lines.append("")

    lines.append(
        "JESI = 100 × G^0.20 × P^0.25 × C^0.20 × R^0.20 × A^0.15"
    )
    lines.append("")

    lines.append(
        "The production weights remain unchanged throughout "
        "the validation exercise."
    )
    lines.append("")

    lines.append(
        "## Analytical sample"
    )
    lines.append("")

    lines.extend(
        [
            "- Countries: Bangladesh, India, Indonesia, Malaysia, Vietnam",
            "- Historical period: 2016-2023",
            "- Theoretical country-year observations: "
            f"{summary.iloc[0]['theoretical_country_year_observations']}",
            "- Complete-case observations: "
            f"{summary.iloc[0]['complete_case_country_year_observations']}",
            "- Missing-data treatment: complete-case only",
            "",
        ]
    )

    lines.append(
        "The common historical period is constrained by the "
        "available Productivity pillar series."
    )
    lines.append("")

    lines.append(
        "## Historical trajectory validation"
    )
    lines.append("")

    lines.append(
        "Historical JESI values and year-to-year changes are "
        "reported by country and year."
    )
    lines.append("")

    lines.append(
        "The annual change analysis is descriptive. "
        "A change in JESI is not interpreted as proof that any "
        "single pillar caused the change."
    )
    lines.append("")

    lines.append(
        "## Pillar contribution decomposition"
    )
    lines.append("")

    lines.append(
        "For each consecutive complete year, the change in "
        "log(JESI) is decomposed according to:"
    )
    lines.append("")

    lines.append(
        "Δln(JESI) = Σ weight_i × Δln(Pillar_i)"
    )
    lines.append("")

    lines.append(
        "This is an exact mathematical decomposition of the "
        "production geometric index, subject to numerical tolerance. "
        "It is not a causal attribution."
    )
    lines.append("")

    lines.append(
        "## Pre-specified historical windows"
    )
    lines.append("")

    lines.append(
        event_windows.to_markdown(
            index=False,
            floatfmt=".6f",
        )
    )
    lines.append("")

    lines.append(
        "The historical windows are pre-specified descriptive "
        "comparisons. They are not treated as causal event-study "
        "estimates."
    )
    lines.append("")

    lines.append(
        "## Independent external outcomes"
    )
    lines.append("")

    lines.append(
        "Two World Bank World Development Indicators are used "
        "as external validation outcomes:"
    )
    lines.append("")

    lines.extend(
        [
            "- Unemployment rate: SL.UEM.TOTL.ZS",
            "- Inflation, consumer prices: FP.CPI.TOTL.ZG",
            "",
        ]
    )

    lines.append(
        "Neither external outcome is used to construct JESI."
    )
    lines.append("")

    lines.append(
        "## External-outcome correlations"
    )
    lines.append("")

    lines.append(
        correlations.to_markdown(
            index=False,
            floatfmt=".6f",
        )
    )
    lines.append("")

    lines.append(
        "The reported Spearman correlations describe statistical "
        "association in the available observations. They do not "
        "establish causality, predictive validity, or a universal "
        "direction of effect."
    )
    lines.append("")

    lines.append(
        "First-difference correlations are especially useful as a "
        "supplement because they examine co-movement rather than "
        "only cross-country level differences."
    )
    lines.append("")

    lines.append(
        "## Methodological limitations"
    )
    lines.append("")

    lines.extend(
        [
            "1. The historical sample contains five countries.",
            "2. The common historical period is limited by the available "
            "Productivity pillar series.",
            "3. External outcome availability may differ across "
            "country-years.",
            "4. Spearman correlations are descriptive and do not "
            "establish causality.",
            "5. Historical event windows are not causal event-study "
            "estimates.",
            "6. External outcomes can themselves be affected by many "
            "factors unrelated to JESI.",
            "7. Historical validation is one component of the broader "
            "JESI methodological validation sequence.",
            "",
        ]
    )

    lines.append(
        "## Validation sequence position"
    )
    lines.append("")

    lines.append(
        "This historical validation follows the earlier "
        "conceptual, pillar, indicator, redundancy/correlation, "
        "normalization-sensitivity, weight-sensitivity, and "
        "aggregation-sensitivity stages."
    )
    lines.append("")

    lines.append(
        "The final methodological judgment should only be made "
        "after the complete empirical evidence from these stages "
        "has been reviewed together."
    )
    lines.append("")

    lines.append(
        "## Numerical integrity"
    )
    lines.append("")

    lines.append(
        "The pillar contribution decomposition was independently "
        "checked against the production JESI log-change identity "
        "using a numerical tolerance of 1e-10."
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    print("=" * 78)
    print("JESI HISTORICAL VALIDATION")
    print("=" * 78)

    # ---------------------------------------------------------------
    # Validate production weights.
    # ---------------------------------------------------------------

    validate_weights()

    print()
    print("Production weights validated.")

    # ---------------------------------------------------------------
    # Build historical pillar panel.
    # ---------------------------------------------------------------

    print()
    print(
        "Loading persisted pillar-score sources..."
    )

    panel = build_pillar_panel()

    print(
        f"Historical theoretical panel rows: {len(panel)}"
    )

    # ---------------------------------------------------------------
    # Complete-case panel.
    # ---------------------------------------------------------------

    complete_panel = (
        build_complete_case_panel(
            panel
        )
    )

    print(
        "Historical complete-case rows: "
        f"{len(complete_panel)}"
    )

    # ---------------------------------------------------------------
    # Calculate production JESI.
    # ---------------------------------------------------------------

    jesi_series = (
        build_jesi_series(
            complete_panel
        )
    )

    print(
        "Historical JESI series constructed."
    )

    # ---------------------------------------------------------------
    # Pillar contribution decomposition.
    # ---------------------------------------------------------------

    contribution_panel = (
        build_pillar_contributions(
            jesi_series
        )
    )

    print(
        "Pillar contribution decomposition: PASSED"
    )

    # ---------------------------------------------------------------
    # Historical event windows.
    # ---------------------------------------------------------------

    event_windows = (
        build_event_windows(
            jesi_series
        )
    )

    print(
        "Historical event-window analysis constructed."
    )

    # ---------------------------------------------------------------
    # External outcomes.
    # ---------------------------------------------------------------

    print()
    print(
        "Fetching independent World Bank external outcomes..."
    )

    external = fetch_external_outcomes()

    print(
        f"External observations retrieved: {len(external)}"
    )

    # ---------------------------------------------------------------
    # Merge.
    # ---------------------------------------------------------------

    validation_panel = (
        merge_external_outcomes(
            jesi_series,
            external,
        )
    )

    # ---------------------------------------------------------------
    # Correlations.
    # ---------------------------------------------------------------

    correlations = (
        build_correlations(
            validation_panel
        )
    )

    print(
        "External-outcome correlation analysis constructed."
    )

    # ---------------------------------------------------------------
    # Summary.
    # ---------------------------------------------------------------

    summary = (
        build_summary(
            jesi_series,
            event_windows,
            contribution_panel,
            correlations,
            validation_panel,
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

    validation_panel.to_csv(
        COUNTRY_YEAR_OUTPUT,
        index=False,
    )

    event_windows.to_csv(
        EVENT_OUTPUT,
        index=False,
    )

    contribution_panel.to_csv(
        PILLAR_CONTRIBUTION_OUTPUT,
        index=False,
    )

    correlations.to_csv(
        CORRELATION_OUTPUT,
        index=False,
    )

    summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
    )

    report = build_report(
        jesi_series,
        event_windows,
        contribution_panel,
        correlations,
        summary,
    )

    REPORT_OUTPUT.write_text(
        report,
        encoding="utf-8",
    )

    # ---------------------------------------------------------------
    # Numerical integrity.
    # ---------------------------------------------------------------

    max_error = (
        contribution_panel[
            "decomposition_error"
        ]
        .abs()
        .max()
    )

    if max_error > 1e-10:
        fail(
            "Final numerical integrity validation failed."
        )

    print()
    print("=" * 78)
    print("HISTORICAL VALIDATION SUMMARY")
    print("=" * 78)

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("External correlations:")

    print(
        correlations.to_string(
            index=False
        )
    )

    print()
    print("Output files:")

    print(
        f"  - {COUNTRY_YEAR_OUTPUT}"
    )
    print(
        f"  - {EVENT_OUTPUT}"
    )
    print(
        f"  - {PILLAR_CONTRIBUTION_OUTPUT}"
    )
    print(
        f"  - {CORRELATION_OUTPUT}"
    )
    print(
        f"  - {SUMMARY_OUTPUT}"
    )
    print(
        f"  - {REPORT_OUTPUT}"
    )

    print()
    print(
        "Historical validation: PASSED"
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
