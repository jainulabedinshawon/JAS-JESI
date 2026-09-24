JAS UNIFIED ECONOMIC STRENGTH INDEX (JESI)

Master Version 1.0

A Framework for Measuring Structural Economic Strength

---

1. Purpose

The JAS Unified Economic Strength Index (JESI) is a proposed multidimensional analytical framework for measuring the structural strength of an economy beyond GDP size.

The framework evaluates an economy through five interconnected pillars:

1. Growth (G)
2. Productivity (P)
3. Connectivity (C)
4. Resilience (R)
5. Strategic Autonomy (A)

The central principle is:

«Economic Strength = Growth × Productivity × Connectivity × Resilience × Strategic Autonomy»

JESI is a proposed JAS analytical framework and is not an established international statistical index.

---

2. Core Equation

The Master Version 1.0 specification is:

[
JESI = 100 \times G^{0.20} \times P^{0.25} \times C^{0.20} \times R^{0.20} \times A^{0.15}
]

Where:

- G = Growth score
- P = Productivity score
- C = Connectivity score
- R = Resilience score
- A = Strategic Autonomy score

All pillar scores are normalized to a 0–1 scale before aggregation.

The weights are:

Pillar| Weight
Growth| 20%
Productivity| 25%
Connectivity| 20%
Resilience| 20%
Strategic Autonomy| 15%
Total| 100%

---

3. Conceptual Framework

JESI is based on the proposition that economic size alone does not adequately describe structural economic strength.

GDP primarily measures the size and production value of an economy.

JESI asks a broader question:

«How strong is the economic system, and how capable is it of sustaining growth, absorbing shocks, remaining globally connected, and preserving strategic economic choice?»

The framework therefore distinguishes:

GDP SIZE ≠ ECONOMIC STRENGTH

---

4. Pillar I — Growth (G)

Growth represents the economy's capacity to expand its productive output and income over time.

Proposed indicators

- Real GDP Growth Rate
- GNI per Capita Growth

Proposed pillar weight

20%

Growth captures dynamic economic expansion but is not treated as sufficient by itself to define economic strength.

---

5. Pillar II — Productivity (P)

Productivity measures the efficiency with which an economy converts labor and other productive resources into economic output.

Proposed indicators

- GDP per Person Employed
- Total Factor Productivity (TFP) Growth

Proposed pillar weight

25%

Productivity receives the highest baseline weight because long-term improvements in living standards and economic capacity depend substantially on productive efficiency and technological progress.

---

6. Pillar III — Connectivity (C)

Connectivity measures the degree to which an economy is integrated into global trade, investment, information, and production networks.

Proposed indicators

- Trade Openness
- FDI Inflows
- ICT and Global Integration

Proposed pillar weight

20%

Connectivity is intended to capture beneficial participation in the global economy.

However, connectivity must be distinguished from excessive critical dependency.

---

7. Pillar IV — Resilience (R)

Resilience represents an economy's capacity to absorb external and internal shocks while maintaining macroeconomic stability and economic functioning.

Proposed indicators

- Foreign Exchange Reserves / Import Cover
- Public Debt / GDP
- Current Account Position

Proposed pillar weight

20%

Resilience should not be interpreted through simplistic assumptions that lower debt or higher current-account balances are always better.

Debt sustainability depends on factors including economic growth, interest rates, maturity structure, currency composition, and fiscal capacity.

Similarly, current-account performance should be evaluated within a sustainable range rather than assuming that either permanent deficits or permanent surpluses are inherently optimal.

---

8. Pillar V — Strategic Autonomy (A)

Strategic Autonomy measures the ability of an economy to preserve meaningful economic choice while remaining globally connected.

Strategic autonomy does not mean autarky or economic isolation.

It means reducing critical vulnerabilities that could substantially constrain economic policy or national economic functioning.

Proposed indicators

- Economic Complexity Index (ECI)
- High-Tech Exports as % of Manufactured Exports
- Critical Import Concentration

Proposed pillar weight

15%

Strategic autonomy is therefore understood as:

«The capacity to remain globally connected without becoming critically dependent on a narrow set of external sources, technologies, markets, or inputs.»

---

9. Indicator Normalization

Because the underlying indicators have different units and scales, each indicator must be normalized before pillar construction.

Positive-direction indicators

For indicators where a higher value represents better structural performance:

[
X_{norm} =
\frac{X-X_{min}}
{X_{max}-X_{min}}
]

Negative-direction indicators

For indicators where a lower value represents better structural performance:

[
X_{norm} =
\frac{X_{max}-X}
{X_{max}-X_{min}}
]

