
# JESI Normalization Audit — Phase 2

**Status:** Preliminary code-level audit  
**Scope:** Productivity scoring, final JESI construction, missing-data coverage, and normalization sensitivity  
**Production changes:** None authorized  
**Audit principle:** Preserve the existing baseline until the source data, current outputs, and alternative methods have been independently verified.

---

## 1. Purpose

Phase 2 continues the normalization audit by examining how the Productivity indicators are scored, how the final JESI panel is constructed, and how unequal data coverage affects country-level comparisons.

The purpose is to identify discrepancies between documented methodology and implemented code before considering any changes to production scoring.

This document records preliminary code-level findings. It does not certify the scientific validity of the current results.

## 2. Files Examined

The preliminary review covered the following repository files:

- `scripts/15_score_productivity_p1.py`
- `scripts/14_analyze_productivity_distribution.py`
- `scripts/19_score_productivity_p2.py`
- `scripts/18_analyze_productivity_p2_distribution.py`
- `scripts/20_construct_productivity_pillar.py`
- `scripts/36_calculate_jesi.py`
- `scripts/38_generate_final_jesi_results.py`
- `scripts/45_normalization_sensitivity.py`
- `docs/methodology/normalization_protocol_v1.md`

Findings should be rechecked against the exact commit, source data, and generated outputs used for the next reproducibility review.

## 3. Productivity Indicator P1

**File:** `scripts/15_score_productivity_p1.py`

The implementation:

1. Restricts the scoring period to 2016–2023.
2. Filters observations to the expected five countries.
3. Excludes observations missing `gdp_per_person_employed`.
4. Calculates pooled percentile ranks using pandas ranking with `method="average"` and `pct=True`.
5. Clips the lower score boundary to `1e-6` and the upper boundary to `1.0`.
6. Writes scores to `productivity_p1_scores_2016_2023.csv`.

### Distribution-analysis period

` scripts/14_analyze_productivity_distribution.py` analyzes the raw Productivity P1 distribution using the 2015–2024 period.

Consequently, the distribution-analysis period differs from the P1 scoring period.

This is not automatically an error: the periods could serve different analytical purposes. However, the methodology documentation must clearly explain whether the broader period is used only for exploratory analysis or is intended to define a fixed reference population.

## 4. Productivity Indicator P2

**File:** `scripts/19_score_productivity_p2.py`

The implementation:

1. Restricts scoring to 2016–2023.
2. Excludes missing TFP-growth observations.
3. Checks for duplicate observations.
4. Calculates pooled percentile ranks using `method="average"` and `pct=True`.
5. Clips scores to the interval from `1e-6` to `1.0`.
6. Requires exactly 40 observations, corresponding to five countries across eight years; otherwise, the script raises an error.

**Distribution-analysis file:** `scripts/18_analyze_productivity_p2_distribution.py`

This file analyzes the 2016–2023 TFP-growth distribution. It excludes 2015 because calculating growth requires a preceding year's TFP level.

The P2 distribution-analysis period therefore matches the P2 scoring period, although the underlying TFP calculation may require an earlier raw-data observation.

## 5. Productivity Pillar Construction

**File:** `scripts/20_construct_productivity_pillar.py`

The previously inspected implementation uses the P1 and P2 scores for 2016–2023 and constructs the Productivity pillar using an arithmetic mean as the baseline, with a geometric-mean alternative available for comparison.

The audit should verify:

- The exact alignment of P1 and P2 by country and year.
- Whether both indicator scores are present for every expected observation.
- Whether the arithmetic-mean baseline is consistently documented.
- Whether alternative aggregation results are kept separate from production outputs.

No change to pillar aggregation is authorized by this audit alone.

## 6. Final JESI Panel and Missing Data

**File:** `scripts/36_calculate_jesi.py`

The final calculation targets five countries over 2016–2023, giving a theoretical panel of 40 country-year observations.

The inspected implementation:

- Merges pillar scores by country code and year.
- Identifies rows with missing pillar values.
- Retains complete cases without imputing missing pillar scores.
- Checks country-year uniqueness and representation of all five countries and all eight years in the retained panel.
- Calculates JESI using the weighted geometric mean.

The validation of country and year representation does not, by itself, establish that the panel is balanced. A panel can contain all five countries and all eight years while still having missing country-year combinations.

### Reported coverage requiring revalidation

The existing project context reports 34 complete-case observations out of 40. It also reports that Bangladesh has 2 complete observations out of 8, while each of the other four countries has 8 out of 8.

These are reported production figures, not newly certified results from this audit. They must be checked against the actual output files and the exact commit being audited.

The next verification should establish:

- Expected observations: 40.
- Actual complete-case observations.
- Missing country-year combinations.
- Complete-case counts and coverage percentages by country.
- Whether each pillar's missingness is responsible for each excluded observation.

## 7. Country-Level Average Interpretation

**File:** `scripts/38_generate_final_jesi_results.py`

The inspected reporting logic calculates country-level average JESI values and reports observation counts and coverage.

Unequal coverage creates an important comparability limitation. A country average based on two observations should not be interpreted as directly equivalent in representativeness to an average based on eight observations.

Previously reported averages were:

| Country | Reported mean JESI | Reported observations |
|---|---:|---:|
| Malaysia | 59.283 | 8 |
| Vietnam | 57.161 | 8 |
| India | 48.635 | 8 |
| Indonesia | 46.824 | 8 |
| Bangladesh | 34.464 | 2 |

These values are included as previously reported figures for audit context only. They must be reproduced from the current saved outputs before publication or formal certification.

