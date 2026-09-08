Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-2C_Discipline.md, REF_CP-2C_ScoringTaxonomy.md, REF_CP-2C_Workflow.md.

Original files, in this bundle: REF_CP-2C_01_SourceGateReadiness.md, REF_CP-2C_02-03_OwnershipGovernanceRegisters.md, REF_CP-2C_04_SponsorBehaviorFlags.md, REF_CP-2C_05_CapitalAllocationRisk.md, REF_CP-2C_06_AcquisitionAppetiteIntegration.md, REF_CP-2C_07_DisclosureQualityLog.md, REF_CP-2C_08_CreditorAlignmentFinancialPolicy.md, REF_CP-2C_09_SponsorRiskAssessment.md, REF_CP-2C_10_CrossModuleHandoffRegister.md, REF_CP-2C_11_GapsLedger.md, REF_CP-2C_12_OverallGovernanceView.md, REF_CP-2C_Discipline.md, REF_CP-2C_ScoringTaxonomy.md, REF_CP-2C_Workflow.md

## REF_CP-2C_01_SourceGateReadiness.md
<!-- REF_CP-2C_01 (T2) | 2026-06-03 -->
<step_reference module="CP-2C" step="01" name="Source Gate & Readiness">
<input>All available governance, sponsor, shareholder, ownership, capital-allocation, legal-capacity, disclosure, reporting, and creditor-treatment source materials; CP-0 registry; CP-1A, CP-2 outputs.</input>
<gate>Always executes. This IS the gate check.</gate>

## Instructions
1. Catalogue all available source materials for governance/sponsor analysis.
2. For each source, record: source_document_id, source_document_name, source_quality (High/Medium/Low/Insufficient), period, entity_covered, data_supplied, limitation, and downstream_use.
3. Confirm external-source usage status (allowed for CP-2C where explicitly permitted; label [External]).
4. Identify missing required inputs: ownership documents, sponsor materials, governance disclosures, CP-4/CP-4A legal-capacity data, financial policy evidence.
5. Assign Module Status:
   - **Full Run:** Sufficient governance/sponsor evidence for all core steps.
   - **Ready with Limitations:** Partial evidence; proceed but flag gaps.
   - **Blocked:** Critical sources absent (e.g., no ownership/sponsor identification possible).
6. State citation discipline requirement.

## Output
T2D.1: `source_document_id`|`source_document_name`|`source_quality`|`period`|`entity_covered`|`data_supplied`|`limitation`|`downstream_use`  
\+ Module Status: Full Run / Ready with Limitations / Blocked
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-2C_02-03_OwnershipGovernanceRegisters.md
<!-- REF_CP-2C_02-03 (T2) | 2026-06-03 -->
<step_reference module="CP-2C" step="02" name="Ownership, Sponsor & Control Register">
<input>T2D.1 Source Register; all ownership, sponsor, shareholder, and governance source materials.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Build the issuer ownership and control register covering: current owner/sponsor/shareholder, ownership percentage, sponsor fund/vehicle, fund vintage/life-left, acquisition date/ownership transition, equity contribution/purchase price/entry multiple, board/control/veto/consent rights, restricted-group/holdco structure, sponsor/shareholder fees.
2. For each item: record Source-Supported Fact, Evidence Quality (High/Medium/Low/Insufficient), Source Trace, Credit Mechanic, Credit Implication, and Limitation.
3. If fund vintage, fund life-left, ownership percentage, or control rights are not explicitly disclosed, write [Insufficient Information].
4. Do not infer exit pressure from vintage unless both fund vintage and life-left are disclosed.
5. Use names only to identify disclosed roles, signatories, ownership interests, or governance functions — do not evaluate persons.

## Output
T2D.2: `Item`|`Source-Supported Fact`|`Evidence Quality`|`Source Trace`|`Credit Mechanic`|`Credit Implication`|`Limitation`
</step_reference>

