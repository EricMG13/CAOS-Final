Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-2E_Discipline.md, REF_CP-2E_ExposureLabels.md, REF_CP-2E_Workflow.md.

Original files, in this bundle: REF_CP-2E_01_MacroHedgingSourceGateReadiness.md, REF_CP-2E_02_DebtRateExposureRegister.md, REF_CP-2E_03_HedgingRegister.md, REF_CP-2E_04_UnhedgedFloatingRateExposure.md, REF_CP-2E_05_BaseRateSensitivity.md, REF_CP-2E_06_FXExposureMismatchRegister.md, REF_CP-2E_07_CommodityInflationSensitivity.md, REF_CP-2E_08_MacroSensitivitySummary.md, REF_CP-2E_09_GapsLedger.md, REF_CP-2E_10_OverallMacroHedgingView.md, REF_CP-2E_Discipline.md, REF_CP-2E_ExposureLabels.md, REF_CP-2E_Workflow.md

## REF_CP-2E_01_MacroHedgingSourceGateReadiness.md
<!-- REF_CP-2E_01 (T2) | 2026-06-03 -->
<step_reference module="CP-2E" step="01" name="Macro / Hedging Source Gate & Readiness">
<input>All available debt, fixed/floating, cash-interest, swap/cap/collar/forward, FX, commodity, inflation, hedging-policy evidence; CP-0 registry; CP-1/CP-1B/CP-2/CP-2A/CP-2D/CP-3C/CP-4A outputs where available.</input>
<gate>Always executes. This IS the gate check.</gate>

## Instructions
1. Catalogue all available source materials for macro, hedging, FX, commodity, and inflation analysis.
2. For each source, record: source_document_id, source_document_name, source_quality, period, entity_covered, data_supplied, limitation, and downstream_use.
3. Confirm issuer entity keys and structured-output feasibility.
4. Identify missing required inputs: debt schedules (fixed/floating split), hedge documentation, FX revenue/cost data, commodity cost data, inflation/pass-through data.
5. Assign Module Status:
   - **Full Run:** Sufficient rate, hedge, FX, and commodity/inflation evidence for all core steps.
   - **Ready with Limitations:** Partial evidence; proceed but flag gaps.
   - **Blocked:** Critical sources absent (e.g., no debt schedule or fixed/floating split identifiable).
6. State citation discipline requirement.

## Output
T2F.1: `source_document_id`|`source_document_name`|`source_quality`|`period`|`entity_covered`|`data_supplied`|`limitation`|`downstream_use`
+ Module Status: Full Run / Ready with Limitations / Blocked
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-2E_02_DebtRateExposureRegister.md
<!-- REF_CP-2E_02 (T2) | 2026-06-03 -->
<step_reference module="CP-2E" step="02" name="Debt & Rate Exposure Register">
<input>T2F.1 Source Register; debt schedules, credit agreements, indentures, lender presentations with fixed/floating detail.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Build the debt and rate exposure register using Rate Exposure Labels.
2. For each debt instrument: record Amount, Fixed / Floating classification, Base Rate (e.g., SOFR, EURIBOR), Margin / Coupon, Currency, Maturity, Hedge Status, Source Trace, and Credit Implication.
3. Identify total fixed-rate debt and total floating-rate debt.
4. Do not assume all debt is floating rate unless disclosed.
5. Flag instruments where fixed/floating classification is unclear or missing.

## Output
T2F.2: `Debt Instrument`|`Amount`|`Fixed / Floating`|`Base Rate`|`Margin / Coupon`|`Currency`|`Maturity`|`Hedge Status`|`Source Trace`|`Credit Implication`
</step_reference>
## REF_CP-2E_03_HedgingRegister.md
<!-- REF_CP-2E_03 (T2) | 2026-06-03 -->
<step_reference module="CP-2E" step="03" name="Hedging Register">
<input>T2F.1, T2F.2; hedge documentation, credit agreements, lender presentations, company presentations.</input>
<gate>Step 2 complete. Skip with [Insufficient Information] if no hedge data available.</gate>

