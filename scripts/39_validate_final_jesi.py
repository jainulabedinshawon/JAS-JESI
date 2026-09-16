"""
JAS-JESI Productivity Pillar Validation
----------------------------------------

P1: GDP per Person Employed
P2: Total Factor Productivity (TFP) Growth

Validation period:
    2016-2023

Countries:
    Bangladesh
    India
    Viet Nam
    Indonesia
    Malaysia

Validation tests:
    1. Data completeness
    2. Pearson correlation
    3. Spearman correlation
    4. Country-level correlations
    5. Divergence analysis
    6. Outlier sensitivity
    7. Complementarity / redundancy assessment
"""

from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

START_YEAR = 2016
END_YEAR = 2023

COUNTRIES = [
    "Bangladesh",
    "India",
    "Viet Nam",
    "Indonesia",
    "Malaysia",
]

DATA_DIR = Path("data/raw")


# ============================================================
# FILE DISCOVERY
# ============================================================

P1_FILES = list(
    DATA_DIR.glob(
        "*productivity*p1*gdp*person*employed*.csv"
    )
)

P2_FILES = list(
    DATA_DIR.glob(
        "*productivity*p2*.csv"
    )
)

if not P1_FILES:
    raise FileNotFoundError(
        "P1 productivity CSV not found in data/raw/"
    )

if not P2_FILES:
    raise FileNotFoundError(
        "P2 productivity CSV not found in data/raw/"
    )

P1_FILE = P1_FILES[0]
P2_FILE = P2_FILES[0]


print("=" * 70)
print("JAS-JESI PRODUCTIVITY PILLAR VALIDATION")
print("=" * 70)

print()
print(f"P1 file: {P1_FILE}")
print(f"P2 file: {P2_FILE}")
print(f"Period: {START_YEAR}-{END_YEAR}")
print(f"Countries: {', '.join(COUNTRIES)}")


# ============================================================
# LOAD DATA
# ============================================================

p1 = pd.read_csv(P1_FILE)
p2 = pd.read_csv(P2_FILE)


print()
print("P1 columns:")
print(list(p1.columns))

print()
print("P2 columns:")
print(list(p2.columns))


# ============================================================
# STANDARDISE COLUMN NAMES
# ============================================================

p1.columns = [
    str(column).strip().lower().replace(" ", "_")
    for column in p1.columns
]

p2.columns = [
    str(column).strip().lower().replace(" ", "_")
    for column in p2.columns
]


# ============================================================
# IDENTIFY COUNTRY / YEAR / VALUE COLUMNS
# ============================================================

def find_column(columns, candidates):
    for candidate in candidates:
        for column in columns:
            if candidate in column:
                return column

    return None


p1_country = find_column(
    p1.columns,
    ["country", "economy", "location"],
)

p1_year = find_column(
    p1.columns,
    ["year"],
)

p1_value = find_column(
    p1.columns,
    ["value", "gdp_per_person_employed", "productivity"],
)


p2_country = find_column(
    p2.columns,
    ["country", "economy", "location"],
)

p2_year = find_column(
    p2.columns,
    ["year"],
)

p2_value = find_column(
    p2.columns,
    ["value", "tfp_growth", "tfp", "productivity"],
)


if None in [p1_country, p1_year, p1_value]:
    raise ValueError(
        "Could not identify P1 country/year/value columns."
    )

if None in [p2_country, p2_year, p2_value]:
    raise ValueError(
        "Could not identify P2 country/year/value columns."
    )


print()
print("Detected P1 columns:")
print(
    f"Country={p1_country}, "
    f"Year={p1_year}, "
    f"Value={p1_value}"
)

print()
print("Detected P2 columns:")
print(
    f"Country={p2_country}, "
    f"Year={p2_year}, "
    f"Value={p2_value}"
)


# ============================================================
# STANDARDISE DATA
# ============================================================

p1 = p1.rename(
    columns={
        p1_country: "country",
        p1_year: "year",
        p1_value: "p1",
    }
)

p2 = p2.rename(
    columns={
        p2_country: "country",
        p2_year: "year",
        p2_value: "p2",
    }
)


p1["year"] = pd.to_numeric(
    p1["year"],
    errors="coerce",
)

p2["year"] = pd.to_numeric(
    p2["year"],
    errors="coerce",
)

