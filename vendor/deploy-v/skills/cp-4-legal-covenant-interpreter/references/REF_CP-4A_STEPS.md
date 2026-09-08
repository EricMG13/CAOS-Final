Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-4A_CalculationRules.md.

Original files, in this bundle: REF_CP-4A_01_CapacitySourceGate.md, REF_CP-4A_02_ControllingCapacitySourceMap.md, REF_CP-4A_03_CovenantDefinitionRatioMechanicsRegister.md, REF_CP-4A_04_HeadroomTable.md, REF_CP-4A_05_CapacityRegister.md, REF_CP-4A_06_DebtLienPrimingCapacityAnalysis.md, REF_CP-4A_07_RPInvestmentAssetTransferLeakageAnalysis.md, REF_CP-4A_08_EBITDAAddBackCapacityInflationAnalysis.md, REF_CP-4A_09_LeakageBasketFlags.md, REF_CP-4A_10-11-13_DecisionSynthesis.md, REF_CP-4A_10_NearestPressurePoint.md, REF_CP-4A_11_CapacityRiskPrioritizationMatrix.md, REF_CP-4A_12_GapsLedger.md, REF_CP-4A_13_OverallCovenantCapacityView.md, REF_CP-4A_CalculationRules.md

## REF_CP-4A_01_CapacitySourceGate.md
<!-- REF_CP-4A_01 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="01" name="Capacity Source Gate">
<input>All available source materials: CP-4 Legal/Covenant Review output, CP-1 financial foundation, executed credit agreements, indentures, intercreditor agreements, amendments, compliance certificates, debt schedules, basket usage trackers, covenant schedules, guarantor/collateral/subsidiary schedules.</input>
<gate>Always executes. This IS the gate check. BLOCKING: CP-4 Legal/Covenant Review output or at least one executed governing legal document must be available. If neither: Module Status = Blocked, STOP.</gate>

## Instructions
1. Confirm execution mode and required input availability.
2. Check: CP-4 output available? Executed legal documents available? CP-1 financial inputs available? Usage data available?
3. Assess legal formula availability, current financial input availability, usage data availability, and source quality.
4. Verify structured-export readiness.
5. Assign Module Status:
   - **Completed:** Legal formulas + current financial inputs + usage data all available.
   - **Completed with Limitations:** Legal formulas available but missing financial inputs, usage data, compliance certificates, or CP-4 output is itself limited.
   - **Blocked:** No executed governing document AND no CP-4 output. Output blocked message and STOP.
6. If CP-1 financials missing: headroom/capacity calculations limited — flag.
7. If CP-4 output missing or limited: legal provision extraction may be incomplete — flag.

## Output
T4C.1: Source gate register (input inventory + availability + quality + limitations)
+ Module Status: Completed / Completed with Limitations / Blocked
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-4A_02_ControllingCapacitySourceMap.md
<!-- REF_CP-4A_02 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="02" name="Controlling Capacity Source Map">
<input>T4C.1 Source Gate output; all available legal and financial documents.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Build a source-authority map for capacity calculations.
2. For each source: record Authority Rank, Source, Source Type, Version/Date, Status, Controls (Legal Formula / Financial Input / Usage), Credit Relevance, and Evidence ID.
3. Explain which source controls covenant formula extraction, which controls financial inputs, and which controls usage.
4. Identify secondary/summary sources and their limitations.
5. If source conflicts exist, note which source governs for capacity calculations.

## Output
T4C.2: `Authority Rank`|`Source`|`Source Type`|`Version / Date`|`Status`|`Controls Legal Formula / Financial Input / Usage`|`Credit Relevance`|`Evidence ID`
</step_reference>
## REF_CP-4A_03_CovenantDefinitionRatioMechanicsRegister.md
<!-- REF_CP-4A_03 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="03" name="Covenant Definition and Ratio Mechanics Register">
<input>T4C.1, T4C.2; controlling legal documents; CP-4 definition analysis (Step 4).</input>
<gate>Step 2 complete.</gate>

