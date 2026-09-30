# JAS Unified Economic Strength Index (JESI)

## Final Empirical Results Report

**Version:** Master Version 1.0  
**Study period:** 2016-2023  
**Benchmark countries:** 5  
**Country-year observations:** 34

---

## 1. Framework

The JAS Unified Economic Strength Index (JESI) is a multidimensional
framework designed to evaluate economic strength through five structural
pillars:

- **G — Growth**
- **P — Productivity**
- **C — Connectivity**
- **R — Resilience**
- **A — Strategic Autonomy**

The baseline weighting structure is:

| Pillar | Weight |
|---|---:|
| Growth | 0.20 |
| Productivity | 0.25 |
| Connectivity | 0.20 |
| Resilience | 0.20 |
| Strategic Autonomy | 0.15 |

The baseline aggregation is a weighted geometric index:

`JESI = 100 × G^0.20 × P^0.25 × C^0.20 × R^0.20 × A^0.15`

All pillar scores are normalized to the interval (0, 1].

---

## 2. Final Country Results

|   Rank | Country    |   Growth |   Productivity |   Connectivity |   Resilience |   Strategic Autonomy |   JESI |   JESI SD |   Observations |
|-------:|:-----------|---------:|---------------:|---------------:|-------------:|---------------------:|-------:|----------:|---------------:|
|      1 | Malaysia   |    0.323 |          0.713 |          0.762 |        0.767 |                0.687 | 59.231 |    14.105 |              8 |
|      2 | Vietnam    |    0.602 |          0.469 |          0.823 |        0.69  |                0.482 | 57.161 |    11.886 |              8 |
|      3 | India      |    0.618 |          0.562 |          0.372 |        0.852 |                0.271 | 48.644 |    13.388 |              8 |
|      4 | Indonesia  |    0.353 |          0.562 |          0.406 |        0.804 |                0.361 | 46.865 |     8.355 |              8 |
|      5 | Bangladesh |    0.701 |          0.237 |          0.157 |        0.796 |                0.274 | 34.464 |    10.617 |              2 |

---

## 3. Robustness Analysis

The robustness module compares the baseline strategic weighting with
equal weighting and compares arithmetic with geometric aggregation.

| Country    |   JAS Arithmetic |   JAS Geometric |   Equal Arithmetic |   Equal Geometric |
|:-----------|-----------------:|----------------:|-------------------:|------------------:|
| Bangladesh |           43.12  |          34.464 |             43.305 |            34.783 |
| Indonesia  |           50.733 |          46.865 |             49.726 |            45.812 |
| India      |           54.98  |          48.644 |             53.521 |            46.766 |
| Malaysia   |           65.177 |          59.231 |             65.05  |            59.07  |
| Vietnam    |           61.259 |          57.161 |             61.325 |            57.275 |

### Rank Correlations

- **JAS vs Equal:** 1.0000
- **Arithmetic vs Geometric:** 1.0000
- **JAS Arithmetic vs Equal Geometric:** 1.0000

These correlations describe the degree of rank-order similarity between
the tested specifications. They are sensitivity measures rather than
proof that one specification is universally superior.

---

## 4. Year-Level JESI Summary

|   Year |   Mean JESI |   Median JESI |   Minimum |   Maximum |   Observations |
|-------:|------------:|--------------:|----------:|----------:|---------------:|
|   2016 |      52.934 |        54.066 |    40.759 |    62.844 |              4 |
|   2017 |      50.797 |        48.855 |    26.956 |    68.882 |              5 |
|   2018 |      53.035 |        50.32  |    41.971 |    66.739 |              5 |
|   2019 |      50.981 |        51.719 |    38.203 |    62.285 |              4 |
|   2020 |      31.659 |        33.169 |    21.976 |    38.323 |              4 |
|   2021 |      53.125 |        54.379 |    42.368 |    61.375 |              4 |
|   2022 |      68.542 |        66.33  |    57.237 |    84.271 |              4 |
|   2023 |      54     |        54.37  |    47.233 |    60.029 |              4 |

---

## 5. Interpretation

The final JESI results provide a multidimensional representation of
economic strength across the five benchmark countries during the
2016-2023 common sample.

