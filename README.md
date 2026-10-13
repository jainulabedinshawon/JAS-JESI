
# 🏛️ JAS-JESI — JAS Unified Economic Strength Index

<p align="center">
  <img src="https://img.shields.io/badge/Master%20Version-1.0-blue?style=for-the-badge" alt="Master Version 1.0">
  <img src="https://img.shields.io/badge/Study%20Period-2016--2023-emerald?style=for-the-badge" alt="Study Period 2016–2023">
  <img src="https://img.shields.io/badge/Framework-Research-orange?style=for-the-badge" alt="Research Framework">
  <img src="https://img.shields.io/badge/License-MIT-informational?style=for-the-badge" alt="MIT License">
</p>

<p align="center">
  <strong>A Data-Driven Multidimensional Framework for Measuring Structural Economic Strength</strong>
</p>

---

## 📌 Executive Summary

The **JAS Unified Economic Strength Index (JESI)** is a proposed analytical framework for assessing and comparing the structural economic strength of selected countries.

Rather than relying exclusively on Gross Domestic Product (GDP) or another single indicator, JESI organizes economic strength into five analytical pillars:

- 📈 Growth
- ⚙️ Productivity
- 🌐 Connectivity
- 🛡️ Resilience
- 🧭 Strategic Autonomy

The framework combines normalized pillar values using a predefined baseline weighting scheme and a weighted geometric aggregation approach.

> **Research status:** JESI is a proposed research-based composite indicator. It is not presented as an established international statistical standard, a universally validated measure of national economic power, or a proven predictor of future economic performance.

## 🎯 1. Research Objectives

The project aims to:

- Develop a transparent, multidimensional framework for comparative economic analysis.
- Document the baseline pillar definitions and weights.
- Compare selected benchmark countries over the 2016–2023 study period.
- Examine how incomplete data coverage affects cross-country comparisons.
- Assess sensitivity to alternative methodological specifications.
- Maintain traceability between published results, supporting data, and analysis scripts.
- Encourage reproducible research and independent verification.

## 🌍 2. Benchmark Countries

The current benchmark sample contains five countries.

| ISO Code | Country | Region |
|:---:|---|---|
| `BGD` | 🇧🇩 Bangladesh | South Asia |
| `IND` | 🇮🇳 India | South Asia |
| `IDN` | 🇮🇩 Indonesia | Southeast Asia |
| `MYS` | 🇲🇾 Malaysia | Southeast Asia |
| `VNM` | 🇻🇳 Vietnam | Southeast Asia |

This is a selected comparative sample, not a comprehensive ranking of all countries worldwide.

## 📅 3. Study Period and Data Coverage

**Study period:** 2016–2023, covering eight annual periods.

The project distinguishes between two types of analysis.

### Main production ranking

Reports the available country results under the production methodology. Countries may have different numbers of available observations.

### Balanced-panel sensitivity analysis

Restricts the comparison to countries with complete observations for all eight study years.

### Data integrity principles

- Missing observations are not treated as zero.
- Missing values are not silently presented as observed outcomes.
- Data must not be fabricated to complete a country panel.
- Imputation or interpolation must not be introduced without explicit documentation and methodological justification.
- Observation counts and coverage must accompany results when incomplete coverage affects interpretation.

A country excluded from the balanced-panel analysis is excluded because of the coverage rule, not because of a judgment about its economic importance.

## 🏛️ 4. The Five JESI Pillars

| Pillar | Symbol | Baseline Weight | Analytical Dimension |
|---|:---:|---:|---|
| 📈 Growth | `G` | 20% | Economic expansion over time |
| ⚙️ Productivity | `P` | 25% | Output efficiency relative to productive inputs |
| 🌐 Connectivity | `C` | 20% | Trade, investment, ICT, and external economic linkages |
| 🛡️ Resilience | `R` | 20% | Capacity to absorb shocks and withstand economic stress |
| 🧭 Strategic Autonomy | `A` | 15% | Economic diversification, complexity, and strategic flexibility |
| **Total** | | **100%** | |

The pillar descriptions summarize the framework's intended analytical dimensions. The exact indicators, data sources, transformations, and normalization procedures must be established from the methodology documentation and implementation.

