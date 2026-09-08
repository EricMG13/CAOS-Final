Consolidated method bundle. Each section retains its reference filename as a heading; the text reflects the current CP-3 workflow.

This is an absorbed phase of CP-3. References to CP-3/CP-3A outputs mean the source-grounded results already produced in the current run, or a matching validated handoff when available. No intermediate export, separate invocation or user approval is required. Apply SKILL.md’s maintained Sector RV loan-reference policy here, including its current-source basis and date treatment. Append this phase’s registers to the single CP-3 handoff.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-3A_TaxonomyAndLabels.md.

Original files, in this bundle: REF_CP-3A_01_InstrumentDataGate.md, REF_CP-3A_02_CapitalStructureDashboard.md, REF_CP-3A_03_InstrumentMatrix.md, REF_CP-3A_04_StructuralPositioningLog.md, REF_CP-3A_05_LegalCovenantLMEOverlay.md, REF_CP-3A_06_RecoverySensitivity.md, REF_CP-3A_07_CompensationCrossCheck.md, REF_CP-3A_08_PreferenceDecisionTable.md, REF_CP-3A_09_RankingTradeOffSummary.md, REF_CP-3A_10_MonitoringTriggers.md, REF_CP-3A_11_GapsLedger.md, REF_CP-3A_12_OverallInstrumentPreferenceView.md, REF_CP-3A_TaxonomyAndLabels.md

## REF_CP-3A_01_InstrumentDataGate.md
<!-- REF_CP-3A_01 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="01" name="Instrument Data Gate">
<input>All available source materials: CP-3 RV output, capital structure data (credit agreements, indentures, lender presentations), instrument terms, market data (pricing/spread/yield/DM), CP-4/CP-4A legal/recovery outputs, CP-3C refinancing/LME outputs, CP-0/CP-1/CP-2 fundamentals.</input>
<gate>Always executes. This IS the gate check. BLOCKING: CP-3 RV analysis must be available AND capital structure must include seniority/subordination. If not met: mark the affected preference assessment Blocked with UPSTREAM_DEPENDENCY_MISSING and stop only its dependent conclusions. Preserve supported RV results, record the actual gap, and continue independent work in the same CP-3 handoff.</gate>

## Instructions
1. Verify Gate 1: CP-3 RV analysis available.
2. Verify Gate 2: Capital structure includes seniority/subordination detail.
3. If either gate fails: mark the affected preference assessment Blocked with UPSTREAM_DEPENDENCY_MISSING; withhold its dependent conclusions, preserve supported RV results and continue independent work.
4. Catalogue all sources: record source_document_id, source_document_name, source_quality, period, entity_covered, data_supplied, limitation, downstream_use.
5. Reuse Sector RV loan observations and their maintained-current source basis from the CP-3 stage. Record quote quality and metric basis; assess pricing dates normally for other sources.
6. Assess legal-data quality (credit agreement, indenture, intercreditor availability).
7. Assess recovery-data quality (CP-4/CP-4A availability, CP-3C refinancing/LME outputs).
8. Flag draft, unsigned, stale, incomplete, or conflicting documents — reduce confidence.
9. Assign Module Status: Full Run / Ready with Limitations / Blocked.

## Output
T3B.1: `source_document_id`|`source_document_name`|`source_quality`|`period`|`entity_covered`|`data_supplied`|`limitation`|`downstream_use`
+ Module Status: Full Run / Ready with Limitations / Blocked
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-3A_02_CapitalStructureDashboard.md
<!-- REF_CP-3A_02 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="02" name="Capital Structure Dashboard">
<input>T3B.1 Source Register; capital structure data from credit agreements, indentures, lender presentations, CP-3 output.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Map all instruments in the issuer's capital structure.
2. Order instruments by structural priority (not maturity).
3. For each instrument: record Type (using Instrument Type Taxonomy), Amount, Currency, Maturity, Seniority/Lien position, Collateral, Guarantors, Coupon/Margin, Fixed/Floating, and Source Trace.
4. Identify total secured debt, total unsecured debt, total debt.
5. Flag instruments where seniority, collateral, or guarantor information is incomplete.