## Instructions
1. Map legal definitions that control capacity calculations.
2. Cover (where available): covenant EBITDA, pro forma adjustments, synergies, cash netting, debt definition, secured/first-lien/priority debt, restricted group/unrestricted subsidiaries, lien/collateral definitions, grower bases, CNI/retained ECF/available amount, ratio debt tests, RP leverage tests.
3. For each: record Definition/Ratio, Source/Clause, Formula/Definition Summary, Required Inputs, Capacity Effect, Risk Mechanic, Credit Implication (8-value label), and Evidence ID.
4. Flag definition conflicts between CP-1 and CP-4 — use governing legal definition and log conflict.
5. Flag where covenant EBITDA materially diverges from reported EBITDA.

## Output
T4C.3: `Definition / Ratio`|`Source / Clause`|`Formula / Definition Summary`|`Required Inputs`|`Capacity Effect`|`Risk Mechanic`|`Credit Implication`|`Evidence ID`
</step_reference>
## REF_CP-4A_04_HeadroomTable.md
<!-- REF_CP-4A_04 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="04" name="Headroom Table">
<input>T4C.2, T4C.3; maintenance/incurrence test provisions; CP-1 financial inputs; compliance certificates.</input>
<gate>Step 3 complete.</gate>

## Instructions
1. Build the Headroom Table for all identified covenant tests.
2. For max-ratio tests: headroom = covenant threshold − current tested ratio. Identify ratio distance to breach and, where supportable, incremental debt/EBITDA decline implied by threshold.
3. For min-ratio tests (coverage): headroom = current tested ratio − covenant threshold. Identify cushion to minimum.
4. If exact headroom unsupported, state [Insufficient Information] and identify whether the missing item is: current tested ratio, covenant definition, denominator, numerator, threshold, or basket usage.
5. Apply Calculation Rules: use governing legal definitions, not reported EBITDA.
6. Apply null-handling: Not Available / Provisional / Insufficient Information as appropriate.
7. Include status and limitation for each test.

## Output
T4C.4: `Test`|`Test Type`|`Threshold`|`Current Basis`|`Formula`|`Headroom`|`Status`|`Limitation`|`Risk Mechanic`|`Credit Implication`|`Evidence ID`
</step_reference>
## REF_CP-4A_05_CapacityRegister.md
<!-- REF_CP-4A_05 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="05" name="Capacity Register">
<input>T4C.2, T4C.3, T4C.4; all capacity provisions from controlling documents; financial inputs; usage data.</input>
<gate>Step 4 complete.</gate>

## Instructions
1. Build the Capacity Register covering: debt incurrence, incremental facilities, incremental equivalent debt, ratio debt, acquisition debt, refinancing debt, liens, restricted payments, junior debt payments, investments, permitted acquisitions, asset sales/transfers, unrestricted subsidiaries, non-guarantor transfers, add-backs, leakage paths, collateral release capacity, and guarantor release capacity.
2. For each: record Capacity Type, Basket/Test, Formula, Conditions, Current Input, Usage, Estimated Capacity, Remaining Capacity, Status (7-value), Severity (5-value), Risk Mechanic, Credit Implication, Evidence ID.
3. Apply Double-Counting Discipline: identify fungibility, shared caps, reclassification constraints.
4. Apply Calculation Rules: every calculated item must include formula, source inputs, result, period, status, limitation, source trace.
5. Apply null-handling strictly: null for unavailable numerics, [Insufficient Information] in narrative.

## Output
T4C.5: `Capacity Type`|`Basket / Test`|`Formula`|`Conditions`|`Current Input`|`Usage`|`Estimated Capacity`|`Remaining Capacity`|`Status`|`Severity`|`Risk Mechanic`|`Credit Implication`|`Evidence ID`
</step_reference>
## REF_CP-4A_06_DebtLienPrimingCapacityAnalysis.md
<!-- REF_CP-4A_06 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="06" name="Debt, Lien, and Priming Capacity Analysis">
<input>T4C.5 Capacity Register; debt/lien/incremental provisions.</input>
<gate>Step 5 complete.</gate>