The pillar structure allows economic performance to be examined beyond
a single output measure by separating growth, productivity, connectivity,
resilience, and strategic autonomy.

Country-level differences should therefore be interpreted together with
the underlying pillar scores rather than through the composite score
alone.

The robustness results indicate how sensitive the measured country
ordering is to alternative weighting and aggregation specifications.
They should be treated as methodological sensitivity evidence, not as
proof of causal relationships.

---

## 6. Methodological Status

JESI is a proposed composite economic-strength framework developed by
JAS. The present results represent an empirical implementation of the
specified Master Version 1.0 methodology for the stated benchmark
sample and period.

The index should not be interpreted as an established international
standard or as a causal measure of economic performance.

Important methodological limitations include:

1. Indicator availability and missing observations.
2. Cross-country comparability of source data.
3. Sensitivity to normalization choices.
4. Sensitivity to pillar weights.
5. Sensitivity to aggregation method.
6. Data revisions and measurement error.
7. The limited benchmark-country and time-period sample.
8. The distinction between association and causality.

---

## 7. Reproducibility

The empirical pipeline is implemented through the repository scripts.

The final calculation produces:

- Country-year JESI scores
- Country-level averages
- Country rankings
- Robustness results
- Year-level summaries
- Final research-ready tables
- This research report

The final validation script checks data completeness, duplicate
country-year observations, score ranges, mathematical consistency,
country aggregation, ranking integrity, yearly aggregation, research
table consistency, and robustness-output integrity.

---

## 8. Historical Validation

Historical validation was completed as part of the empirical validation program for JESI Master Version 1.0 through Script 48 ("48_historical_validation.py").

The purpose of this analysis was to examine whether changes in the JESI index and its five component pillars were empirically associated with selected external economic indicators over the available historical sample. The analysis therefore provides an additional empirical validation layer for the current JESI specification.

The completed historical validation is based on the available country-year observations and the documented data-availability and complete-case requirements of the Master Version 1.0 research design. No missing observations were fabricated, interpolated, or otherwise artificially generated for the purpose of historical validation.

The analysis evaluates historical associations between:

- Overall JESI changes and selected external economic outcomes;
- Changes in the Growth (G) pillar and relevant external indicators;
- Changes in the Productivity (P) pillar and relevant external indicators;
- Changes in the Connectivity (C) pillar and relevant external indicators;
- Changes in the Resilience (R) pillar and relevant external indicators;
- Changes in the Strategic Autonomy (A) pillar and relevant external indicators.

The historical validation results are interpreted as empirical associations rather than causal effects. A statistical association between JESI changes and an external economic indicator does not, by itself, establish that changes in JESI caused changes in that indicator. The results should therefore be interpreted within the limits of the available sample, measurement choices, country coverage, historical period, and external validation variables.

Completion of Script 48 does not imply that JESI has been universally validated or that it has demonstrated predictive superiority over alternative economic-strength indices. Rather, it constitutes the historical-validation component of the completed empirical validation program for the Master Version 1.0 specification.

Accordingly, the historical validation stage of Master Version 1.0 is considered completed. Future research may extend this evidence base through broader historical periods, additional countries, alternative datasets, additional external outcomes, out-of-sample testing, predictive evaluation, independent replication, and other forms of longitudinal or cross-country validation.

---

## 9. Research Status

Pipeline status: Empirical construction and validation completed for Master Version 1.0.

The reported results are specific to the documented JESI Master Version 1.0 methodology, benchmark sample, data sources, normalization rules, weights, aggregation choices, and available observations.

The completed empirical validation program consists of:

44 — Indicator Redundancy / Correlation →
45 — Normalization Sensitivity →
46 — Weight Sensitivity →
47 — Aggregation Sensitivity →
48 — Historical Validation

This completed validation program supports the methodological judgment documented in the main README and methodology documentation:

«JESI is an empirically supported but not universally validated multidimensional framework for assessing structural economic strength.»

This conclusion is specific to the documented Master Version 1.0 specification, sample, data availability, and validation procedures. It does not establish universal validity, causal relationships, predictive superiority, or superiority over alternative economic-strength indices.

Future research may extend the evidence base through broader country coverage, longer historical periods, additional external outcomes, alternative datasets, predictive and out-of-sample testing, independent replication, and further methodological research.