<step_reference module="CP-2C" step="03" name="Governance Register">
<input>T2D.2 Ownership & Control Register; governance, reporting, and disclosure source materials.</input>
<gate>Step 2 complete.</gate>

## Instructions
1. Assess governance structure, reporting transparency, disclosure quality, and creditor control.
2. Cover topics: board/control rights, related-party transactions, management/monitoring/advisory fees, reporting cadence, audit status/reporting quality, covenant reporting/certificates, disclosure completeness, conflicts between shareholder and creditor interests.
3. For each topic: record Source-Supported Fact, Risk Direction (Supportive / Neutral / Mixed / Creditor-Adverse / Insufficient Information), Risk Mechanic, Credit Implication, Evidence Quality, Source Trace, and Limitation.
4. Credit focus: explain whether governance improves or weakens creditor visibility, lender control, recovery protection, refinancing confidence, and monitoring posture.

## Output
T2D.3: `Governance Topic`|`Source-Supported Fact`|`Risk Direction`|`Risk Mechanic`|`Credit Implication`|`Evidence Quality`|`Source Trace`|`Limitation`
</step_reference>
## REF_CP-2C_04_SponsorBehaviorFlags.md
<!-- REF_CP-2C_04 (T2) | 2026-06-03 -->
<step_reference module="CP-2C" step="04" name="Sponsor / Shareholder Behavior Flags">
<input>T2D.2, T2D.3; all sponsor action, transaction, distribution, LME, amendment, and support evidence.</input>
<gate>Steps 2–3 complete.</gate>

## Instructions
1. Build a source-backed behavior flag register. Assign sequential Flag IDs (CP-2C-FLAG-001, etc.).
2. For each flag: record Behavior Type (dividend recap / distribution / support / LME / amendment / acquisition / disposal / reporting / other), Documented Action, Behavior Category (Supportive / Neutral / Mixed / Extraction-Oriented / Creditor-Adverse / Insufficient Information per Taxonomy A–E), Amount / Funding Source, Legal-Capacity Link (CP-4 / CP-4A / document / Insufficient Information), Risk Mechanic, Credit Implication, Evidence Quality, Source Trace, Limitation.
3. Cover where supported: dividend recap history, shareholder distributions, management/monitoring/advisory fees, related-party leakage, LME history, priming/uptier/drop-down/non-pro-rata, amendment/waiver/A&E/exchange/restructuring, sponsor equity support/cure/injection/deleveraging, acquisition funding, disposal/asset-sale behavior, open-market repurchases, creditor-aligned or creditor-adverse refinancing, transparency/reporting behavior.
4. Apply Taxonomy categories strictly per evidence; do not infer behavior from sponsor identity.

## Output
T2D.4: `Flag ID`|`Behavior Type`|`Documented Action`|`Behavior Category`|`Amount / Funding Source`|`Legal-Capacity Link`|`Risk Mechanic`|`Credit Implication`|`Evidence Quality`|`Source Trace`|`Limitation`
</step_reference>
## REF_CP-2C_05_CapitalAllocationRisk.md
<!-- REF_CP-2C_05 (T2) | 2026-06-03 -->
<step_reference module="CP-2C" step="05" name="Capital Allocation Risk Table">
<input>T2D.2, T2D.3, T2D.4; capital allocation, investment, distribution, and debt-management evidence.</input>
<gate>Steps 2–4 complete.</gate>

## Instructions
1. Translate capital allocation into leverage, FCF, liquidity, and refinancing mechanics.
2. Cover items: organic investment, M&A / roll-up strategy, integration / restructuring spend, capex discipline, dividends / distributions, debt paydown / deleveraging, refinancing / amend-and-extend, equity contribution / sponsor support, asset sales / disposals, tax distributions / fees, liquidity preservation actions.
3. For each: record Source-Supported Fact, Direction (Supportive / Neutral / Mixed / Adverse / Insufficient Information), Risk Mechanic, Credit Implication, Evidence Quality, Source Trace, Limitation.