## Instructions
1. Analyze capacity that can increase debt or dilute creditor priority.
2. For each route: record Route, Supported Legal Capacity, Current Calculation Status, Priming/Dilution Mechanic, PD Effect, LGD/Recovery Effect, RV/Security Selection Effect, Evidence ID.
3. Focus on: pari secured incremental, free-and-clear baskets, ratio debt, grower baskets tied to inflated EBITDA, junior/unsecured layering, MFN weakness/sunset, drop-down mechanics.
4. Translate each route into PD and LGD/recovery effects separately.
5. Flag priming-enabling provisions and quantify capacity where source-supported.

## Output
T4C.6: `Route`|`Supported Legal Capacity`|`Current Calculation Status`|`Priming / Dilution Mechanic`|`PD Effect`|`LGD / Recovery Effect`|`RV / Security Selection Effect`|`Evidence ID`
</step_reference>
## REF_CP-4A_07_RPInvestmentAssetTransferLeakageAnalysis.md
<!-- REF_CP-4A_07 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="07" name="RP, Investment, Asset Transfer, and Leakage Analysis">
<input>T4C.5 Capacity Register; RP/investment/asset transfer/USub provisions.</input>
<gate>Step 6 complete.</gate>

## Instructions
1. Analyze value movement away from creditor reach.
2. For each route: record Leakage Route, Supported Fact, Formula/Basket, Usage/Remaining Capacity, Restricted-Group/Collateral Impact, Severity (5-value), Credit Implication, Evidence ID.
3. Cover: RP baskets, builder basket, available amount, dividends, sponsor distributions, investments in non-guarantors, USub designation, IP/material asset transfers, non-guarantor transfers, asset sale reinvestment flexibility.
4. Aggregate total leakage capacity while applying Double-Counting Discipline.
5. Translate leakage capacity into recovery/LGD implications.

## Output
T4C.7: `Leakage Route`|`Supported Fact`|`Formula / Basket`|`Usage / Remaining Capacity`|`Restricted-Group / Collateral Impact`|`Severity`|`Credit Implication`|`Evidence ID`
</step_reference>
## REF_CP-4A_08_EBITDAAddBackCapacityInflationAnalysis.md
<!-- REF_CP-4A_08 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="08" name="EBITDA Add-Back and Capacity Inflation Analysis">
<input>T4C.3, T4C.4, T4C.5; EBITDA definition provisions; CP-1 financials.</input>
<gate>Step 7 complete.</gate>

## Instructions
1. Analyze EBITDA and pro forma mechanics that can expand capacity across all ratio-based tests.
2. For each feature: record Add-Back/Definition Feature, Source/Clause, Cap/Condition, Calculation Status, Capacity Inflation Mechanic, PD/LGD/RV Implication, Evidence ID.
3. Cover: synergy add-backs, cost savings, pro forma adjustments, exceptional add-backs, uncapped add-backs, time limits, documentation requirements.
4. Quantify capacity inflation where supportable (e.g., "uncapped add-backs inflate covenant EBITDA by X%, expanding grower baskets by Y").
5. Flag where covenant EBITDA diverges materially from reported EBITDA and downstream implications.

## Output
T4C.8: `Add-Back / Definition Feature`|`Source / Clause`|`Cap / Condition`|`Calculation Status`|`Capacity Inflation Mechanic`|`PD / LGD / RV Implication`|`Evidence ID`
</step_reference>
## REF_CP-4A_09_LeakageBasketFlags.md
<!-- REF_CP-4A_09 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="09" name="Leakage and Basket Flags">
<input>All capacity analysis from Steps 5–8.</input>
<gate>Step 8 complete.</gate>

