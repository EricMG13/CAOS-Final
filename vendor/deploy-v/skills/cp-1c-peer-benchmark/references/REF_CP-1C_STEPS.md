Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-1C_Discipline.md, REF_CP-1C_ValuationAndOutlierRules.md, REF_CP-1C_Workflow.md.

Original files, in this bundle: REF_CP-1C_00_PeerDiscoveryGate.md, REF_CP-1C_01_PeerDataGate.md, REF_CP-1C_02_PeerUniverseRegister.md, REF_CP-1C_03_MetricAlignmentRegister.md, REF_CP-1C_04_PeerBenchmarkRegisters.md, REF_CP-1C_05_OutlierRegister.md, REF_CP-1C_06_ValuationComps.md, REF_CP-1C_07_PeerInterpretationCreditTranslation.md, REF_CP-1C_08_GapsLimitationsLedger.md, REF_CP-1C_09_OverallPeerBenchmarkingView.md, REF_CP-1C_Discipline.md, REF_CP-1C_ValuationAndOutlierRules.md, REF_CP-1C_Workflow.md

## REF_CP-1C_00_PeerDiscoveryGate.md
<!-- REF_CP-1C_00 (T2) | 2026-06-02 -->
<step_reference module="CP-1C" step="00" name="Peer Discovery Gate">
<input>CP-1 borrower profile + input payload</input>
<gate>User peer list present?</gate>

## Instructions
IF NO user list → Execute web discovery: construct queries from CP-1 profile (sector/geography/revenue scale/business model/capital structure/public-private/key product), query 6 source types (regulatory filings, rating disclosures, industry DBs, LevFin databases, financial news, IR pages), promote if ≥3/16 dimensions assessable, and tag all promoted candidates `Web-Scraped — Unverified`. Record candidate, query/source, URL or source locator, retrieval date, dimensions assessed, promotion decision and limitation in T4.D1 inside the canonical Markdown appendix. Carry selected peers into T4.1; do not create a JSON sidecar.
IF YES → Proceed to Step 1. Web scrape optional supplement.

## Output
Conditional T4.D1 Peer Discovery Source Register inside the canonical Markdown handoff when discovery runs; otherwise record that discovery was not required. No separate artifact.
</step_reference>
## REF_CP-1C_01_PeerDataGate.md
<!-- REF_CP-1C_01 (T2) | 2026-06-02 -->
<step_reference module="CP-1C" step="01" name="Peer Data Gate">
<input>Step 0 output + sources</input>
<gate>Sufficient peer data</gate>

## Instructions
Validate each candidate has accessible financial data. If web-scraped, confirm data beyond entity identification. Identify all peer source materials by name/type/period/evidence quality/provenance. Confirm CP-1 borrower data available. Flag if insufficient.

## Output
Data sufficiency assessment. Status: Full Run / Ready with Limitations / Blocked.
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-1C_02_PeerUniverseRegister.md
<!-- REF_CP-1C_02 (T2) | 2026-06-02 -->
<step_reference module="CP-1C" step="02" name="Peer Universe Register">
<input>Steps 0-1</input>
<gate>Peer-First Gate</gate>

## Instructions
Apply Peer Source Hierarchy. Per peer: entity name, category label, source provenance, scrape URL/date (if web-scraped), 16 dimensions assessed, strengths, limitations, data availability, evidence quality, usability scope. Apply 13 exclusion rules. Log excluded with reasons.

## Output
T4.1: `Entity Name`|`Peer Category Label`|`Source of Selection`|`Dimensions Assessed`|`Strengths`|`Limitations`|`Data Availability`|`Evidence Quality Tier`|`Usable For`|`Exclusion Reason`
</step_reference>
## REF_CP-1C_03_MetricAlignmentRegister.md
<!-- REF_CP-1C_03 (T2) | 2026-06-02 -->
<step_reference module="CP-1C" step="03" name="Metric Alignment Register">
<input>T4.1 + CP-1 data</input>
<gate>T4.1 complete</gate>

## Instructions
For every planned comparison, apply 11-point alignment standard. Assign comparability status. Log limitations. Web-scraped vs audited = provenance gap flag.

Apply the 9 Non-Comparability Triggers in REF_CP-1C_ValuationAndOutlierRules.md when assigning Not Comparable / Comparable with Limitations.