## Output
T2D.5: `Capital Allocation Item`|`Source-Supported Fact`|`Direction`|`Risk Mechanic`|`Credit Implication`|`Evidence Quality`|`Source Trace`|`Limitation`
</step_reference>
## REF_CP-2C_06_AcquisitionAppetiteIntegration.md
<!-- REF_CP-2C_06 (T2) | 2026-06-03 -->
<step_reference module="CP-2C" step="06" name="Acquisition Appetite & Integration Behavior">
<input>T2D.2–T2D.5; acquisition history, funding mix, pro forma data, integration evidence.</input>
<gate>Steps 2–5 complete. Skip with [Insufficient Information] if no acquisition data available.</gate>

## Instructions
1. Assess whether acquisition behavior increases scale, diversification, integration risk, leverage tolerance, FCF volatility, or refinancing pressure.
2. For each acquisition / period: record Source-Supported Fact, Funding Mix (debt / equity / cash / Insufficient Information), EBITDA / Pro Forma Basis (Fact / Insufficient Information), Integration Evidence, Leverage / Liquidity Effect (Fact / Directional Only), Risk Mechanic, Credit Implication, Source Trace, Limitation.
3. Do not infer acquisition appetite from one acquisition unless source language or history supports a pattern.
4. Do not infer synergy realization unless source evidence supports it.

## Output
T2D.6: `Acquisition / Period`|`Source-Supported Fact`|`Funding Mix`|`EBITDA / Pro Forma Basis`|`Integration Evidence`|`Leverage / Liquidity Effect`|`Risk Mechanic`|`Credit Implication`|`Source Trace`|`Limitation`
</step_reference>
## REF_CP-2C_07_DisclosureQualityLog.md
<!-- REF_CP-2C_07 (T2) | 2026-06-03 -->
<step_reference module="CP-2C" step="07" name="Disclosure Quality Log">
<input>T2D.1–T2D.6; all source materials reviewed for completeness.</input>
<gate>Steps 1–6 complete.</gate>

## Instructions
1. Evaluate disclosure limitations that affect creditor monitoring and structured export.
2. Cover items: financial statements, cash-flow statement, debt schedule, maturity schedule, liquidity / revolver availability, covenant certificate, EBITDA bridge / add-backs, sponsor economics / fees, dividend / distribution detail, acquisition funding detail, board / control rights, basket usage tracker.
3. For each: record Available? (Yes / No / Partial / Insufficient Information), Source-Supported Detail, Credit Relevance (monitoring / PD / liquidity / refinancing / RV relevance), Severity (Critical / Material / Minor per Red-Flag Guide), Source Trace, Required Follow-Up.
4. Red-Flag Severity Guide:
   - **Critical:** Could change credit conclusion, legal meaning, recovery, recommendation, security selection, portfolio sizing, or committee decision.
   - **Material:** Important for monitoring or sizing but not necessarily thesis-changing alone.
   - **Minor:** Formatting, presentation, stale-but-noncritical source, or immaterial disclosure issue.

## Output
T2D.7: `Disclosure Item`|`Available?`|`Source-Supported Detail`|`Credit Relevance`|`Severity`|`Source Trace`|`Required Follow-Up`
</step_reference>
## REF_CP-2C_08_CreditorAlignmentFinancialPolicy.md
<!-- REF_CP-2C_08 (T2) | 2026-06-03 -->
<step_reference module="CP-2C" step="08" name="Creditor Alignment & Financial Policy Assessment">
<input>T2D.2–T2D.7; all behavior flags, capital allocation, governance, and disclosure evidence.</input>
<gate>Steps 2–7 complete.</gate>

