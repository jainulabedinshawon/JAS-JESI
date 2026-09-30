JAS Unified Economic Strength Index (JESI)

A Data-Driven Framework for Measuring Structural Economic Strength

JAS-JESI (JAS Unified Economic Strength Index) is a proposed multidimensional analytical framework designed to assess structural economic strength beyond conventional measures of economic size such as Gross Domestic Product (GDP).

The framework conceptualizes economic strength through five structural dimensions:

«Growth × Productivity × Connectivity × Resilience × Strategic Autonomy»

The project is being developed as a reproducible empirical research framework using internationally comparable economic data and transparent statistical methodology.

JESI is explicitly treated as a proposed analytical framework, not as an established international statistical index. Its empirical validity, robustness, explanatory usefulness, and methodological stability remain subjects of investigation.

---

1. Research Motivation

GDP is one of the most important measures of economic activity, but GDP size and structural economic strength are not equivalent concepts.

An economy may have:

- large GDP but weak productivity,
- rapid growth but low resilience,
- strong global connectivity but excessive external dependency,
- substantial resources but limited economic complexity,
- or high income but significant structural vulnerabilities.

JESI therefore asks a broader question:

«How strong is the underlying economic system, rather than simply how large is it?»

The framework evaluates five dimensions:

1. Growth
2. Productivity
3. Connectivity
4. Resilience
5. Strategic Autonomy

---

2. Research Question

The central research question is:

«Can a multidimensional index combining Growth, Productivity, Connectivity, Resilience, and Strategic Autonomy provide a meaningful empirical measure of structural economic strength across countries and over time?»

The empirical research program examines:

- whether the five pillars are empirically distinguishable,
- whether indicators contain substantial redundancy,
- how sensitive results are to normalization choices,
- how sensitive results are to pillar weights,
- how sensitive results are to aggregation methods,
- and how the resulting index behaves in historical validation exercises.

These are empirical questions and are not treated as established conclusions in advance.

---

3. Conceptual Framework

JESI consists of five structural pillars.

G — Growth

Measures the economy's capacity to expand.

Proposed indicators:

- Real GDP Growth Rate
- GNI per Capita Growth

Strategic weight: 20%

---

P — Productivity

Measures the efficiency with which productive resources generate economic output.

Proposed indicators:

- GDP per Person Employed
- Total Factor Productivity (TFP) Growth

Strategic weight: 25%

Productivity receives the highest initial strategic weight in Master Version 1.0. This is a theoretical specification and is subject to empirical weight-sensitivity testing.

---

C — Connectivity

Measures integration with international trade, investment, technology, and information networks.

Proposed indicators:

- Trade Openness
- FDI Inflows
- ICT & Global Integration

Strategic weight: 20%

Connectivity represents access to markets, capital, technology, knowledge, and international economic networks.

High connectivity is not automatically interpreted as high resilience. Concentration and external dependency are examined separately.

---

R — Resilience

Measures the capacity of an economy to absorb and withstand economic and external shocks.

Proposed indicators:

- Foreign Exchange Reserves / Import Cover
- Public Debt / GDP
- Current Account Position

Strategic weight: 20%

The empirical implementation does not assume that every resilience indicator has a simple linear "higher is always better" relationship.

---

A — Strategic Autonomy

Measures the capacity to preserve strategic economic choice while remaining globally connected.

Proposed indicators:

- Economic Complexity Index (ECI)
- High-Tech Exports
- Import Product Concentration

Strategic weight: 15%

Strategic autonomy does not mean economic isolation or autarky.

It refers to productive capability, technological capacity, diversification, and the ability to preserve economic choice while reducing excessive dependence on concentrated external sources.

---

4. Core Mathematical Specification

Master Version 1.0 specifies:

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

where:

[
0 \leq G,P,C,R,A \leq 1
]

and:

[
0.20+0.25+0.20+0.20+0.15=1
]

The production JESI currently uses a weighted geometric aggregation.

The research-validation layer separately evaluates the sensitivity of the production results to alternative methodological specifications.

---

