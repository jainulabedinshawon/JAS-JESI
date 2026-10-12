from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import streamlit as st


# ============================================================
# JAS-JESI Interactive Dashboard
# Reads existing JESI CSV outputs.
# Does NOT recalculate JESI scores or change the methodology.
# ============================================================

st.set_page_config(
    page_title="JAS-JESI | Economic Strength Dashboard",
    page_icon="🌐",
    layout="wide",
)

ROOT_DIR = Path(__file__).resolve().parent.parent

COUNTRY_CSV = (
    ROOT_DIR / "data" / "results" / "final_jesi_country_results.csv"
)

HISTORICAL_CSV = (
    ROOT_DIR / "data" / "results" / "jesi_country_year_2016_2023.csv"
)


# ============================================================
# Helpers
# ============================================================

def normalize_column_name(name: object) -> str:
    """Normalize column names for flexible matching."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def find_column(
    columns: list[str],
    aliases: list[str],
) -> str | None:
    """Find a column using common alternative names."""
    normalized = {
        normalize_column_name(column): column
        for column in columns
    }

    for alias in aliases:
        match = normalized.get(normalize_column_name(alias))
        if match is not None:
            return match

    return None


def read_csv_file(path: Path) -> pd.DataFrame:
    """Read a repository CSV with common encodings."""
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    errors: list[str] = []

    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except (UnicodeDecodeError, pd.errors.ParserError) as exc:
            errors.append(f"{encoding}: {exc}")

    raise ValueError(
        f"Could not read CSV file: {path}\n"
        + "\n".join(errors)
    )


def prepare_dataframe(
    source: pd.DataFrame,
    source_name: str,
) -> tuple[pd.DataFrame, str, str, str | None, str | None]:
    """Identify and validate the basic dashboard columns."""
    df = source.copy()
    df.columns = [str(column).strip() for column in df.columns]
    df = df.dropna(how="all").copy()

    if df.empty:
        raise ValueError(f"{source_name} contains no data rows.")

    columns = list(df.columns)

    country_col = find_column(
        columns,
        [
            "country",
            "country_name",
            "country name",
            "economy",
            "economy_name",
            "nation",
        ],
    )

    score_col = find_column(
        columns,
        [
            "JESI",
            "JESI_score_100",
            "JESI_score",
            "JESI score",
            "final_jesi_score",
            "economic_strength_score",
            "economic strength",
            "composite_score",
            "overall_score",
            "score",
        ],
    )

    year_col = find_column(
        columns,
        [
            "year",
            "year_id",
            "observation_year",
            "reference_year",
        ],
    )

    rank_col = find_column(
        columns,
        [
            "rank",
            "ranking",
            "JESI_rank",
            "country_rank",
            "position",
        ],
    )

    if country_col is None:
        raise ValueError(
            f"{source_name}: country column not found. "
            f"Available columns: {columns}"
        )

    if score_col is None:
        raise ValueError(
            f"{source_name}: JESI score column not found. "
            f"Available columns: {columns}"
        )

    # Convert score values for display and sorting only.
    df[score_col] = pd.to_numeric(
        df[score_col],
        errors="coerce",
    )

    df[country_col] = (
        df[country_col]
        .astype("string")
        .str.strip()
    )

    df = df.dropna(subset=[country_col, score_col]).copy()
    df = df[df[country_col] != ""]

    if df.empty:
        raise ValueError(
            f"{source_name}: no usable country/score records."
        )

    if year_col is not None:
        df["_dashboard_year"] = pd.to_numeric(
            df[year_col],
            errors="coerce",
        )

    return df, country_col, score_col, year_col, rank_col


def calculate_display_rank(
    df: pd.DataFrame,
    country_col: str,
    score_col: str,
    year_col: str | None = None,
) -> pd.DataFrame:
    """
    Calculate a display-only ranking.
    This does not modify JESI scores or official source results.
    """
    result = df.copy()

    if year_col is not None:
        result["_dashboard_rank"] = (
            result.groupby("_dashboard_year")[score_col]
            .rank(method="min", ascending=False)
        )
    else:
        result["_dashboard_rank"] = result[score_col].rank(
            method="min",
            ascending=False,
        )

    result["_dashboard_rank"] = (
        result["_dashboard_rank"].astype("Int64")
    )

    return result


# ============================================================
# Header
# ============================================================

st.title("🌐 JAS-JESI Economic Strength Dashboard")

st.caption(
    "Explore country rankings, score comparisons and historical "
    "trends using the existing JAS-JESI research outputs."
)

st.info(
    "Research integrity: this dashboard reads existing JESI results. "
    "It does not recalculate JESI scores, weights, normalization "
    "or aggregation."
)


# ============================================================
# Load repository data
# ============================================================

try:
    country_source = read_csv_file(COUNTRY_CSV)
    country_df, country_name_col, country_score_col, _, country_rank_col = (
        prepare_dataframe(country_source, "Country results CSV")
    )
except (OSError, ValueError, pd.errors.ParserError) as exc:
    st.error(f"Could not load country results: {exc}")
    st.code(str(COUNTRY_CSV))
    st.stop()

historical_df: pd.DataFrame | None = None
historical_country_col: str | None = None
historical_score_col: str | None = None
historical_year_col: str | None = None

historical_error: str | None = None

try:
    historical_source = read_csv_file(HISTORICAL_CSV)

    (
        historical_df,
        historical_country_col,
        historical_score_col,
        historical_year_col,
        _,
    ) = prepare_dataframe(
        historical_source,
        "Historical results CSV",
    )

    if historical_year_col is None:
        raise ValueError(
            "Historical CSV does not contain a recognized year column."
        )

    historical_df = historical_df.dropna(
        subset=["_dashboard_year"]
    ).copy()

    historical_df["_dashboard_year"] = (
        historical_df["_dashboard_year"].astype(int)
    )

except (OSError, ValueError, pd.errors.ParserError) as exc:
    historical_error = str(exc)


# ============================================================
# Sidebar filters
# ============================================================

with st.sidebar:
    st.header("Data sources")

    st.success("Country results CSV loaded")

    st.caption(
        "Country file: "
        "data/results/final_jesi_country_results.csv"
    )

    if historical_error is None:
        st.success("Historical results CSV loaded")
    else:
        st.warning("Historical results are unavailable")
        st.caption(historical_error)

    st.divider()
    st.header("Filters")

    available_countries = sorted(
        country_df[country_name_col]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_countries = st.multiselect(
        "Countries",
        options=available_countries,
        default=[],
        help="Leave empty to include all countries.",
    )

    selected_years: list[int] = []

    if historical_df is not None:
        available_years = sorted(
            historical_df["_dashboard_year"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_years = st.multiselect(
            "Historical years",
            options=available_years,
            default=[],
            help="Leave empty to include all available years.",
        )


# ============================================================
# Filter country-level data
# ============================================================

country_filtered = country_df.copy()

if selected_countries:
    country_filtered = country_filtered[
        country_filtered[country_name_col]
        .astype(str)
        .isin(selected_countries)
    ]

if country_filtered.empty:
    st.warning("No country results match the selected filters.")
    st.stop()


# ============================================================
# Overview
# ============================================================

st.subheader("Overview")

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "Countries represented",
    f"{country_filtered[country_name_col].nunique():,}",
)

metric2.metric(
    "Country records displayed",
    f"{len(country_filtered):,}",
)

metric3.metric(
    "Mean country-level JESI",
    f"{country_filtered[country_score_col].mean():.4f}",
)

st.divider()


# ============================================================
# Country ranking
# ============================================================

st.subheader("🏆 Country Ranking")

ranking = country_filtered.copy()

# Calculate ranking from the displayed country-level scores.
# The source JESI score values remain unchanged.
ranking["_dashboard_rank"] = ranking[country_score_col].rank(
    method="min",
    ascending=False,
).astype("Int64")

ranking = ranking.sort_values(
    [country_score_col, country_name_col],
    ascending=[False, True],
)

ranking_display = ranking[
    [
        "_dashboard_rank",
        country_name_col,
        country_score_col,
    ]
].copy()

ranking_display = ranking_display.rename(
    columns={
        "_dashboard_rank": "Display rank",
        country_name_col: "Country",
        country_score_col: "JESI score",
    }
)

st.caption(
    "Display rank is calculated from the selected country-level "
    "scores. The official rank, if present in the source file, "
    "is not overwritten."
)

st.dataframe(
    ranking_display,
    use_container_width=True,
    hide_index=True,
)

st.subheader("📊 Country Score Comparison")

chart_data = ranking[
    [country_name_col, country_score_col]
].copy()

chart_data = chart_data.sort_values(
    country_score_col,
    ascending=True,
)

st.bar_chart(
    chart_data.set_index(country_name_col)[country_score_col],
    horizontal=True,
    use_container_width=True,
)


# ============================================================
# Historical trends
# ============================================================

st.divider()
st.subheader("📈 Historical Trends")

if historical_df is None:
    st.warning(
        "Historical trends could not be loaded. "
        "Check that the year-level CSV exists and contains "
        "country, year and JESI columns."
    )
else:
    trend_df = historical_df.copy()

    if selected_countries:
        trend_df = trend_df[
            trend_df[historical_country_col]
            .astype(str)
            .isin(selected_countries)
        ]

    if selected_years:
        trend_df = trend_df[
            trend_df["_dashboard_year"].isin(selected_years)
        ]

    if trend_df.empty:
        st.info("No historical records match the selected filters.")
    else:
        # Use the source year-level JESI values directly.
        # No JESI score recalculation is performed.
        trend_df = trend_df[
            [
                "_dashboard_year",
                historical_country_col,
                historical_score_col,
            ]
        ].copy()

        trend_df = trend_df.rename(
            columns={
                "_dashboard_year": "Year",
                historical_country_col: "Country",
                historical_score_col: "JESI",
            }
        )

        trend_pivot = trend_df.pivot_table(
            index="Year",
            columns="Country",
            values="JESI",
            aggfunc="first",
        ).sort_index()

        st.line_chart(
            trend_pivot,
            use_container_width=True,
        )

        with st.expander("View historical source records"):
            st.dataframe(
                trend_df.sort_values(["Year", "Country"]),
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# Source data and download
# ============================================================

st.divider()
st.subheader("📄 Source Data")

with st.expander("View country-level source records"):
    st.dataframe(
        country_filtered,
        use_container_width=True,
        hide_index=True,
    )

country_csv_bytes = country_filtered.to_csv(
    index=False,
).encode("utf-8")

st.download_button(
    label="Download country results as CSV",
    data=country_csv_bytes,
    file_name="jesi_country_results.csv",
    mime="text/csv",
)

if historical_df is not None:
    historical_download = historical_df.copy()

    if selected_countries:
        historical_download = historical_download[
            historical_download[historical_country_col]
            .astype(str)
            .isin(selected_countries)
        ]

    if selected_years:
        historical_download = historical_download[
            historical_download["_dashboard_year"].isin(selected_years)
        ]

    historical_csv_bytes = historical_download.to_csv(
        index=False,
    ).encode("utf-8")

    st.download_button(
        label="Download historical results as CSV",
        data=historical_csv_bytes,
        file_name="jesi_historical_results.csv",
        mime="text/csv",
    )

st.caption(
    "JAS-JESI research note: dashboard rankings are for display "
    "and exploration. Interpret results alongside observation "
    "coverage, missing-data limitations and the validated research "
    "methodology. This dashboard does not independently validate "
    "the research findings."
)