## Instructions
1. Assess the combined creditor-alignment signal across 9 scoring dimensions.
2. Dimensions: Leverage tolerance, Shareholder extraction risk, Acquisition appetite, Support behavior, Disclosure transparency, Creditor treatment / amendment behavior, Legal-capacity linkage, Reporting quality, Related-party leakage risk.
3. For each dimension: record Assessment (Creditor-favorable / Mixed / Adverse / Not Scorable), Evidence, Risk Mechanic, Credit Implication, Score (1 / 3 / 5 / Not Scorable), Evidence Quality, Source Trace, Limitation.
4. Do not score a dimension if evidence is missing — use Not Scorable.
5. If legal capacity is high but willingness evidence is missing, separate capacity from willingness.
6. Do not calculate a composite governance score unless ≥4 dimensions are evidence-supported. If <4, mark composite as Not Scorable and assign Risk Level = Insufficient Information (unless one clearly High-risk documented action).

## Output
T2D.8: `Dimension`|`Assessment`|`Evidence`|`Risk Mechanic`|`Credit Implication`|`Score`|`Evidence Quality`|`Source Trace`|`Limitation`
</step_reference>
## REF_CP-2C_09_SponsorRiskAssessment.md
<!-- REF_CP-2C_09 (T2) | 2026-06-03 -->
<step_reference module="CP-2C" step="09" name="Sponsor Risk Assessment">
<input>T2D.2–T2D.8; cumulative evidence from all prior steps.</input>
<gate>Steps 2–8 complete.</gate>

## Instructions
1. Assign one Sponsor / Governance Risk Level: Low | Medium | High | Insufficient Information.
2. Build risk-level driver table: for each driver, record Evidence, Risk Mechanic, Credit Implication (PD / LGD / liquidity / refinancing / RV / monitoring), Evidence Quality, Source Trace, Countervailing Evidence, Limitation.
3. Before assigning risk level, run Required Gate Tests:
   - Is issuer identity supported?
   - Is ownership / sponsor / shareholder identity supported?
   - Is relevant behavior issuer-specific (not sponsor-generic)?
   - Is timing of the behavior disclosed?
   - Is funding source disclosed where distributions, acquisitions, refinancings, support, or value transfers are discussed?
   - Is credit impact traceable to leverage, liquidity, FCF, refinancing, recovery, legal capacity, disclosure, creditor control, or RV?
   - Are legal capacity and willingness evidence separated?
   - Are unsupported facts marked [Insufficient Information]?
   - Are external claims labelled [External]?
   - Are source_quality and source_trace preserved?
   - Are structured-export records mapped to correct record_type and database target?
4. Provide required explanation: "The risk level is driven by [evidence], because [risk mechanic], which implies [credit implication]. Countervailing evidence is [evidence / Insufficient Information]."
5. Risk Level Guide:
   - **Low:** No documented extraction / creditor-adverse behavior, creditor-aligned financial policy, adequate disclosure, no LME history, low legal-capacity concerns.
   - **Medium:** Mixed / incomplete evidence, some distributions / releveraging but moderate impact, adequate disclosure with gaps, support and extraction coexist.
   - **High:** Documented extraction, aggressive leverage tolerance, documented LME / priming / uptier, weak disclosure blocking monitoring, governance materially reducing creditor protection.
   - **Insufficient Information:** Cannot assign decision-useful level.

## Output
T2D.9: `Risk-Level Driver`|`Evidence`|`Risk Mechanic`|`Credit Implication`|`Evidence Quality`|`Source Trace`|`Countervailing Evidence`|`Limitation`  
\+ Sponsor / Governance Risk Level: [Low / Medium / High / Insufficient Information]
</step_reference>
## REF_CP-2C_10_CrossModuleHandoffRegister.md
<!-- REF_CP-2C_10 (T2) | 2026-06-03 -->
<step_reference module="CP-2C" step="10" name="Cross-Module Handoff Register">
<input>T2D.1–T2D.9; all flags, risk level, gaps, and behavior evidence.</input>
<gate>Steps 1–9 complete.</gate>