5. Indicator-Level Construction

Each pillar is constructed from its underlying normalized indicators.

In general:

[
Pillar_j=f(X_{1j},X_{2j},...,X_{nj})
]

The methodological framework considers alternative aggregation approaches, including arithmetic and geometric aggregation.

The production specification is preserved during research-validation analysis.

Validation scripts do not automatically replace the production methodology.

---

6. Normalization

Because the underlying indicators have different units and scales, they must be transformed into a common range.

For positive-direction indicators:

[
X_{norm}=
\frac{X-X_{min}}
{X_{max}-X_{min}}
]

For negative-direction indicators:

[
X_{norm}=
\frac{X_{max}-X}
{X_{max}-X_{min}}
]

The directional assumption for each indicator is documented in the empirical implementation.

Normalization sensitivity is evaluated separately in Script 45.

---

7. Weighting Methodology

Master Version 1.0 uses the following baseline pillar weights:

Pillar| Weight
Growth| 20%
Productivity| 25%
Connectivity| 20%
Resilience| 20%
Strategic Autonomy| 15%

The research-validation program tests alternative specifications without automatically replacing the production weights.

Current weight-sensitivity analysis is implemented in Script 46.

---

8. Data Sources

The empirical implementation prioritizes internationally comparable datasets.

Current and intended sources include:

- World Bank
- International Monetary Fund (IMF)
- UNCTAD
- Other recognized international statistical databases where required

The repository documents, where applicable:

- indicator definitions,
- source databases,
- retrieval procedures,
- country codes,
- units,
- transformations,
- missing-data treatment,
- and validation procedures.

Raw datasets subject to third-party licensing are not necessarily redistributed.

---

9. Empirical Research Pipeline

The empirical implementation follows the general process:

International Source Data
        ↓
Data Acquisition
        ↓
Data Cleaning
        ↓
Indicator Construction
        ↓
Normalization
        ↓
Pillar Construction
        ↓
Production JESI Calculation
        ↓
Research Validation
        ↓
Robustness Analysis
        ↓
Historical Validation
        ↓
Final Methodological Judgment

The production calculation and research-validation layers are kept conceptually separate.

---

10. Research-Validation Sequence

The current research-validation sequence is:

Script 44 — Indicator Redundancy / Correlation

"scripts/44_analyze_indicator_redundancy.py"

Purpose:

- evaluate relationships among persisted indicator-score representations,
- calculate Pearson and Spearman relationships,
- retain pairwise sample sizes,
- examine missingness,
- identify potential redundancy-review flags.

This is a research-validation layer only.

It does not automatically remove indicators, reweight pillars, impute observations, or modify production JESI.

---

Script 45 — Normalization Sensitivity

"scripts/45_normalization_sensitivity.py"

Purpose:

- evaluate sensitivity to alternative normalization specifications,
- compare the production baseline with alternative normalization approaches,
- examine country-year and country-level sensitivity,
- assess rank relationships across specifications.

The production normalization is not automatically replaced.

---

Script 46 — Weight Sensitivity

"scripts/46_weight_sensitivity.py"

Purpose:

- evaluate sensitivity to alternative pillar-weight specifications,
- compare the Master Version 1.0 strategic weights with alternative weighting structures,
- examine country-year results and rank relationships.

The production weights remain unchanged.

---

Script 47 — Aggregation Sensitivity

"scripts/47_aggregation_sensitivity.py"

Purpose:

- evaluate sensitivity to alternative aggregation functions,
- preserve the same pillar scores,
- preserve the production weights,
- preserve the production normalization,
- preserve the documented missing-data treatment.

The production aggregation method is not automatically replaced.

---

Script 48 — Historical Validation

"scripts/48_historical_validation.py"

Purpose:

- reconstruct the production JESI historical series,
- evaluate historical event windows,
- decompose JESI changes into pillar contributions,
- compare JESI with independent World Bank outcomes,
- calculate level and first-difference Spearman correlations.

Historical validation is treated as empirical validation evidence rather than proof of causality.

---

11. Methodological Sequence

