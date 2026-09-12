JAS Unified Economic Strength Index (JESI)

A Data-Driven Framework for Measuring Structural Economic Strength

JAS-JESI (JAS Unified Economic Strength Index) is a proposed multidimensional analytical framework designed to assess the structural strength of an economy beyond conventional measures of economic size such as Gross Domestic Product (GDP).

The framework conceptualizes economic strength as the interaction of five structural dimensions:

«Growth × Productivity × Connectivity × Resilience × Strategic Autonomy»

The project aims to translate this conceptual framework into a reproducible empirical index using internationally comparable economic data and transparent statistical methodology.

---

Abstract

Conventional measures such as GDP primarily describe the size of an economy. However, economic size alone does not fully capture an economy's productive efficiency, global integration, capacity to absorb shocks, or ability to preserve strategic economic choice.

The JAS Unified Economic Strength Index (JESI) proposes a multidimensional framework based on five pillars: Growth (G), Productivity (P), Connectivity (C), Resilience (R), and Strategic Autonomy (A).

The Master Version 1.0 specifies a weighted multiplicative index:

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

Each pillar is constructed from normalized economic indicators.

This repository develops the empirical implementation of the framework using real-world international economic data. The research program includes data acquisition, indicator construction, normalization, index calculation, cross-country comparison, historical back-testing, sensitivity analysis, alternative weighting schemes, and robustness testing.

The framework is explicitly treated as a proposed analytical framework, rather than an established international statistical index. Its empirical validity, predictive usefulness, and robustness remain subjects of investigation.

---

1. Research Motivation

GDP is one of the most important measures of economic activity, but GDP size and structural economic strength are not equivalent concepts.

An economy may have:

- large GDP but weak productivity,
- rapid growth but low resilience,
- strong global connectivity but excessive external dependency,
- substantial resources but limited economic complexity,
- or high income but significant strategic vulnerabilities.

JESI therefore asks a broader question:

«How strong is the underlying economic system, rather than simply how large is it?»

The framework seeks to evaluate an economy's capacity to:

1. Grow,
2. Produce efficiently,
3. Connect to global markets and networks,
4. Absorb economic shocks,
5. Preserve strategic economic choice.

---

2. Research Question

The central research question is:

«Can a multidimensional index combining Growth, Productivity, Connectivity, Resilience, and Strategic Autonomy provide a meaningful empirical measure of structural economic strength across countries and over time?»

Secondary questions include:

- Does JESI provide information that GDP size alone does not capture?
- Are countries with higher JESI scores more resilient during major economic shocks?
- How sensitive are country rankings to indicator selection and weighting?
- Does the proposed multiplicative structure outperform simpler aggregation methods?
- Are the five pillars empirically distinguishable?
- How stable is JESI across different periods and normalization methods?

---

3. Conceptual Framework

JESI consists of five structural pillars.

G — Growth

Measures the economy's capacity to expand and improve economic welfare.

Proposed indicators:

- Real GDP Growth Rate
- GNI per Capita Growth

Weight: 20%

---

P — Productivity

Measures the efficiency with which labor and other productive factors generate economic output.

Proposed indicators:

- GDP per Person Employed
- Total Factor Productivity (TFP) Growth

Weight: 25%

Productivity receives the highest initial strategic weight because sustained improvements in living standards and productive capacity ultimately depend heavily on efficiency and technological capability.

---

C — Connectivity

Measures integration with international trade, investment, technology and information networks.

Proposed indicators:

- Trade Openness
- FDI Inflows
- ICT & Global Integration

Weight: 20%

Connectivity represents access to markets, capital, technology, knowledge and international economic networks.

However, high connectivity does not automatically imply high resilience. Excessive concentration or dependency may increase vulnerability. This relationship will therefore be examined empirically.

---

R — Resilience

Measures the ability of an economy to absorb and withstand economic and external shocks.

Proposed indicators:

- Foreign Exchange Reserves / Import Cover
- Public Debt / GDP
- Current Account Position

Weight: 20%

The empirical implementation will avoid assuming that every resilience indicator has a simple linear "higher is always better" relationship.

For example, debt sustainability depends on factors including economic growth, interest rates, maturity structure, currency composition and fiscal capacity.

Similarly, both persistent current-account deficits and unusually large surpluses may reflect structural distortions. Alternative specifications will therefore be evaluated.

---

A — Strategic Autonomy

Measures an economy's capacity to preserve strategic economic choice while remaining globally connected.

Proposed indicators:

- Economic Complexity Index (ECI)
- High-Tech Exports as % of Manufactured Exports
- Critical Import Concentration

Weight: 15%

Strategic autonomy does not mean economic isolation or autarky.

It refers to the ability to maintain productive capability, technological capacity and economic choice while reducing excessive dependence on concentrated critical external sources.