## Output
T4.2: `Metric`|`Borrower Value`|`Borrower Period`|`Peer Entity`|`Peer Value`|`Peer Period`|`AP1-AP11`|`Comparability Status`|`Limitation Notes`
</step_reference>
## REF_CP-1C_04_PeerBenchmarkRegisters.md
<!-- REF_CP-1C_04 (T2) | 2026-06-02 -->
<step_reference module="CP-1C" step="04A" name="Operating Benchmark Table">
<input>T4.1 + T4.2</input>
<gate>Alignment complete</gate>

## Instructions
Borrower-vs-peer operating metrics. Include peer statistics per rules (min 3 median, 5 avg). State N.

## Output
T4.3: `Entity`|`Revenue`|`Rev Growth`|`Gross Margin`|`EBITDA`|`EBITDA Margin`|`EBIT Margin`|`Period`|`Currency`|`Calc Status`|`Comp Status`
</step_reference>

<step_reference module="CP-1C" step="04B" name="Cash Flow & Capital Intensity">
<input>T4.1 + T4.2</input>
<gate>Alignment complete</gate>

## Instructions
Borrower-vs-peer cash flow and capex. Same cell specs as 4A.

## Output
T4.4: `Entity`|`FCF`|`FCF Conversion`|`Capex/Rev`|`Capex/EBITDA`|`WC/Rev`|`Period`|`Currency`|`Calc Status`|`Comp Status`
</step_reference>

<step_reference module="CP-1C" step="04C" name="Credit Metric Benchmark">
<input>T4.1 + T4.2</input>
<gate>Alignment complete</gate>

## Instructions
Borrower-vs-peer leverage, coverage, liquidity. Same specs.

## Output
T4.5: `Entity`|`Total Lev`|`Net Lev`|`Sr Sec Lev`|`Int Coverage`|`Adj Int Coverage`|`FFO/Debt`|`Liquidity`|`Period`|`Currency`|`Calc Status`|`Comp Status`
</step_reference>

<step_reference module="CP-1C" step="04D" name="Summary Statistics">
<input>T4.3+T4.4+T4.5</input>
<gate>≥1 benchmark table</gate>

## Instructions
Summary peer statistics with borrower positioning. Min 3 for median, 4 quartile, 5 avg. <2 → no stats.

## Output
T4.6: `Metric`|`Borrower Value`|`Peer Avg`|`Median`|`Min`|`Max`|`Q1`|`Q3`|`N`|`Borrower Position`
</step_reference>
## REF_CP-1C_05_OutlierRegister.md
<!-- REF_CP-1C_05 (T2) | 2026-06-02 -->
<step_reference module="CP-1C" step="05" name="Outlier Register">
<input>T4.3-T4.6</input>
<gate>Sufficient peer data</gate>

## Instructions
Apply outlier logic per the Outlier Rules in REF_CP-1C_ValuationAndOutlierRules.md. Per outlier: entity, metric, value, peer range, deviation, direction (5 labels), credit translation (6 dimensions). If borrower outlier → flag prominently. Comparability-caused → Non-Comparable.

Additional rules: quantify deviation magnitude against the peer range; assess cause (operational difference / data quality / comparability misalignment / one-off event); if an outlier distorts peer statistics, recalculate excluding it and show both versions; flag outlier-status changes across periods with credit implication.

## Output
T4.7: `Entity`|`Metric`|`Value`|`Peer Range (Min/Max/Med/Avg)`|`Deviation`|`Direction`|`Operating Impl`|`CF Impl`|`Lev/Liq Impl`|`Refi Impl`|`Valuation Impl`|`Downstream Handoff`
</step_reference>
## REF_CP-1C_06_ValuationComps.md
<!-- REF_CP-1C_06 (T2) | 2026-06-02 -->
<step_reference module="CP-1C" step="06A" name="Public Trading Comps">
<input>T4.1 (public peers)</input>
<gate>Public peers available</gate>

## Instructions
Produce trading comps table. Apply the 12-point Valuation Discipline and EV formula in REF_CP-1C_ValuationAndOutlierRules.md. Stale multiples (>12mo) labelled. No averaging non-comparable.

## Output
T4.8: `Entity`|`Mkt Cap`|`Mkt Cap Date`|`EV`|`EV/Rev`|`EV/EBITDA`|`Period Used`|`Metric Def`|`Comp Status`|`Source`
</step_reference>

<step_reference module="CP-1C" step="06B" name="Transaction Comps">
<input>T4.1 (transaction comps)</input>
<gate>Transaction data available</gate>

## Instructions
Produce transaction comps. Multiples use contemporaneous financial data.