## Instructions
1. Identify how CP-2C output should be consumed downstream.
2. Use predefined handoff tags:
   - **CP-2C-HANDOFF-CP-2:** fundamental governance / financial-policy input
   - **CP-2C-HANDOFF-CP-2A:** downside-pathway behavior input
   - **CP-2C-HANDOFF-CP-2D:** liquidity support / extraction input
   - **CP-2C-HANDOFF-CP-3:** scorecard and RV governance input
   - **CP-2C-HANDOFF-CP-3C:** sponsor willingness / LME behavior input
   - **CP-2C-HANDOFF-CP-4A:** legal capacity / leakage monitoring input
   - **CP-2C-HANDOFF-CP-5A:** QA citation and supportability input
   - **CP-2C-HANDOFF-CP-5:** evidence traceability input
   - **CP-2C-HANDOFF-CP-6:** IC debate sponsor / governance input
   - **CP-2C-HANDOFF-CP-6A:** portfolio debate sponsor / concentration / behavior input
3. For each: record Downstream Module, Handoff Tag, Handoff Item, Why It Matters, Required Consumer Action, Source / Flag Link, Limitation.

## Output
T2D.10: `Downstream Module`|`Handoff Tag`|`Handoff Item`|`Why It Matters`|`Required Consumer Action`|`Source / Flag Link`|`Limitation`
</step_reference>
## REF_CP-2C_11_GapsLedger.md
<!-- REF_CP-2C_11 (T2) | 2026-06-03 -->
<step_reference module="CP-2C" step="11" name="Gaps Ledger">
<input>All prior step outputs (T2D.1–T2D.10); cumulative gaps identified throughout workflow.</input>
<gate>Always executes.</gate>

## Instructions
1. Compile all gaps identified across Steps 1–10 into a consolidated ledger with sequential Gap IDs (CP-2C-GAP-001, etc.).
2. For each gap: record Missing Data, Why It Matters (credit relevance), Affected Section / Flag / Export Record, Consequence for Confidence (High / Medium / Low impact), Required Follow-Up Source.
3. Cover gaps in: ownership percentage, sponsor fund vintage / life-left, sponsor economics, equity contribution, dividend / distribution history, related-party payments, management fees, acquisition funding, amendment history, LME / restructuring history, board / control rights, governance documents, covenant reporting, basket usage, disclosure cadence, debt schedule, liquidity / revolver availability, maturity wall, legal capacity for RP / investments / debt / liens / asset transfers / unrestricted subsidiaries / priming / amendments.
4. Use Required Follow-Up Question Bank where relevant:
   - What is the current ownership percentage by sponsor / shareholder?
   - What is the sponsor fund vintage and remaining fund life?
   - What was the sponsor equity contribution at transaction close?
   - Has the issuer completed dividend recaps or shareholder distributions? Amount, timing, funding source?
   - What related-party, management, advisory, monitoring, transaction, or shareholder fees are paid?
   - What acquisitions have been completed, and how were they funded?
   - Has the issuer required covenant waivers, amendments, A&E, exchange offers, or restructuring?
   - Has the sponsor provided equity support, cure, deleveraging capital, or liquidity support?
   - What board / consent / veto rights does the sponsor or shareholder hold?
   - What reporting package is provided to lenders and how frequently?
   - Are compliance certificates, debt schedules, maturity schedules, liquidity schedules, and basket-usage trackers available?
   - Does CP-4A identify RP, investment, debt, lien, unrestricted-subsidiary, asset-transfer, priming, or amendment capacity?
   - Has any unrestricted-subsidiary, drop-down, priming, collateral-release, or non-pro-rata mechanism been used?

