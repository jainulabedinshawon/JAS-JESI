JESI Normalization Audit — Phase 1

Status: Preliminary code and documentation review
Production score changes: None
Study countries: Bangladesh, India, Indonesia, Malaysia, Vietnam
Primary study period: 2016–2023
Documented benchmark period: 2015–2024

1. Audit Objective

This audit identifies discrepancies between the written JESI normalization methodology and the scoring implementation in the repository.

The objective is to establish an evidence-based, reproducible specification before making any changes to production scoring code.

This report records preliminary findings. It does not certify the entire pipeline or establish that the current JESI results are incorrect.

2. Preliminary Findings

2.1 Growth

Relevant implementation:

- "scripts/27_score_growth.py"
- "scripts/28_construct_growth_pillar.py"

The scoring implementation uses pooled percentile ranks. The rank calculation uses average ranks for tied observations, preserves missing values during ranking, and clips valid scores to the interval 0.001–1.0.

The scoring scripts define a 2015–2024 observation window.

Documentation discrepancy: "docs/methodology/normalization_protocol_v1.md" describes full-sample min–max normalization as the baseline method.

Required follow-up: Verify the exact observations used to calculate each indicator's percentile rank and confirm the effective study-window filter in the final index calculation.

2.2 Connectivity

Relevant implementation:

- "scripts/24_score_connectivity.py"
- "scripts/25_construct_connectivity_pillar.py"

The indicator-scoring implementation calculates empirical percentile scores using the proportion of non-missing pooled observations less than or equal to each observed value.

The baseline Connectivity pillar construction uses the arithmetic mean of three indicator scores.

The code expects five countries across 2015–2024, corresponding to 50 country-year rows.

Documentation discrepancy: The direction matrix describes min–max normalization for Connectivity indicators.

Required follow-up: Inspect the distribution-analysis script and confirm that its reference population matches the scoring implementation. Verify tie handling and missing-data behavior.

2.3 Productivity

Relevant implementation:

- "scripts/20_construct_productivity_pillar.py"
- The upstream P1 and P2 scoring scripts.

The pillar-construction script expects separate P1 and P2 scores for 2016–2023 and uses the arithmetic mean as its baseline aggregation method.

Required follow-up: Inspect both upstream scoring scripts to establish their exact transformations, reference populations, and handling of incomplete observations.

The indicator-level normalization method is not certified by this preliminary review.

2.4 Resilience

Relevant implementation:

- "scripts/11_score_resilience_pillar.py"
- "src/nonlinear_resilience_scoring.py"

The implementation uses:

- Positive min–max scoring for FX reserves/import cover.
- A nonlinear reference-zone score for government debt/GDP.
- A nonlinear reference-zone score for current-account balance/GDP.
- Arithmetic-mean aggregation for the three indicators.

The nonlinear scoring module contains fixed reference-zone boundaries:

- Government debt/GDP: 29.287000 to 77.458300.
- Current-account balance/GDP: -2.427516 to 3.881556.

Outside the applicable reference zone, the score declines exponentially according to normalized distance from the boundary.

Documentation requirement: Explain how the reference boundaries were estimated, identify the data used for calibration, and establish whether those bounds are fixed for the production specification.

2.5 Strategic Autonomy

Relevant implementation:

- "scripts/34_score_autonomy.py"
- "scripts/35_construct_autonomy_pillar.py"

The scoring script excludes observations missing any of its three required indicators before calculating empirical P10–P90 bounds.

Positive-direction normalization is used for the Economic Complexity Index and high-tech exports. Negative-direction normalization is used for import-product concentration.

The pillar-construction script calculates arithmetic and geometric alternatives.

Documentation requirement: Specify the reference population after exclusions, the percentile calculation convention, indicator directions, and the handling of zero scores in geometric aggregation.

3. Cross-Cutting Issues

The following questions remain open:

1. Do all pillars use the intended normalization reference population?
2. Are 2015 and 2024 used only for reference calibration, or do they also enter the reported comparison?
3. Are the study period and benchmark period clearly distinguished in the final index calculation?
4. Are indicator directions consistent between code and the direction matrix?
5. Are missing observations excluded consistently across all pillars?
6. Are zero scores and positive floors treated consistently before geometric aggregation?
7. Are reference bounds fixed, recalculated on each run, or recalculated from complete cases?
8. Can the published scores be independently reproduced from saved pillar scores?

4. Required Evidence Before Code Changes

Before changing production scoring, collect:

- The complete upstream scoring code for every indicator.
- The exact study-window filter in the final JESI calculation.
- Raw and processed data schemas and observation counts.
- The source and derivation of all fixed or empirical reference bounds.
- A baseline snapshot of final country-year scores and country averages.
- The current successful pipeline run and source commit.
- Automated tests covering ties, missing values, constant series, boundary values, and score-domain constraints.

5. Change-Control Rules

1. Do not overwrite the original production results.
2. Do not impute or fabricate missing observations.
3. Do not change normalization methods solely to make documentation appear consistent.
4. Treat any score-changing methodology revision as a separate specification.
5. Compare original and revised scores, country averages, ranks, and observation counts.
6. Run the complete validation pipeline before accepting a revised specification.
7. Document unresolved failures and limitations.
8. Do not describe a proposed change as implemented until the code, tests, and resulting outputs have been verified.

6. Next Audit Phase

Phase 2 will complete the indicator-level specification, inspect the upstream Productivity scripts, reconcile the study period with the normalization reference population, and establish a reproducible original-results baseline.

No production scoring change is authorized by this report.
