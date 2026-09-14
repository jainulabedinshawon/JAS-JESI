JAS Unified Economic Strength Index (JESI)

Indicator Direction Matrix — Version 1.0

Project: JAS Unified Economic Strength Index (JESI)
Benchmark Period: 2015–2024
Countries: Bangladesh, India, Viet Nam, Indonesia, Malaysia

---

1. Purpose

This matrix defines the baseline economic direction and normalization treatment for each indicator included in JESI Master Version 1.0.

The direction of an indicator represents the relationship between its observed value and the conceptual strength of the relevant JESI pillar.

Direction assumptions are theoretical baseline specifications and will be subjected to empirical robustness testing.

---

2. Growth Pillar

G1 — Real GDP Growth Rate

Direction: Higher = Better

Baseline transformation: Positive min–max normalization.

Rationale: Sustained real economic growth generally indicates an economy's capacity to expand productive output.

---

G2 — GNI per Capita Growth

Direction: Higher = Better

Baseline transformation: Positive min–max normalization.

Rationale: Growth in GNI per capita provides an indication of whether economic expansion is translating into higher income availability on a per-person basis.

---

3. Productivity Pillar

P1 — GDP per Person Employed

Direction: Higher = Better

Baseline transformation: Positive min–max normalization.

Rationale: Higher output per employed person generally indicates stronger labor productivity and productive capacity.

---

P2 — Total Factor Productivity Growth

Direction: Higher = Better

Baseline transformation: Positive min–max normalization.

Rationale: TFP growth captures improvements in the efficiency with which labor, capital and other productive inputs are transformed into output.

---

4. Connectivity Pillar

C1 — Trade Openness

Direction: Higher = Better — Baseline

Baseline transformation: Positive min–max normalization.

Rationale: Greater trade integration generally provides access to international markets, goods, services, technology and global production networks.

Caution: Extremely high external exposure may also increase vulnerability. This possibility will be evaluated through robustness analysis rather than imposed directly in the baseline specification.

---

C2 — FDI Inflows

Direction: Higher = Better — Baseline

Baseline transformation: Positive min–max normalization.

Rationale: FDI can provide capital, technology, managerial knowledge, productive linkages and access to international business networks.

Caution: FDI quantity does not fully capture FDI quality, sectoral composition, domestic value creation or concentration. These limitations should be considered in interpretation.

---

C3 — ICT & Global Integration

Direction: Higher = Better

Baseline transformation: Positive min–max normalization.

Rationale: Greater digital and international integration can improve access to information, markets, knowledge, technology and global economic networks.

---

5. Resilience Pillar

R1 — Foreign Exchange Reserves / Import Cover

Direction: Higher = Better — Baseline

Baseline transformation: Positive min–max normalization.

Rationale: Greater reserve coverage generally provides a stronger external liquidity buffer against import needs, balance-of-payments pressure and external shocks.

Caution: Excessive reserve accumulation may have opportunity costs and does not automatically imply stronger overall economic performance. Alternative specifications may therefore be tested.

---

R2 — General Government Gross Debt / GDP

Direction: Nonlinear / Context-Dependent

Baseline transformation: Target/penalty-based specification.

Rationale: Government debt cannot reliably be interpreted through a universal "lower is always better" rule. Debt sustainability depends on economic growth, interest rates, maturity structure, currency composition, refinancing conditions and fiscal capacity.

Methodological requirement: The baseline score should penalize potentially unsustainable debt levels while avoiding the assumption that the lowest observed debt ratio is automatically optimal.

---

R3 — Current Account Balance / GDP

Direction: Target-Optimal / Nonlinear

Baseline transformation: Distance-from-reference-zone specification.

Rationale: Both persistent large current-account deficits and unusually large surpluses may indicate structural imbalances under different circumstances.

A generic deviation measure is:

[
D_i = |CA_i-CA^*|
]

where CA^* represents a theoretically justified reference level or zone.

Greater deviation from the reference zone will generally receive a lower resilience score.

---

6. Strategic Autonomy Pillar

A1 — Economic Complexity Index

Direction: Higher = Better

Baseline transformation: Positive min–max normalization.

Rationale: Greater economic complexity generally reflects a broader and more sophisticated productive structure and greater capacity to produce diverse and knowledge-intensive goods.

---

A2 — High-Tech Exports / Manufactured Exports

Direction: Higher = Better

Baseline transformation: Positive min–max normalization.

Rationale: A greater share of high-technology exports may indicate stronger technological capability and participation in technologically advanced production networks.

Caution: Export share alone does not fully measure domestic technological ownership or value-added depth.

---

A3 — Critical Import Concentration

Direction: Lower = Better

Baseline transformation: Negative min–max normalization.

[
N_i =
\frac{X_{max}-X_i}
{X_{max}-X_{min}}
]

Rationale: Greater concentration of critical imports among a small number of external suppliers can increase vulnerability to geopolitical, logistical, financial or supply-chain disruptions.

Lower concentration therefore represents stronger strategic autonomy.

---

7. Summary Matrix

Code| Indicator| Pillar| Baseline Direction| Transformation
G1| Real GDP Growth| Growth| Higher = Better| Positive min–max
G2| GNI per Capita Growth| Growth| Higher = Better| Positive min–max
P1| GDP per Person Employed| Productivity| Higher = Better| Positive min–max
P2| TFP Growth| Productivity| Higher = Better| Positive min–max
C1| Trade Openness| Connectivity| Higher = Better*| Positive min–max
C2| FDI Inflows| Connectivity| Higher = Better*| Positive min–max
C3| ICT & Global Integration| Connectivity| Higher = Better| Positive min–max
R1| FX Reserves / Import Cover| Resilience| Higher = Better*| Positive min–max
R2| Government Gross Debt / GDP| Resilience| Nonlinear| Target/Penalty
R3| Current Account / GDP| Resilience| Target-Optimal| Distance-based
A1| Economic Complexity Index| Strategic Autonomy| Higher = Better| Positive min–max
A2| High-Tech Exports / Manufactured Exports| Strategic Autonomy| Higher = Better| Positive min–max
A3| Critical Import Concentration| Strategic Autonomy| Lower = Better| Negative min–max

* Subject to robustness testing for possible nonlinear relationships.

---

8. General Direction Rule

The baseline JESI methodology distinguishes between:

Positive indicators

Higher values indicate stronger structural performance.

[
N_i=\frac{X_i-X_{min}}{X_{max}-X_{min}}
]

Negative indicators

Lower values indicate stronger structural performance.

[
N_i=\frac{X_{max}-X_i}{X_{max}-X_{min}}
]

Nonlinear or target-optimal indicators

Neither a purely positive nor purely negative transformation is assumed.

These indicators require economically justified transformations and explicit robustness testing.

---

9. Interpretation Principle

The direction assigned to an indicator is a methodological hypothesis, not a claim of universal causality.

JESI therefore distinguishes between:

1. theoretical direction,
2. baseline statistical transformation,
3. alternative specifications,
4. empirical robustness,
5. and eventual interpretation.

No individual indicator should be interpreted as a complete measure of economic strength on its own.

---

Status: Version 1.0 — Baseline Direction Matrix

Next methodological task: Final mathematical specification for nonlinear Resilience indicators, particularly Government Debt and Current Account Balance.
