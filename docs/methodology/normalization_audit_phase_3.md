
# JESI Normalization Audit — Phase 3

**Status:** Reproducibility and sensitivity testing protocol  
**Study period:** 2016–2023  
**Countries:** Bangladesh, India, Indonesia, Malaysia, Vietnam  
**Theoretical panel:** 40 country-year observations  
**Production changes:** Not authorized by this protocol  
**Certification:** Pending execution and evidence review

---

## 1. Objective

Phase 3 establishes a controlled procedure to determine whether the current JESI production results can be reproduced and whether country scores and rankings are sensitive to alternative normalization specifications.

This phase separates three questions:

1. Can the existing production baseline be reproduced from the same code and source data?
2. Can alternative normalization methods be tested without overwriting production outputs?
3. Do alternative methods materially change country-year scores, country averages, or country rankings?

This document defines the testing protocol. It does not claim that any test has already passed.

## 2. Preconditions

Before testing begins, record:

- The exact Git commit SHA being audited.
- The target branch and production baseline commit.
- The relevant successful GitHub Actions workflow run.
- The source-data files and their SHA-256 checksums.
- The Python version and relevant package versions.
- The paths of the existing final JESI outputs.
- The expected input and output schemas.
- Any environment variables or configuration values affecting scoring.

If the original inputs or outputs cannot be identified, record the limitation. Do not substitute unverified data and describe the result as a baseline reproduction.

## 3. Baseline Preservation

Before executing any scoring script:

1. Identify the currently published production outputs.
2. Save or otherwise preserve a versioned copy of the original outputs.
3. Record the source commit and input checksums.
4. Confirm that the testing procedure writes to a separate audit-output directory.
5. Confirm that production CSV files and published results will not be overwritten.

Suggested audit output directory:

`artifacts/normalization_audit/phase_3/`

Use the repository's established artifact conventions if they differ. Do not commit large or sensitive raw datasets merely to preserve a baseline.

## 4. Test A — Baseline Reproducibility

Run the existing production pipeline in a controlled environment using the identified source commit and inputs.

Compare the reproduced outputs with the preserved baseline.

### Required comparisons

- Country-year JESI scores.
- Pillar scores for Growth, Productivity, Connectivity, Resilience, and Strategic Autonomy.
- Country-level average scores.
- Observation counts and coverage percentages.
- Missing country-year combinations.
- Country ranking order.
- Output schemas and row counts.

### Numerical comparison

Predeclare a numerical tolerance appropriate to the stored precision and calculations.

Report, at minimum:

- Maximum absolute score difference.
- Mean absolute score difference.
- Number of rows compared.
- Number of exact matches at stored precision.
- Number of values outside the declared tolerance.
- Whether country ranking order changed.

Do not round scores before comparison in a way that conceals meaningful differences.

### Pass criteria

Baseline reproduction passes only when:

- The input data and code version are identified.
- All required baseline outputs are available.
- Row keys and schemas match.
- Score differences fall within the declared tolerance, or every deviation is explained and accepted.
- Coverage and ranking differences are reported.
- Production outputs remain unchanged.

A successful workflow status alone is not sufficient evidence of numerical reproducibility.

## 5. Test B — Panel and Missing-Data Audit

The theoretical panel contains 5 countries multiplied by 8 years, giving 40 country-year observations.

Verify the actual complete-case panel from the current output files.

Report:

- Expected rows.
- Observed rows before complete-case filtering.
- Retained complete-case rows.
- Excluded rows.
- Missing country-year combinations.
- Complete observations per country.
- Coverage percentage per country.
- Missing pillar values responsible for exclusions.

The previously reported production coverage is 34 out of 40 observations, with Bangladesh reported at 2 out of 8. These values are hypotheses to verify against the exact audited output, not assumed test results.

Do not impute or fabricate missing observations during this test.

## 6. Test C — Normalization Sensitivity

Use `scripts/45_normalization_sensitivity.py` as the starting point.

First inspect the script's actual inputs, transformations, output paths, and side effects. Confirm that it preserves the baseline before executing it.

Where supported by the existing data and methodology, compare:

1. The current production normalization.
2. Full-sample min–max normalization.
3. Winsorized min–max normalization using P5–P95 bounds.
4. Pooled percentile-rank normalization.
5. Alternative Resilience reference zones using P5–P95 and P20–P80 bounds.

These are candidate specifications, not automatically approved alternatives. Each method must be applied only to compatible indicators and documented with its reference population, direction, boundaries, and missing-data rules.

