Contributing to JAS-JESI

Thank you for your interest in contributing to JAS-JESI (JAS Unified Economic Strength Index).

JAS-JESI is a research project focused on the empirical construction, validation, and reproducible analysis of a composite economic-strength index. Contributions from economists, statisticians, data scientists, software engineers, and other researchers are welcome.

Our goal is to improve the scientific validity, transparency, reproducibility, and practical usefulness of the project while protecting the integrity of its validated research outputs.

1. Guiding Principles

All contributions should follow these principles:

- Scientific integrity: Claims must be supported by evidence and appropriate references.
- Reproducibility: Changes should be testable and their results reproducible.
- Transparency: Data sources, transformations, assumptions, and limitations must be documented.
- Methodological consistency: Changes to the JESI methodology must be proposed and reviewed explicitly.
- Backward compatibility: Existing validated outputs must not be silently replaced.
- Respectful collaboration: Contributors must communicate professionally and constructively.

2. Ways to Contribute

You can contribute by:

- Identifying relevant economic indicators and authoritative data sources.
- Reviewing indicator validity, coverage, and measurement limitations.
- Improving normalization, missing-data handling, and robustness analysis.
- Identifying potentially redundant or highly correlated indicators.
- Improving data acquisition, validation, documentation, and reproducibility.
- Developing tests, dashboards, visualizations, and research utilities.
- Reporting bugs, proposing enhancements, and reviewing pull requests.

3. Before Making Changes

Before beginning substantial work:

1. Read the repository documentation and relevant methodology notes.
2. Search existing issues and pull requests to avoid duplicate work.
3. Open an issue to discuss significant methodological or architectural changes.
4. Clearly describe the problem, proposed solution, expected benefit, and possible risks.
5. Wait for appropriate discussion before implementing changes that could affect validated research outputs.

Small documentation corrections and isolated bug fixes may not require a separate issue.

4. Proposing a New Economic Indicator

New indicator proposals should use the repository's economic-indicator issue template when available.

A proposal should include:

- Indicator name and operational definition.
- Theoretical or empirical justification for measuring economic strength.
- Primary data source and relevant documentation.
- Geographic and temporal coverage.
- Units, frequency, and direction of interpretation.
- Known measurement problems and limitations.
- Missing-data patterns and proposed treatment.
- Potential overlap or redundancy with existing indicators.
- Proposed transformation and normalization, where relevant.
- References to peer-reviewed research or authoritative institutional publications.

A proposal is not automatically accepted because the data are available or the indicator appears economically relevant. Each candidate requires appropriate conceptual, statistical, and methodological review.

5. Data Provenance and Research Integrity

Contributors must:

- Prefer authoritative and documented sources, such as the World Bank, IMF, and relevant national statistical agencies.
- Record source identifiers, retrieval dates, units, and transformation steps where applicable.
- Preserve source values and distinguish them from processed values.
- Document revisions, estimation, interpolation, and other data treatments.
- Never fabricate observations, references, test results, or validation evidence.
- Respect applicable data licenses and terms of use.
- Clearly disclose known limitations and uncertainty.

When upstream data providers revise historical observations, the revision must be documented rather than silently treated as an unchanged dataset.

6. Code Contributions

Before submitting code:

1. Keep the change focused on a clearly defined purpose.
2. Follow the existing project structure and supported Python version.
3. Add or update tests where appropriate.
4. Avoid unrelated refactoring or dependency upgrades.
5. Do not commit credentials, access tokens, private data, or other secrets.
6. Do not modify validated baseline files unless the change has been explicitly justified and approved.
7. Document new configuration, dependencies, and user-facing behavior.

Where practical, changes should be tested using the repository's documented environment and test commands.

7. Methodology and Validated Outputs

The integrity of the JESI methodology and its validated outputs is a core project requirement.

Changes affecting indicator selection, weighting, normalization, missing-data treatment, scoring, country rankings, or historical results must include:

- A clear description of the methodological change.
- The rationale and supporting evidence.
- Relevant tests and validation results.
- Numerical-equivalence testing where applicable.
- Sensitivity or robustness analysis when appropriate.
- A comparison with the previous validated results.
- Explicit documentation of any expected changes in scores or rankings.

A successful software test alone does not establish scientific validity.

Data-refresh jobs may collect new data and produce validation reports and audit artifacts. They must not silently replace the validated baseline or publish changed results without the required review and validation.

8. Pull Request Process

Submit changes through a dedicated branch and pull request targeting "main".

A pull request should explain:

- What changed and why.
- Which files, indicators, workflows, or outputs are affected.
- How the change was tested.
- Any known limitations or unresolved questions.
- Whether the change can affect numerical results or backward compatibility.

Before merging, maintainers should review the relevant code, documentation, test results, data provenance, and methodological implications.

Do not merge changes that fail required checks or have unresolved material correctness, security, or reproducibility concerns.

Separate unrelated changes into separate pull requests whenever practical.

9. Dependencies and Security

Dependency changes must be justified and tested against the project's supported Python version.

Contributors should:

- Avoid unnecessary dependency additions.
- Preserve reproducible dependency specifications.
- Review dependency compatibility and known security vulnerabilities.
- Avoid introducing excessive permissions into GitHub Actions workflows.
- Prefer least-privilege workflow permissions.
- Never expose secrets in logs or generated artifacts.

Automated dependency-update pull requests must be evaluated individually. Version changes should not be merged solely because an automated tool proposed them.

10. Review and Acceptance

Maintainers may request clarification, additional tests, revised documentation, or further empirical validation.

A contribution may be declined if it lacks sufficient evidence, introduces unacceptable reproducibility risks, conflicts with the project's research objectives, or cannot be maintained reliably.

Acceptance of a contribution does not imply that every scientific claim associated with it has been independently established.

11. Research References and Attribution

Cite relevant datasets, documentation, software, and scholarly publications.

Contributors should distinguish established findings from hypotheses, interpretations, and proposed methods. Existing authorship and attribution must be respected.

Do not submit material that infringes copyright, violates data-use restrictions, or misrepresents another researcher's work.

12. Questions and Discussion

For questions, bug reports, research proposals, or methodological discussions, use the repository's GitHub Issues and Pull Requests.

Please provide enough context for others to understand, reproduce, and evaluate the issue.

Thank you for helping make JAS-JESI more transparent, reliable, and useful to the international research community.
