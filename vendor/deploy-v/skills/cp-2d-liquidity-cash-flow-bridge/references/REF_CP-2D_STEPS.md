Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-2D_LabelsAndCalc.md.

Original files, in this bundle: REF_CP-2D_01_LiquiditySourceGateReadiness.md, REF_CP-2D_02_BeginningLiquidityRegister.md, REF_CP-2D_03_MandatoryCashUsesRegister.md, REF_CP-2D_04_WorkingCapitalCapexPressure.md, REF_CP-2D_05_TwelveMonthLiquidityBridge.md, REF_CP-2D_06_MonthsToEmptyCalculation.md, REF_CP-2D_07_LiquidityMitigantsConstraints.md, REF_CP-2D_08_LiquidityRiskAssessment.md, REF_CP-2D_09_GapsLedger.md, REF_CP-2D_10_OverallLiquidityView.md, REF_CP-2D_LabelsAndCalc.md

## REF_CP-2D_01_LiquiditySourceGateReadiness.md
<!-- REF_CP-2D_01 (T2) | 2026-06-03 -->
<step_reference module="CP-2D" step="01" name="Liquidity Source Gate & Readiness">
<input>All available liquidity, cash-flow, debt-amortization, maturity, revolver, covenant, working-capital, capex, cash-interest, cash-tax evidence; CP-0 registry; CP-1/CP-1B/CP-2/CP-2A/CP-2C/CP-2E/CP-3C/CP-4A outputs where available.</input>
<gate>Always executes. This IS the gate check.</gate>

## Instructions
1. Catalogue all available source materials for liquidity and cash-flow bridge analysis.
2. For each source, record: source_document_id, source_document_name, source_quality, period, entity_covered, data_supplied, limitation, and downstream_use.
3. Confirm issuer entity keys and structured-output feasibility.
4. Identify missing required inputs: cash balances, revolver data, debt schedules, cash-flow statements, covenant documents, working-capital data, capex data.
5. Assign Module Status:
   - **Full Run:** Sufficient liquidity/cash-flow evidence for all core steps.
   - **Ready with Limitations:** Partial evidence; proceed but flag gaps.
   - **Blocked:** Critical sources absent (e.g., no cash position or cash-flow data identifiable).
6. State citation discipline requirement.

## Output
T2E.1: `source_document_id`|`source_document_name`|`source_quality`|`period`|`entity_covered`|`data_supplied`|`limitation`|`downstream_use`
+ Module Status: Full Run / Ready with Limitations / Blocked
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-2D_02_BeginningLiquidityRegister.md
<!-- REF_CP-2D_02 (T2) | 2026-06-03 -->
<step_reference module="CP-2D" step="02" name="Beginning Liquidity Register">
<input>T2E.1 Source Register; cash balance, revolver, and committed-facility source materials.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Build the beginning accessible liquidity register using permitted Liquidity Component labels.
2. Include: cash, restricted cash, revolver commitment, undrawn revolver, accessible revolver capacity (after borrowing-base/covenant constraints), and other committed liquidity where disclosed.
3. For each component: record Source-Supported Amount, Accessibility Status, Source Trace, Limitation / Restriction, Risk Mechanic, and Credit Implication.
4. Distinguish reported cash from accessible liquidity. Distinguish committed available revolver from inaccessible or covenant-constrained capacity.
5. Do not assume undrawn revolver availability is accessible unless disclosed. Restricted cash excluded unless source explicitly confirms availability.
6. Calculate Beginning Accessible Liquidity = Cash + Accessible Revolver + Other Committed Accessible Liquidity.

## Output
T2E.2: `Liquidity Component`|`Source-Supported Amount`|`Accessibility Status`|`Source Trace`|`Limitation / Restriction`|`Risk Mechanic`|`Credit Implication`
</step_reference>
## REF_CP-2D_03_MandatoryCashUsesRegister.md
<!-- REF_CP-2D_03 (T2) | 2026-06-03 -->
<step_reference module="CP-2D" step="03" name="Mandatory Cash Uses Register">
<input>T2E.1, T2E.2; debt schedules, cash-flow statements, covenant documents, capex data, interest/tax schedules.</input>
<gate>Step 2 complete.</gate>

## Instructions
1. Build the mandatory and discretionary cash uses register over the 12-month bridge horizon using permitted Cash-Use Category labels.
2. Cover: cash interest, cash taxes, debt amortization, maturities within 12 months, leases, mandatory capex, restructuring/integration cash costs, working-capital outflows, dividends/distributions, and other committed cash uses where supported.
3. For each: record Amount, Timing, Mandatory / Discretionary classification, Source Trace, Risk Mechanic, Credit Implication, and Limitation.
4. Do not assume any cash-use category is zero unless explicitly supported.
5. Flag any cash uses that are management-guided, provisional, or analyst-estimated with the appropriate Liquidity Data Status Label.