## 🧮 5. Baseline Mathematical Specification

The Master Version 1.0 framework specifies weighted geometric aggregation.

The general form is:

$$
JESI_i = 100 \prod_{k=1}^{5} X_{ik}^{w_k}
$$

where:

- \(JESI_i\) represents the composite score for country \(i\).
- \(X_{ik}\) represents the normalized value for country \(i\) on pillar \(k\).
- \(w_k\) represents the baseline weight assigned to pillar \(k\).
- The baseline weights sum to 1.00.

The specified baseline weights are:

$$
(w_G,w_P,w_C,w_R,w_A)
=
(0.20,0.25,0.20,0.20,0.15)
$$

Geometric aggregation makes the composite score sensitive to weaknesses across individual pillars. However, the exact numerical implementation—including scaling, treatment of zero values, missing data, and output transformations—must match the production code.

**Reproducibility requirement:** This mathematical expression describes the intended baseline specification. The production implementation should be checked against the source code before this expression is treated as a complete technical specification.

## 📊 6. Main Production Results

The following table reproduces the country results documented in the current final-results report.

| Rank | ISO | Country | Growth | Productivity | Connectivity | Resilience | Strategic Autonomy | JESI | SD | Observations |
|---:|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `MYS` | 🇲🇾 Malaysia | 0.323 | 0.713 | 0.767 | 0.767 | 0.687 | **59.283** | 14.064 | 8 |
| 2 | `VNM` | 🇻🇳 Vietnam | 0.602 | 0.469 | 0.823 | 0.690 | 0.482 | **57.161** | 11.886 | 8 |
| 3 | `IND` | 🇮🇳 India | 0.618 | 0.562 | 0.372 | 0.852 | 0.271 | **48.635** | 13.408 | 8 |
| 4 | `IDN` | 🇮🇩 Indonesia | 0.353 | 0.562 | 0.404 | 0.804 | 0.361 | **46.824** | 8.354 | 8 |
| 5 | `BGD` | 🇧🇩 Bangladesh | 0.701 | 0.237 | 0.157 | 0.796 | 0.274 | **34.464** | 10.617 | 2 |

**Important interpretation notes**

- Malaysia has the highest reported composite score in the main production ranking.
- Vietnam ranks second under the reported baseline specification.
- India has the highest reported Resilience pillar value among the five benchmark countries.
- Bangladesh has the highest reported Growth pillar value in this table, but only two observations are reported for the study period.
- Bangladesh's result should therefore be interpreted cautiously relative to countries with complete eight-year coverage.
- `SD` is retained as reported in the results table. Its precise statistical interpretation should be confirmed from the final-results report or calculation code.

These are reported empirical outputs for the selected sample. They are not independent proof of a country's overall economic power or welfare.

## ⚖️ 7. Balanced-Panel Sensitivity Analysis

The balanced-panel comparison includes only countries with complete eight-year coverage.

| Rank | ISO | Country | JESI | Coverage | Balanced-Panel Status |
|---:|:---:|---|---:|:---:|---|
| 1 | `MYS` | 🇲🇾 Malaysia | **59.283** | 8/8 | Included |
| 2 | `VNM` | 🇻🇳 Vietnam | **57.161** | 8/8 | Included |
| 3 | `IND` | 🇮🇳 India | **48.635** | 8/8 | Included |
| 4 | `IDN` | 🇮🇩 Indonesia | **46.824** | 8/8 | Included |
| — | `BGD` | 🇧🇩 Bangladesh | 34.464* | 2/8 | Excluded: incomplete panel |

\*Bangladesh's score is shown for reference from the main production results; it is **not** a balanced-panel result.

Bangladesh has 2 of 8 observations, equivalent to 25% coverage, and is excluded from the balanced-panel ranking under the complete-coverage rule.

The main production ranking and balanced-panel comparison answer different analytical questions. They must not be presented as if they use identical coverage criteria.

## 🧪 8. Robustness and Historical Validation

The repository includes a historical-validation pipeline designed to
reconstruct the JESI series, examine historical event windows,
decompose pillar contributions, and compare JESI with selected
external economic outcomes.