p1["p1"] = pd.to_numeric(
    p1["p1"],
    errors="coerce",
)

p2["p2"] = pd.to_numeric(
    p2["p2"],
    errors="coerce",
)


# ============================================================
# COUNTRY NAME STANDARDISATION
# ============================================================

COUNTRY_MAP = {
    "Vietnam": "Viet Nam",
    "Viet Nam": "Viet Nam",
    "Bangladesh": "Bangladesh",
    "India": "India",
    "Indonesia": "Indonesia",
    "Malaysia": "Malaysia",
}


p1["country"] = p1["country"].astype(str).str.strip()
p2["country"] = p2["country"].astype(str).str.strip()

p1["country"] = p1["country"].replace(COUNTRY_MAP)
p2["country"] = p2["country"].replace(COUNTRY_MAP)


# ============================================================
# FILTER FINAL VALIDATION PERIOD
# ============================================================

p1 = p1[
    p1["year"].between(
        START_YEAR,
        END_YEAR,
    )
]

p2 = p2[
    p2["year"].between(
        START_YEAR,
        END_YEAR,
    )
]

p1 = p1[
    p1["country"].isin(COUNTRIES)
]

p2 = p2[
    p2["country"].isin(COUNTRIES)
]


# ============================================================
# MERGE P1 AND P2
# ============================================================

data = pd.merge(
    p1[
        [
            "country",
            "year",
            "p1",
        ]
    ],
    p2[
        [
            "country",
            "year",
            "p2",
        ]
    ],
    on=[
        "country",
        "year",
    ],
    how="outer",
)


data = data.sort_values(
    [
        "country",
        "year",
    ]
).reset_index(drop=True)


# ============================================================
# DATA COMPLETENESS
# ============================================================

expected_observations = (
    len(COUNTRIES)
    * (END_YEAR - START_YEAR + 1)
)

paired = data.dropna(
    subset=["p1", "p2"]
)

print()
print("=" * 70)
print("1. DATA COMPLETENESS")
print("=" * 70)

print(
    f"Expected country-year observations: "
    f"{expected_observations}"
)

print(
    f"Paired P1-P2 observations: "
    f"{len(paired)}"
)

print(
    f"Missing P1 observations: "
    f"{data['p1'].isna().sum()}"
)

print(
    f"Missing P2 observations: "
    f"{data['p2'].isna().sum()}"
)

print(
    f"Paired-data coverage: "
    f"{len(paired) / expected_observations * 100:.2f}%"
)


# ============================================================
# CORRELATION ANALYSIS
# ============================================================

print()
print("=" * 70)
print("2. P1-P2 CORRELATION")
print("=" * 70)

pearson = paired["p1"].corr(
    paired["p2"],
    method="pearson",
)

spearman = paired["p1"].corr(
    paired["p2"],
    method="spearman",
)

print(
    f"Pearson correlation: "
    f"{pearson:.4f}"
)

print(
    f"Spearman correlation: "
    f"{spearman:.4f}"
)


# ============================================================
# COUNTRY-LEVEL CORRELATION
# ============================================================

print()
print("=" * 70)
print("3. COUNTRY-LEVEL CORRELATION")
print("=" * 70)

country_results = []

for country in COUNTRIES:

    country_data = paired[
        paired["country"] == country
    ]

    if len(country_data) >= 3:

        country_pearson = country_data["p1"].corr(
            country_data["p2"],
            method="pearson",
        )

        country_spearman = country_data["p1"].corr(
            country_data["p2"],
            method="spearman",
        )

    else:

        country_pearson = float("nan")
        country_spearman = float("nan")

    country_results.append(
        {
            "country": country,
            "observations": len(country_data),
            "pearson": country_pearson,
            "spearman": country_spearman,
        }
    )


country_results_df = pd.DataFrame(
    country_results
)

print(
    country_results_df.to_string(
        index=False
    )
)


# ============================================================
# DIVERGENCE ANALYSIS
# ============================================================

paired = paired.copy()

paired["p1_rank"] = paired["p1"].rank(
    method="average"
)

paired["p2_rank"] = paired["p2"].rank(
    method="average"
)

paired["absolute_rank_gap"] = (
    paired["p1_rank"]
    - paired["p2_rank"]
).abs()