## Output
T3B.2: `Instrument`|`Type`|`Amount`|`Currency`|`Maturity`|`Seniority / Lien`|`Collateral`|`Guarantors`|`Coupon / Margin`|`Fixed / Floating`|`Source Trace`
</step_reference>
## REF_CP-3A_03_InstrumentMatrix.md
<!-- REF_CP-3A_03 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="03" name="Instrument Matrix">
<input>T3B.1, T3B.2; market data (pricing sheets, trading data, CP-3 RV table).</input>
<gate>Step 2 complete.</gate>

## Instructions
1. Build the instrument matrix combining structural data with market data.
2. For each instrument: record Price, Spread/Yield/DM, Market Date, Pricing Source, Quote Quality, Call Schedule (if bond), Covenant Package summary, Liquidity assessment, and Source Trace.
3. If market data is absent for an instrument, record [Insufficient Information] for market fields.
4. Preserve source dates. Sector RV loan observations are current under the maintained-source policy; assess potential staleness only for other pricing sources.
5. Note liquidity limitations (bid-ask spread, dealer count, trading frequency where available).

## Output
T3B.3: `Instrument`|`Price`|`Spread / Yield / DM`|`Market Date`|`Source`|`Quote Quality`|`Call Schedule`|`Covenant Package`|`Liquidity`|`Source Trace`
</step_reference>
## REF_CP-3A_04_StructuralPositioningLog.md
<!-- REF_CP-3A_04 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="04" name="Structural Positioning Log">
<input>T3B.2, T3B.3; legal/structural evidence from credit agreements, indentures, intercreditor agreements.</input>
<gate>Step 3 complete.</gate>

## Instructions
1. Assess structural positioning for each instrument using Structural Concepts.
2. For each: record Structural Rank (ordinal position), Contractual Seniority, Lien Priority, Guarantee Coverage, Collateral Coverage, Structural Subordination (Yes/No/Partial), Priming Capacity (risk of being primed by incremental debt), Key Risk Mechanic (from Key Risk Mechanics list), and Source Trace.
3. Identify intercreditor limitations affecting junior claims.
4. Flag priming capacity, collateral release provisions, guarantor release provisions, and amendment thresholds.
5. Flag instruments where structural positioning is ambiguous or dependent on legal interpretation.

## Output
T3B.4: `Instrument`|`Structural Rank`|`Contractual Seniority`|`Lien Priority`|`Guarantee Coverage`|`Collateral Coverage`|`Structural Subordination`|`Priming Capacity`|`Key Risk Mechanic`|`Source Trace`
</step_reference>
## REF_CP-3A_05_LegalCovenantLMEOverlay.md
<!-- REF_CP-3A_05 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="05" name="Legal / Covenant and LME Overlay">
<input>T3B.4; CP-4/CP-4A outputs (priming, leakage, weak collateral, covenant weakness); CP-3C outputs (refinancing/LME vulnerability).</input>
<gate>Step 4 complete. Skip with [Insufficient Information] if no legal/covenant or CP-4/CP-4A/CP-3C data available.</gate>

## Instructions
1. Overlay legal, covenant, and LME findings onto the structural positioning.
2. If CP-4/CP-4A identify priming, leakage, weak collateral, or covenant weakness: carry into structural and recovery assessment per instrument.
3. If CP-3C identifies refinancing or LME vulnerability: identify the exposed creditor class.
4. For each instrument: record Legal/Structural Finding, Priming Risk, Leakage Risk, Weak Collateral flag, Covenant Weakness flag, LME Vulnerability, Exposed Creditor Class, Source (CP-4/CP-4A/CP-3C reference), and Source Trace.
5. Flag instruments where legal review is unavailable — note impact on confidence.

## Output
T3B.5: `Instrument`|`Legal / Structural Finding`|`Priming Risk`|`Leakage Risk`|`Weak Collateral`|`Covenant Weakness`|`LME Vulnerability`|`Exposed Creditor Class`|`Source (CP-4 / CP-4A / CP-3C)`|`Source Trace`
</step_reference>
## REF_CP-3A_06_RecoverySensitivity.md
<!-- REF_CP-3A_06 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="06" name="Recovery Sensitivity by Instrument">
<input>T3B.2–T3B.5; CP-4/CP-4A recovery evidence where available.</input>
<gate>Steps 4–5 complete.</gate>