### Historical Validation Status

**Status: Successfully executed on the current `main` revision.**

GitHub Actions run
[38465489004](https://github.com/jainulabedinshawon/JAS-JESI/actions/runs/38465489004)
completed successfully against commit
`e3a8d7c26332eaf4284d370bc2839127f5f518f8`.

The workflow verified the generated historical-validation outputs
and uploaded the `jesi-historical-validation-analysis` artifact.

### Reported Validation Coverage

- Theoretical panel: 40 country-year observations.
- Complete-case panel: 34 observations.
- Study period: 2016–2023.
- Historical event-window observations: 16.
- Pillar-contribution observations: 29.
- Missing-data treatment: complete-case analysis.
- Imputation, interpolation, and fabricated observations: none reported.
- Production JESI modification: none.

### External Outcome Correlations

The workflow calculated Spearman correlations between JESI and
selected World Bank economic outcomes.

| Analysis | Outcome | Spearman correlation | N |
|---|---|---:|---:|
| Country-year level | Unemployment | -0.4698 | 34 |
| Country-year level | Inflation | -0.0387 | 34 |
| First difference | Unemployment | -0.4143 | 29 |
| First difference | Inflation | +0.3020 | 29 |
| Country mean | Unemployment | -0.6000 | 5 |
| Country mean | Inflation | -0.9000 | 5 |

These correlations are diagnostic findings for the observed sample.
They do not establish causation, predictive validity, or universal
methodological superiority. Country-mean comparisons are especially
limited by the small sample size.

### Interpretation and Reproducibility

A successful workflow confirms that the configured analysis ran and
its required output files were generated. It does not, by itself,
establish that JESI predicts future economic performance or that the
underlying framework is universally valid.

The validation artifact is available from the
[GitHub Actions run](https://github.com/jainulabedinshawon/JAS-JESI/actions/runs/38465489004).

Historical validation is conducted as a diagnostic research layer.
It does not overwrite the production JESI results or change the
baseline weights.

## 🛡️ 9. Research Integrity

The project follows these reporting principles:

- **No data fabrication:** Do not invent observations to complete a panel.
- **Missing-data transparency:** Clearly distinguish missing values from observed outcomes.
- **Traceability:** Published numbers should match the corresponding generated results.
- **Methodological consistency:** Do not silently change the baseline weights or aggregation method.
- **No unsupported claims:** Do not claim that a test passed without evidence of its execution and result.
- **Version control:** Document material changes to inputs, scripts, methods, and published outputs.
- **Coverage transparency:** Clearly identify the countries included in each comparison.
- **Reproducibility:** Preserve the instructions and dependencies required to reproduce the analysis.

## 📂 10. Repository Structure

The following is the intended logical organization. Confirm actual file and directory names in the repository before relying on this tree as a complete inventory.

```text
JAS-JESI/
├── README.md
├── LICENSE
├── DATA_LICENSES.md
├── requirements.txt
├── requirements.lock
├── methodology/
│   └── JESI_Master_V1.0.md
├── docs/
│   └── JESI_Final_Results_Report.md
├── data/
│   ├── raw/
│   ├── processed/
│   └── results/
│       ├── jesi_balanced_panel_country_means.csv
│       ├── jesi_balanced_panel_country_results.csv
│       └── jesi_balanced_panel_summary.csv
├── src/
├── scripts/
└── .github/
    └── workflows/
```

The actual repository may contain additional files or use a different structure. The tree above highlights key paths referenced by the project documentation.

## 💻 11. Quickstart and Reproducibility

### Clone the repository

```bash
git clone https://github.com/jainulabedinshawon/JAS-JESI.git
cd JAS-JESI
```

### Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

Activate it in Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If the repository documents a separate procedure for `requirements.lock`, use that procedure when reproducing the locked environment.

### Run the analysis

Inspect the available scripts and their documented execution order before running the production pipeline. Do not assume that running every script in numerical or alphabetical order is safe.

A reproducible run should record:

1. The source commit or release tag.
2. The Python and dependency versions.
3. The input dataset versions.
4. The scripts and configuration used.
5. The generated output files.
6. Any validation errors or warnings.

## 🔄 12. Automated Workflows

GitHub Actions may be used to run project checks or generate updated results.

The existence of a workflow does not, by itself, prove that a run passed or that its output was reviewed and merged into the `main` branch.

For each automated update:

1. Inspect the workflow run and logs.
2. Confirm which files were changed or generated.
3. Check the output values and observation counts.
4. Compare the README with the final-results report and CSV outputs.
5. Review the proposed changes.
6. Confirm that the approved commit is present on the intended branch.

Workflows should receive only the permissions required for their tasks. Pull-request creation and merging depend on the workflow permissions and repository settings.

## 🔍 13. Results Update Policy

Whenever production results change, reconcile all relevant published files.

The update should include:

- Country scores and pillar values.
- Country observation counts and coverage percentages.
- Balanced-panel eligibility and results.
- The final-results report.
- The README tables and explanatory text.
- Any release notes that quote the results.

Remove obsolete tables rather than leaving conflicting versions of the same results in different sections.

**Single-source-of-truth principle:** The README, detailed report, and generated outputs must correspond to the same intended analysis run. If a discrepancy is found, investigate the source before publishing a replacement value.

## ⚠️ 14. Methodological Limitations

JESI has limitations that should accompany interpretation of its results.

### Selected sample

The study includes five benchmark countries and does not establish a global ranking.

### Unequal coverage

Bangladesh has incomplete reported coverage, which limits direct comparison with full eight-year panels.

### Indicator selection

Results depend on which indicators are selected and how they are measured.

### Normalization

Different normalization procedures can change the scale and relative values of pillar scores.

### Weighting

The baseline weights are methodological choices, not universally established optimal weights.

### Aggregation

Geometric aggregation responds differently to weak pillar values than arithmetic aggregation.

### Interpretation and prediction

The current composite scores do not, on their own, establish causal relationships or predictive validity.

These limitations should be considered in research, policy discussions, and external presentations of the index.

## 🔬 15. Future Research

Potential future work includes:

1. Expanding the benchmark country sample.
2. Improving the documentation and coverage of source data.
3. Comparing alternative normalization procedures.
4. Testing alternative weights and aggregation methods.
5. Examining indicator redundancy and individual indicator influence.
6. Conducting independently verifiable historical back-testing.
7. Comparing JESI with established economic indicators.
8. Examining sensitivity to the inclusion or exclusion of countries.
9. Supporting independent replication of the analysis.
10. Publishing versioned datasets and reproducible releases.

These items are research opportunities, not claims that the work has already been completed.

## 📜 16. Citation

Suggested citation:

> Shawon, Jainul Abedin. (2026). *JAS Unified Economic Strength Index (JESI): Master Version 1.0.* JAS-JESI Research Repository. https://github.com/jainulabedinshawon/JAS-JESI

For any research publication, also specify the particular repository commit or release, the results report used, and the date on which the data were retrieved.

## ⚖️ 17. License

The repository indicates an MIT License. Confirm that a valid `LICENSE` file is present and that the licensing terms are appropriate for the code and materials being distributed.

Data and third-party datasets may have separate license and attribution requirements. See [`DATA_LICENSES.md`](DATA_LICENSES.md) if that file is present.

## 📑 18. Detailed Documentation

- [Repository home](https://github.com/jainulabedinshawon/JAS-JESI)
- [Final Empirical Results Report](docs/JESI_Final_Results_Report.md)
- [Methodology document](methodology/JESI_Master_V1.0.md)
- [Data licensing and attribution](DATA_LICENSES.md)

Repository paths above should be checked against the actual files in the release being cited.

## 🏁 19. Project Status

JAS-JESI documents a five-pillar analytical framework, a baseline weighting scheme, reported production results, and a balanced-panel comparison.

The reported results should be interpreted within the limits of the study period, selected country sample, data coverage, and methodological choices.

**Release integrity rule:** A release should be published only after the intended source revision, numerical results, supporting files, and validation evidence have been reviewed for consistency. A version label alone does not establish independent peer review or universal validation.

---

<p align="center">
  <strong>JAS-JESI · Master Version 1.0</strong><br>
  <em>Transparency · Reproducibility · Methodological Accountability</em>
</p>