The methodological sequence is intentionally preserved:

«JESI Concept → Pillar validity → Indicator validity → Redundancy/Correlation → Normalization sensitivity → Weight sensitivity → Aggregation sensitivity → Historical validation → Final methodological judgment»

This sequence is a core methodological requirement of the project.

Research-validation scripts are not intended to bypass this sequence or prematurely produce a final methodological judgment.

---

12. Research-Validation Principles

The research-validation layer follows several safeguards:

- No fabricated observations.
- No silent replacement of missing observations.
- No automatic indicator deletion.
- No automatic reweighting.
- No automatic production-methodology replacement.
- No undocumented methodological changes.
- No interpretation of correlation as proof of causality.
- Production JESI remains separate from alternative validation specifications.

Where a sensitivity analysis identifies an issue, the finding is treated as methodological evidence to be reviewed rather than automatically converted into a production change.

---

13. Historical Validation

Historical validation evaluates the behavior of the existing production JESI over the documented historical sample.

The analysis may examine:

- historical economic stress periods,
- changes in JESI over time,
- pillar-level contributions,
- relationships with independent economic outcomes,
- and event-window behavior.

Historical association does not by itself establish causality.

The historical-validation layer therefore reports empirical relationships together with their sample and methodological limitations.

---

14. Robustness Testing

The broader JESI robustness program includes evaluation of:

- indicator redundancy,
- normalization sensitivity,
- weight sensitivity,
- aggregation sensitivity,
- missing-data treatment,
- alternative specifications,
- sample sensitivity,
- historical validation,
- and other methodological assumptions where appropriate.

The objective is to determine how stable the empirical results are when methodological assumptions change.

---

15. Missing Data

International datasets frequently contain incomplete observations.

The repository documents missing-data procedures rather than silently replacing missing values.

Depending on the specific research-validation task, the project may use:

- complete-case analysis,
- explicitly documented time-series procedures where justified,
- cross-sectional procedures where justified,
- pillar-level data requirements,
- explicit missingness reporting.

No universal imputation method is assumed.

Research-validation scripts may deliberately restrict analysis to complete-case observations when required by the methodological design.

---

16. GDP Size vs Economic Strength

A central proposition of JESI is:

«GDP SIZE ≠ ECONOMIC STRENGTH»

GDP primarily describes the size of an economy.

JESI is designed to examine a broader structural combination of:

- growth,
- productivity,
- connectivity,
- resilience,
- and strategic autonomy.

The empirical research program is intended to determine how useful this multidimensional representation is rather than assuming its superiority in advance.

---

17. Research Hypotheses

The project may empirically examine propositions concerning:

H1 — Structural Strength

Whether higher JESI is associated with broader measures of structural economic performance.

H2 — Resilience

Whether higher JESI is associated with smaller economic deterioration during selected external shocks.

H3 — Recovery

Whether higher JESI is associated with faster post-shock recovery.

H4 — Beyond GDP

Whether JESI contains structural information not fully represented by GDP size alone.

H5 — Robustness

Whether principal empirical relationships remain reasonably stable under alternative methodological specifications.

These are empirical propositions, not established findings.

---

18. Final Empirical-Validation Status

Current project stage: Empirical Validation Program Completed — Master Version 1.0

The documented empirical validation sequence for JESI Master Version 1.0 has been completed for the current production specification, sample, data coverage, and validation design.

The completed validation sequence was:

1. Indicator redundancy and correlation analysis — Script 44
2. Normalization sensitivity analysis — Script 45
3. Pillar-weight sensitivity analysis — Script 46
4. Aggregation sensitivity analysis — Script 47
5. Historical validation — Script 48

The validation program preserved the production JESI methodology and did not automatically modify production indicators, pillar weights, normalization, aggregation, or missing-data treatment.

The completed validation program provides empirical evidence relevant to the framework's internal coherence, methodological robustness, and historical empirical relevance within the tested research design. The evidence remains conditional on the documented five-country, 2016–2023 sample, available data, complete-case requirements, and external validation measures.