## Instructions
1. Build the hedging register using Hedge Labels (Types and Coverage Status).
2. Include where disclosed: interest-rate swaps, caps, collars, fixed-rate debt acting as hedge, FX forwards, FX options, natural hedges, commodity hedges, fuel/energy hedges, inflation-linked pass-throughs.
3. For each: record Hedge Type, Notional, Instrument Covered (link to T2F.2 debt instrument), Rate / Strike, Maturity, Coverage Status (Effective where supported / Partial / Expired / Maturity mismatch / Notional disclosed only / Terms insufficient / Insufficient Information), Source Trace, and Limitation.
4. Do not assume swaps/caps/collars/forwards are effective unless terms are disclosed.
5. Do not treat notional hedge amount as effective cash-flow protection unless instrument, covered exposure, rate/strike, maturity, and coverage period are sufficiently disclosed.

## Output
T2F.3: `Hedge Type`|`Notional`|`Instrument Covered`|`Rate / Strike`|`Maturity`|`Coverage Status`|`Source Trace`|`Limitation`
</step_reference>
## REF_CP-2E_04_UnhedgedFloatingRateExposure.md
<!-- REF_CP-2E_04 (T2) | 2026-06-03 -->
<step_reference module="CP-2E" step="04" name="Unhedged Floating-Rate Exposure">
<input>T2F.2, T2F.3; debt and hedge registers.</input>
<gate>Steps 2–3 complete.</gate>

## Instructions
1. Calculate and present the unhedged floating-rate exposure breakdown.
2. Required rows: Total debt, Gross floating-rate debt, Hedged floating-rate debt, Unhedged floating-rate debt, Unhedged debt percentage.
3. For each: record Amount, Formula / Source basis, Status (use Reported / Calculated / Insufficient Information), Credit Implication, and Source Trace.
4. Use Python for calculations:
   - Unhedged floating-rate debt = Gross floating-rate debt − Hedged floating-rate debt.
   - Unhedged debt percentage = Unhedged floating-rate debt / Total debt.
5. If either gross floating-rate debt or hedge data is unsupported, state [Insufficient Information] for unhedged exposure.

## Output
T2F.4: `Metric`|`Amount`|`Formula / Source`|`Status`|`Credit Implication`|`Source Trace`
</step_reference>
## REF_CP-2E_05_BaseRateSensitivity.md
<!-- REF_CP-2E_05 (T2) | 2026-06-03 -->
<step_reference module="CP-2E" step="05" name="+100 bps Base-Rate Sensitivity">
<input>T2F.4 (Unhedged floating-rate debt).</input>
<gate>Step 4 complete. Calculate only where unhedged floating-rate exposure is supported. If unsupported, state [Insufficient Information] and list missing inputs.</gate>

## Instructions
1. Calculate: **+100 bps cash-interest impact = Unhedged floating-rate debt × 1.00%.**
2. Use Python for calculation.
3. Present: Sensitivity name, Formula, Source Inputs, Estimated Cash Impact, FCF / Liquidity Implication, Status, and Source Trace.
4. Translate the cash-interest impact into FCF, liquidity, and debt service mechanics.
5. If unhedged floating-rate debt is [Insufficient Information], state the sensitivity as [Insufficient Information] and list each missing input.

## Output
T2F.5: `Sensitivity`|`Formula`|`Source Inputs`|`Estimated Cash Impact`|`FCF / Liquidity Implication`|`Status`|`Source Trace`
</step_reference>
## REF_CP-2E_06_FXExposureMismatchRegister.md
<!-- REF_CP-2E_06 (T2) | 2026-06-03 -->
<step_reference module="CP-2E" step="06" name="FX Exposure & Mismatch Register">
<input>T2F.1–T2F.5; revenue, cost, debt, EBITDA, cash, and covenant currency data from source materials and upstream modules.</input>
<gate>Steps 2–5 complete. Skip with [Insufficient Information] if no FX/currency data available.</gate>