## Instructions
1. Build the Leakage and Basket Flags table consolidating creditor-adverse findings.
2. For each: record Flag, Supported Fact, Creditor Risk, Severity (Low/Moderate/High/Critical/Insufficient Information), Confidence (5-value), Downstream Module, Evidence ID.
3. Prioritize flags with highest severity and broadest downstream impact.
4. Include flags for: double-counting risk, reclassification features, fungibility between baskets, USub designation capacity, collateral/guarantor release mechanics, amendment flexibility.
5. Map each flag to the downstream module(s) it affects.

## Output
T4C.9: `Flag`|`Supported Fact`|`Creditor Risk`|`Severity`|`Confidence`|`Downstream Module`|`Evidence ID`
</step_reference>
## REF_CP-4A_10-11-13_DecisionSynthesis.md
# Consolidated companion — REF_CP-4A_10-11-13_DecisionSynthesis.md

<!-- MERGED_FROM:REF_CP-4A_10_NearestPressurePoint.md sha256=c9387f47da838e808bc1ab9a93cc1641fd0ab338b9ad29c33294e55e44dac6bb -->
## Source: REF_CP-4A_10_NearestPressurePoint.md

<!-- REF_CP-4A_10 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="10" name="Nearest Pressure Point">
<input>All capacity analysis from Steps 4–9.</input>
<gate>Step 9 complete.</gate>

## Instructions
1. Identify exactly ONE covenant, basket, definition, or leakage route most relevant to deterioration or creditor leakage.
2. Apply Nearest Pressure Point Selection Rules (preference order):
   (1) Maintenance covenant headroom with near-term breach relevance.
   (2) Debt/lien capacity that can prime or dilute existing creditors.
   (3) RP/investment/USub capacity that can leak value from the restricted group.
   (4) EBITDA add-back mechanics that inflate all ratio-based capacity.
   (5) Amendment/waiver mechanics that weaken lender control.
3. For the selected pressure point, provide:
   - Pressure Point: [one capacity item]
   - Evidence: [provision / formula / financial input]
   - Risk Mechanic: [how deterioration or borrower action uses this capacity]
   - Credit Implication: [PD / LGD / liquidity / recovery / RV / portfolio impact]
   - Monitoring Signal: [specific observable data or event]
   - Evidence Needed to Tighten View: [specific missing source]
4. If evidence insufficient: [Insufficient Information] and state what is missing.

## Output
Narrative: single nearest pressure point with 6 required fields. No table.
</step_reference>

<!-- MERGED_FROM:REF_CP-4A_11_CapacityRiskPrioritizationMatrix.md sha256=30f3a1bc9a15c472ceb4c29ed9bb93fce0b0b71e1276758a314ed83d63e81830 -->
## Source: REF_CP-4A_11_CapacityRiskPrioritizationMatrix.md

<!-- REF_CP-4A_11 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="11" name="Capacity Risk Prioritization Matrix">
<input>All capacity analysis from Steps 4–10.</input>
<gate>Step 10 complete.</gate>

## Instructions
1. Prioritize supported capacity items by creditor relevance.
2. For each: record Priority (rank), Capacity Item, Severity, Confidence, Primary Risk Mechanic, PD Effect, LGD/Recovery Effect, Monitoring Action, Evidence ID.
3. Rank only supported items — do not rank items with [Insufficient Information] unless they can be partially characterized.
4. If ranking is not supportable, use [Insufficient Information].
5. Do not create exact scores unless evidence supports them.
6. This matrix is a key downstream input for CP-6 (bear legal-control attack) and CP-6A (portfolio sizing constraint).

## Output
T4C.11: `Priority`|`Capacity Item`|`Severity`|`Confidence`|`Primary Risk Mechanic`|`PD Effect`|`LGD / Recovery Effect`|`Monitoring Action`|`Evidence ID`
</step_reference>

<!-- MERGED_FROM:REF_CP-4A_13_OverallCovenantCapacityView.md sha256=b4bbdea25e3682853f30fcad5d78635d44bced523d31c62af3723c095a43ace7 -->
## Source: REF_CP-4A_13_OverallCovenantCapacityView.md