The benchmark period and reference population used to determine minimum and maximum values must be explicitly documented.

---

10. Benchmark Protocol

The normalization benchmark must be fixed before final index construction.

Possible approaches include:

- Historical global benchmark
- Fixed reference-period benchmark
- Rolling benchmark
- Percentile-based normalization
- Rank-based normalization

The baseline implementation should use a clearly documented fixed benchmark.

Sensitivity analysis should compare alternative normalization approaches.

Extreme observations should be examined for their effect on the final index.

Winsorization or percentile-based methods may be evaluated where appropriate.

---

11. Pillar Construction

After normalization, indicators within each pillar are aggregated to produce the five pillar scores:

[
G,\ P,\ C,\ R,\ A
]

The initial implementation should document:

- Indicator selection
- Direction of each indicator
- Missing-data treatment
- Indicator weights
- Aggregation method
- Benchmark period
- Outlier treatment

Equal weighting within pillars may be used as the baseline unless empirical evidence supports an alternative.

---

12. Aggregation Method

JESI uses a weighted geometric aggregation:

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

The geometric structure is intentional.

It prevents an exceptionally strong performance in one pillar from completely compensating for severe weakness in another pillar.

Therefore, JESI is sensitive to structural imbalance.

This reflects the conceptual proposition that a strong economy requires multiple complementary capabilities.

---

13. Weighting Methodology

Baseline JAS Strategic Weights

The Master Version 1.0 weights are:

- Growth — 20%
- Productivity — 25%
- Connectivity — 20%
- Resilience — 20%
- Strategic Autonomy — 15%

Equal-Weight Alternative

A robustness specification will assign:

- Growth — 20%
- Productivity — 20%
- Connectivity — 20%
- Resilience — 20%
- Strategic Autonomy — 20%

Statistical Alternatives

Future versions may evaluate:

- Principal Component Analysis (PCA)
- Multivariate statistical methods
- Predictive-validity-based weighting
- Expert-derived weighting
- Data-driven optimization

Statistical weighting and policy-based weighting should be tested as alternative specifications rather than mixed without methodological justification.

---

14. Data Sources

Potential international data sources include:

- World Bank
- International Monetary Fund (IMF)
- World Trade Organization (WTO)
- UNCTAD
- International Labour Organization (ILO)
- OECD
- World Intellectual Property Organization (WIPO)
- Harvard Growth Lab / Atlas of Economic Complexity
- Other internationally recognized statistical databases

All datasets used in the final calculation must record:

- Source
- Indicator code
- Definition
- Unit
- Frequency
- Coverage period
- Download date
- Transformation method

---

15. Missing Data

Missing observations must be handled using a documented,
reproducible, and indicator-specific protocol.

The baseline JESI implementation follows a
"No Silent Imputation" principle.

15.1 Source-Missing Observations

If an official source does not report a valid observation
for a country-year, the observation must remain missing.

A missing observation must NOT be replaced by:

- Zero
- An arbitrary constant
- Unrelated proxy indicators
- Unverified secondary estimates
- Interpolation solely to complete the dataset

The absence of reported data must not be interpreted as
a value of zero.

For example, if an official trade-data source does not
report a high-technology export value for a country-year,
JESI will preserve that observation as missing unless an
independently documented and methodologically equivalent
source provides a valid observation.

15.2 Imputation

Imputation may be considered only when all of the following
conditions are satisfied:

1. The method is economically defensible.
2. The method is explicitly documented.
3. The source and transformation are reproducible.
4. The imputation does not introduce an artificial
   advantage or disadvantage for a country.
5. Results are tested against a no-imputation specification.

Any imputed observations must be explicitly flagged in the
research dataset.

15.3 Indicator Coverage

Indicator validity and data availability are separate
methodological questions.

An indicator must not be declared theoretically invalid
merely because its international coverage is incomplete.

However, an indicator with substantial missingness may be
excluded from the baseline specification if its coverage
prevents reliable construction of the intended country-year
sample.

Such an exclusion must be documented as a methodological
decision and tested through sensitivity analysis.

15.4 Country-Year Eligibility

A country-year may enter the baseline JESI calculation only
when valid observations are available for all required
indicators and all five pillar scores can be constructed
without undocumented imputation.

Country-years failing this condition must be excluded from
the corresponding baseline index calculation rather than
assigned artificial values.

The number and identity of excluded country-years must be
reported in the final research outputs.

15.5 Missingness Sensitivity

Missing-data sensitivity must be evaluated separately from
the baseline calculation.

Where feasible, robustness analysis should compare:

- Complete-case baseline results
- Alternative indicator specifications
- Alternative defensible data sources
- Explicitly documented imputation scenarios, if justified