---

4. Core Mathematical Specification

The Master Version 1.0 is:

[
\boxed{
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
}
]

where:

[
0 \leq G,P,C,R,A \leq 1
]

The weights satisfy:

[
0.20+0.25+0.20+0.20+0.15=1
]

The multiplicative structure means that weaknesses in one structural dimension can materially reduce the aggregate index.

---

5. Indicator-Level Construction

Each pillar is constructed from its underlying normalized indicators.

In general:

[
Pillar_j=f(X_{1j},X_{2j},...,X_{nj})
]

The initial implementation will evaluate both:

Arithmetic aggregation

[
Pillar =
\sum_{i=1}^{n} w_iX_i
]

and:

Geometric aggregation

[
Pillar =
\prod_{i=1}^{n}X_i^{w_i}
]

The preferred method will be determined through methodological and robustness testing rather than assumed in advance.

---

6. Normalization

Because the underlying indicators have different units and scales, they must be transformed into a common range.

Positive-direction indicators

For indicators where higher values are structurally preferable:

[
X_{norm}=
\frac{X-X_{min}}
{X_{max}-X_{min}}
]

Negative-direction indicators

For indicators where lower values are structurally preferable:

[
X_{norm}=
\frac{X_{max}-X}
{X_{max}-X_{min}}
]

The empirical implementation will document the directional assumption for every indicator.

---

7. Benchmark and Outlier Protocol

Simple minimum-maximum normalization can be highly sensitive to extreme observations.

Therefore, the empirical project will test alternative approaches including:

- Full-sample min-max normalization
- Winsorized min-max normalization
- Percentile-based normalization
- Rank-based approaches
- Fixed benchmark ranges where theoretically justified

The benchmark period will be documented and kept consistent for comparable cross-country analysis.

---

8. Weighting Methodology

Master Version 1.0 uses the following strategic baseline:

Pillar| Weight
Growth| 20%
Productivity| 25%
Connectivity| 20%
Resilience| 20%
Strategic Autonomy| 15%

Alternative specifications will be tested.

Model A — JAS Strategic Weights

20 / 25 / 20 / 20 / 15

Model B — Equal Weights

20 / 20 / 20 / 20 / 20

Model C — Statistical Weights

Potential methods include:

- Principal Component Analysis (PCA)
- Factor-based approaches
- Multivariate statistical methods
- Predictive-validity-based weighting

Statistical weighting will be treated as an alternative empirical specification rather than automatically replacing theoretical weights.

---

9. Data Sources

The empirical implementation will prioritize internationally comparable datasets.

Potential sources include:

- World Bank
- International Monetary Fund (IMF)
- UNCTAD
- Other recognized international statistical databases

The repository will document:

- Indicator definitions
- Source databases
- API endpoints where applicable
- Retrieval dates
- Country codes
- Units
- Transformation procedures
- Missing-data treatment

---

10. Empirical Strategy

The research pipeline will follow:

Raw International Data
        ↓
Data Cleaning
        ↓
Indicator Construction
        ↓
Missing-Data Treatment
        ↓
Normalization
        ↓
Pillar Aggregation
        ↓
JESI Calculation
        ↓
Cross-Country Comparison
        ↓
Historical Back-Testing
        ↓
Sensitivity Analysis
        ↓
Robustness Testing

The objective is to make the entire analytical process reproducible.

---

11. Historical Back-Testing

The framework will be evaluated against historical economic shocks.

Potential episodes include:

- Global Financial Crisis
- Major commodity-price shocks
- COVID-19 economic shock
- Foreign-exchange and balance-of-payments crises
- Major country-specific economic stress episodes

The analysis will investigate whether pre-shock JESI values are associated with subsequent economic resilience.

The project will not assume causality merely because a statistical association exists.

---

12. Predictive and Explanatory Testing

Potential empirical outcomes include:

Cross-sectional analysis

[
JESI_{i,t}
]

will be compared across countries.

Time-series analysis

[
JESI_{i,t}
]

will be examined across years.

Shock-response analysis

Pre-shock JESI may be compared with subsequent:

- GDP contraction
- investment performance
- employment performance
- inflation pressure
- external-balance stress
- recovery speed

Where sufficient data exist, regression and out-of-sample tests may be used.

---

13. Robustness Testing

The framework will be tested under alternative assumptions.

Key tests include:

- Alternative weights
- Alternative normalization methods
- Alternative aggregation methods
- Alternative indicator sets
- Different benchmark periods
- Outlier treatment
- Missing-data treatment
- Pillar exclusion tests
- Country-sample changes

A major objective is to determine whether conclusions remain reasonably stable when methodological assumptions change.

---

14. Missing Data

International datasets frequently contain incomplete observations.

The empirical implementation will document missing-data procedures rather than silently replacing missing values.

