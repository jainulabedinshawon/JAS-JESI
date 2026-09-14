JAS Unified Economic Strength Index (JESI)

Normalization & Scoring Protocol — Version 1.0

Project: JAS Unified Economic Strength Index (JESI)
Framework: A Data-Driven Framework for Measuring Structural Economic Strength
Benchmark Countries: Bangladesh, India, Viet Nam, Indonesia, Malaysia
Baseline Benchmark Period: 2015–2024

---

1. Purpose

Normalization converts heterogeneous economic indicators into a common scale so that indicators measured in different units can be aggregated into pillar scores and, ultimately, into the JAS Unified Economic Strength Index (JESI).

The normalization framework is designed to preserve the economic interpretation of each indicator while allowing systematic robustness testing across alternative statistical specifications.

---

2. Baseline Benchmark Period

The baseline empirical comparison period for JESI Version 1.0 is:

2015–2024

The same benchmark period will be applied across all five countries and, subject to data availability, across all five pillars.

The benchmark period is distinct from historical back-testing periods. Historical shock periods may be examined separately to evaluate whether JESI is associated with economic resilience, deterioration, or recovery.

---

3. Baseline Normalization Method

The baseline normalization method is full-sample min–max normalization.

For indicators where a higher value represents stronger structural performance:

[
N_i = \frac{X_i-X_{min}}{X_{max}-X_{min}}
]

where:

- X_i = observed value
- X_{min} = minimum value in the defined benchmark sample
- X_{max} = maximum value in the defined benchmark sample
- N_i = normalized score between 0 and 1

For indicators where a lower value represents stronger structural performance:

[
N_i = \frac{X_{max}-X_i}{X_{max}-X_{min}}
]

All normalized indicators are therefore expressed on a common 0–1 scale.

---

4. Indicator Direction

Indicator direction shall be determined using economic theory and the conceptual purpose of each JESI pillar.

The baseline direction classifications are documented separately in the JESI Indicator Direction Matrix.

A higher raw value will not automatically be treated as better for every indicator.

Particular care will be applied to indicators for which the economic relationship may be nonlinear or target-dependent.

---

5. Nonlinear and Target-Optimal Indicators

Some economic indicators cannot be interpreted reliably using a simple monotonic transformation.

In particular:

- Government Gross Debt / GDP
- Current Account Balance / GDP

may exhibit nonlinear relationships with economic resilience.

For such indicators, JESI will use theoretically justified transformations rather than automatically assuming that either the maximum or minimum observed value represents optimal performance.

Alternative specifications will be evaluated through robustness testing.

---

6. Government Debt

Government Gross Debt / GDP will not be classified under a simple universal rule that lower debt always implies greater resilience.

Debt sustainability depends on factors including:

- economic growth,
- interest rates,
- debt maturity,
- currency composition,
- fiscal capacity,
- refinancing conditions,
- and broader macroeconomic conditions.

Therefore, the baseline JESI methodology will evaluate a target/penalty-based transformation for government debt, with alternative specifications tested for robustness.

---

7. Current Account Balance

Current Account Balance / GDP will not be treated as a simple "higher is always better" or "lower is always better" indicator.

Both persistent large deficits and unusually large surpluses may reflect structural imbalances under different circumstances.

The baseline specification will therefore evaluate distance from a theoretically justified reference zone.

A generic target-distance representation is:

[
D_i = |CA_i-CA^*|
]

where:

- CA_i = observed current account balance
- CA^* = reference or target level
- D_i = distance from the reference level

Greater distance from the reference zone will generally imply a lower resilience score, subject to the final specification and robustness testing.

---

8. Outlier Treatment

The baseline specification will use full-sample min–max normalization without arbitrary outlier removal.

Robustness analysis will evaluate alternative approaches including:

1. Winsorized min–max normalization
2. Percentile-based normalization
3. Rank-based normalization

The purpose is to determine whether JESI results depend materially on extreme observations.

---

9. Benchmark Consistency

The benchmark definition, country sample, time period, transformation rules, and direction assumptions shall be documented and kept consistent within each comparable JESI specification.

Any change in benchmark construction will be explicitly identified as an alternative specification.

---

10. Missing Data

Missing observations will not be silently replaced.

Potential approaches include:

- complete-case analysis,
- limited interpolation where economically and statistically appropriate,
- cross-sectional imputation where justified,
- minimum-data requirements for pillar construction,
- and explicit uncertainty flags.

The impact of missing-data treatment will be examined through robustness analysis.

---

11. Pillar Aggregation

After normalization, indicators will be aggregated into the five JESI pillars.

Two principal aggregation approaches will be evaluated:

Arithmetic aggregation

[
P_j = \sum_i w_iN_i
]

Geometric aggregation

[
P_j = \prod_i N_i^{w_i}
]

The baseline aggregation method will be selected and documented after methodological and robustness evaluation.

---

12. JESI Aggregation

The Master Version 1.0 strategic weights are:

- Growth = 20%
- Productivity = 25%
- Connectivity = 20%
- Resilience = 20%
- Strategic Autonomy = 15%

The weighted multiplicative formulation is:

[
JESI =
100 \times
G^{0.20}
\times
P^{0.25}
\times
C^{0.20}
\times
R^{0.20}
\times
A^{0.15}
]

where each pillar score lies on a normalized 0–1 scale.

Alternative weighting and aggregation specifications will be evaluated during robustness testing.

---

13. Robustness Framework

JESI results will be tested under alternative methodological specifications, including:

- alternative pillar weights,
- equal weights,
- statistical weighting,
- alternative normalization methods,
- alternative benchmark periods,
- alternative outlier treatments,
- alternative indicator sets,
- alternative missing-data treatments,
- alternative pillar aggregation methods,
- and pillar exclusion tests.

The purpose is to determine whether the principal conclusions remain reasonably stable under plausible methodological alternatives.

---

14. Reproducibility

All normalization procedures should be implemented through reproducible scripts.

The computational pipeline should document:

- source database,
- indicator code,
- country code,
- observation year,
- unit,
- transformation,
- direction,
- normalization method,
- missing-data treatment,
- and benchmark definition.

Raw international data should remain separate from processed and normalized datasets.

---

15. Methodological Principle

JESI does not assume that one statistical transformation is universally correct.

The baseline specification provides a transparent reference model, while alternative specifications are used to evaluate sensitivity and robustness.

The objective is not to produce a single unquestionable number, but to construct a transparent, reproducible, theoretically grounded and empirically testable measure of structural economic strength.

---

Status: Draft for Version 1.0 methodological implementation

Next methodological component: JESI Indicator Direction Matrix