Historical associations are not interpreted as causal effects. The current evidence does not establish universal validity, predictive superiority, or superiority over alternative economic indices.

Final Methodological Status

«JESI is an empirically supported but not universally validated multidimensional framework for assessing structural economic strength.»

This is the final methodological judgment for the current Master Version 1.0 empirical validation phase.

The completion of the empirical validation phase does not mean that JESI is an established international statistical index or that future scientific testing is unnecessary.

Future research may extend the evidence base through broader country coverage, longer historical periods, additional external outcomes, predictive testing, independent replication, and further methodological research.

The completion of the empirical validation phase therefore represents a methodological milestone, not the end of scientific testing.

---

19. Reproducibility

A core objective of the repository is:

«Retrieve → Process → Calculate → Reproduce → Evaluate»

The codebase is structured so that the transformation from source data to production JESI and research-validation outputs can be inspected and reproduced.

Where permitted by data-provider licensing, users should be able to reproduce the analysis using the repository's code and documented data sources.

---

20. Installation

Clone the repository:

git clone https://github.com/jainulabedinshawon/JAS-JESI.git
cd JAS-JESI

Create a virtual environment:

python -m venv .venv

Activate it.

Windows

.venv\Scripts\activate

Linux / macOS

source .venv/bin/activate

Install the repository dependencies:

python -m pip install --upgrade pip
pip install -r requirements.txt

The research-validation scripts additionally use scientific-computing dependencies:

pip install numpy scipy

---

21. Running the Production Validation Pipeline

The main production workflow is:

GitHub Actions → Final JESI Pipeline

It is designed to validate the production repository pipeline and related outputs.

The production pipeline should not be confused with the separate research-validation sequence.

---

22. Running Research Validation

Each research-validation stage has a dedicated GitHub Actions workflow.

Script 44

python scripts/44_analyze_indicator_redundancy.py

Workflow:

Indicator Redundancy Analysis

Script 45

python scripts/45_normalization_sensitivity.py

Workflow:

JESI Normalization Sensitivity

Script 46

python scripts/46_weight_sensitivity.py

Workflow:

JESI Weight Sensitivity

Script 47

python scripts/47_aggregation_sensitivity.py

Workflow:

JESI Aggregation Sensitivity

Script 48

python scripts/48_historical_validation.py

Workflow:

JESI Historical Validation

The completed research-validation sequence is:

44 → 45 → 46 → 47 → 48

This sequence constitutes the completed empirical validation program for Master Version 1.0.

The final methodological judgment is documented in Section 18 and Section 27.

Future research may extend the evidence base through broader samples, longer historical periods, additional external outcomes, predictive testing, independent replication, and further methodological research.

---

23. Current Repository Structure

The current repository contains the following core structure:

JAS-JESI/
│
├── README.md
├── DATA_LICENSES.md
├── requirements.txt
├── .gitignore
│
├── methodology/
│   └── JESI_Master_V1.0.md
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── results/
│
├── docs/
│   └── JESI_Final_Results_Report.md
│
├── src/
│   ├── __init__.py
│   ├── data_download.py
│   ├── data_cleaning.py
│   ├── normalization.py
│   ├── pillar_construction.py
│   ├── jesi_calculation.py
│   └── robustness_tests.py
│
├── scripts/
│   ├── 44_analyze_indicator_redundancy.py
│   ├── 45_normalization_sensitivity.py
│   ├── 46_weight_sensitivity.py
│   ├── 47_aggregation_sensitivity.py
│   └── 48_historical_validation.py
│
├── tests/
│   └── test_jesi.py
│
└── .github/
    └── workflows/
        ├── python-app.yml
        ├── final-jesi.yml
        ├── indicator-redundancy.yml
        ├── normalization-sensitivity.yml
        ├── weight-sensitivity.yml
        ├── aggregation-sensitivity.yml
        └── historical-validation.yml

Additional data files and research outputs are maintained under the relevant "data/" directories.

---

24. Production Results Snapshot

The current production repository contains the following JESI empirical results for the documented production sample.