## Instructions
1. Assign a Recovery Sensitivity Label to each instrument:
   - **Low:** Strong priority, collateral/guarantor support, limited senior dilution risk.
   - **Moderate:** Meaningful protection but recovery can move with EV, collateral value, incremental debt, or guarantor changes.
   - **High:** Materially exposed to EV, structural subordination, priming, weak guarantors, or collateral leakage.
   - **Binary / highly uncertain:** Depends on litigation, LME participation, asset transfer, non-pro-rata exchange, or uncertain collateral/guarantor perimeter.
   - **Insufficient Information:** Missing ranking, collateral, guarantor, intercreditor, or recovery data.
2. For each: provide Evidence, Risk Mechanic, Credit Implication, Confidence (using Evidence Confidence Labels), and Source Trace.
3. Use Evidence → Risk Mechanic → Credit Implication chain.
4. Do not infer recovery values unless supported by provided evidence.

## Output
T3B.6: `Instrument`|`Recovery Sensitivity`|`Evidence`|`Risk Mechanic`|`Credit Implication`|`Confidence`|`Source Trace`
</step_reference>
## REF_CP-3A_07_CompensationCrossCheck.md
<!-- REF_CP-3A_07 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="07" name="Relative Value and Compensation Cross-Check">
<input>T3B.3 (market data), T3B.4 (structural positioning), T3B.6 (recovery sensitivity); CP-3 RV table.</input>
<gate>Step 6 complete.</gate>

## Instructions
1. Cross-check market compensation against structural rank, recovery sensitivity, maturity risk, liquidity, and LME exposure for each instrument.
2. Assign Compensation Adequacy Label: Attractive / Adequate / Inadequate / Unclear / Insufficient Information.
3. Do not allow yield alone to override weak recovery, legal position, maturity concentration, liquidity, or LME exposure.
4. If market data is absent, Compensation Adequacy = Unclear or Insufficient Information.
5. For each: record Market Level, Market Date, Structural Rank, Recovery Sensitivity, Compensation Adequacy, Compensation vs. Risk assessment narrative, and Source Trace.

## Output
T3B.7: `Instrument`|`Market Level`|`Market Date`|`Structural Rank`|`Recovery Sensitivity`|`Compensation Adequacy`|`Compensation vs. Risk`|`Source Trace`
</step_reference>
## REF_CP-3A_08_PreferenceDecisionTable.md
<!-- REF_CP-3A_08 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="08" name="Preference Decision Table">
<input>T3B.2–T3B.7; all structural, recovery, legal, and compensation evidence.</input>
<gate>Step 7 complete.</gate>

## Instructions
1. Apply Preference Decision Rules to each instrument:
   - **Preferred:** Supported structural position + adequate/attractive compensation + manageable maturity/liquidity + no overriding legal/recovery weakness.
   - **Secondary:** Acceptable but inferior to Preferred on one or more dimensions.
   - **Avoid:** Risk not adequately compensated OR structural/legal/recovery/LME exposure is adverse.
   - **Requires More Work:** Missing evidence prevents decision-useful recommendation.
2. For each: record Preference Label, Structural Position summary, Recovery Sensitivity, Compensation Adequacy, Confidence (Evidence Confidence Label), Key Reason, Monitoring Trigger, and Source Trace.
3. Do not force a preference where data is insufficient.

## Output
T3B.8: `Instrument`|`Preference`|`Structural Position`|`Recovery Sensitivity`|`Compensation Adequacy`|`Confidence`|`Key Reason`|`Monitoring Trigger`|`Source Trace`
</step_reference>
## REF_CP-3A_09_RankingTradeOffSummary.md
<!-- REF_CP-3A_09 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="09" name="Instrument Ranking and Trade-Off Summary">
<input>T3B.8 Preference Decision Table; all prior evidence.</input>
<gate>Step 8 complete.</gate>

## Instructions
1. Rank instruments by preference (Preferred first, then Secondary, then Avoid, then Requires More Work).
2. Within each preference tier, order by structural priority.
3. Provide a narrative trade-off summary explaining:
   - Why Preferred instruments are preferred (structural, recovery, compensation justification).
   - Key trade-offs between Preferred and Secondary instruments.
   - Why Avoid instruments are avoided (specific risk mechanics).
   - What would change Requires More Work to a decision-useful conclusion.