## Output
T4.9: `Txn Name`|`Date`|`Type`|`Buyer/Seller`|`TV`|`TV/Rev`|`TV/EBITDA`|`Period Used`|`Metric Def`|`Comp Status`|`Source`
</step_reference>

<step_reference module="CP-1C" step="06C" name="Implied EV Table">
<input>T4.8+T4.9+CP-1 metrics</input>
<gate>Sufficient multiples</gate>

## Instructions
Calculate implied EV: 4 methods (EV/EBITDA, EV/Revenue, TV/EBITDA, TV/Revenue) + range (Low/Median/High) using the Implied EV Formulas and Valuation Calculation Constraints in REF_CP-1C_ValuationAndOutlierRules.md. Each calculation states: multiple source, borrower metric used, period, definition, calculation status. State: indicative context ONLY, NOT recovery estimate (recovery belongs to CP-4 / CP-4A). Web-scraped multiples → 'Provisional — Web-Sourced' if not cross-checked.

## Output
T4.10: `Method`|`Multiple Source`|`Multiple Value`|`Borrower Metric`|`Period`|`Implied EV`|`Low`|`Median`|`High`|`Calc Status`|`Limitations`
</step_reference>
## REF_CP-1C_07_PeerInterpretationCreditTranslation.md
<!-- REF_CP-1C_07 (T2) | 2026-06-02 -->
<step_reference module="CP-1C" step="07" name="Peer Interpretation & Credit Translation">
<input>T4.1-T4.10</input>
<gate>≥1 benchmark table</gate>

## Instructions
Synthesize benchmarking tables, outliers, valuation context into credit conclusions. Apply analytical chain. Address: competitive position, leverage/coverage, cash-flow quality, valuation-support, uncertainties. Connect to downstream. Synthesis only — no new data.

## Output
Peer-interpretation narrative in `## Analysis` of the canonical Markdown handoff. It supports, but does not replace, the final Step 9 Overall Peer View and creates no separate artifact.
</step_reference>
## REF_CP-1C_08_GapsLimitationsLedger.md
<!-- REF_CP-1C_08 (T2) | 2026-06-02 -->
<step_reference module="CP-1C" step="08" name="Gaps & Limitations Ledger">
<input>Steps 0-7</input>
<gate>Always</gate>

## Instructions
Comprehensive cumulative ledger. Web scrape provenance rules: (a) count by provenance, (b) list unverified peers, (c) downstream impact. All web-scraped + uncorroborated → severity=High.

## Output
T4.11: `Gap`|`Affected Metric/Section`|`Affected Peer(s)`|`Downstream Impact`|`Severity`|`Recommended Action`
</step_reference>
## REF_CP-1C_09_OverallPeerBenchmarkingView.md
<!-- REF_CP-1C_09 (T2) | 2026-06-02 -->
<step_reference module="CP-1C" step="09" name="Overall Peer View">
<input>Steps 0-8</input>
<gate>Always</gate>

## Instructions
Module summary: (a) borrower + peer universe, (b) key findings (operating/CF/credit-metric/valuation), (c) borrower outlier positions, (d) material comparability limitations, (e) implied-EV context with caveats, (f) important gaps, (g) downstream readiness, (h) peer provenance composition + confidence impact.

## Output
Module summary narrative in the canonical Markdown handoff.
</step_reference>
## REF_CP-1C_Discipline.md
<!-- REF_CP-1C_Discipline (T2 Library) | 2026-07-11 | Relocated from CP-1C_ACTIVE_PROMPT.md §Prohibited Behaviors per SEC8 compression -->
<library_reference module="CP-1C" name="Prohibited Behaviors — Full Binding List">
<consumers>CP-1C_ACTIVE_PROMPT.md (Prohibited Behaviors section)</consumers>

# CP-1C Prohibited Behaviors — Full Binding List (relocated from ACTIVE_PROMPT 2026-07-11)