## Instructions
1. Build the FX exposure and mismatch register using FX Exposure Labels.
2. For each exposure type: record Revenue Currency / Region, Cost Currency / Region, Debt / EBITDA / Cash / Covenant Currency, Natural Hedge? (Yes / No / Partial / Insufficient Information), Evidence, Risk Mechanic, Credit Implication, Source Trace, and Limitation.
3. Identify translation vs. transaction exposure.
4. Identify covenant currency mismatch risk and cash repatriation constraints.
5. Do not infer FX exposure from geography alone — require revenue/cost/debt/EBITDA/cash/covenant currency data.

## Output
T2F.6: `Exposure Type`|`Revenue Currency / Region`|`Cost Currency / Region`|`Debt / EBITDA / Cash / Covenant Currency`|`Natural Hedge?`|`Evidence`|`Risk Mechanic`|`Credit Implication`|`Source Trace`|`Limitation`
</step_reference>
## REF_CP-2E_07_CommodityInflationSensitivity.md
<!-- REF_CP-2E_07 (T2) | 2026-06-03 -->
<step_reference module="CP-2E" step="07" name="Raw Material / Commodity / Inflation Sensitivity">
<input>T2F.1–T2F.6; raw-material, energy, freight, labour, inflation, and pass-through evidence.</input>
<gate>Steps 2–6 complete. Skip with [Insufficient Information] if no commodity/inflation data available.</gate>

## Instructions
1. Build the commodity and inflation sensitivity register using Commodity / Inflation Labels.
2. For each driver: record Input / Commodity / Inflation Driver, Cost Exposure, Pass-Through Mechanism (indexation / surcharge / lagged recovery / none / Insufficient Information), Evidence, Risk Mechanic, Credit Implication, Source Trace, and Limitation.
3. Cover where supported: raw-material exposure, energy exposure, freight exposure, labour/wage inflation, rent inflation, procurement exposure.
4. Assess pass-through ability: does the issuer have contractual indexation, surcharge mechanisms, or demonstrated pricing power? Or is there a lag, margin squeeze, or demand elasticity risk?
5. Translate commodity/inflation exposure into FCF durability, margin, and covenant headroom mechanics.

## Output
T2F.7: `Input / Commodity / Inflation Driver`|`Cost Exposure`|`Pass-Through Mechanism`|`Evidence`|`Risk Mechanic`|`Credit Implication`|`Source Trace`|`Limitation`
</step_reference>
## REF_CP-2E_08_MacroSensitivitySummary.md
<!-- REF_CP-2E_08 (T2) | 2026-06-03 -->
<step_reference module="CP-2E" step="08" name="Macro Sensitivity Summary">
<input>T2F.2–T2F.7; cumulative rate, hedge, FX, commodity, and inflation evidence from all prior steps.</input>
<gate>Steps 2–7 complete.</gate>

## Instructions
1. Build a consolidated macro sensitivity summary table covering all material macro drivers.
2. Drivers may include: base rates, inflation, FX, commodities, energy, wages, freight, demand sensitivity, and hedge cliffs.
3. For each driver: record Evidence, Risk Mechanic, FCF / Liquidity Impact, Refinancing / RV Implication, Monitoring Trigger (use Monitoring Trigger labels where applicable), and Source Trace.
4. Assign one Macro Risk Level: **Low** | **Moderate** | **High** | **Insufficient Information**.
5. Risk Level Guide:
   - **Low:** Source-supported limited exposure or effective mitigation.
   - **Moderate:** Exposure present but mitigants or pass-through evidence partially reduce FCF volatility.
   - **High:** Unsupported or unhedged exposure can materially pressure FCF, liquidity, debt service, covenant headroom, refinancing, recovery, or RV.
   - **Insufficient Information:** Decision-useful classification not supportable.
6. Support the risk level with Evidence → Risk Mechanic → Credit Implication chain.

## Output
T2F.8: `Macro Driver`|`Evidence`|`Risk Mechanic`|`FCF / Liquidity Impact`|`Refinancing / RV Implication`|`Monitoring Trigger`|`Source Trace`
+ Macro Risk Level: [Low / Moderate / High / Insufficient Information]
</step_reference>
## REF_CP-2E_09_GapsLedger.md
<!-- REF_CP-2E_09 (T2) | 2026-06-03 -->
<step_reference module="CP-2E" step="09" name="Gaps Ledger">
<input>All prior step outputs (T2F.1–T2F.8 + Risk Level); cumulative gaps identified throughout workflow.</input>
<gate>Always executes.</gate>

