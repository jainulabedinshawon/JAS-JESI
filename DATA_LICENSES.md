# JAS-JESI Data Sources and Licensing

This document records the provenance, licensing status, attribution requirements, and repository treatment of third-party datasets used or retrieved by the JAS Unified Economic Strength Index (JESI).

> **Scope:** This document concerns third-party data and does not replace the terms of the original data providers. Provider terms control where they differ from the repository's MIT License.

## 1. Licensing Boundary

### 1.1 JAS-original code

The repository's original source code is released under the repository's MIT License, unless an individual file or component states otherwise.

This includes JAS-original code in, where applicable:

- `src/`
- `scripts/`
- `tests/`
- `.github/workflows/`

The MIT License does **not** automatically relicense third-party datasets, third-party documentation, provider trademarks, or other external materials.

### 1.2 Third-party data

A third-party dataset remains subject to the provider's applicable license or data-use terms even when a copy, subset, or derived table is stored in this repository.

Accordingly:

- Third-party data must not be described as MIT-licensed merely because it is inside this repository.
- Provider attribution requirements must be preserved.
- Any applicable restrictions on redistribution, commercial use, systematic downloading, or third-party material must be respected.
- Where the applicable terms are uncertain, the preferred repository treatment is **retrieval-only**: retain the retrieval/processing script and document the official source rather than committing the raw dataset.

### 1.3 Derived data and transformations

JESI may clean, validate, normalize, score, aggregate, or otherwise transform third-party data.

A transformation does not by itself remove the provider's rights or terms applying to the underlying source data.

For research reproducibility, users should distinguish:

1. original provider data;
2. JAS retrieval and processing code;
3. JAS-derived analytical outputs; and
4. the JAS/JESI methodological framework.

Where a provider requires material transformation to be identified, JESI documentation should make that distinction explicit.

---

## 2. Audited Current Data Sources

The following sources have been reviewed for the current JESI repository and pipeline.

| Provider | Dataset / variables used | Current repository treatment | Verified licensing / usage position | Attribution / notes |
|---|---|---|---|---|
| **World Bank** | World Development Indicators (WDI), including `NY.GDP.MKTP.KD.ZG` (GDP growth) and `NY.GNP.PCAP.KD.ZG` (GNI per capita growth), plus other WDI indicators used by JESI scripts | **Repository-stored subset:** `data/raw/growth_indicators_2015_2025.csv`; other WDI data are retrieved by scripts as needed | The audited WDI indicator metadata identifies **CC BY 4.0**. | Cite World Bank/WDI and identify the relevant indicator codes. The audited indicators list national/OECD data sources in their metadata. |
| **International Monetary Fund (IMF)** | World Economic Outlook (WEO), including `GGXWDG_NGDP` for government gross debt | **Repository-stored source file:** `WEOApr2026all.xlsx` | IMF's special statistical **Data** terms expressly include the World Economic Outlook database and permit use subject to the stated conditions. The terms require attribution and require materially transformed data to be identified as transformed. Some statistical products may contain third-party material with separate terms. | Cite IMF, the specific WEO edition, and the official source. Do not treat the WEO file as MIT-licensed. |
| **Penn World Table (PWT)** | PWT 11.0, including `rtfpna` used to construct TFP growth | **Retrieval-only:** the raw PWT dataset is not currently committed to `data/raw/`; `scripts/04_download_pwt_productivity.py` retrieves it | PWT 11.0 is explicitly licensed **CC BY 4.0** by the University of Groningen/GGDC. | Required attribution includes Feenstra, Inklaar and Timmer (2015), *The Next Generation of the Penn World Table*. |
| **UN Trade and Development (UNCTAD)** | Merchandise import product concentration and related trade/concentration data | **Retrieval-only:** the raw UNCTAD bulk dataset is not currently committed to `data/raw/`; `scripts/31_download_import_concentration.py` retrieves it | UNCTAD Data Hub provides data under its stated reuse/attribution conditions. Because the current raw dataset is not stored in the repository, the pipeline uses the conservative retrieval-only treatment. | Cite UN Trade and Development / UNCTAD Data Hub and the exact dataset. Re-check the provider terms before any future raw-data redistribution. |
| **Harvard Growth Lab / Atlas of Economic Complexity** | Economic Complexity Index (ECI) used by Strategic Autonomy | **Retrieval-only:** ECI is retrieved through the Atlas API by `scripts/29_download_autonomy_data.py`; no raw Atlas dataset is currently committed | Atlas makes its data/tools available for research and applied use with appropriate attribution. A standalone machine-readable license statement was not sufficiently pinned down in this audit for the specific API dataset. | Cite the Harvard Growth Lab / Atlas of Economic Complexity and the exact dataset/API. Maintain retrieval-only treatment unless the applicable dataset terms are confirmed for redistribution. |

### 2.1 World Bank indicator-level audit

The current Growth download script uses:

- `NY.GDP.MKTP.KD.ZG` — GDP growth (annual %)
- `NY.GNP.PCAP.KD.ZG` — GNI per capita growth (annual %)

The World Bank metadata and dataset licensing documentation identify WDI as available under **Creative Commons Attribution 4.0 International (CC BY 4.0)** unless specifically labeled otherwise.

The repository should therefore retain these retrieved observations only with appropriate World Bank attribution and indicator identification.