## Output
T2E.3: `Cash Use`|`Amount`|`Timing`|`Mandatory / Discretionary`|`Source Trace`|`Risk Mechanic`|`Credit Implication`|`Limitation`
</step_reference>
## REF_CP-2D_04_WorkingCapitalCapexPressure.md
<!-- REF_CP-2D_04 (T2) | 2026-06-03 -->
<step_reference module="CP-2D" step="04" name="Working Capital & Capex Pressure">
<input>T2E.1–T2E.3; working-capital, inventory, receivables, payables, and capex source materials.</input>
<gate>Steps 2–3 complete. Skip with [Insufficient Information] if no WC/capex data available.</gate>

## Instructions
1. Assess working-capital and capex pressure on near-term liquidity.
2. Address where supported: seasonal working capital, inventory build, receivables collection, payables unwind, maintenance capex, growth capex flexibility, and capex deferral risk.
3. For each driver: record Evidence, Expected Cash Impact, Risk Mechanic, Credit Implication, Source Trace, and Limitation.
4. Translate WC/capex facts into liquidity mechanics:
   - Material WC outflow → cash absorption before EBITDA converts to cash → weaker debt service and runway.
   - Capex deferral flexibility → temporary liquidity preservation → FCF durability trade-off if maintenance deferred.

## Output
T2E.4: `Driver`|`Evidence`|`Expected Cash Impact`|`Risk Mechanic`|`Credit Implication`|`Source Trace`|`Limitation`
</step_reference>
## REF_CP-2D_05_TwelveMonthLiquidityBridge.md
<!-- REF_CP-2D_05 (T2) | 2026-06-03 -->
<step_reference module="CP-2D" step="05" name="12-Month Liquidity Bridge">
<input>T2E.2, T2E.3, T2E.4; all beginning liquidity, cash-use, and WC/capex data.</input>
<gate>Steps 2–4 complete.</gate>

## Instructions
1. Build an Excel-ready Markdown table consolidating the 12-month liquidity bridge.
2. Required rows: Beginning cash, Accessible revolver availability, Beginning accessible liquidity, Operating cash inflow/outflow, Working-capital impact, Cash interest, Cash taxes, Mandatory capex, Debt amortization/maturities, Other cash uses, Ending accessible liquidity.
3. For each row: record Amount, Source / Calculation basis, Status (use Liquidity Data Status Labels), Credit Comment, and Source Trace.
4. Use Python for all bridge arithmetic.
5. Ending accessible liquidity = Beginning accessible liquidity + operating cash inflow/outflow + WC impact − cash interest − cash taxes − mandatory capex − debt amortization/maturities − other cash uses + committed inflows (source-supported).
6. Flag any row where status is Provisional, Management-guided, or Analyst estimate.

## Output
T2E.5: `Bridge Item`|`Amount`|`Source / Calculation`|`Status`|`Credit Comment`|`Source Trace`
</step_reference>
## REF_CP-2D_06_MonthsToEmptyCalculation.md
<!-- REF_CP-2D_06 (T2) | 2026-06-03 -->
<step_reference module="CP-2D" step="06" name="Months to Empty Calculation">
<input>T2E.5 (Beginning accessible liquidity, cash-burn data).</input>
<gate>Step 5 complete. Calculate only where beginning accessible liquidity AND cash-burn basis are both supported. If either is unsupported, state [Insufficient Information] and list missing inputs.</gate>

## Instructions
1. Calculate: **Months to Empty = Beginning accessible liquidity / average monthly cash burn.**
2. Use Python for calculation.
3. State the source period for cash burn and whether it is recurring, seasonal, or distorted.
4. Do not annualize or monthly-average volatile cash flows without explaining the limitation.
5. If cash-burn basis is from a non-representative period (seasonal, one-off, restructuring), state the limitation and its impact on the MTE figure.
6. If unsupported, state [Insufficient Information] and list each missing input.

## Output
T2E.6: Months to Empty result (numeric) + calculation basis narrative, OR [Insufficient Information] with missing-input list.
</step_reference>
## REF_CP-2D_07_LiquidityMitigantsConstraints.md
<!-- REF_CP-2D_07 (T2) | 2026-06-03 -->
<step_reference module="CP-2D" step="07" name="Liquidity Mitigants & Constraints">
<input>T2E.2–T2E.6; all liquidity, covenant, revolver, capex, sponsor, and refinancing evidence.</input>
<gate>Steps 2–6 complete.</gate>