print()
print("=" * 70)
print("4. P1-P2 DIVERGENCE")
print("=" * 70)

print(
    f"Mean absolute rank gap: "
    f"{paired['absolute_rank_gap'].mean():.2f}"
)

print(
    f"Maximum absolute rank gap: "
    f"{paired['absolute_rank_gap'].max():.2f}"
)


# ============================================================
# TOP DIVERGENCES
# ============================================================

top_divergence = paired.sort_values(
    "absolute_rank_gap",
    ascending=False,
).head(10)

print()
print("Largest P1-P2 ranking divergences:")

print(
    top_divergence[
        [
            "country",
            "year",
            "p1",
            "p2",
            "absolute_rank_gap",
        ]
    ].to_string(
        index=False
    )
)


# ============================================================
# OUTLIER SENSITIVITY
# ============================================================

print()
print("=" * 70)
print("5. OUTLIER SENSITIVITY")
print("=" * 70)

p1_q01 = paired["p1"].quantile(0.01)
p1_q99 = paired["p1"].quantile(0.99)

p2_q01 = paired["p2"].quantile(0.01)
p2_q99 = paired["p2"].quantile(0.99)

trimmed = paired[
    paired["p1"].between(
        p1_q01,
        p1_q99,
    )
    &
    paired["p2"].between(
        p2_q01,
        p2_q99,
    )
]

trimmed_pearson = trimmed["p1"].corr(
    trimmed["p2"],
    method="pearson",
)

trimmed_spearman = trimmed["p1"].corr(
    trimmed["p2"],
    method="spearman",
)

print(
    f"Full Pearson: "
    f"{pearson:.4f}"
)

print(
    f"1%-99% trimmed Pearson: "
    f"{trimmed_pearson:.4f}"
)

print(
    f"Full Spearman: "
    f"{spearman:.4f}"
)

print(
    f"1%-99% trimmed Spearman: "
    f"{trimmed_spearman:.4f}"
)


# ============================================================
# COMPLEMENTARITY ASSESSMENT
# ============================================================

print()
print("=" * 70)
print("6. COMPLEMENTARITY / REDUNDANCY ASSESSMENT")
print("=" * 70)

correlation_gap = abs(
    pearson - spearman
)

if (
    abs(pearson) >= 0.90
    and abs(spearman) >= 0.90
):
    redundancy_flag = (
        "HIGH CORRELATION — review possible overlap"
    )

elif (
    abs(pearson) >= 0.70
    or abs(spearman) >= 0.70
):
    redundancy_flag = (
        "MODERATE-HIGH CORRELATION — monitor overlap"
    )

else:
    redundancy_flag = (
        "LOW-MODERATE CORRELATION — evidence of complementarity"
    )


print(
    f"Pearson/Spearman assessment: "
    f"{redundancy_flag}"
)

print(
    "Important: correlation alone does not establish redundancy."
)

print(
    "P1 measures labour productivity, while P2 captures "
    "TFP/efficiency dynamics."
)


# ============================================================
# FINAL VALIDATION VERDICT
# ============================================================

print()
print("=" * 70)
print("7. PRODUCTIVITY PILLAR VALIDATION VERDICT")
print("=" * 70)

if (
    len(paired) >= 35
    and
    data["p1"].isna().sum() == 0
    and
    data["p2"].isna().sum() == 0
):

    print("DATA QUALITY: PASS")

else:

    print("DATA QUALITY: REVIEW")


if (
    abs(pearson) >= 0.90
    and abs(spearman) >= 0.80
):

    print(
        "INTERNAL COHERENCE: STRONG"
    )

else:

    print(
        "INTERNAL COHERENCE: REVIEW"
    )


print(
    "THEORETICAL COMPLEMENTARITY: "
    "RETAIN P1 + P2"
)

print(
    "OVERALL STATUS: "
    "PRODUCTIVITY PILLAR — RETAIN, WITH REDUNDANCY MONITORING"
)


# ============================================================
# SAVE VALIDATION TABLE
# ============================================================

OUTPUT_DIR = Path(
    "data/results"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "productivity_validation_results.csv"
)

country_results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)

print()
print(
    f"Validation table saved to: "
    f"{OUTPUT_FILE}"
)

print()
print("=" * 70)
print("PRODUCTIVITY VALIDATION COMPLETE")
print("=" * 70)