The final methodological judgment must report whether
missing-data assumptions materially affect the conclusions.

Missing-data treatment must never be hidden from the final
research dataset or final research report.

---

16. Empirical Validation

The framework requires empirical testing before any claim of predictive or explanatory superiority.

Validation should include:

16.1 Historical Back-Testing

JESI should be calculated across historical periods and evaluated against major economic stress episodes, including:

- Global Financial Crisis
- COVID-19 shock
- Major commodity shocks
- External financing stress
- Foreign-exchange crises
- Banking-sector stress

16.2 Cross-Country Comparison

The index should initially be tested across a diverse sample of economies.

The sample should include:

- Advanced economies
- Emerging markets
- Developing economies
- Commodity exporters
- Manufacturing economies
- Service-oriented economies
- Small and large economies

16.3 Predictive Testing

Future research should test whether JESI levels or changes are associated with outcomes such as:

- Future economic growth
- Growth volatility
- Crisis probability
- Investment performance
- Employment performance
- External-sector stability

---

17. Robustness Testing

The following specifications should be compared:

1. Baseline JAS weights
2. Equal weights
3. Alternative normalization methods
4. Alternative benchmark periods
5. Alternative indicator combinations
6. PCA-based weighting
7. Alternative aggregation methods

The objective is to determine whether country rankings and empirical conclusions remain reasonably stable under plausible methodological changes.

---

18. Sensitivity Analysis

Sensitivity analysis should evaluate the effect of:

- Individual indicators
- Pillar weights
- Normalization methods
- Outlier treatment
- Missing-data assumptions
- Benchmark selection
- Geometric versus alternative aggregation

A framework that produces highly unstable results under minor methodological changes should be interpreted cautiously.

---

19. Strategic Interpretation

The JAS framework is based on three strategic principles:

«Maximum connectivity.
Minimum critical dependency.
Maximum strategic autonomy.»

The objective is not economic isolation.

Rather, the objective is to combine global integration with sufficient domestic and diversified capacity to preserve economic choice.

---

20. GDP Size vs Economic Strength

GDP remains an essential measure of economic scale.

However:

«GDP SIZE ≠ ECONOMIC STRENGTH»

GDP answers:

«“How large is the economy?”»

JESI asks:

«“How strong is the economic system?”»

Two economies with similar GDP may have substantially different:

- Productivity
- External vulnerability
- Reserve capacity
- Economic complexity
- Supply-chain dependence
- Global connectivity
- Strategic economic flexibility

JESI is designed to capture these structural differences.

---

21. Research Hypotheses

The framework generates several testable hypotheses.

H1 — Structural Strength Hypothesis

Higher JESI is associated with stronger long-term economic performance.

H2 — Resilience Hypothesis

Higher JESI is associated with lower economic vulnerability during major external shocks.

H3 — Productivity Hypothesis

Higher productivity contributes positively to structural economic strength and long-term income growth.

H4 — Connectivity Hypothesis

Greater productive global connectivity improves economic strength when accompanied by adequate resilience and diversification.

H5 — Strategic Autonomy Hypothesis

Lower critical dependency and greater productive capability are associated with greater economic resilience.

H6 — Balanced-Strength Hypothesis

Economies with more balanced performance across the five pillars should demonstrate greater structural strength than economies whose performance is concentrated in only one or two pillars.

---

22. Methodological Limitations

JESI has several limitations.

First, indicator selection necessarily involves conceptual judgment.

Second, international datasets may contain measurement differences across countries.

Third, normalization choices can influence rankings.

Fourth, weighting assumptions can influence final scores.

Fifth, strategic autonomy is inherently more difficult to measure than conventional macroeconomic variables.

Sixth, correlation between JESI and economic outcomes does not automatically establish causality.

Therefore, JESI should be treated as an analytical framework requiring continuous empirical validation.

---

23. Reproducibility

The project aims to make the full JESI methodology reproducible.

The repository should ultimately contain:

JAS-JESI/
│
├── README.md
├── methodology/
│   └── JESI_Master_V1.0.md
│
├── data/
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

All transformations and calculations should be implemented through reproducible code.

---

24. Research Status

Status: Proposed Framework — Master Version 1.0

JESI is currently a research framework under empirical development.

The framework should not be presented as an established international economic index until its methodology has been empirically tested, validated, peer reviewed, and independently reproduced.

---

25. Core JAS Principle

«An economy should not be judged by its size alone. Its true strength lies in its ability to grow, produce efficiently, connect globally, absorb shocks and preserve strategic economic choice.»

— JAS
