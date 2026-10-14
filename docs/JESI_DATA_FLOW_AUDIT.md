JESI Data-Flow Audit

Project: JAS-JESI — JAS Unified Economic Strength Index
Methodology: Master Version 1.0
Purpose: Document the scoring contract and define the scope of end-to-end regression tests.

1. Current production scoring contract

The production scoring module is "src/jesi_calculation.py".

Pillar| Key| Fixed weight
Growth| G| 0.20
Productivity| P| 0.25
Connectivity| C| 0.20
Resilience| R| 0.20
Strategic Autonomy| A| 0.15
Total| | 1.00

The scorer requires exactly five pillar scores. Each score must be between 0 and 1.

The Master Version 1.0 formula is:

"JESI = 100 × G^0.20 × P^0.25 × C^0.20 × R^0.20 × A^0.15"

The weights are fixed in the current scoring module. The scorer does not itself calculate PCA eigenvectors or derive weights from explained-variance ratios.

2. Normalization contract

The module "src/normalization.py" provides scalar normalization functions.

- "normalize_positive(value, minimum, maximum)": higher values are better.
- "normalize_negative(value, minimum, maximum)": lower values are better.
- "normalize_positive_clipped(...)": positive-direction normalization clipped to [0, 1].
- "normalize_negative_clipped(...)": negative-direction normalization clipped to [0, 1].

The functions reject a zero-width range where "minimum == maximum".

3. Test coverage added by this change

"tests/test_end_to_end_pipeline.py" checks:

1. The five fixed pillar weights and their sum.
2. Normalization direction and endpoint behavior.
3. Rejection of zero-width normalization ranges.
4. Clipping of normalized values outside the [0, 1] range.
5. A synthetic indicator → normalization → pillar → JESI scoring path.
6. Rejection of missing, extra, and out-of-range pillar scores.
7. Whether changing each pillar changes the final score.
8. Zero-score behavior under geometric aggregation.

The synthetic fixture uses an arithmetic mean to construct test pillars. This is a testing choice, not a claim that all empirical pillar scripts use that aggregation method.

4. Full empirical pipeline: further audit required

These tests do not prove that every real input dataset is correctly connected to every production scoring script. A separate code review should trace:

1. Raw data acquisition and source provenance.
2. Cleaning, missing values, outliers, and country-year keys.
3. Indicator direction and normalization.
4. Construction of all five empirical pillars.
5. Joins, duplicate handling, and complete-case rules.
6. Final JESI calculation and output generation.
7. Audit logs and reproducibility metadata.

Any missing-value or outlier policy should be documented from the actual implementation rather than assumed.

5. PCA and reproducibility

PCA-specific tests must target the actual PCA implementation used by the approved methodology. They should check component dimensions, explained-variance ratios, input ordering, and numerical stability. Eigenvector comparisons should account for the fact that component signs may flip without changing the underlying solution.

Do not claim that PCA-derived weights feed the production scorer unless a verified code path demonstrates this connection. If PCA is introduced into production later, record the chosen solver, any required random seed, and dependency versions.

6. Run the tests

From the repository root:

PYTHONPATH=. pytest -q tests/test_end_to_end_pipeline.py

Then run the existing test suite:

PYTHONPATH=. pytest -q

A local pass is not a substitute for a successful GitHub Actions run.

7. Scope of this PR

This change adds tests and documentation only. It does not change production scoring, empirical results, pillar weights, or the approved methodology.

The PR should be reviewed and merged only after the new tests and the repository's existing CI checks pass.