Do not silently substitute a candidate method for the production baseline.

### Required sensitivity metrics

For each valid specification, report:

- Country-year score differences from the baseline.
- Mean and maximum absolute score differences.
- Country-level average scores.
- Country ranking and rank changes.
- Spearman rank correlation with the baseline ranking.
- Pearson correlation of comparable scores, where appropriate.
- Number of comparable observations.
- Missing-data and coverage differences.
- Whether any output was written to a production path.

Explain whether the comparison uses the same observations for every specification. If the eligible samples differ, disclose this limitation and avoid treating the results as directly equivalent.

## 7. Test D — Aggregation and Score-Domain Checks

Verify the existing production rules without changing them.

The current documented JESI weights are:

| Pillar | Weight |
|---|---:|
| Growth | 20% |
| Productivity | 25% |
| Connectivity | 20% |
| Resilience | 20% |
| Strategic Autonomy | 15% |

Verify that the weights sum to 100% and that the implementation uses the intended weighted geometric mean.

Check that:

- Pillar scores satisfy the production score-domain constraints.
- Country-year keys are unique.
- No unapproved imputation occurs.
- No invalid or infinite values enter the final calculation.
- The reported output can be traced to its input pillar scores.
- The actual aggregation agrees with an independent calculation within the declared tolerance.

Any failure should be investigated and documented before results are certified.

## 8. Test E — Automated Validation

Where feasible, add or run tests for:

- Duplicate country-year records.
- Missing required pillar scores.
- Out-of-range scores.
- Zero or negative inputs to geometric aggregation.
- Missing indicator observations.
- Tied values in percentile ranking.
- Constant-value indicator series.
- Reference-boundary behavior.
- Inconsistent country or year labels.
- Unexpected changes in output row counts.
- Accidental overwriting of production artifacts.

Tests must reflect the actual intended scoring specification. Do not alter production formulas merely to make a test pass.

## 9. Evidence and Deliverables

Store the audit evidence using the repository's established artifact conventions.

The evidence package should include:

1. Baseline commit and workflow identifiers.
2. Source-data manifest and checksums.
3. Baseline output manifest and checksums.
4. Reproducibility comparison report.
5. Missing-data and coverage report.
6. Normalization sensitivity comparison table.
7. Country ranking comparison.
8. Test results and any failed checks.
9. A record of production outputs before and after testing.
10. A list of unresolved questions and limitations.

If the evidence cannot be reproduced from the repository and identified inputs, label the relevant finding as unverified.

## 10. Decision Rules

### Outcome A — Baseline reproduced

Proceed to review normalization sensitivity results and documentation consistency.

### Outcome B — Baseline not reproduced

Stop sensitivity interpretation until differences in inputs, code, environment, or calculations are explained.

### Outcome C — Material sensitivity detected

Document which indicators, countries, years, or rankings are affected. Propose a separate methodology review rather than changing the production baseline immediately.

### Outcome D — Incomplete evidence

Record the missing evidence and keep the audit status pending.

No result should be labelled independently certified solely because the automated workflow passes.

## 11. Production Change Control

During Phase 3:

- Preserve the current production baseline.
- Do not overwrite published output files.
- Do not change production normalization or aggregation formulas.
- Do not impute or fabricate observations.
- Keep sensitivity outputs separate from production artifacts.
- Do not describe unexecuted tests as successful.
- Do not claim causality, predictive superiority, universal validity, or external endorsement without separate evidence.

Any proposed production change must be reviewed in a separate branch with a documented comparison against the preserved baseline.

## 12. Completion Criteria

Phase 3 is complete only when:

- The baseline commit and inputs are identified.
- Baseline reproduction has been executed and assessed.
- Coverage has been recomputed from actual outputs.
- The sensitivity script has been executed and its behavior verified.
- Candidate specifications have been compared using declared metrics.
- Production output integrity has been checked.
- Failures and limitations are documented.
- The evidence supports an explicit next-step decision.

## 13. Conclusion

Phase 3 is designed to establish reproducibility before any production methodology changes are considered.

The protocol distinguishes successful code execution from successful numerical reproduction and distinguishes sensitivity analysis from methodological approval.

Until the required tests are executed and the evidence is reviewed, the JESI baseline remains unverified by Phase 3.

---

**Audit status:** Pending execution  
**Production scoring changes:** None authorized  
**Baseline reproduction:** Not yet certified  
**Normalization sensitivity:** Not yet certified