Possible approaches include:

- Complete-case analysis
- Limited interpolation for appropriate time-series variables
- Cross-sectional imputation where justified
- Pillar-level minimum data requirements
- Explicit uncertainty flags

No imputation method will be applied universally without evaluating its effect on results.

---

15. GDP Size vs Economic Strength

A central proposition of JESI is:

«GDP SIZE ≠ ECONOMIC STRENGTH»

GDP primarily asks:

«How large is the economy?»

JESI asks:

«How strong is the economic system?»

An economy can therefore have:

- high GDP but low resilience,
- high growth but low productivity,
- high connectivity but excessive concentration,
- or moderate GDP but strong structural resilience and autonomy.

JESI is designed to capture these multidimensional differences.

---

16. Research Hypotheses

The empirical project may test the following hypotheses.

H1 — Structural Strength

Higher JESI is positively associated with broader measures of structural economic performance.

H2 — Resilience

Higher JESI is associated with smaller economic deterioration during major external shocks.

H3 — Recovery

Higher JESI is associated with faster post-shock economic recovery.

H4 — Beyond GDP

JESI provides information about economic resilience and structure that is not fully captured by GDP size alone.

H5 — Robustness

The principal cross-country conclusions remain reasonably stable under alternative weighting and normalization specifications.

These hypotheses are empirical propositions and are not treated as established facts.

---

17. Limitations

JESI has several potential limitations.

Measurement limitations

Some concepts, particularly strategic autonomy and economic connectivity, cannot be perfectly represented by a small number of indicators.

Data limitations

International datasets may contain:

- missing observations,
- revisions,
- methodological differences,
- inconsistent time coverage.

Weighting limitations

The initial weights are theoretically motivated rather than empirically proven universal weights.

Causality limitations

A correlation between JESI and economic outcomes does not by itself establish causation.

Normalization limitations

Country rankings can change depending on benchmark selection and treatment of outliers.

These limitations will be explicitly evaluated rather than hidden.

---

18. Expected Research Contribution

The project aims to contribute a structured framework for examining economic strength as a multidimensional system.

Its potential contributions include:

1. Moving beyond GDP-size comparisons.
2. Combining productive, external, resilience and strategic dimensions.
3. Providing a transparent mathematical specification.
4. Developing reproducible country-level calculations.
5. Testing the framework against historical economic shocks.
6. Evaluating methodological robustness.
7. Creating an open computational implementation.

The ultimate value of JESI will depend on the results of empirical validation.

---

19. Reproducibility

A core objective of this repository is:

«Retrieve → Process → Calculate → Reproduce → Evaluate»

The codebase will document the transformation from source data to final JESI scores.

Where permitted by data-provider licensing, users should be able to reproduce the analysis using the repository's code and documented data sources.

Raw datasets subject to third-party licensing will not necessarily be redistributed; instead, the repository may provide retrieval scripts and source references.

---

20. Planned Repository Structure

JAS-JESI/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── methodology/
│   └── JESI_Master_V1.0.pdf
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── data_download.py
│   ├── data_cleaning.py
│   ├── normalization.py
│   ├── pillar_construction.py
│   ├── jesI_calculation.py
│   └── robustness_tests.py
│
├── notebooks/
│   ├── JESI_Data_Exploration.ipynb
│   └── JESI_Backtesting.ipynb
│
└── results/
    ├── country_scores.csv
    ├── rankings.csv
    └── charts/

---

21. Development Roadmap

Master Version 1.0

Theoretical Specification

- Five-pillar architecture
- Mathematical formulation
- Initial indicators
- Strategic weighting

Empirical Version 1.1

Data Implementation

- World Bank / IMF data pipeline
- Automated data retrieval
- Indicator construction
- Normalization
- Country-level JESI calculation

Validation Version 1.5

Empirical Testing

- Cross-country analysis
- Historical back-testing
- Sensitivity analysis
- Alternative weighting
- Robustness testing

JESI Version 2.0

Empirically Refined Framework

Potential improvements based on evidence:

- Validated indicator set
- Refined aggregation methodology
- Empirically evaluated weighting
- Improved resilience measures
- Expanded country/time coverage
- Out-of-sample validation

---

22. Research Status

«JESI is a proposed JAS analytical framework, not an established international statistical index.»

The framework has not yet been empirically validated as a universally superior measure of economic strength.

Claims regarding predictive power, causal relationships, or superiority over existing indices should only be made after appropriate statistical testing.

---

23. Guiding Principle

«An economy should not be judged by its size alone. Its true strength lies in its ability to grow, produce efficiently, connect globally, absorb shocks and preserve strategic economic choice.»

— JAS

---

License

The source code in this repository is released under the MIT License.

Methodological text, documentation and future research outputs may be subject to separate attribution and publication terms where applicable.