## Instructions
1. Build a mitigants and constraints register covering both positive liquidity levers and negative access restrictions.
2. Include where supported: revolver access, capex deferral, working-capital release, sponsor support, asset sales, covenant constraints, restricted cash, borrowing-base constraints, maturities, and refinancing access.
3. For each: record Evidence, Risk Mechanic, Credit Implication, Source Trace, and Limitation.
4. Use Monitoring Trigger Type labels where applicable (cash below threshold, revolver draw, covenant access constraint, maturity wall, etc.).
5. Distinguish mitigants (liquidity-positive) from constraints (liquidity-negative).

## Output
T2E.7: `Mitigant / Constraint`|`Evidence`|`Risk Mechanic`|`Credit Implication`|`Source Trace`|`Limitation`
</step_reference>
## REF_CP-2D_08_LiquidityRiskAssessment.md
<!-- REF_CP-2D_08 (T2) | 2026-06-03 -->
<step_reference module="CP-2D" step="08" name="Liquidity Risk Assessment">
<input>T2E.2–T2E.7; cumulative liquidity evidence from all prior steps.</input>
<gate>Steps 2–7 complete.</gate>

## Instructions
1. Assign one Liquidity Risk Level: **Adequate** | **Tight** | **Weak** | **Insufficient Information**.
2. Support the assessment using Evidence → Risk Mechanic → Credit Implication chain.
3. Risk Level Guide:
   - **Adequate:** Source-supported liquidity coverage of mandatory cash uses; no identified access constraint that materially weakens availability.
   - **Tight:** Liquidity covers near-term needs but headroom is narrow, seasonal, covenant-constrained, or dependent on execution.
   - **Weak:** Accessible liquidity appears insufficient, near-term maturities/cash burn are material, or covenant/revolver access constraints materially pressure liquidity.
   - **Insufficient Information:** Decision-useful classification not supportable.
4. Reference Months to Empty result from Step 6 where available.
5. Reference key mitigants and constraints from Step 7.
6. State countervailing evidence where applicable.

## Output
Liquidity Risk Level: [Adequate / Tight / Weak / Insufficient Information] + supporting narrative using Evidence → Risk Mechanic → Credit Implication.
</step_reference>
## REF_CP-2D_09_GapsLedger.md
<!-- REF_CP-2D_09 (T2) | 2026-06-03 -->
<step_reference module="CP-2D" step="09" name="Gaps Ledger">
<input>All prior step outputs (T2E.1–T2E.8 + Risk Assessment); cumulative gaps identified throughout workflow.</input>
<gate>Always executes.</gate>

## Instructions
1. Compile all gaps identified across Steps 1–8 into a consolidated ledger.
2. For each gap: record Missing Data, Why It Matters (credit relevance), Impact on Output (which step/table/calculation is affected), Required Follow-Up (what source is needed), and Downstream Module Affected.
3. Cover gaps in: cash balances, restricted cash classification, revolver commitment/availability, borrowing-base data, covenant constraints on revolver, debt amortization schedules, maturity schedules, cash interest schedules, cash tax estimates, working-capital data, capex breakdown (mandatory vs. growth), lease obligations, restructuring/integration costs, dividend/distribution commitments, sponsor support evidence, asset-sale proceeds, covenant headroom data (CP-4A), refinancing-window data (CP-3C).
4. Flag gaps that prevent Months to Empty calculation or Liquidity Risk Level assignment.

## Output
T2E.9: `Gap`|`Missing Data`|`Why It Matters`|`Impact on Output`|`Required Follow-Up`|`Downstream Module Affected`
</step_reference>
## REF_CP-2D_10_OverallLiquidityView.md
<!-- REF_CP-2D_10 (T2) | 2026-06-03 -->
<step_reference module="CP-2D" step="10" name="Overall Liquidity View">
<input>All prior step outputs (T2E.1–T2E.9); Liquidity Risk Level from Step 8.</input>
<gate>Always executes. Synthesis only — no new data.</gate>

## Instructions
1. Write a committee-ready narrative synthesis using the template:
   "Overall, [Issuer] has [adequate / tight / weak / insufficient information] near-term liquidity. Beginning accessible liquidity is [amount / insufficient information], while expected 12-month cash uses are [amount / insufficient information]. The key liquidity pressure is [driver], which matters because [risk mechanic] and implies [credit implication]. Months to Empty is [result / insufficient information]. Further analysis requires [missing data]."