1. No fabrication of peer metrics/ownership/market shares/EV/multiples/sponsor behavior
2. No presenting comparisons as conclusive where comparability limited
3. No equity-upside framing, promotional language, unsupported superlatives
4. No standalone investment recommendations from multiples
5. No forced conclusions from incomplete data
6. No peer statistics where insufficient comparable datapoints
7. No mixing financial bases (IFRS/GAAP, FYE, perimeters, currencies) without flagging
8. No treating web-scraped peers as equivalent to analyst-selected
9. No suppressing "Web-Scraped — Unverified" evidence tag
</library_reference>
## REF_CP-1C_ValuationAndOutlierRules.md
<!-- REF_CP-1C_ValuationAndOutlierRules (T2 Library) | 2026-06-10 | Restored from CP-1C__SUPPORT__Metric_Alignment_Calculation_Outlier_and_Valuation_Rules §2.6.3, 2.7.3–2.7.4, 2.8, 2.9.5 -->
<library_reference module="CP-1C" name="Valuation and Outlier Rules">
<consumers>REF_CP-1C_03 (Metric Alignment); REF_CP-1C_05 (Outlier Register); REF_CP-1C_06A/06B/06C (Comps & Implied EV)</consumers>

# CP-1C Valuation and Outlier Rules

## Non-Comparability Triggers (9)
The following situations trigger Not Comparable or Comparable with Limitations:
1. Different EBITDA definitions (reported vs adjusted vs credit-agreement) without reconciliation.
2. Different FYE alignment without period adjustment.
3. IFRS vs US GAAP treatment of leases, pensions, or intangibles without adjustment.
4. Currency mismatch without exchange-rate disclosure.
5. Different leverage definition (gross vs net, total vs senior) without reconciliation.
6. Perimeter difference (consolidated vs restricted group vs guarantor group).
7. Peer data more than 12 months older than borrower data without disclosure.
8. Different capex classification (maintenance vs growth vs total).
9. Peer metric calculated from insufficient source data.

## Outlier Rules
- Apply outlier classification to both borrower and peers. If the borrower is an outlier among its peer group, flag it prominently and state the credit implication.
- Quantify outlier materiality: state the datapoint, the peer range (min, max, median, average where available), and the magnitude of the deviation.
- Do not dismiss outliers without credit-relevant explanation. Assess whether the outlier reflects (a) genuine operational difference, (b) data-quality issue, (c) comparability misalignment, or (d) one-off event.
- If an outlier distorts peer statistics, recalculate the statistic excluding the outlier and show both versions.
- Outlier classification must be consistent across periods. If outlier status changes between periods, flag the change and the credit implication.
- Where an outlier results from a known comparability limitation (different definition, accounting standard, or perimeter), classify it as Non-Comparable rather than Favorable or Unfavorable.

## Enterprise Value Formula
EV = Equity Value (market cap or transaction equity value) + Total Debt + Minority Interests + Preferred Equity − Cash & Cash Equivalents − Short-Term Investments (if liquid and available).
State the EV formula explicitly. If any component is estimated or unavailable, flag the limitation.

## Implied EV Formulas
- Implied EV from EV/EBITDA = Peer EV/EBITDA multiple × Borrower EBITDA.
- Implied EV from EV/Revenue = Peer EV/Revenue multiple × Borrower Revenue.
- Implied EV from Transaction EV/EBITDA = Transaction multiple × Borrower EBITDA.
- Implied EV from Transaction EV/Revenue = Transaction multiple × Borrower Revenue.
- Implied EV Range: Low = minimum peer multiple × borrower metric; Median = median peer multiple × borrower metric; High = maximum peer multiple × borrower metric.

Each implied-EV calculation must state: the multiple source, the borrower metric used, the period, the definition, and the calculation status.

## Valuation Discipline (12 Points)
1. All multiples must be sourced, with source file and date stated.
2. All multiples must use the same metric definition as the borrower metric they are compared against, or the definition difference must be flagged.
3. Stale multiples (more than 12 months old) must be labelled as such.
4. Transaction multiples must state transaction date, transaction type, buyer/seller, and perimeter.
5. Public-company multiples must state the market-cap date and the financial period used for the denominator.
6. Do not average multiples from non-comparable entities.
7. Do not present implied EV without stating all assumptions and limitations.
8. Do not present implied EV as a recovery estimate or debt-coverage conclusion — that belongs to CP-4 / CP-4A.
9. Implied EV calculations are indicative context, not definitive valuations.
10. If the borrower is private and no equity value is available, state the limitation and use implied-EV methods only.
11. Currency must be consistent across all valuation calculations, or exchange rates disclosed.
12. Sector multiples require a minimum of 3 comparable datapoints to be meaningful.

## Valuation Calculation Constraints
- EV/EBITDA and EV/Revenue must use the same-period EBITDA and Revenue as the borrower comparison basis.
- Transaction multiples must use the EBITDA or Revenue figure contemporaneous with the transaction date.
- Do not blend trading multiples and transaction multiples in the same average or median without flagging.