<!-- REF_CP-4A_13 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="13" name="Overall Covenant Capacity View">
<input>All prior step outputs (T4C.1–T4C.12); all capacity analysis, flags, pressure point, and gaps.</input>
<gate>Always executes. Synthesis only — no new data.</gate>

## Instructions
1. Write a committee-ready narrative synthesis using this required formulation:
   "Overall, [Issuer] has [documented / limited / insufficient] covenant-capacity visibility. The main capacity concern is [capacity item], because [risk mechanic] and [credit implication]. Exact headroom is [supported / not supported]. Further analysis requires [missing data]."
2. Then add 3–5 supported bullets ONLY where evidence supports them:
   - Most important documented headroom point.
   - Most important debt/lien capacity point.
   - Most important RP/leakage point.
   - Most important EBITDA add-back/definition point.
   - Most important downstream CP-3/CP-6/CP-6A implication.
3. Reference the nearest pressure point (Step 10).
4. Reference critical gaps (Step 12).
5. Do not introduce new data, new calculations, or new assessments — synthesize only from Steps 1–12.
6. End with module completion statement:
   - "CP-4A Completed. Gate Status: Completed."
   - "CP-4A Completed with Limitations. Key Gaps: [List]."
   - "CP-4A Blocked. Required source unavailable."

## Output
Narrative synthesis (no table). Module completion statement with Gate Status.
</step_reference>
## REF_CP-4A_10_NearestPressurePoint.md
<!-- REF_CP-4A_10 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="10" name="Nearest Pressure Point">
<input>All capacity analysis from Steps 4–9.</input>
<gate>Step 9 complete.</gate>

## Instructions
1. Identify exactly ONE covenant, basket, definition, or leakage route most relevant to deterioration or creditor leakage.
2. Apply Nearest Pressure Point Selection Rules (preference order):
   (1) Maintenance covenant headroom with near-term breach relevance.
   (2) Debt/lien capacity that can prime or dilute existing creditors.
   (3) RP/investment/USub capacity that can leak value from the restricted group.
   (4) EBITDA add-back mechanics that inflate all ratio-based capacity.
   (5) Amendment/waiver mechanics that weaken lender control.
3. For the selected pressure point, provide:
   - Pressure Point: [one capacity item]
   - Evidence: [provision / formula / financial input]
   - Risk Mechanic: [how deterioration or borrower action uses this capacity]
   - Credit Implication: [PD / LGD / liquidity / recovery / RV / portfolio impact]
   - Monitoring Signal: [specific observable data or event]
   - Evidence Needed to Tighten View: [specific missing source]
4. If evidence insufficient: [Insufficient Information] and state what is missing.

## Output
Narrative: single nearest pressure point with 6 required fields. No table.
</step_reference>
## REF_CP-4A_11_CapacityRiskPrioritizationMatrix.md
<!-- REF_CP-4A_11 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="11" name="Capacity Risk Prioritization Matrix">
<input>All capacity analysis from Steps 4–10.</input>
<gate>Step 10 complete.</gate>

## Instructions
1. Prioritize supported capacity items by creditor relevance.
2. For each: record Priority (rank), Capacity Item, Severity, Confidence, Primary Risk Mechanic, PD Effect, LGD/Recovery Effect, Monitoring Action, Evidence ID.
3. Rank only supported items — do not rank items with [Insufficient Information] unless they can be partially characterized.
4. If ranking is not supportable, use [Insufficient Information].
5. Do not create exact scores unless evidence supports them.
6. This matrix is a key downstream input for CP-6 (bear legal-control attack) and CP-6A (portfolio sizing constraint).

## Output
T4C.11: `Priority`|`Capacity Item`|`Severity`|`Confidence`|`Primary Risk Mechanic`|`PD Effect`|`LGD / Recovery Effect`|`Monitoring Action`|`Evidence ID`
</step_reference>
## REF_CP-4A_12_GapsLedger.md
<!-- REF_CP-4A_12 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="12" name="Gaps Ledger">
<input>All prior step outputs (T4C.1–T4C.11); cumulative gaps identified throughout workflow.</input>
<gate>Always executes.</gate>