Official sources:

- World Bank, World Development Indicators:
  https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators
- World Bank Data Access and Licensing:
  https://datacatalog.worldbank.org/public-licenses
- World Bank Summary Terms of Use:
  https://data.worldbank.org/summary-terms-of-use

### 2.2 IMF WEO audit

The IMF Copyright and Usage page contains special terms for published statistical **Data**. Those terms expressly include the **World Economic Outlook database**.

For the JESI WEO source:

- provider: International Monetary Fund;
- dataset: World Economic Outlook;
- current repository file: `WEOApr2026all.xlsx`;
- JESI use: government gross debt indicator and related resilience processing;
- attribution is required;
- materially transformed IMF Data should be identified as transformed;
- third-party material incorporated into a statistical product may have separate terms.

Official sources:

- IMF Copyright and Usage:
  https://www.imf.org/en/about/copyright-and-terms
- IMF WEO database:
  https://www.imf.org/en/Publications/WEO/weo-database

The WEO file is therefore **not** treated as MIT-licensed.

### 2.3 PWT 11.0 audit

PWT 11.0 is published by the Groningen Growth and Development Centre at the University of Groningen.

The official PWT 11.0 documentation states that the dataset is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)** and specifies the required citation to Feenstra, Inklaar and Timmer (2015).

Official source:

https://www.rug.nl/ggdc/productivity/pwt/?lang=en

The repository currently uses the preferable reproducible arrangement of keeping the retrieval/processing script while not committing the complete PWT raw dataset.

### 2.4 UNCTAD audit

The Strategic Autonomy pipeline retrieves the official UNCTAD merchandise import product concentration bulk dataset.

Current repository treatment:

- retrieval script retained;
- official endpoint retained in the script;
- raw bulk dataset not committed to the repository.

This avoids unnecessary redistribution of a large provider dataset while preserving reproducibility. Before a future release adds the raw UNCTAD dataset, the exact current provider terms and attribution requirements should be rechecked.

### 2.5 Harvard Atlas audit

The Strategic Autonomy pipeline retrieves ECI through the Harvard Growth Lab Atlas of Economic Complexity API.

Current repository treatment:

- retrieval script retained;
- API endpoint and country/year selection logic retained;
- raw Atlas dataset not committed to the repository.

Because this audit did not establish a sufficiently precise standalone license statement for the exact API dataset, the conservative policy is to keep it retrieval-only and re-check the applicable provider terms before redistributing raw Atlas data.

---

## 3. Current Repository Data Inventory

As of this review, the repository contains the following externally sourced raw data files:

| File | External source | Treatment |
|---|---|---|
| `data/raw/growth_indicators_2015_2025.csv` | World Bank WDI | **Keep in repository**, with attribution |
| `WEOApr2026all.xlsx` | IMF WEO April 2026 | **Keep in repository**, with IMF attribution and applicable transformation disclosure |

The following source datasets are **not currently committed as raw files**:

- Penn World Table 11.0
- UNCTAD import concentration bulk data
- Harvard Atlas ECI data

Their retrieval and processing scripts remain part of the reproducible pipeline.

---

## 4. Retrieval-Only Policy

For an external dataset that is not clearly licensed for repository redistribution, or where the exact applicable terms cannot be established with sufficient confidence, JESI should prefer retrieval-only treatment.

A retrieval-only source should retain, where practical:

- official provider name;
- exact dataset name;
- version/release or reference period;
- official source/API URL;
- variable/indicator names;
- retrieval script;
- transformation procedure;
- validation procedure; and
- attribution/citation information.

This approach is intended to preserve reproducibility without assuming redistribution rights that have not been verified.

---

## 5. Additional or Future Sources

Potential future JESI sources include:

- World Trade Organization (WTO)
- International Labour Organization (ILO)
- Organisation for Economic Co-operation and Development (OECD)
- World Intellectual Property Organization (WIPO)
- additional Harvard Growth Lab / Atlas datasets

No additional provider should be added to the repository's raw-data distribution set without a source-specific licensing and redistribution review.

---

## 6. Data Attribution Principles

For each external dataset used in JESI research, the project should record, where practical:

- provider;
- dataset name;
- exact indicator/variable;
- version, edition, or release date;
- official source URL;
- retrieval date;
- applicable license or terms;
- attribution requirement;
- redistribution status;
- material transformation applied by JESI; and
- relevant methodological documentation.

---

## 7. Provider Independence

Use of third-party data within JESI does not imply endorsement of JESI by the World Bank, IMF, Penn World Table/University of Groningen, UN Trade and Development, Harvard Growth Lab, or any other data provider.

JESI is an independent research framework developed by JAS.

---

## 8. Research Status

JESI is a proposed analytical framework and research index.

It is not an official statistical product of the World Bank, IMF, United Nations, UN Trade and Development, Penn World Table, WTO, ILO, OECD, WIPO, Harvard Growth Lab, or any other external institution.

Its methodological validity, robustness, historical performance, and comparative usefulness remain subjects of empirical research and validation.

---

## 9. Maintenance and Re-Audit

Provider licenses and data-use terms may change.

Before a major public or research release, the applicable terms for every external dataset used in that release should be re-checked against the provider's current official documentation.

**Last reviewed:** 2026-09-28