## Output
T2D.11: `Gap ID`|`Missing Data`|`Why It Matters`|`Affected Section / Flag / Export Record`|`Consequence for Confidence`|`Required Follow-Up Source`
</step_reference>
## REF_CP-2C_12_OverallGovernanceView.md
<!-- REF_CP-2C_12 (T2) | 2026-06-03 -->
<step_reference module="CP-2C" step="12" name="Overall Governance View">
<input>All prior step outputs (T2D.1–T2D.11); Sponsor / Governance Risk Level from Step 9.</input>
<gate>Always executes. Synthesis only — no new data.</gate>

## Instructions
1. Write a committee-ready narrative synthesis using the template:
   "Overall, [Issuer] presents [Low / Medium / High / Insufficient Information] sponsor / governance risk. The key supported behavior is [evidence], which matters because [risk mechanic] and implies [credit implication]. Countervailing evidence is [evidence / Insufficient Information]. Further analysis requires [missing data]."
2. Do not introduce new data, new flags, or new assessments — synthesize only from Steps 1–11.
3. End with one of:
   - "CP-2C Completed. Sponsor / Governance Risk Level: [Level]."
   - "CP-2C Completed with Limitations. Sponsor / Governance Risk Level: [Level]. Key Gaps: [List]."
   - "CP-2C Blocked. Missing Required Inputs: [List]."

## Output
Narrative synthesis (no table). Module completion statement with Risk Level.
</step_reference>
## REF_CP-2C_Discipline.md
<!-- REF_CP-2C Discipline (full Prohibited Behaviors list) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-2C" name="Prohibited Behaviors — full binding list (relocated from ACTIVE_PROMPT 2026-07-11)">

## Prohibited Behaviors (full binding list)
1. Do not evaluate individual employee performance, personal qualities, competence, intelligence, motivation, leadership style, or interpersonal behavior.
2. Do not rank, score, or compare named individuals.
3. Do not make claims about private personal attributes of executives, directors, employees, founders, or sponsor professionals.
4. Do not infer sponsor willingness from sponsor identity, brand, private-equity ownership, or generalized market reputation — use only issuer-specific transaction history, documented actions, legal capacity, financial policy, and source-supported behavior.
5. Do not infer fund life-left, exit pressure, valuation target, dividend capacity, amendment strategy, or LME willingness unless directly supported.
6. Do not infer motive — translate behavior into incentives and credit mechanics only where evidence supports it.
7. Do not convert missing evidence into an adverse conclusion — missing evidence is [Insufficient Information].
8. Do not write: "management is good/bad", "aggressive sponsor", "creditor-friendly sponsor", "best-in-class governance", "weak/strong management team", or "shareholder-friendly" without evidence → mechanic → implication chain.
9. Do not cite a source for a claim not explicitly supported by that source.
10. Do not calculate a composite governance score unless ≥4 dimensions are evidence-supported.