Study period: 2016–2023
Benchmark countries: 5
Aggregation: Weighted geometric mean
Baseline weights: G 0.20, P 0.25, C 0.20, R 0.20, A 0.15

Rank| Code| Country| Growth| Productivity| Connectivity| Resilience| Strategic Autonomy| JESI
1| MYS| Malaysia| 0.323| 0.713| 0.762| 0.767| 0.687| 59.231
2| VNM| Vietnam| 0.602| 0.469| 0.823| 0.690| 0.482| 57.161
3| IND| India| 0.618| 0.562| 0.372| 0.852| 0.271| 48.644
4| IDN| Indonesia| 0.353| 0.562| 0.406| 0.804| 0.361| 46.865
5| BGD| Bangladesh| 0.701| 0.237| 0.157| 0.796| 0.274| 34.464

«Research note: These are production JESI results for the documented methodology, sample, data, normalization rules, weights, aggregation method, and study period. They are not presented as an established international standard, nor as proof of causal economic relationships.»

---

25. Limitations

JESI has several methodological limitations that are subject to ongoing evaluation.

Measurement limitations

Concepts such as strategic autonomy and economic connectivity cannot be perfectly represented by a small number of indicators.

Data limitations

International datasets may contain:

- missing observations,
- revisions,
- methodological differences,
- inconsistent time coverage.

Weighting limitations

The Master Version 1.0 weights are theoretically motivated and are subject to empirical sensitivity testing.

Normalization limitations

Country-level results may vary depending on normalization and benchmark assumptions.

Causality limitations

Statistical association does not by itself establish causation.

These limitations are treated as research questions rather than hidden assumptions.

---

26. Expected Research Contribution

The project aims to develop a transparent, reproducible framework for examining economic strength as a multidimensional system.

Potential contributions include:

1. Moving beyond GDP-size comparisons.
2. Combining productive, external, resilience, and strategic dimensions.
3. Providing an explicit mathematical specification.
4. Developing reproducible country-level calculations.
5. Testing the framework against historical economic conditions.
6. Evaluating methodological robustness.
7. Maintaining an open computational implementation.

The research contribution of Master Version 1.0 is therefore evaluated in light of the completed empirical validation program, while broader scientific contribution remains subject to future research and independent testing.
---

27. Research Status and Interpretation

«JESI is a proposed JAS analytical framework, not an established international statistical index.»

The current repository contains a production empirical implementation and a completed empirical validation program for Master Version 1.0.

The documented validation sequence — Indicator Redundancy/Correlation, Normalization Sensitivity, Weight Sensitivity, Aggregation Sensitivity, and Historical Validation — has been completed for the current production specification, sample, data coverage, and validation design.

The completion of this validation program provides empirical evidence relevant to the framework's internal coherence, methodological robustness, and historical empirical relevance within the tested research design. However, the evidence remains conditional on the documented five-country, 2016–2023 sample, available data, complete-case requirements, and external validation measures.

The current evidence does not establish:

- universal validity,
- causal relationships,
- predictive superiority,
- or methodological superiority over existing economic indices.

The final methodological judgment for the current Master Version 1.0 empirical validation phase is:

«JESI is an empirically supported but not universally validated multidimensional framework for assessing structural economic strength.»

This judgment applies to the current documented empirical specification and should not be interpreted as a claim that JESI is an established international statistical standard.

Future research remains open and may extend the evidence base through:

- broader country coverage,
- longer historical periods,
- additional independent external outcomes,
- predictive testing,
- independent replication,
- alternative datasets,
- and further methodological research.

Accordingly, completion of the Master Version 1.0 empirical validation program represents a methodological milestone, not the end of scientific testing.
---

28. Guiding Principle

«An economy should not be judged by its size alone. Its structural strength should be examined through its ability to grow, produce efficiently, connect globally, absorb shocks, and preserve strategic economic choice.»

— JAS

---

License

The source code in this repository is released under the MIT License.

Methodological text, documentation, and future research outputs may be subject to separate attribution and publication terms where applicable.