## Numeric Hygiene
- Percentages: decimals or percentage notation, consistent throughout the module.
- Multiples: Nx format (e.g., 5.2x).
- Currency stated for every absolute figure.
- Rounding matches the precision established by CP-1 or the peer source.
- Null handling: if any input to a formula is null, the result is null — not zero, not estimated.

## Label Taxonomies (closed sets — use only these values)
- **Comparability Status** (REF_CP-1C_03 `Comparability Status`): `Comparable` | `Comparable with Limitations` | `Not Comparable` | `Insufficient Information`.
- **Calculation Status** (any computed peer/borrower metric): `Reported` | `Calculated` | `Derived` | `Provisional` | `Not Comparable` | `Insufficient Information`.
- **Outlier Direction** (REF_CP-1C_05 `Direction`, the "5 labels"): `Favorable` | `Unfavorable` | `Mixed` | `Non-Comparable` | `Insufficient Information`.
  - Where an outlier arises from a comparability limitation (definition / accounting standard / perimeter), classify `Non-Comparable`, not `Favorable`/`Unfavorable`.
  - Each outlier maps to the 6 credit-translation dimensions in REF_CP-1C_05's output: operating, cash-flow, leverage/liquidity, refinancing, valuation-context, and downstream handoff.

## 11-Point Metric Alignment Standard (AP1–AP11, REF_CP-1C_03)
Every planned comparison records: AP1 borrower definition · AP2 peer definition · AP3 source period ·
AP4 currency · AP5 accounting basis (IFRS/US GAAP) · AP6 actual vs pro forma basis · AP7 reported vs
adjusted basis · AP8 LTM/YTD/quarterly/annualized basis · AP9 source quality / provenance · AP10
normalization treatment · AP11 resulting comparability status. Any unbridged mismatch on AP1–AP10
drives AP11 to `Not Comparable` or `Comparable with Limitations`.

## Peer Statistic Rules
Do not calculate average, median, quartile, range, standard deviation, or percentile unless sufficient
comparable datapoints exist (minimum 2 for any "range"/"average" label; minimum 3 for a meaningful
sector multiple). Exclude non-comparable datapoints from summary statistics and state why. Do not rank
the borrower where the peer set is incomplete or definitions differ materially.

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Institutional-grade, committee-ready, creditor-first, evidence-led. Tables for numeric benchmarking. Prose for narrative. No filler. No equity-upside framing.

## Web Scrape Discovery Protocol (relocated from ACTIVE_PROMPT 2026-07-11)
Trigger: Auto when no user list. Optional supplement when user list present.
Scrape Params (from CP-1): Sector/sub-sector, geography, revenue scale band, business model, capital structure, public/private, key product/service.
Permitted Sources (ranked): (1) Regulatory filings (2) Rating agency disclosures (3) Industry classification DBs (4) LevFin deal databases (5) Financial news (6) Company IR pages.
Promotion: ≥3 of 16 comparability dimensions assessable. Evidence floor: "Web-Scraped — Unverified".
Output: conditional T4.D1 Peer Discovery Source Register in the canonical Markdown appendix. Carry promoted peers into T4.1. Do not create a JSON sidecar.

## Execution Rules (relocated from ACTIVE_PROMPT 2026-07-11)
1. Peer-First Gate: No benchmark tables until Peer Universe Register + Metric Alignment Register complete.
2. Definition Inheritance: All borrower metrics from CP-1. Peer metrics aligned or flagged.
3. Comparability-Before-Statistics: Assign status before any aggregate.

## Peer Statistic Rules — ACTIVE_PROMPT Thresholds (relocated from ACTIVE_PROMPT 2026-07-11)
Min 3 for median, 4 for quartile, 5 for average. <2 → no statistics. Exclude non-comparable. State N. Outlier distorts average → median alongside + flag.

## 15 Core Formulas — inherited from CP-1 (relocated from ACTIVE_PROMPT 2026-07-11)
1 Gross Margin = Gross Profit / Revenue | 2 EBITDA Margin = EBITDA / Revenue | 3 EBIT Margin = EBIT / Revenue | 4 Net Income Margin = Net Income / Revenue | 5 Revenue Growth = (Current − Prior Revenue) / Prior Revenue | 6 EBITDA Growth = (Current − Prior EBITDA) / Prior EBITDA | 7 Total Leverage = Total Debt / EBITDA | 8 Net Leverage = Net Debt / EBITDA | 9 Senior Secured Leverage = Senior Secured Debt / EBITDA | 10 Interest Coverage = EBITDA / Cash Interest Paid | 11 Adjusted Interest Coverage = (EBITDA − Capex) / Cash Interest Paid | 12 FFO / Total Debt | 13 FCF Conversion = FCF / EBITDA | 14 Capex / Revenue | 15 Liquidity = Cash + Undrawn Committed Facilities