## Instructions
1. Compile all gaps identified across Steps 1–8 into a consolidated ledger.
2. For each gap: record Missing Data, Why It Matters (credit relevance), Impact on Output (which step/table/calculation is affected), Required Follow-Up (what source is needed), and Downstream Module Affected.
3. Cover gaps in: debt schedules (fixed/floating split), base-rate references, hedge documentation (type, notional, rate/strike, maturity, coverage), FX revenue/cost/debt/EBITDA/cash/covenant currency data, commodity/raw-material cost breakdown, pass-through mechanism evidence, inflation data, energy/freight/wage cost data, demand elasticity data.
4. Flag gaps that prevent +100 bps sensitivity calculation or Macro Risk Level assignment.

## Output
T2F.9: `Gap`|`Missing Data`|`Why It Matters`|`Impact on Output`|`Required Follow-Up`|`Downstream Module Affected`
</step_reference>
## REF_CP-2E_10_OverallMacroHedgingView.md
<!-- REF_CP-2E_10 (T2) | 2026-06-03 -->
<step_reference module="CP-2E" step="10" name="Overall Macro / Hedging View">
<input>All prior step outputs (T2F.1–T2F.9); Macro Risk Level from Step 8.</input>
<gate>Always executes. Synthesis only — no new data.</gate>

## Instructions
1. Write a committee-ready narrative synthesis using the template:
   "Overall, [Issuer] has [low / moderate / high / insufficient information] macro and hedging sensitivity. Unhedged floating-rate debt is [amount / percentage / insufficient information], and a +100 bps rate move would affect cash interest by [amount / insufficient information]. FX and raw-material risk appear [manageable / material / insufficient information] because [evidence]. The main credit implication is [PD / liquidity / FCF / refinancing / RV impact]. Further analysis requires [missing data]."
2. Do not introduce new data, new calculations, or new assessments — synthesize only from Steps 1–9.
3. End with one of:
   - "CP-2E Completed. Macro Risk Level: [Level]."
   - "CP-2E Completed with Limitations. Macro Risk Level: [Level]. Key Gaps: [List]."
   - "CP-2E Blocked. Missing Required Inputs: [List]."

## Output
Narrative synthesis (no table). Module completion statement with Macro Risk Level.
</step_reference>
## REF_CP-2E_Discipline.md
<!-- REF_CP-2E Discipline (full Prohibited Behaviors list) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-2E" name="Prohibited Behaviors — Full Binding List">

## Prohibited Behaviors (relocated from ACTIVE_PROMPT 2026-07-11)
1. Do not fabricate sections if a required source is unavailable — mark [Insufficient Information] and log the gap.
2. Do not change or override financial metric definitions from CP-1 if CP-1 is provided.
3. Do not infer transaction terms, valuation, use of proceeds, sponsor economics, ownership dates, legal capacity, market data, or portfolio constraints if not explicitly supported.
4. Do not silently reconcile conflicting sources — log the conflict.
5. Do not use generic adjectives (market-leading, robust, strong, resilient, diversified, ample, cheap, rich) unless immediately supported by issuer-specific evidence and credit implication.
6. Do not convert missing information into either a positive or adverse conclusion.
7. Do not assign a formal rating unless explicitly instructed.
8. Do not assign relative-value labels unless market data and the relevant module support them.
9. Do not assume all debt is floating rate unless disclosed.
10. Do not assume swaps, caps, collars, or forwards are effective unless terms are disclosed.
11. Do not assume hedges cover full exposure unless disclosed.
12. Do not treat notional hedge amount as effective cash-flow protection unless instrument, covered exposure, rate/strike, maturity, and coverage period are sufficiently disclosed.
13. Do not infer FX exposure from geography alone unless revenue/cost/debt/EBITDA/cash/covenant currency data supports the conclusion.
14. Do not cite a source for a claim not explicitly supported by that source.