Any presentation of country averages should prominently disclose the observation count and coverage. A balanced-panel sensitivity analysis may help evaluate how unequal coverage affects comparisons, but it must not silently replace the baseline.

## 8. Documentation–Implementation Discrepancy

The preliminary audit identified a discrepancy between the documented normalization protocol and the Productivity scoring code.

The documentation in `docs/methodology/normalization_protocol_v1.md` describes a full-sample min–max baseline, whereas the inspected P1 and P2 scoring implementations use pooled percentile ranks.

This is a methodology-documentation inconsistency that requires resolution. It does not, on its own, demonstrate that the computed scores are incorrect.

The audit must determine which method was intended, approved, and used to produce the currently reported results. Documentation must not be rewritten to imply historical approval or methodological intent that cannot be supported by repository evidence.

## 9. Pooled Percentile-Rank Implications

A pooled percentile rank measures an observation relative to the other eligible observations in the reference sample.

Therefore, the resulting score depends on the selected reference population, time period, missing-data pattern, and ranking implementation.

The audit should document:

- The countries included in the ranking population.
- The exact years included.
- Whether missing values are excluded before ranking.
- How ties are handled.
- The score-boundary clipping rule.
- Whether scores are intended to support within-sample comparisons or comparisons against a fixed external reference.
- Whether the ranking population is consistent across indicators.

Percentile scores should not be described as absolute measures unless a separately justified interpretation supports that claim.

## 10. Normalization Sensitivity Script

**File:** `scripts/45_normalization_sensitivity.py`

The script is intended to compare alternative normalization specifications without overwriting the production baseline. The inspected description includes alternatives such as:

- Full-sample min–max normalization.
- Winsorized min–max normalization using P5–P95 bounds.
- Pooled percentile-rank normalization.
- Alternative Resilience reference zones using P5–P95 and P20–P80 bounds.

The existence of this script does not establish that the sensitivity analysis has successfully run or reproduced the baseline.

Before relying on its outputs, verify:

1. All required input files exist and match the intended source-data version.
2. The script completes successfully on the audited commit.
3. Its baseline specification reproduces the existing production results within a predeclared numerical tolerance.
4. Alternative outputs are saved separately from production artifacts.
5. No production files are overwritten.
6. The treatment of missing values and indicator direction is consistent across specifications.
7. Country rankings, rank changes, score differences, and relevant correlations are reported.
8. The output identifies the exact specification and reference period for each sensitivity result.

Any sensitivity result that cannot reproduce the baseline must be investigated before the alternative comparisons are interpreted.

## 11. Required Evidence Before Methodological Changes

The following evidence should be collected before proposing a production-method change:

### A. Baseline identification

- Record the exact Git commit SHA.
- Record the relevant workflow run and status.
- Identify the source-data files used.
- Record checksums or another reproducible means of identifying those input files.
- Preserve copies of the existing production outputs.

### B. Reproducibility

- Run the existing workflow or the relevant scoring stages in a controlled environment.
- Confirm whether the reported 34-of-40 coverage is reproduced.
- Recalculate country-level observation counts and averages from the saved outputs.
- Investigate any mismatch before proceeding.

### C. Sensitivity validation

- Execute `scripts/45_normalization_sensitivity.py` in a controlled environment.
- Confirm baseline reproduction.
- Check output paths and verify that production artifacts remain unchanged.
- Compare alternative methods using predeclared measures and explicit reference populations.

### D. Documentation alignment

- Establish the intended normalization rule for each indicator.
- Resolve the discrepancy between documented min–max normalization and implemented percentile ranks.
- Document the reference population, years, missing-value rules, indicator direction, score boundaries, and aggregation method.
- Preserve a record of the decision and supporting evidence.

## 12. Risks and Limitations

The preliminary review identifies the following issues for further verification:

1. **Methodology documentation mismatch:** The documented normalization baseline may not match the active Productivity scoring implementation.
2. **Reference-period clarity:** Productivity distribution analysis and scoring use different periods for P1.
3. **Unequal coverage:** The reported complete-case panel is not balanced, and Bangladesh has substantially fewer observations in the reported output.
4. **Sensitivity reproducibility:** The alternative-normalization script has not been certified merely by inspecting its source code.
5. **Historical traceability:** The reported scores and coverage require verification against a specific commit, input dataset, and saved output.

These findings are audit items, not evidence of misconduct or proof that the JESI framework is invalid.

## 13. Production Change Control

During this phase:

- Do not modify production scoring formulas.
- Do not change normalization methods in the active production pipeline.
- Do not impute or fabricate missing observations.
- Do not overwrite the baseline output files.
- Do not describe preliminary findings as independently certified.
- Do not claim predictive superiority, causal identification, universal validity, or external endorsement without separate evidence.

Any future method change should be proposed in a separate branch, supported by a reproducible comparison against the preserved baseline, and reviewed before merging.

## 14. Phase 2 Conclusion

The preliminary code review indicates that the Productivity scoring implementation uses pooled percentile ranks, while the methodology documentation describes a full-sample min–max baseline. It also identifies a difference between the P1 distribution-analysis period and the P1 scoring period.

The final JESI implementation uses complete-case observations rather than imputing missing pillar scores. The reported unequal coverage makes transparent observation counts and balanced-panel sensitivity analysis particularly important.

The next phase should focus on evidence collection, baseline reproduction, and controlled sensitivity testing. No production normalization change should be made until those checks are complete and the intended methodology is documented and approved.

---

**Audit status:** Preliminary — pending reproducibility verification  
**Production scoring changes:** None  
**Results certification:** Not performed