2. Do not introduce new data, new calculations, or new assessments — synthesize only from Steps 1–9.
3. End with one of:
   - "CP-2D Completed. Liquidity Risk Level: [Level]."
   - "CP-2D Completed with Limitations. Liquidity Risk Level: [Level]. Key Gaps: [List]."
   - "CP-2D Blocked. Missing Required Inputs: [List]."

## Output
Narrative synthesis (no table). Module completion statement with Liquidity Risk Level.
</step_reference>
## REF_CP-2D_LabelsAndCalc.md
<!-- REF_CP-2D LabelsAndCalc (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-2D" name="Liquidity Labels, Categories & Calculation Rules">

Authoritative for CP-2D bridge construction and risk classification (Steps 2–8). Load alongside the CP-2D workflow. The Liquidity-to-Credit Translation rules stay in the ACTIVE_PROMPT.

## Liquidity Component Labels
Cash | Restricted cash | Revolver commitment | Revolver drawn | Undrawn revolver | Accessible revolver availability | Borrowing-base constrained availability | Covenant-constrained availability | Other committed liquidity | Asset-sale proceeds | Sponsor support | Equity cure | Working-capital release

## Cash-Use Categories
Cash interest | Cash taxes | Debt amortization | Maturity | Lease payment | Mandatory capex | Growth capex | Restructuring cost | Integration cost | Working-capital outflow | Dividend / distribution | Litigation / settlement | Pension contribution | Other mandatory cash use | Other discretionary cash use

## Liquidity Data Status Labels
NOTE: These classify the data-quality basis of individual bridge items. Distinct from the canonical 8-value Calculation Status taxonomy (CP-1).
Reported | Calculated | Provisional | Management-guided | Analyst estimate | Insufficient Information | Not Available | Not Comparable | Conflict Logged | Blocked

## Liquidity Risk Levels
**Adequate:** Source-supported liquidity coverage of mandatory cash uses; no identified access constraint that materially weakens availability.
**Tight:** Liquidity covers near-term needs but headroom is narrow, seasonal, covenant-constrained, or dependent on execution.
**Weak:** Accessible liquidity appears insufficient, near-term maturities/cash burn are material, or covenant/revolver access constraints materially pressure liquidity.
**Insufficient Information:** Decision-useful classification not supportable.

## Monitoring Trigger Types
Cash below threshold | Revolver draw | Revolver availability decline | Working-capital outflow | Cash burn acceleration | Capex inflexibility | Maturity wall | Covenant access constraint | Borrowing-base deterioration | Sponsor support dependence | Asset-sale dependence | Refinancing failure | Reporting gap

## Core Calculation Definitions
- **Cash** = reported cash and cash equivalents, excluding restricted cash unless source explicitly says available.
- **Accessible revolver** = disclosed undrawn and available committed capacity after borrowing-base, covenant, jurisdictional, collateral, and other known constraints.
- **Beginning accessible liquidity** = Cash + Accessible revolver + Other committed accessible liquidity (source-supported).
- **12-month cash uses** = mandatory + source-supported discretionary cash uses within bridge horizon.
- **Ending accessible liquidity** = Beginning accessible liquidity + operating cash inflow/outflow + WC impact − cash interest − cash taxes − mandatory capex − debt amortization/maturities − other cash uses + committed inflows (source-supported).
- **Months to Empty** = Beginning accessible liquidity / average monthly cash burn. Calculate only where both inputs are supported.

## Calculation Rules
1. Use Python for all liquidity runway, bridge total, average monthly cash burn, revolver availability, cash-use, headroom, and Months to Empty calculations.
2. Distinguish cash from total liquidity; distinguish committed available revolver from inaccessible/covenant-constrained liquidity.
3. Do not calculate Months to Empty unless beginning accessible liquidity and cash-burn basis are supported.
4. If cash burn is based on a recent period, state source period and whether recurring, seasonal, or distorted.
5. Store unavailable numeric values as null in structured exports, not zero.
6. Percentages must be stored as decimals where numeric storage is required.
7. Preserve CP-1 metric definitions where applicable.

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Institutional-grade, committee-ready, creditor-first, evidence-led, data-dense. Prefer registers, source gates, calculation tables, sensitivity tables, and evidence traces over broad prose. Every material conclusion must connect Evidence → Risk Mechanic → Credit Implication. Use limitation language explicitly where the source set does not support a conclusion. Target 1–5 pages per issuer, scaled to source quality and issuer complexity.

</reference>