4. Use Evidence → Risk Mechanic → Credit Implication chains.
5. Do not force ranking where evidence is insufficient.

## Output
Narrative: instrument ranking and trade-off analysis. Reference T3B.8 for tabular detail.
</step_reference>
## REF_CP-3A_10_MonitoringTriggers.md
<!-- REF_CP-3A_10 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="10" name="Monitoring Triggers">
<input>T3B.2–T3B.9; all structural, recovery, legal, compensation, and preference evidence.</input>
<gate>Step 9 complete.</gate>

## Instructions
1. Generate specific, observable monitoring triggers per instrument.
2. For each trigger: record Instrument affected, Threshold/Signal, Why It Matters (structural/recovery/compensation impact), Credit/Recovery Impact, and Evidence ID.
3. Focus on: maturity events, covenant test dates, collateral revaluation, guarantor changes, priming events, LME actions, spread/price movements, rating actions, liquidity changes.
4. If hard thresholds are unsupported, state: "Quantitative threshold not available in provided materials."
5. Triggers should be actionable: tied to observable data points that would change preference.

## Output
T3B.10: `Trigger`|`Instrument`|`Threshold / Signal`|`Why It Matters`|`Credit / Recovery Impact`|`Evidence ID`
</step_reference>
## REF_CP-3A_11_GapsLedger.md
<!-- REF_CP-3A_11 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="11" name="Gaps Ledger">
<input>All prior step outputs (T3B.1–T3B.10); cumulative gaps identified throughout workflow.</input>
<gate>Always executes.</gate>

## Instructions
1. Compile all gaps identified across Steps 1–10 into a consolidated ledger.
2. For each gap: record Missing Data, Why It Matters, Impact on Output (which step/table/preference/recovery assessment is affected), and Required Follow-Up.
3. Cover gaps in: capital structure detail (seniority, collateral, guarantors), legal documentation (credit agreements, indentures, intercreditor), recovery evidence (CP-4/CP-4A), refinancing/LME data (CP-3C), market data (pricing, spreads, yields), instrument terms (call schedules, covenants), structural positioning (priming capacity, amendment thresholds).
4. Flag gaps that prevent preference assignment or recovery sensitivity classification.

## Output
T3B.11: `Gap`|`Missing Data`|`Why It Matters`|`Impact on Output`|`Required Follow-Up`
</step_reference>
## REF_CP-3A_12_OverallInstrumentPreferenceView.md
<!-- REF_CP-3A_12 (T2) | 2026-06-03 -->
<step_reference module="CP-3A" step="12" name="Overall Instrument Preference View">
<input>All prior step outputs (T3B.1–T3B.11); all preference, recovery, structural, and compensation evidence.</input>
<gate>Always executes. Synthesis only — no new data.</gate>

## Instructions
1. Write a committee-ready narrative synthesis covering:
   - Capital structure overview (number of instruments, total debt, structural layers).
   - Which instrument(s) are Preferred and why (structural position + recovery + compensation).
   - Which instrument(s) are Secondary and the key trade-offs vs. Preferred.
   - Which instrument(s) are Avoid and the specific risk mechanics.
   - Which instrument(s) Require More Work and what evidence is needed.
   - Top monitoring trigger across the capital structure.
   - Key structural/recovery/LME risk to the capital structure as a whole.
2. Do not introduce new data, new calculations, or new assessments — synthesize only from Steps 1–11.
3. End with one of:
   - "CP-3A Completed. Preferred: [Instrument(s)]. Secondary: [Instrument(s)]. Avoid: [Instrument(s)]."
   - "CP-3A Completed with Limitations. Preferred: [Instrument(s)]. Key Gaps: [List]."
   - "CP-3A Blocked. Missing Required Inputs: [List]."