</reference>
## REF_CP-2C_ScoringTaxonomy.md
<!-- REF_CP-2C ScoringTaxonomy (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-2C" name="Behavior Taxonomy, Evidence Labels & Scoring Rubric">

Authoritative for CP-2C sponsor-behavior classification (Step 4), evidence grading, and the governance scorecard (Step 9). Load alongside the CP-2C workflow.

## Sponsor Behavior Taxonomy
**A. Supportive / Creditor-Aligned:** Equity injection, deleveraging, voluntary paydown, non-subordinating refinance, transparent reporting, conservative acquisition funding, distribution suspension during stress, sponsor liquidity support without priority weakening.
**B. Neutral / Mixed:** Strategic acquisition with unclear funding, maturity extension with increased encumbrance, support plus simultaneous fees, adequate reporting with missing details, debt-funded growth with undisclosed leverage impact.
**C. Extraction-Oriented:** Dividend recap, debt-funded distribution, non-ordinary-course fees, related-party leakage, asset-sale proceeds distributed, leveraged acquisition then distributions, excess tax distributions, stressed share repurchases.
**D. Creditor-Adverse:** Uptier/priming, drop-down, non-pro-rata exchange, coercive exchange, sacred-rights amendments, unrestricted-subsidiary asset moves, stressed RP/investment capacity use, repeated waivers without deleveraging, collateral/guarantee release.
**E. Insufficient Information:** Sponsor identity only, generic reputation, unverified press, missing dates/detail, unclear funding, missing legal capacity, missing sponsor economics/vintage/ownership/control.

## Evidence Quality Labels
**High:** Primary source, dated, issuer-specific (OM, credit agreement, indenture, annual report, audited financials, signed amendment, restructuring agreement, filed ownership document).
**Medium:** Secondary source or module output citing primary evidence (CP-0 registry, CP-1A/CP-2 ownership, CP-3C sponsor-willingness, CP-4A capacity table, internal note with references).
**Low:** High-level summary, promotional, stale, incomplete, undated, non-primary without full support. Use only with limitation language.
**Insufficient:** Unsupported assertion, generic reputation, source missing claimed fact, unclear date, no issuer link, no source, claim from sponsor identity alone.

## Scoring Rubric (Downstream Scorecard Input)
Directional raw scores where evidence supports each dimension:
- **1** = creditor-favorable / conservative / transparent
- **3** = mixed / market-standard / monitor
- **5** = creditor-adverse / extraction-oriented / opaque
- **Not Scorable** = missing evidence

Dimensions: Leverage tolerance | Shareholder extraction risk | Acquisition appetite | Support behavior | Disclosure transparency | Creditor treatment / amendment behavior | Legal-capacity linkage | Reporting quality | Related-party leakage risk
Composite: require ≥4 dimensions supported; else Not Scorable → Risk Level = Insufficient Information (unless one clearly High-risk documented action).

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Institutional-grade, committee-ready, creditor-first, evidence-led, data-dense. Prefer registers, flags, and evidence tables over broad prose. Avoid generic governance commentary unless tied to issuer-specific evidence. Use limitation language explicitly where the source set does not support a conclusion. Permitted replacement format: "Documented financial policy / disclosure / capital allocation is [creditor-favorable / mixed / adverse / insufficient information] because [evidence] → [risk mechanic] → [credit implication]."

</reference>
## REF_CP-2C_Workflow.md
<!-- REF_CP-2C Workflow (full 12-step table) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-2C" name="Workflow — 12 Steps (full table, relocated from ACTIVE_PROMPT 2026-07-11)">

## Workflow — 12 Steps
| Step | Name | REF File | Output |
|------|------|----------|--------|
| 1 | Source Gate & Readiness | REF_CP-2C_01 | T2D.1 Source Register + Module Status |
| 2 | Ownership, Sponsor & Control Register | REF_CP-2C_02 | T2D.2 Ownership & Control Register |
| 3 | Governance Register | REF_CP-2C_03 | T2D.3 Governance Register |
| 4 | Sponsor / Shareholder Behavior Flags | REF_CP-2C_04 | T2D.4 Behavior Flag Register |
| 5 | Capital Allocation Risk Table | REF_CP-2C_05 | T2D.5 Capital Allocation Risk Table |
| 6 | Acquisition Appetite & Integration | REF_CP-2C_06 | T2D.6 Acquisition Appetite Table |
| 7 | Disclosure Quality Log | REF_CP-2C_07 | T2D.7 Disclosure Quality Log |
| 8 | Creditor Alignment & Financial Policy | REF_CP-2C_08 | T2D.8 Creditor Alignment Table |
| 9 | Sponsor Risk Assessment | REF_CP-2C_09 | T2D.9 Sponsor Risk Assessment Table + Risk Level |
| 10 | Cross-Module Handoff Register | REF_CP-2C_10 | T2D.10 Handoff Register |
| 11 | Gaps Ledger | REF_CP-2C_11 | T2D.11 Gaps Ledger |
| 12 | Overall Governance View | REF_CP-2C_12 | Narrative synthesis |

</reference>
