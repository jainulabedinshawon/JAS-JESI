
# JESI Normalization Harmonization: Reproducible Change Plan

**Status:** Proposed — not yet implemented. This document does not change production scores or scoring code.

## 1. Purpose

The JESI repository contains differences between the written normalization protocol and the active production scoring pipeline. Before preparing the SSRN paper, the normalization reference population, scoring transformations, missing-data rules, and benchmark period must be documented consistently.

The current production results must be preserved as a baseline before any score-changing modification.

## 2. Confirmed Audit Findings

- The primary study period is 2016–2023.
- Five countries are included: Bangladesh, India, Indonesia, Malaysia, and Vietnam.
- The theoretical study sample contains 40 country-year observations.
- The current reported production sample contains 34 complete country-year observations.
- Growth scoring uses pooled percentile ranks.
- Connectivity scoring uses pooled percentile-rank scoring.
- Productivity pillar outputs cover 2016–2023.
- Resilience uses min–max scoring for FX reserves/import cover and nonlinear scoring for government debt and current-account balance.
- Strategic Autonomy uses empirical P10–P90 bounds.
- Several methodology documents describe a 2015–2024 benchmark and min–max normalization, which do not fully match the active scoring implementation.

These differences require indicator-level verification before a harmonized specification is adopted.

## 3. Preserve the Original Production Baseline

Before changing scoring code:

1. Record the source commit SHA and the successful Final JESI Pipeline workflow run.
2. Preserve the existing final report, README results, processed pillar files, and final JESI scores.
3. Label the preserved results as the Original Production Baseline.
4. Record the source commit and workflow run for each reported result.
5. Do not overwrite or relabel the existing scores as harmonized results.

## 4. Proposed Primary Reference Period

The proposed primary comparison period is 2016–2023.

Raw data for 2015 and 2024 may be retained for descriptive analysis or separately labelled robustness checks. However, these years should not silently determine the normalization reference population for only selected pillars.

Before implementing a common reference population, inspect data coverage and scoring formulas for every indicator.

For each indicator, document:

- Study period.
- Normalization reference period.
- Countries and observations used to estimate reference values.
- Indicator direction.
- Exact scoring transformation.
- Treatment of ties, outliers, missing observations, and constant series.
- Score bounds and any positive floor used for geometric aggregation.
- Exclusions and the reason for each exclusion.

Do not automatically replace percentile or nonlinear transformations with min–max normalization. A transformation change must be treated as a separate methodological specification and evaluated through sensitivity analysis.

## 5. Code Areas Requiring Review

### Growth
- `scripts/27_score_growth.py`
- `scripts/28_construct_growth_pillar.py`

Verify the years entering pooled percentile ranks, tie handling, and missing-value behavior.

### Connectivity
- `scripts/24_score_connectivity.py`
- `scripts/25_construct_connectivity_pillar.py`
- The corresponding connectivity distribution-analysis script.

Verify that distribution analysis and scoring use the same reference population.

### Productivity
- P1 and P2 indicator-scoring scripts.
- `scripts/20_construct_productivity_pillar.py`

Verify the reference period and consistency between P1 and P2 scoring.

### Resilience
- `scripts/11_score_resilience_pillar.py`
- `src/nonlinear_resilience_scoring.py`

Document the FX reserve reference bounds and the exact nonlinear debt and current-account formulas.

### Strategic Autonomy
- `scripts/34_score_autonomy.py`
- `scripts/35_construct_autonomy_pillar.py`

Document the P10–P90 reference population, direction assumptions, and complete-case exclusions.

### Final Index and Validation
- `scripts/36_calculate_jesi.py`
- `scripts/37_robustness_tests.py`
- `scripts/39_validate_final_jesi.py`
- `scripts/50_balanced_panel_sensitivity.py`

Verify the study-window filter, weights, score-domain requirements, and independent recomputation.

### Documentation
- `docs/methodology/normalization_protocol_v1.md`
- `docs/methodology/indicator_direction_matrix_v1.md`
- Master Version 1.0
- Final results report
- README

All documentation must accurately describe the code that produced the reported results.

## 6. Required Validation Tests

The revised implementation must pass the following checks:

1. No duplicate country-year or country-year-indicator records where uniqueness is required.
2. Validate the five-country sample and the 2016–2023 study period.
3. Recompute complete-case coverage from generated data; do not hard-code the expected number of complete cases.
4. Verify all pillar inputs to the weighted geometric mean are finite and strictly positive.
5. Verify score ranges and documented transformations.
6. Verify that the JESI weights sum to 1 within a defined numerical tolerance:
   - Growth: 0.20
   - Productivity: 0.25
   - Connectivity: 0.20
   - Resilience: 0.20
   - Strategic Autonomy: 0.15
7. Independently recompute final JESI from saved pillar scores.
8. Test reproducibility using identical inputs and code.
9. Run alternative-weight, alternative-aggregation, and balanced-panel sensitivity tests.
10. Compare original and revised country-year scores, country averages, ranks, and observation counts.
11. Update the methodology documents, generated report, and README consistently.
12. Run the full GitHub Actions pipeline and review the resulting outputs before merging.

The complete-case count may remain 34, but this must be verified from the revised outputs.

## 7. Required Outputs

The implementation pull request should include:

- An indicator-level normalization specification.
- Justified scoring-code changes.
- Tests for reference-period selection and score invariants.
- An original-versus-revised results comparison.
- Updated methodology documents and reports.
- A successful validation workflow, or a clear record of unresolved failures.

## 8. Implications for the SSRN Paper

Until harmonization and validation are complete, report the existing numbers as results from the current production specification.

Disclose the benchmark-period and methodology-documentation discrepancy as unresolved until it is corrected.

Do not claim that harmonization has been implemented unless the revised pipeline has run successfully and the resulting outputs have been checked.

The final paper must describe the exact methodology used to generate its reported tables and scores.