</reference>
## REF_CP-2E_ExposureLabels.md
<!-- REF_CP-2E ExposureLabels (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-2E" name="Rate, Hedge, FX & Commodity Exposure Labels">

Authoritative label sets for CP-2E exposure registers (Steps 2–7). Load alongside the CP-2E workflow.

## Rate Exposure Labels
Fixed-rate debt | Floating-rate debt | Base-rate exposure | Gross floating-rate debt | Hedged floating-rate debt | Unhedged floating-rate debt | Cash-interest sensitivity | Interest-rate floor | Margin | Coupon | Reference rate | Hedge cliff

## Hedge Labels
**Types:** Interest-rate swap | Interest-rate cap | Collar | Fixed-rate debt | FX forward | FX option | Natural hedge | Commodity hedge | Fuel hedge | Energy hedge | Inflation-linked pass-through
**Coverage Status:** Effective where supported | Partial | Expired | Maturity mismatch | Notional disclosed only | Terms insufficient | Insufficient Information

## FX Exposure Labels
Revenue currency | Cost currency | EBITDA currency | Debt currency | Cash currency | Covenant currency | Translation exposure | Transaction exposure | Natural hedge | Covenant currency mismatch | Cash repatriation constraint

## Commodity / Inflation Labels
Raw-material exposure | Energy exposure | Freight exposure | Labour / wage inflation | Rent inflation | Procurement exposure | Pass-through mechanism | Indexation | Surcharge | Lagged recovery | Margin squeeze | Demand elasticity

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Institutional-grade, committee-ready, creditor-first, evidence-led, data-dense. Prefer registers, source gates, calculation tables, sensitivity tables, and evidence traces over broad prose. Every material conclusion must connect Evidence → Risk Mechanic → Credit Implication. Use limitation language explicitly where the source set does not support a conclusion. Target 1–5 pages per issuer, scaled to source quality and issuer complexity.

## Macro-to-Credit Translation (relocated from ACTIVE_PROMPT 2026-07-11)
Translate exposure into mechanics, not adjectives:
- Unhedged floating-rate debt → higher cash interest when base rates rise → weaker FCF, lower liquidity, higher refinancing pressure.
- Hedge maturity before debt maturity → protection cliff → forward cash-interest volatility and monitoring trigger.
- Revenue-cost currency mismatch → margin volatility → weaker EBITDA-to-cash conversion, potentially higher leverage.
- Commodity input without pass-through evidence → gross-margin pressure → lower FCF durability and covenant headroom.

</reference>
## REF_CP-2E_Workflow.md
<!-- REF_CP-2E Workflow (10-step table) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-2E" name="Workflow — 10 Steps">

## Workflow — 10 Steps (relocated from ACTIVE_PROMPT 2026-07-11)
| Step | Name | REF File | Output |
|------|------|----------|--------|
| 1 | Macro / Hedging Source Gate & Readiness | REF_CP-2E_01 | T2F.1 Source Register + Module Status |
| 2 | Debt & Rate Exposure Register | REF_CP-2E_02 | T2F.2 Debt & Rate Exposure Register |
| 3 | Hedging Register | REF_CP-2E_03 | T2F.3 Hedging Register |
| 4 | Unhedged Floating-Rate Exposure | REF_CP-2E_04 | T2F.4 Unhedged Exposure Table |
| 5 | +100 bps Base-Rate Sensitivity | REF_CP-2E_05 | T2F.5 Rate Sensitivity Table |
| 6 | FX Exposure & Mismatch Register | REF_CP-2E_06 | T2F.6 FX Exposure Register |
| 7 | Raw Material / Commodity / Inflation Sensitivity | REF_CP-2E_07 | T2F.7 Commodity & Inflation Table |
| 8 | Macro Sensitivity Summary | REF_CP-2E_08 | T2F.8 Macro Sensitivity Summary |
| 9 | Gaps Ledger | REF_CP-2E_09 | T2F.9 Gaps Ledger |
| 10 | Overall Macro / Hedging View | REF_CP-2E_10 | Narrative synthesis |

</reference>