## Peer Source Hierarchy — 7 Tiers (relocated from ACTIVE_PROMPT 2026-07-11)
| Tier | Source | Evidence Quality |
|------|--------|-----------------|
| 1 | Web-scraped discovery (auto when no user list) | Web-Scraped — Unverified |
| 2 | User-provided peer list (analyst instruction) | Highest override |
| 3 | Document-disclosed (LP, OM, rating report) | Document-Disclosed |
| 4 | Internal sector review / portfolio screening | Internal |
| 5 | Public-company peers (sector/product overlap) | Public Sources |
| 6 | Transaction comparables (deal databases) | Transaction Sources |
| 7 | Broader sector comparables (directional only) | Contextual |

## 16 Comparability Dimensions (relocated from ACTIVE_PROMPT 2026-07-11)
Product/service similarity | Revenue model | End-market exposure | Geography | Customer type/concentration | Contract structure | Margin structure | Capex intensity | Working-capital dynamics | Leverage/capital structure | Public vs private | Accounting standard | Fiscal-period alignment | Data availability | Valuation relevance | Source provenance

## 8 Peer Category Labels (relocated from ACTIVE_PROMPT 2026-07-11)
Borrower/Issuer | Direct Operating Peer | Sector Peer | Rating/Leverage Peer | Public Trading Comp | Transaction Comp | Internal RV Peer | Excluded/Not Comparable

## Exclusion Rules — 13 Triggers (relocated from ACTIVE_PROMPT 2026-07-11)
No overlapping periods | Irreconcilable accounting | Different business model | Data >18mo stale | Insufficient data | Distress distortion | Irreconcilable perimeter | Irreconcilable currency/unit | Misleading to committee | [Web Scrape] Unverifiable | [Web Scrape] Sector overlap unconfirmed | [Web Scrape] Data contradicted | [Web Scrape] Financials behind paywall

## 11-Point Alignment Standard — ACTIVE_PROMPT form (relocated from ACTIVE_PROMPT 2026-07-11)
(1) Metric definition (2) Adjustment basis (3) Reporting period (4) Period length (5) Accounting standard (6) Currency (7) Unit (8) Perimeter (9) Data source quality (10) Calculation status (11) Source provenance parity
</library_reference>
## REF_CP-1C_Workflow.md
<!-- REF_CP-1C_Workflow (T2 Library) | 2026-07-11 | Relocated from CP-1C_ACTIVE_PROMPT.md §Workflow per SEC8 compression -->
<library_reference module="CP-1C" name="Workflow Steps 0-9">
<consumers>CP-1C_ACTIVE_PROMPT.md (Workflow section)</consumers>

# CP-1C Workflow — Steps 0–9 (relocated from ACTIVE_PROMPT 2026-07-11)

| Step | Name | REF File | Output |
|------|------|----------|--------|
| 0 | Peer Discovery Gate | REF_CP-1C_00 | Peer candidate list |
| 1 | Peer Data Gate | REF_CP-1C_01 | Data sufficiency |
| 2 | Peer Universe Register | REF_CP-1C_02 | T4.1 |
| 3 | Metric Alignment Register | REF_CP-1C_03 | T4.2 |
| 4A | Operating Benchmark | REF_CP-1C_04A | T4.3 |
| 4B | Cash Flow & Cap Intensity | REF_CP-1C_04B | T4.4 |
| 4C | Credit Metric Benchmark | REF_CP-1C_04C | T4.5 |
| 4D | Summary Statistics | REF_CP-1C_04D | T4.6 |
| 5 | Outlier Register | REF_CP-1C_05 | T4.7 |
| 6A | Public Trading Comps | REF_CP-1C_06A | T4.8 |
| 6B | Transaction Comps | REF_CP-1C_06B | T4.9 |
| 6C | Implied EV | REF_CP-1C_06C | T4.10 |
| 7 | Peer Interpretation | REF_CP-1C_07 | Analytical narrative |
| 8 | Gaps & Limitations | REF_CP-1C_08 | T4.11 |
| 9 | Overall Peer View | REF_CP-1C_09 | Module summary |
</library_reference>