## Instructions
1. Compile all gaps identified across Steps 1–11 into a consolidated ledger.
2. For each gap: record Gap, Missing Data, Why It Matters, Impact on Output (which step/table/calculation is affected), and Required Follow-Up.
3. Reference Standard Gaps Library where applicable:
   - Missing executed CA/indenture → cannot confirm governing capacity provisions.
   - Missing compliance certificate → maintenance headroom unconfirmable.
   - Missing covenant EBITDA bridge → ratio capacity unreliable.
   - Missing debt schedule → debt numerator/capacity limited.
   - Missing basket usage tracker → remaining capacity undetermined.
   - Missing guarantor/collateral/USub schedules → recovery/leakage incomplete.
   - Missing MFN details → incremental debt economics unassessable.
   - Conflicting EBITDA definitions → capacity may be materially misstated.
4. Every [Insufficient Information] in Steps 1–11 must have a corresponding gap entry.
5. Flag gaps with downstream impact on CP-6, CP-6A, CP-3C.

## Output
T4C.12: `Gap`|`Missing Data`|`Why It Matters`|`Impact on Output`|`Required Follow-Up`
</step_reference>
## REF_CP-4A_13_OverallCovenantCapacityView.md
<!-- REF_CP-4A_13 (T2) | 2026-06-03 -->
<step_reference module="CP-4A" step="13" name="Overall Covenant Capacity View">
<input>All prior step outputs (T4C.1–T4C.12); all capacity analysis, flags, pressure point, and gaps.</input>
<gate>Always executes. Synthesis only — no new data.</gate>

## Instructions
1. Write a committee-ready narrative synthesis using this required formulation:
   "Overall, [Issuer] has [documented / limited / insufficient] covenant-capacity visibility. The main capacity concern is [capacity item], because [risk mechanic] and [credit implication]. Exact headroom is [supported / not supported]. Further analysis requires [missing data]."
2. Then add 3–5 supported bullets ONLY where evidence supports them:
   - Most important documented headroom point.
   - Most important debt/lien capacity point.
   - Most important RP/leakage point.
   - Most important EBITDA add-back/definition point.
   - Most important downstream CP-3/CP-6/CP-6A implication.
3. Reference the nearest pressure point (Step 10).
4. Reference critical gaps (Step 12).
5. Do not introduce new data, new calculations, or new assessments — synthesize only from Steps 1–12.
6. End with module completion statement:
   - "CP-4A Completed. Gate Status: Completed."
   - "CP-4A Completed with Limitations. Key Gaps: [List]."
   - "CP-4A Blocked. Required source unavailable."

