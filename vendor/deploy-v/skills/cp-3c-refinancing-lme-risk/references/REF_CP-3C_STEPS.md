Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-3C_PathsAndScoring.md.

Original files, in this bundle: REF_CP-3C_01_RefinancingLMESourceGate.md, REF_CP-3C_02_MaturityWallRefinancingRegister.md, REF_CP-3C_03_LiquidityFCFMarketAccess.md, REF_CP-3C_04_LegalCapacityForLME.md, REF_CP-3C_05_SponsorGovernanceWillingness.md, REF_CP-3C_06_RefinancingPathAssessment.md, REF_CP-3C_07_PrimeLMEVulnerabilityScore.md, REF_CP-3C_08_CreditorClassExposure.md, REF_CP-3C_09_MonitoringTriggers.md, REF_CP-3C_10_ScenarioMap.md, REF_CP-3C_11_GapsLedger.md, REF_CP-3C_12_OverallRefinancingLMEView.md, REF_CP-3C_PathsAndScoring.md

## REF_CP-3C_01_RefinancingLMESourceGate.md
<!-- REF_CP-3C_01 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="01" name="Refinancing / LME Source Gate">
<input>All available source materials: debt schedules, maturity profiles, credit agreements, indentures, CP-1/CP-1A financials, CP-2A downside pathways, CP-2D liquidity bridge, CP-4/CP-4A legal/covenant outputs, CP-2C sponsor evidence, market data, lender presentations, term sheets, rating agency reports.</input>
<gate>Always executes. This IS the gate check. BLOCKING: Minimum maturity/debt-schedule data must be available. If no debt maturity or capital structure data: Module Status = Blocked, STOP.</gate>

## Instructions
1. Catalogue all sources: source_document_id, source_document_name, source_quality, period/date, entity_covered, data_supplied, limitation, downstream_use.
2. Verify minimum evidence: maturity/debt-schedule data available.
3. If no maturity data: Module Status = Blocked, STOP.
4. Assess source quality: governing executed legal documents outrank drafts, summaries, term sheets, posting memoranda, lender presentations, and third-party covenant-review reports.
5. Check availability of each evidence category: maturity/debt schedule, liquidity/FCF, market data, legal/covenant (CP-4/CP-4A), sponsor/governance (CP-2C), downside (CP-2A), liquidity bridge (CP-2D).
6. Flag draft, unsigned, stale, incomplete, or conflicting documents — reduce confidence.
7. Assign Module Status: Full Run / Ready with Limitations / Blocked.

## Output
T3D.1: `source_document_id`|`source_document_name`|`source_quality`|`period / date`|`entity_covered`|`data_supplied`|`limitation`|`downstream_use`
+ Module Status: Full Run / Ready with Limitations / Blocked

