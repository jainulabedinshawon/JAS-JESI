# JAS-JESI Data Sources and Licensing

This document records the provenance and source-specific usage conditions for external datasets used or retrieved by the JAS Unified Economic Strength Index (JESI).

> **Important:** The repository's MIT License applies to JAS-original source code unless a file states otherwise. It does not automatically relicense third-party datasets. Each third-party dataset remains subject to the terms of its original provider.

## 1. Current and Implemented Data Sources

| Source | Dataset / Indicator | Repository Use | Licensing / Terms | Attribution |
|---|---|---|---|---|
| World Bank | World Development Indicators (WDI), including GDP growth, GNI per capita growth and other indicators | Retrieved and processed by repository scripts and source modules; selected derived data may be stored under `data/raw/` | Subject to the World Bank's applicable dataset terms and licensing conditions | World Bank and the relevant dataset/indicator should be cited |
| International Monetary Fund (IMF) | World Economic Outlook (WEO), including government debt indicators | Used by the Resilience pillar pipeline; `WEOApr2026all.xlsx` is currently stored in the repository | Subject to the IMF's applicable data-use and redistribution terms | IMF and the specific WEO edition should be cited |
| Penn World Table | PWT 11.0, including Total Factor Productivity data | Used for Productivity P2 and related validation/scoring scripts | Subject to the Penn World Table's published license and attribution requirements | Cite Penn World Table and Feenstra, Inklaar and Timmer (2015) |
| UN Trade and Development (UNCTAD) | Trade/import concentration and related data | Used by Strategic Autonomy data-processing scripts | Subject to UNCTAD / United Nations applicable data terms | UN Trade and Development / UNCTAD Data Hub should be cited |

## 2. Planned or Potential Sources

The JESI methodology may use additional international sources, including:

- World Trade Organization (WTO)
- International Labour Organization (ILO)
- Organisation for Economic Co-operation and Development (OECD)
- World Intellectual Property Organization (WIPO)
- Harvard Growth Lab / Atlas of Economic Complexity

Before redistributing data from any additional source, the exact dataset, version, date, licensing terms, attribution requirements and redistribution permissions should be verified and recorded.

## 3. Repository Licensing Boundary

### 3.1 JAS-original source code

The repository's original source code is released under the MIT License, unless an individual file or component states otherwise.

This includes, where applicable:

- `src/`
- `scripts/`
- `tests/`
- `.github/workflows/`

The MIT License applies to JAS-original code and does not automatically apply to third-party data, third-party documentation, or third-party software components.

### 3.2 Third-party datasets

Third-party datasets are not automatically MIT-licensed merely because they are stored in this repository.

The terms of the original data provider remain applicable to the corresponding dataset.

Where a provider's terms differ from the repository's MIT License, the provider's terms control the use of that third-party material.

### 3.3 Derived data

JESI processing may transform, normalize, validate, aggregate or otherwise derive analytical variables from third-party data.

Such transformation does not automatically transfer ownership or licensing rights over the underlying third-party data.

Users should distinguish:

1. the original source data;
2. JAS processing code;
3. JAS-derived analytical outputs; and
4. the JESI methodological framework.

## 4. Data Attribution Principles

For each external dataset used in JESI research, the repository should record, where practical:

- Data provider
- Dataset name
- Indicator or variable
- Dataset/version or release
- Source URL
- Retrieval date
- License or applicable terms
- Attribution requirement
- Whether redistribution is permitted
- Any material transformation applied by the JESI pipeline

## 5. Redistribution Policy

Raw third-party datasets should only be redistributed when the applicable provider terms permit such redistribution.

Where redistribution rights are uncertain or restricted, the preferred approach is to provide:

- a retrieval script;
- the official source reference;
- dataset/version information;
- documented retrieval instructions; and
- the transformation and validation procedures required to reproduce the analysis.

## 6. Provider Independence

Use of third-party data within JESI does not imply endorsement of JESI by the World Bank, IMF, Penn World Table, UN Trade and Development, or any other data provider.

JESI is an independent research framework developed by JAS.

## 7. Research Status

JESI is a proposed analytical framework and research index.

It is not an official statistical product of the World Bank, IMF, United Nations, UN Trade and Development, Penn World Table, WTO, ILO, OECD, WIPO, Harvard Growth Lab, or any other external institution.

Its methodological validity, robustness, historical performance and comparative usefulness remain subjects of empirical research and validation.

## 8. Maintenance

Provider licensing and data-use terms may change over time.

Before a major public or research release, the applicable terms for every external dataset used in that release should be re-checked.

**Last reviewed:** 2026-09-28