## Output
Narrative synthesis (no table). Module completion statement with Gate Status.
</step_reference>
## REF_CP-4A_CalculationRules.md
<!-- REF_CP-4A CalculationRules (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-4A" name="Calculation Rules, Severity & Status Labels">

Authoritative for all CP-4A capacity calculations (Steps 4–11). Load alongside the CP-4A workflow.

## Calculation Rules
### General Rules
- Use governing legal definitions for covenant tests and capacity formulas.
- Use CP-1 financial definitions only for non-legal reference metrics or where the legal definition explicitly aligns with CP-1.
- Never substitute reported EBITDA for covenant EBITDA without bridge support.
- Never assume cash netting is permitted unless the covenant definition allows it.
- Never assume basket capacity is unused unless source-supported.
- Every calculated item must include: formula, numerator, denominator, source inputs, result, period, status, limitation, and source trace.

### Null/Unavailable Handling
- **Not Available:** source does not disclose a figure.
- **Not Applicable:** provision does not exist or is not relevant.
- **Provisional:** source quality, timing, definition alignment, or completeness limits confidence.
- **Insufficient Information:** calculation cannot be performed without inventing data.
- Store unavailable numeric values as null (not zero) in structured exports, unless the source explicitly states zero.
- Store percentages as decimals where numeric storage is required.

### Core Formulas (Where Legally Supported)
- Maintenance headroom = covenant threshold − current tested ratio (max-ratio tests).
- Coverage headroom = current tested ratio − covenant threshold (min-ratio tests).
- Max additional debt before breach = solve for incremental debt at covenant threshold, using governing EBITDA/netting/pro forma/lien rules.
- Fixed basket remaining = fixed amount − documented utilization.
- Grower basket = greater of fixed amount and % of applicable base (or exact formulation as drafted).
- Builder basket = retained ECF/CNI/available amount build-up + permitted additions − documented usage.
- Ratio debt capacity = debt amount permitted while compliant with ratio test, after pro forma adjustments.
- RP capacity = fixed + builder + ratio-based RP + other permitted categories − documented usage.
- Investment capacity = fixed/grower + permitted acquisition/investment + available amount − documented usage.
- Leakage capacity = sum of value-transfer routes outside creditor reach (no double-counting).

### Double-Counting Discipline
- Do not add overlapping baskets unless the legal document permits independent use.
- Identify fungibility between debt, lien, investment, RP, and USub baskets.
- If baskets are subject to shared caps or reclassification, state the constraint.
- If capacity can be used through multiple routes, record each but do not sum as independent capacity.

### Calculation Evidence Requirements
Every calculation must cite: legal formula source, financial input source, period and currency/units, usage source, source-quality label, limitations and confidence.

## Severity Framework
| Severity | Definition |
|----------|-----------|
| Low | Capacity narrow, ordinary-course, capped, unlikely to change creditor outcome materially |
| Moderate | Capacity can affect leverage/liquidity/leakage but bounded by tests/conditions |
| High | Capacity can materially increase debt, move value, dilute collateral, or weaken lender control |
| Critical | Capacity creates plausible priming, material leakage, recovery impairment, or lender-control loss under stress |
| Insufficient Information | Source package does not support a severity conclusion |

## Data-Quality Confidence Labels
| Label | Required Support |
|-------|-----------------|
| High | Executed legal doc + current financial input + usage tracker/certificate |
| Moderate | Executed legal doc + current financial input, but usage history incomplete |
| Low | Legal provision extracted, but financial inputs stale/partial/management-adjusted |
| Formula Only | Legal formula available, no current calculation support |
| Insufficient | Legal formula or key input missing |

## Capacity Status Labels (7)
Completed | Ready with Limitations | Formula Extracted Only | Provisional | Insufficient Information | Not Applicable | Blocked

## Nearest Pressure Point Selection Rules
Preference order when evidence is comparable:
1. Maintenance covenant headroom with near-term breach relevance.
2. Debt/lien capacity that can prime or dilute existing creditors.
3. RP/investment/USub capacity that can leak value from the restricted group.
4. EBITDA add-back mechanics that inflate all ratio-based capacity.
5. Amendment/waiver mechanics that weaken lender control.
If evidence insufficient → [Insufficient Information] and state what is needed.

## Export Detail (relocated from ACTIVE_PROMPT 2026-07-11)
Markdown handoff Header fields: Issuer · Module (CP-4A · CovenantCapacityCalculator) · Reporting period · Analysis date · run_id. Analysis-narrative numerics: right-aligned with aligned decimals.

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Institutional-grade, committee-ready, provision-specific, data-dense, explicitly linked to creditor risk. Prioritize clean, Excel-ready Markdown tables. Use debt-investor language: headroom, capacity, leakage, priming, restricted-group leakage, value transfer, lender control, cure, ratio capacity, fixed basket, grower basket, add-back inflation, recovery leakage, monitoring posture. Separate source fact, legal formula, calculation, analyst interpretation, credit implication, and gap. Target 1–5 pages per issuer scaled to complexity. Do not add generic filler.

</reference>