<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (CP-1/CP-1A financials, CP-2A downside, CP-2D liquidity bridge, CP-4/CP-4A legal/covenant, CP-2C sponsor) with their run_id/period. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
## REF_CP-3C_02_MaturityWallRefinancingRegister.md
<!-- REF_CP-3C_02 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="02" name="Maturity Wall and Refinancing Register">
<input>T3D.1 Source Register; debt schedules, maturity profiles, capital structure data.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Map all debt instruments by maturity date, ordered chronologically.
2. For each instrument: record Instrument, Amount, Currency, Maturity Date, Years to Maturity, Seniority/Lien, Coupon/Margin, Fixed/Floating, Call Date (if applicable), Refinancing Pressure (using Refinancing Pressure Indicators), and Source Trace.
3. Identify maturity wall: cluster maturities by year and assess concentration.
4. Flag near-term maturities relative to liquidity (Refinancing Pressure Indicator #1).
5. Identify springing maturities or maturity acceleration triggers.
6. Translate maturity wall into credit implication using Evidence → Risk Mechanic → Credit Implication.
7. Do not infer maturity wall unless supported by provided evidence.

## Output
T3D.2: `Instrument`|`Amount`|`Currency`|`Maturity Date`|`Years to Maturity`|`Seniority / Lien`|`Coupon / Margin`|`Fixed / Floating`|`Call Date`|`Refinancing Pressure`|`Credit Implication`|`Source Trace`
## REF_CP-3C_03_LiquidityFCFMarketAccess.md
<!-- REF_CP-3C_03 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="03" name="Liquidity, FCF, and Market Access Assessment">
<input>T3D.1, T3D.2; CP-1/CP-1A financials, CP-2D liquidity bridge, market data (pricing/spreads/yields).</input>
<gate>Step 2 complete.</gate>

## Instructions
1. Assess liquidity position: cash, revolver availability, revolver draw status, other liquidity sources.
2. Assess FCF generation: current and projected, cash interest burden, capex requirements.
3. Assess market access: current trading levels (price/spread/yield), distressed trading flag, rating/outlook, market appetite for issuer/sector.
4. For each dimension: record Factor, Evidence, Current Level/Status, Direction (using Probability Direction Labels), Risk Mechanic, Credit Implication, Confidence, and Source Trace.
5. If current market data is missing: mark conclusions as [Market Data Not Provided] or [Insufficient Information].
6. Flag negative FCF/cash burn, high cash interest burden, distressed trading, revolver draw, ratings downgrade/negative outlook.

## Output
T3D.3: `Factor`|`Evidence`|`Current Level / Status`|`Direction`|`Risk Mechanic`|`Credit Implication`|`Confidence`|`Source Trace`
## REF_CP-3C_04_LegalCapacityForLME.md
<!-- REF_CP-3C_04 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="04" name="Legal Capacity for LME">
<input>T3D.1–T3D.3; CP-4/CP-4A legal/covenant outputs, credit agreements, indentures, intercreditor agreements.</input>
<gate>Step 3 complete. If CP-4/CP-4A unavailable, do not infer exact capacity — flag and proceed with [Insufficient Information] for legal fields.</gate>

## Instructions
1. Assess legal capacity across 14 Legal-Capacity Indicators:
   Incremental debt capacity, Lien capacity, Unrestricted subsidiary capacity, Investment capacity, RP/junior debt payment capacity, Collateral release, Guarantor release, Amendment thresholds, Sacred rights, Open-market purchase provisions, MFN protection, Intercreditor terms, Class voting, Pro rata sharing provisions.
2. For each: record Indicator, Available/Not Available/Unclear, Evidence, Risk Mechanic (how it enables or constrains LME paths), Which LME Paths Enabled, Confidence, and Source Trace.
3. Do not infer legal capacity from market convention — use source-supported provisions only.
4. If CP-4A unavailable, do not infer exact basket availability or capacity.
5. Cross-reference legal capacity with each LME path type to identify which paths are legally feasible.
6. Flag where legal capacity creates priming, subordination, or collateral leakage risk.

## Output
T3D.4: `Legal-Capacity Indicator`|`Available / Not Available / Unclear`|`Evidence`|`Risk Mechanic`|`LME Paths Enabled`|`Confidence`|`Source Trace`
## REF_CP-3C_05_SponsorGovernanceWillingness.md
<!-- REF_CP-3C_05 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="05" name="Sponsor / Governance Willingness">
<input>T3D.1–T3D.4; CP-2C sponsor evidence, lender presentations, market commentary, rating reports.</input>
<gate>Step 4 complete. If CP-2C unavailable, do not infer sponsor willingness from sponsor identity alone — flag and proceed with [Insufficient Information].</gate>

## Instructions
1. Assess sponsor/governance willingness and behavior evidence across dimensions:
   - Historical refinancing/LME behavior by this sponsor
   - Current sponsor support signals (equity injection, subordinated capital, asset sales)
   - Sponsor economic incentive (equity value, fund vintage, exit horizon)
   - Governance structure (control, board composition, information rights)
2. For each: record Factor, Evidence, Assessment (Low/Medium/High/Insufficient Information), Risk Mechanic, Credit Implication, and Source Trace.
3. If CP-2C unavailable, do not infer willingness from sponsor identity alone.
4. Distinguish sponsor support (positive for creditors) from sponsor-driven LME (potentially adverse for certain creditor classes).

## Output
T3D.5: `Factor`|`Evidence`|`Assessment`|`Risk Mechanic`|`Credit Implication`|`Source Trace`
## REF_CP-3C_06_RefinancingPathAssessment.md
<!-- REF_CP-3C_06 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="06" name="Refinancing Path Assessment">
<input>T3D.2–T3D.5; all maturity, liquidity, legal, and sponsor evidence.</input>
<gate>Steps 2–5 complete.</gate>

## Instructions
1. Assess feasibility and likelihood for each applicable Refinancing/LME Path from the 12-path taxonomy:
   Consensual refinancing, Amend & Extend, Open-market repurchase, Exchange offer, Distressed exchange, Uptier, Drop-down, J.Crew-style transfer, Serta-style non-pro-rata exchange, Priming debt, Asset sale/partial paydown, Sponsor equity injection.
2. For each applicable path: record Path Type, Feasibility (Low/Medium/High/Insufficient Information), Likelihood Direction (using Probability Direction Labels), Evidence Supporting, Evidence Against, Legal Capacity Required (from T3D.4), Creditor Impact, and Source Trace.
3. Do not label a path High unless pressure, feasibility, and incentive are ALL supported.
4. Do not infer LME intent from maturity pressure alone.
5. Identify the most likely refinancing path and the most adverse creditor-impact path.

## Output
T3D.6: `Path Type`|`Feasibility`|`Likelihood Direction`|`Evidence Supporting`|`Evidence Against`|`Legal Capacity Required`|`Creditor Impact`|`Source Trace`
## REF_CP-3C_07_PrimeLMEVulnerabilityScore.md
<!-- REF_CP-3C_07 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="07" name="Prime / LME Vulnerability Score">
<input>T3D.2–T3D.6; all maturity, liquidity, legal, sponsor, and path evidence.</input>
<gate>Step 6 complete.</gate>

## Instructions
1. Assign Prime/LME Vulnerability Score: Low / Medium / High / Insufficient Information.
2. Apply Score Selection Rules:
   - **High:** Meaningful refinancing pressure + supported legal capacity for coercive action + supported sponsor/issuer incentive (or market pressure creating strong economic incentive).
   - **Medium:** Pressure and capacity partially supported but willingness or market feasibility is mixed.
   - **Low:** Ordinary-course refinancing feasible OR coercive legal capacity/willingness not supported.
3. Score each dimension individually (Low/Medium/High/Insufficient Information):
   - Refinancing pressure (from T3D.2/T3D.3)
   - Legal capacity (from T3D.4)
   - Sponsor willingness (from T3D.5)
   - Market access (from T3D.3)
   - Recovery impact (from path assessment T3D.6)
4. Assign overall score and Evidence Confidence Label.
5. Use Evidence → Risk Mechanic → Credit Implication chain for the overall assessment.

## Output
T3D.7: `Dimension`|`Score`|`Evidence`|`Risk Mechanic`|`Credit Implication`|`Source Trace`
+ Overall Prime/LME Vulnerability Score + Confidence Label
## REF_CP-3C_08_CreditorClassExposure.md
<!-- REF_CP-3C_08 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="08" name="Creditor Class Exposure and Recovery Implications">
<input>T3D.2–T3D.7; capital structure, legal/structural evidence, path assessment, vulnerability score.</input>
<gate>Step 7 complete.</gate>

## Instructions
1. Map each creditor class to its exposure under the most likely and most adverse refinancing/LME paths.
2. For each creditor class: record Creditor Class (e.g., 1L term loan, 2L notes, unsecured), Exposure Under Base Case, Exposure Under Stress Case, Exposure Under LME Case, Recovery Implication, Priming/Subordination Risk, and Source Trace.
3. Identify which creditor classes are most vulnerable to:
   - Priming (new senior/pari debt ahead)
   - Subordination (uptier leaving non-participants junior)
   - Collateral leakage (asset movement reducing recovery)
   - Non-pro-rata treatment (selective exchange favoring participants)
4. Connect creditor-class exposure to downstream: CP-3A (instrument preference), CP-3B (sizing constraints).
5. Use Evidence → Risk Mechanic → Credit Implication chain.

## Output
T3D.8: `Creditor Class`|`Exposure: Base Case`|`Exposure: Stress Case`|`Exposure: LME Case`|`Recovery Implication`|`Priming / Subordination Risk`|`Source Trace`
## REF_CP-3C_09_MonitoringTriggers.md
<!-- REF_CP-3C_09 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="09" name="Monitoring Triggers">
<input>T3D.2–T3D.8; all maturity, liquidity, legal, sponsor, path, vulnerability, and creditor-class evidence.</input>
<gate>Step 8 complete.</gate>

## Instructions
1. Generate specific, observable monitoring triggers for refinancing/LME risk.
2. For each trigger: record Trigger, Indicator, Threshold/Qualitative Signal, Leading/Lagging, Why It Matters (refinancing/LME risk implication), Linked Path(s), and Source Trace.
3. Focus on: maturity approaching within 12–24 months, liquidity deterioration, covenant headroom compression, spread widening/distressed trading, sponsor behavior signals, legal-capacity usage (basket drawdowns), rating actions, asset sales, revolver draw changes.
4. Use quantitative thresholds only if source-supported. If not, use observable qualitative signals and state: "Quantitative threshold not available in provided materials."
5. Triggers must be actionable: tied to observable data points that would change vulnerability score or path assessment.

## Output
T3D.9: `Trigger`|`Indicator`|`Threshold / Qualitative Signal`|`Leading / Lagging`|`Why It Matters`|`Linked Path(s)`|`Source Trace`
## REF_CP-3C_10_ScenarioMap.md
<!-- REF_CP-3C_10 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="10" name="Scenario Map: Base, Stress, and LME Case">
<input>T3D.2–T3D.9; all analytical evidence and path/vulnerability assessments.</input>
<gate>Step 9 complete.</gate>

## Instructions
1. Construct 3 scenarios:
   - **Base Case:** Most likely refinancing path under current conditions. State assumptions, path, timeline, creditor impact, and recovery implication.
   - **Stress Case:** Refinancing under adverse conditions (market dislocation, operational deterioration, covenant breach). State stress assumptions, most likely path under stress, creditor impact, and recovery implication.
   - **LME Case:** Most adverse creditor-impact LME path. State LME assumptions, specific path mechanics, which creditor classes are impaired, priming/subordination mechanics, and recovery implication.
2. For each scenario: record Scenario, Key Assumptions, Refinancing Path, Timeline, Creditor Impact, Recovery Implication, Probability Direction (using labels), Confidence, and Source Trace.
3. Clearly distinguish scenarios from each other.
4. Use Evidence → Risk Mechanic → Credit Implication chain for each scenario.

## Output
T3D.10: `Scenario`|`Key Assumptions`|`Refinancing Path`|`Timeline`|`Creditor Impact`|`Recovery Implication`|`Probability Direction`|`Confidence`|`Source Trace`
## REF_CP-3C_11_GapsLedger.md
<!-- REF_CP-3C_11 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="11" name="Gaps Ledger">
<input>All prior step outputs (T3D.1–T3D.10); cumulative gaps identified throughout workflow.</input>
<gate>Always executes.</gate>

## Instructions
1. Compile all gaps identified across Steps 1–10 into a consolidated ledger.
2. For each gap: record Gap, Missing Data, Why It Matters, Impact on Output (which step/table/score/path/scenario is affected), and Required Follow-Up.
3. Cover gaps in: maturity/debt-schedule detail, liquidity/FCF data, market data (pricing/spreads/yields), legal/covenant evidence (CP-4/CP-4A), sponsor/governance evidence (CP-2C), downside pathways (CP-2A), liquidity bridge (CP-2D), recovery evidence, intercreditor terms, and historical LME precedent.
4. Flag gaps that prevent vulnerability scoring, path assessment, or scenario construction.
5. Flag gaps requiring downstream resolution (CP-4 for legal, CP-2C for sponsor).

## Output
T3D.11: `Gap`|`Missing Data`|`Why It Matters`|`Impact on Output`|`Required Follow-Up`
## REF_CP-3C_12_OverallRefinancingLMEView.md
<!-- REF_CP-3C_12 (T2) | 2026-06-03 -->
<step_reference module="CP-3C" step="12" name="Overall Refinancing / LME View">
<input>All prior step outputs (T3D.1–T3D.11); all maturity, liquidity, legal, sponsor, path, vulnerability, creditor-class, scenario, and gap evidence.</input>
<gate>Always executes. Synthesis only — no new data.</gate>

## Instructions
1. Write a committee-ready narrative synthesis covering:
   - Maturity wall overview (key maturities, concentration, timeline).
   - Liquidity/FCF/market access summary.
   - Legal capacity summary (which LME paths are feasible).
   - Sponsor/governance willingness summary.
   - Most likely refinancing path and timeline.
   - Prime/LME Vulnerability Score and key drivers.
   - Most exposed creditor class(es) and why.
   - Top monitoring trigger.
   - Scenario summary (Base vs. Stress vs. LME case).
   - Critical gaps requiring resolution.
2. Do not introduce new data, new calculations, or new assessments — synthesize only from Steps 1–11.
3. End with one of:
   - "CP-3C Completed. Prime/LME Vulnerability: [Score]. Most Likely Path: [Path]."
   - "CP-3C Completed with Limitations. Prime/LME Vulnerability: [Score]. Key Gaps: [List]."
   - "CP-3C Blocked. Missing Required Inputs: [List]."

## Output
Narrative synthesis (no table). Module completion statement with Vulnerability Score and Most Likely Path.
## REF_CP-3C_PathsAndScoring.md
<!-- REF_CP-3C PathsAndScoring (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-3C" name="Path Taxonomy, Indicators & Vulnerability Scoring">

Authoritative for CP-3C path assessment (Step 6), vulnerability scoring (Step 7), and scenario mapping (Step 10). Load alongside the CP-3C workflow. The Scope Boundary stays in the ACTIVE_PROMPT.

## Refinancing / LME Path Taxonomy (12 paths)
| Path | Description |
|------|------------|
| Consensual refinancing | Ordinary-course market transaction without coercive treatment |
| Amend & Extend | Existing lenders extend maturity with economics/covenant amendments |
| Open-market repurchase | Issuer buys back debt below par using cash or permitted capacity |
| Exchange offer | Issuer offers new securities for old debt |
| Distressed exchange | Stress-driven exchange potentially default-like by rating agency |
| Uptier | Participating creditors exchange into senior/priming debt, non-participants subordinated |
| Drop-down | Assets moved outside collateral/restricted group to raise new debt |
| J.Crew-style transfer | IP or material assets moved away from restricted group or collateral reach |
| Serta-style non-pro-rata exchange | Majority lenders approve transaction favoring participating lenders |
| Priming debt | New debt issued with senior or pari priority over existing creditors |
| Asset sale / partial paydown | Asset proceeds used to reduce maturities |
| Sponsor equity injection | Sponsor contributes equity or subordinated capital |

## Canonical 7 Path Types (Simplified)
Consensual Refinancing | Amend-and-Extend | Exchange Offer | Distressed Exchange | Uptier | Drop-Down | Priming Debt

## Legal-Capacity Indicators (14)
Incremental debt capacity | Lien capacity | Unrestricted subsidiary capacity | Investment capacity | RP/junior debt payment capacity | Collateral release | Guarantor release | Amendment thresholds | Sacred rights | Open-market purchase provisions | MFN protection | Intercreditor terms | Class voting | Pro rata sharing provisions

## Refinancing Pressure Indicators (10)
Near-term maturity relative to liquidity | Distressed trading | Negative FCF/cash burn | High cash interest burden | Covenant headroom compression | Ratings downgrade/negative outlook | Revolver draw | Sponsor support | Asset sale proceeds | Improving EBITDA/deleveraging

## Prime / LME Vulnerability Score
**Low:** Ordinary-course refinancing appears feasible, or maturity pressure/legal capacity/sponsor willingness does not support coercive path.
**Medium:** Refinancing pressure or legal flexibility exists but pressure, capacity, willingness, or market constraint is incomplete or mixed.
**High:** Refinancing pressure, legal capacity, and incentive/willingness are source-supported and ordinary-course refinancing appears constrained.
**Insufficient Information:** Required evidence is unavailable.

## Score Selection Rules
- **High** requires: meaningful refinancing pressure + supported legal capacity for coercive action/priming/asset movement + supported sponsor/issuer incentive or willingness (or market pressure creating strong economic incentive).
- **Medium** requires: pressure and capacity partially supported but willingness or market feasibility is mixed.
- **Low** requires: ordinary-course refinancing appears feasible OR coercive legal capacity/willingness is not supported.

## Dimension Scoring
Assess each dimension as Low / Medium / High / Insufficient Information:
- Refinancing pressure
- Legal capacity
- Sponsor willingness
- Market access
- Recovery impact

## Evidence Confidence Labels
**High:** Current maturity, liquidity, market, legal-capacity, and sponsor/governance evidence.
**Medium:** Core evidence available but one important area incomplete.
**Low:** Maturity, legal, or market data materially incomplete.
**Formula Only:** Calculation from partial inputs without full evidence support.
**Insufficient Information:** Cannot form decision-useful view.

## Probability Direction Labels
Low | Medium | High | Increasing | Stable | Decreasing | Insufficient Information

</reference>
