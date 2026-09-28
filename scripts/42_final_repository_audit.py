from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "data/results/final_jesi_country_results.csv",
    "data/results/final_jesi_yearly_summary.csv",
    "data/results/jesi_country_year_2016_2023.csv",
    "data/results/jesi_robustness_country_results.csv",
    "data/results/jesi_robustness_correlations.csv",
    "docs/JESI_Final_Results_Report.md",
]


EXPECTED_COUNTRIES = [
    "Bangladesh",
    "India",
    "Vietnam",
    "Indonesia",
    "Malaysia",
]

EXPECTED_YEARS = list(range(2016, 2024))

EXPECTED_THEORETICAL_ROWS = len(EXPECTED_COUNTRIES) * len(EXPECTED_YEARS)


def fail(message):
    print(f"ERROR: {message}")
    raise SystemExit(1)


def check_file(path):
    if not path.exists():
        fail(f"Required file is missing: {path.relative_to(ROOT)}")

    print(f"PASS: {path.relative_to(ROOT)} exists.")


def find_column(df, candidates):
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def main():
    print("=" * 70)
    print("JAS-JESI FINAL REPOSITORY AUDIT")
    print("=" * 70)

    # ---------------------------------------------------------------
    # 1. Required repository files
    # ---------------------------------------------------------------
    for relative_path in REQUIRED_FILES:
        check_file(ROOT / relative_path)

    print("PASS: Required repository files are present.")

    # ---------------------------------------------------------------
    # 2. Load final country-year JESI output
    # ---------------------------------------------------------------
    country_year_path = ROOT / "data/results/jesi_country_year_2016_2023.csv"

    try:
        country_year = pd.read_csv(country_year_path)
    except Exception as exc:
        fail(f"Unable to read {country_year_path}: {exc}")

    # ---------------------------------------------------------------
    # 3. Validate theoretical panel size
    #
    # 5 countries × 8 years = 40 theoretical observations.
    #
    # IMPORTANT:
    # The final JESI calculation is complete-case based.
    # Therefore the final country-year file is NOT required to contain
    # all 40 theoretical observations.
    # ---------------------------------------------------------------
    print(
        f"PASS: Theoretical panel contains "
        f"{EXPECTED_THEORETICAL_ROWS} country-year observations "
        f"({len(EXPECTED_COUNTRIES)} countries × {len(EXPECTED_YEARS)} years)."
    )

    # ---------------------------------------------------------------
    # 4. Validate actual complete-case sample
    # ---------------------------------------------------------------
    actual_rows = len(country_year)

    if actual_rows == 0:
        fail("Final JESI country-year output contains zero observations.")

    if actual_rows > EXPECTED_THEORETICAL_ROWS:
        fail(
            f"{country_year_path.relative_to(ROOT)} contains "
            f"{actual_rows} rows; this exceeds the theoretical panel size "
            f"of {EXPECTED_THEORETICAL_ROWS}."
        )

    print(
        f"PASS: Final JESI country-year output contains "
        f"{actual_rows} complete-case observations."
    )

    excluded_rows = EXPECTED_THEORETICAL_ROWS - actual_rows

    print(
        f"PASS: Complete-case retention = "
        f"{actual_rows}/{EXPECTED_THEORETICAL_ROWS} "
        f"({actual_rows / EXPECTED_THEORETICAL_ROWS:.1%})."
    )

    print(
        f"PASS: Excluded theoretical country-year observations = "
        f"{excluded_rows}."
    )

    # ---------------------------------------------------------------
    # 5. Identify country/year columns
    # ---------------------------------------------------------------
    country_col = find_column(
        country_year,
        ["Country", "country", "country_name", "Country Name"]
    )

    year_col = find_column(
        country_year,
        ["Year", "year"]
    )

    if country_col is None:
        fail(
            "Could not identify the country column in "
            f"{country_year_path.relative_to(ROOT)}."
        )

    if year_col is None:
        fail(
            "Could not identify the year column in "
            f"{country_year_path.relative_to(ROOT)}."
        )

    # ---------------------------------------------------------------
    # 6. Validate countries
    # ---------------------------------------------------------------
    observed_countries = set(
        country_year[country_col].dropna().astype(str).str.strip()
    )

    unexpected_countries = observed_countries - set(EXPECTED_COUNTRIES)

    if unexpected_countries:
        fail(
            "Unexpected countries found in final country-year output: "
            + ", ".join(sorted(unexpected_countries))
        )

    print("PASS: Final country-year output contains only expected countries.")

    # ---------------------------------------------------------------
    # 7. Validate years
    # ---------------------------------------------------------------
    try:
        observed_years = set(
            pd.to_numeric(
                country_year[year_col],
                errors="raise"
            ).astype(int)
        )
    except Exception as exc:
        fail(f"Unable to validate year values: {exc}")

    unexpected_years = observed_years - set(EXPECTED_YEARS)

    if unexpected_years:
        fail(
            "Unexpected years found in final country-year output: "
            + ", ".join(str(x) for x in sorted(unexpected_years))
        )

    print("PASS: Final country-year output contains only years 2016–2023.")

    # ---------------------------------------------------------------
    # 8. Check duplicate country-year observations
    # ---------------------------------------------------------------
    duplicate_mask = country_year.duplicated(
        subset=[country_col, year_col],
        keep=False
    )

    duplicate_count = int(duplicate_mask.sum())

    if duplicate_count > 0:
        duplicate_rows = (
            country_year.loc[duplicate_mask, [country_col, year_col]]
            .drop_duplicates()
            .to_dict("records")
        )

        fail(
            "Duplicate country-year observations detected: "
            + str(duplicate_rows)
        )

    print("PASS: No duplicate country-year observations detected.")

    # ---------------------------------------------------------------
    # 9. Verify that the actual sample is a subset of the
    #    theoretical 40-observation panel
    # ---------------------------------------------------------------
    theoretical_pairs = {
        (country, year)
        for country in EXPECTED_COUNTRIES
        for year in EXPECTED_YEARS
    }

    observed_pairs = {
        (
            str(row[country_col]).strip(),
            int(row[year_col])
        )
        for _, row in country_year.iterrows()
    }

    unexpected_pairs = observed_pairs - theoretical_pairs

    if unexpected_pairs:
        fail(
            "Final output contains country-year pairs outside the "
            "theoretical panel: "
            + str(sorted(unexpected_pairs))
        )

    print(
        "PASS: All final country-year observations belong to "
        "the theoretical 40-observation panel."
    )

    # ---------------------------------------------------------------
    # 10. Identify excluded country-year observations
    #
    # These are NOT automatically errors.
    # They represent observations excluded by the complete-case rule.
    # ---------------------------------------------------------------
    excluded_pairs = theoretical_pairs - observed_pairs

    if excluded_pairs:
        print(
            "PASS: Excluded country-year observations are explicitly "
            "identified by complete-case comparison:"
        )

        for country, year in sorted(excluded_pairs):
            print(f"  - {country} {year}")
    else:
        print(
            "PASS: No country-year observations were excluded; "
            "complete theoretical panel is available."
        )

    # ---------------------------------------------------------------
    # 11. Validate final country results
    # ---------------------------------------------------------------
    final_country_path = ROOT / "data/results/final_jesi_country_results.csv"

    try:
        final_country = pd.read_csv(final_country_path)
    except Exception as exc:
        fail(f"Unable to read final country results: {exc}")

    if final_country.empty:
        fail("Final country results file is empty.")

    final_country_col = find_column(
        final_country,
        ["Country", "country", "country_name", "Country Name"]
    )

    if final_country_col is None:
        fail(
            "Could not identify country column in final country results."
        )

    final_countries = set(
        final_country[final_country_col]
        .dropna()
        .astype(str)
        .str.strip()
    )

    unexpected_final_countries = (
        final_countries - set(EXPECTED_COUNTRIES)
    )

    if unexpected_final_countries:
        fail(
            "Unexpected countries found in final country results: "
            + ", ".join(sorted(unexpected_final_countries))
        )

    print("PASS: Final country results contain only expected countries.")

    # ---------------------------------------------------------------
    # 12. Validate yearly summary
    # ---------------------------------------------------------------
    yearly_path = ROOT / "data/results/final_jesi_yearly_summary.csv"

    try:
        yearly = pd.read_csv(yearly_path)
    except Exception as exc:
        fail(f"Unable to read yearly summary: {exc}")

    if yearly.empty:
        fail("Final yearly summary is empty.")

    yearly_col = find_column(
        yearly,
        ["Year", "year"]
    )

    if yearly_col is None:
        fail("Could not identify year column in yearly summary.")

    try:
        yearly_years = set(
            pd.to_numeric(
                yearly[yearly_col],
                errors="raise"
            ).astype(int)
        )
    except Exception as exc:
        fail(f"Unable to validate yearly summary years: {exc}")

    unexpected_summary_years = (
        yearly_years - set(EXPECTED_YEARS)
    )

    if unexpected_summary_years:
        fail(
            "Unexpected years found in yearly summary: "
            + ", ".join(
                str(x) for x in sorted(unexpected_summary_years)
            )
        )

    print("PASS: Final yearly summary years are within 2016–2023.")

    # ---------------------------------------------------------------
    # 13. Validate robustness outputs
    # ---------------------------------------------------------------
    robustness_country_path = (
        ROOT / "data/results/jesi_robustness_country_results.csv"
    )

    robustness_corr_path = (
        ROOT / "data/results/jesi_robustness_correlations.csv"
    )

    try:
        robustness_country = pd.read_csv(robustness_country_path)
        robustness_corr = pd.read_csv(robustness_corr_path)
    except Exception as exc:
        fail(f"Unable to read robustness outputs: {exc}")

    if robustness_country.empty:
        fail("Robustness country results are empty.")

    if robustness_corr.empty:
        fail("Robustness correlation results are empty.")

    print("PASS: Robustness country results are present and non-empty.")
    print("PASS: Robustness correlation results are present and non-empty.")

    # ---------------------------------------------------------------
    # 14. Final audit summary
    # ---------------------------------------------------------------
    print("=" * 70)
    print("FINAL AUDIT SUMMARY")
    print("=" * 70)

    print(
        f"Theoretical panel:       {EXPECTED_THEORETICAL_ROWS}"
    )
    print(
        f"Complete-case sample:     {actual_rows}"
    )
    print(
        f"Excluded observations:    {excluded_rows}"
    )
    print(
        f"Retention rate:           "
        f"{actual_rows / EXPECTED_THEORETICAL_ROWS:.1%}"
    )

    if excluded_pairs:
        print("Excluded country-years:")
        for country, year in sorted(excluded_pairs):
            print(f"  - {country} {year}")

    print("=" * 70)
    print(
        "PASS: Final repository audit completed successfully."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