## Output
Narrative synthesis (no table). Module completion statement with preference assignments.
</step_reference>
## REF_CP-3A_TaxonomyAndLabels.md
<!-- REF_CP-3A TaxonomyAndLabels (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-3A" name="Instrument Taxonomy, Structural Concepts & Decision Labels">

Authoritative for CP-3A instrument mapping (Steps 3–4), recovery sensitivity (Step 6), and preference decisions (Step 8). Load alongside the CP-3A workflow.

## Instrument Type Taxonomy
| Instrument Type | Typical Position | Key Risks |
|----------------|-----------------|-----------|
| Revolving credit facility | Super-senior or 1L senior secured | Draw risk, priming complexity, ABL priority |
| First-lien term loan | Senior secured 1L claim | Collateral, guarantors, incremental pari capacity, maturity, LME |
| First-lien secured notes | Senior secured bond claim | Call schedule, consent thresholds, covenant package, liquidity, pari status |
| Second-lien loan / notes | Junior lien secured claim | Intercreditor limits, 1L cushion, priming exposure, downside convexity |
| Senior unsecured notes | Unsecured issuer/guarantor claim | Structural subordination to secured debt, spread compensation |
| Subordinated notes | Contractually subordinated | Usually Avoid unless source-supported compensation and recovery |
| HoldCo debt | Structurally subordinated to OpCo | High recovery sensitivity |
| Non-guarantor / local debt | May be structurally senior to group debt for local assets | Local asset priority |
| Leasing / factoring / ABL | Asset-specific senior claims | May reduce collateral value or prime term lenders |

## Structural Concepts
Contractual seniority | Lien priority | Guarantee coverage | Collateral coverage | Structural subordination | Non-guarantor debt | Restricted-group perimeter | Unrestricted-subsidiary exposure | Intercreditor limitations | Priming capacity | Collateral release | Guarantor release | Class voting | Amendment thresholds

## Key Risk Mechanics
Maturity concentration | Weak collateral | Guarantor leakage | Priming debt | Drop-down risk | Uptier risk | Unsecured subordination | Illiquidity | Rich pricing | Low price / wide spread not supported by recovery

## Recovery Sensitivity Labels
**Low sensitivity:** Strong priority, collateral/guarantor support, limited senior dilution risk.
**Moderate sensitivity:** Meaningful protection but recovery can move with EV, collateral value, incremental debt, or guarantor changes.
**High sensitivity:** Materially exposed to enterprise value, structural subordination, priming, weak guarantors, or collateral leakage.
**Binary / highly uncertain:** Depends on litigation, LME participation, asset transfer, non-pro-rata exchange, or uncertain collateral/guarantor perimeter.
**Insufficient Information:** Missing ranking, collateral, guarantor, intercreditor, or recovery data.

## Preference Decision Rules
**Preferred:** Supported structural position, adequate/attractive compensation, manageable maturity/liquidity, no overriding legal/recovery weakness.
**Secondary:** Acceptable but inferior to Preferred on one or more dimensions.
**Avoid:** Risk not adequately compensated or structural/legal/recovery/LME exposure is adverse.
**Requires More Work:** Missing evidence prevents decision-useful recommendation.

## Evidence Confidence Labels
**High:** Current pricing, capital structure, legal ranking, collateral/guarantor support, and recovery or CP-4/CP-4A support.
**Medium:** Core evidence available but one important area incomplete.
**Low:** Market data, legal data, or structural data materially incomplete.
**Structural Only:** Legal/structural evidence without market data.
**Market Only:** Market data without legal/structural support.
**Insufficient Information:** Cannot form decision-useful view.

## Compensation Adequacy Labels
**Attractive:** Compensation exceeds what structural rank, recovery sensitivity, maturity, liquidity, and LME exposure require.
**Adequate:** Compensation broadly aligned with risk profile.
**Inadequate:** Compensation insufficient for structural, recovery, maturity, liquidity, or LME risk.
**Unclear:** Market data or structural data insufficient to assess.
**Insufficient Information:** Cannot assess compensation adequacy.

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Institutional-grade, creditor-first, evidence-led, instrument-specific, committee-ready, transparent about gaps. Prefer tables for capital-structure dashboard, instrument matrix, structural positioning, legal/LME overlay, recovery sensitivity, compensation cross-check, preference decision, monitoring triggers, and gaps ledger. Use concise but explicit Evidence → Risk Mechanic → Credit Implication chains. Separate source fact from analyst judgment. Target 1–5 pages per issuer, scaled to capital-structure complexity.

</reference>
