from __future__ import annotations
from pathlib import Path
import re

import pandas as pd
import streamlit as st

# ============================================================
# JAS-JESI Interactive Dashboard
# Reads existing validated CSV outputs; does not recalculate JESI.
# ============================================================

st.set_page_config(
    page_title="JAS-JESI | Economic Strength Dashboard",
    page_icon="🌐",
    layout="wide",
)

ROOT_DIR = Path(__file__).resolve().parent.parent

CSV_CANDIDATES = [
    ROOT_DIR / "final_jesi_country_results.csv",
    ROOT_DIR / "data" / "final_jesi_country_results.csv",
    ROOT_DIR / "outputs" / "final_jesi_country_results.csv",
    ROOT_DIR / "results" / "final_jesi_country_results.csv",
]

def normalize_column_name(name: object) -> str:
    """Normalize a column name for flexible matching."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())

def find_column(
    columns: list[str],
    aliases: list[str],
) -> str | None:
    """Find a column using common alternative names."""
    normalized = {
        normalize_column_name(column): column for column in columns
    }
    for alias in aliases:
        match = normalized.get(normalize_column_name(alias))
        if match is not None:
            return match
    return None

def load_csv(path: Path) -> pd.DataFrame:
    """Read CSV using common text encodings."""
    errors = []
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except (UnicodeDecodeError, pd.errors.ParserError) as exc:
            errors.append(str(exc))
    raise ValueError(
        f"Could not read CSV: {path}\n" + "\n".join(errors)
    )

def discover_csv() -> Path | None:
    """Locate the expected results file."""
    for candidate in CSV_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None

st.title("🌐 JAS-JESI Economic Strength Dashboard")
st.caption(
    "Explore published JESI results, country rankings, "
    "and historical trends from available research outputs."
)

st.info(
    "This dashboard displays existing results. It does not "
    "recalculate scores or independently validate the research."
)

# ============================================================
# Load data
# ============================================================

default_csv = discover_csv()

with st.sidebar:
    st.header("Data source")
    if default_csv:
        st.success(f"Found results file: {default_csv.name}")
        use_uploaded_file = st.checkbox(
            "Upload a different CSV instead",
            value=False,
        )
    else:
        st.warning(
            "The expected results CSV was not found in the "
            "standard locations."
        )
        use_uploaded_file = True

    uploaded_file = st.file_uploader(
        "Upload a JESI results CSV",
        type=["csv"],
        help=(
            "Upload final_jesi_country_results.csv or another "
            "compatible results file."
        ),
    )

try:
    if use_uploaded_file:
        if uploaded_file is None:
            st.warning("Upload a CSV file to start exploring the results.")
            st.stop()
        df = pd.read_csv(uploaded_file)
        data_source = uploaded_file.name
    else:
        if default_csv is None:
            st.error(
                "No results CSV is available. Place the file in "
                "the repository root, data/, outputs/, or results/ "
                "folder, or upload it using the sidebar."
            )
            st.stop()
        df = load_csv(default_csv)
        data_source = str(default_csv.relative_to(ROOT_DIR))
except (OSError, ValueError, pd.errors.ParserError) as exc:
    st.error(f"Could not load the CSV: {exc}")
    st.stop()

if df.empty:
    st.warning("The selected CSV contains no rows.")
    st.stop()

df.columns = [str(column).strip() for column in df.columns]
df = df.dropna(how="all").copy()

if df.empty:
    st.warning("The CSV contains no usable records.")
    st.stop()

st.caption(f"Data source: {data_source}")

# ============================================================
# Detect common column names
# ============================================================

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
        "time",
        "date",
    ],
)

rank_col = find_column(
    columns,
    [
        "rank",
        "ranking",
        "JESI_rank",
        "JESI ranking",
        "country_rank",
        "position",
    ],
)

if country_col is None:
    st.error(
        "Could not identify the country column automatically. "
        "Expected a column such as country or country_name."
    )
    st.write("Available columns:", columns)
    st.dataframe(df, use_container_width=True)
    st.stop()

if score_col is None:
    st.error(
        "Could not identify the JESI score column automatically. "
        "Expected a column such as JESI_score or score."
    )
    st.write("Available columns:", columns)
    st.dataframe(df, use_container_width=True)
    st.stop()

# Convert only the display copy of the score to numeric.
df[score_col] = pd.to_numeric(df[score_col], errors="coerce")
df[country_col] = df[country_col].astype("string").str.strip()

df = df.dropna(subset=[country_col, score_col]).copy()
df = df[df[country_col] != ""]

if df.empty:
    st.error(
        "No usable country/score records remain after parsing. "
        "Check the country and score columns in the source CSV."
    )
    st.stop()

if year_col is not None:
    df["_dashboard_year"] = df[year_col].astype("string").str.strip()
    df.loc[
        df["_dashboard_year"].isin(["", "nan", "None"]),
        "_dashboard_year",
    ] = pd.NA

# ============================================================
# Sidebar filters
# ============================================================

with st.sidebar:
    st.header("Filters")
    available_countries = sorted(
        df[country_col].dropna().astype(str).unique().tolist()
    )
    selected_countries = st.multiselect(
        "Countries",
        options=available_countries,
        default=[],
        help="Leave empty to include all countries.",
    )

    selected_years = None
    if year_col is not None:
        available_years = sorted(
            df["_dashboard_year"].dropna().unique().tolist()
        )
        selected_years = st.multiselect(
            "Years",
            options=available_years,
            default=[],
            help="Leave empty to include all available years.",
        )

filtered = df.copy()

if selected_countries:
    filtered = filtered[
        filtered[country_col].astype(str).isin(selected_countries)
    ]

if year_col is not None and selected_years:
    filtered = filtered[
        filtered["_dashboard_year"].isin(selected_years)
    ]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# ============================================================
# Ranking
# ============================================================

if rank_col is not None:
    filtered["_dashboard_rank"] = pd.to_numeric(
        filtered[rank_col],
        errors="coerce",
    )
else:
    filtered["_dashboard_rank"] = (
        filtered.groupby(
            "_dashboard_year" if year_col is not None else lambda _: 0
        )[score_col]
        .rank(method="min", ascending=False)
    )

# ============================================================
# Summary metrics
# ============================================================

st.subheader("Overview")
metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "Countries represented",
    f"{filtered[country_col].nunique():,}",
)
metric2.metric(
    "Records displayed",
    f"{len(filtered):,}",
)
metric3.metric(
    "Mean displayed score",
    f"{filtered[score_col].mean():.4f}",
)

st.divider()

# ============================================================
# Country ranking
# ============================================================

st.subheader("🏆 Country Ranking")

ranking = filtered.sort_values(
    [score_col, country_col],
    ascending=[False, True],
).copy()

ranking_display = ranking.copy()
if year_col is not None and not selected_years:
    numeric_years = pd.to_numeric(
        ranking_display["_dashboard_year"],
        errors="coerce",
    )
    if numeric_years.notna().any():
        latest_year = numeric_years.max()
        ranking_display = ranking_display[
            numeric_years == latest_year
        ].copy()

display_columns = [country_col]
if year_col is not None:
    display_columns.append(year_col)
display_columns.append(score_col)

if rank_col is not None:
    display_columns.append(rank_col)
else:
    display_columns.append("_dashboard_rank")

if rank_col is None:
    display_columns[-1] = "_dashboard_rank"

ranking_display = ranking_display.sort_values(
    score_col,
    ascending=False,
).copy()

ranking_display = ranking_display.rename(
    columns={"_dashboard_rank": "Calculated display rank"}
)

display_columns = [
    "Calculated display rank"
    if column == "_dashboard_rank"
    else column
    for column in display_columns
]

st.dataframe(
    ranking_display[display_columns],
    use_container_width=True,
    hide_index=True,
)

# ============================================================
# Score chart
# ============================================================

st.subheader("📊 JESI Score Comparison")

chart_data = ranking_display[
    [country_col, score_col]
].copy()
chart_data = chart_data.sort_values(score_col, ascending=True)

if not chart_data.empty:
    st.bar_chart(
        chart_data.set_index(country_col)[score_col],
        horizontal=True,
        use_container_width=True,
    )

# ============================================================
# Historical trend
# ============================================================

st.subheader("📈 Historical Trends")

if year_col is None:
    st.info(
        "No year column was detected. Historical trends are "
        "unavailable until year-based results are provided."
    )
else:
    trend_df = filtered.dropna(subset=["_dashboard_year"]).copy()
    numeric_year = pd.to_numeric(
        trend_df["_dashboard_year"],
        errors="coerce",
    )
    if numeric_year.notna().any():
        trend_df["_chart_year"] = numeric_year
        trend_df = trend_df.dropna(subset=["_chart_year"])
        trend_df = trend_df.groupby(
            ["_chart_year", country_col],
            as_index=False,
        )[score_col].mean()
        trend_df = trend_df.sort_values("_chart_year")
        if not trend_df.empty:
            trend_pivot = trend_df.pivot(
                index="_chart_year",
                columns=country_col,
                values=score_col,
            )
            st.line_chart(
                trend_pivot,
                use_container_width=True,
            )
        else:
            st.info("There are no usable year-based records.")
    else:
        st.info(
            "The detected year column could not be interpreted "
            "as numeric years. Check the source data format."
        )

# ============================================================
# Data preview and download
# ============================================================

st.divider()
st.subheader("📄 Source Data")

with st.expander("View loaded source records"):
    st.dataframe(df, use_container_width=True, hide_index=True)

csv_bytes = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered data as CSV",
    data=csv_bytes,
    file_name="jesi_filtered_results.csv",
    mime="text/csv",
)

st.caption(
    "Research note: a calculated display rank is not an official "
    "JESI rank. Confirm the ranking methodology and source columns "
    "before using these results in research or publication."
)
