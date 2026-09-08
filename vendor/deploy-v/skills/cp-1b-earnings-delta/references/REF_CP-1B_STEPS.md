Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-1B_CalculationDiscipline.md.

Original files, in this bundle: REF_CP-1B_01_FileGateSourceValidation.md, REF_CP-1B_02-03_ScopeAndDefinitionLock.md, REF_CP-1B_02_IssuerPeriodScope.md, REF_CP-1B_03_DefinitionInheritance.md, REF_CP-1B_04_SummaryTopSheet.md, REF_CP-1B_05_FinancialPerformanceTable.md, REF_CP-1B_06_KPIDashboard.md, REF_CP-1B_07_VarianceAnalysis.md, REF_CP-1B_08_CorporateActions.md, REF_CP-1B_09_ComparativeEvaluation.md, REF_CP-1B_10_ConflictLog.md, REF_CP-1B_11_MonitoringAssessment.md, REF_CP-1B_12_GapsLimitations.md, REF_CP-1B_13_OverallEarningsView.md, REF_CP-1B_14_ModelWorkbookValidation.md, REF_CP-1B_CalculationDiscipline.md

## REF_CP-1B_01_FileGateSourceValidation.md
<!-- REF_CP-1B_01 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="01" name="File Gate & Source Validation">
<input>CP-1 data + sources</input>
<gate>CP-1 available</gate>

## Instructions
Validate CP-1 + source availability. Identify all sources by name/type/period/evidence tier.

## Output
T4.1: `Source File Name`|`Document Type`|`Period Coverage`|`Evidence Quality Tier`|`Analytical Use`|`Limitations`
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-1B_02-03_ScopeAndDefinitionLock.md
# Consolidated companion — REF_CP-1B_02-03_ScopeAndDefinitionLock.md

<!-- MERGED_FROM:REF_CP-1B_02_IssuerPeriodScope.md sha256=2a51dd475cb9e6609d7a68d45b0d1e74d758926e62389ab99b0800fcaed3e804 -->
## Source: REF_CP-1B_02_IssuerPeriodScope.md

<!-- REF_CP-1B_02 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="02" name="Issuer & Period Scope">
<input>T4.1 + CP-1 scope</input>
<gate>Source-supported</gate>
## Instructions
Confirm entity/period scope from CP-1. Record FY end, currency, unit, accounting basis. Establish comparison pairs.
## Output
Entity/period scope confirmation narrative.
</step_reference>

<!-- MERGED_FROM:REF_CP-1B_03_DefinitionInheritance.md sha256=aaeae4b05137f6a53679bf7d81a857df730e9d9d351c0d3ed69fb502d97e7192 -->
## Source: REF_CP-1B_03_DefinitionInheritance.md

<!-- REF_CP-1B_03 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="03" name="CP-1 Definition Inheritance">
<input>CP-1 Definition + Calculation Registers</input>
<gate>CP-1 defs loaded</gate>
## Instructions
Load all CP-1 metric definitions. Confirm EBITDA/leverage/FCF inherited. Apply EBITDA priority. Flag conflicts BEFORE proceeding.
## Output
T4.2: `Metric Name`|`CP-1 Definition`|`CP-1 Formula`|`EBITDA Def in Use`|`Inheritance Status`|`Conflict Note`
</step_reference>
## REF_CP-1B_02_IssuerPeriodScope.md
<!-- REF_CP-1B_02 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="02" name="Issuer & Period Scope">
<input>T4.1 + CP-1 scope</input>
<gate>Source-supported</gate>
## Instructions
Confirm entity/period scope from CP-1. Record FY end, currency, unit, accounting basis. Establish comparison pairs.
## Output
Entity/period scope confirmation narrative.
</step_reference>
## REF_CP-1B_03_DefinitionInheritance.md
<!-- REF_CP-1B_03 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="03" name="CP-1 Definition Inheritance">
<input>CP-1 Definition + Calculation Registers</input>
<gate>CP-1 defs loaded</gate>
## Instructions
Load all CP-1 metric definitions. Confirm EBITDA/leverage/FCF inherited. Apply EBITDA priority. Flag conflicts BEFORE proceeding.
## Output
T4.2: `Metric Name`|`CP-1 Definition`|`CP-1 Formula`|`EBITDA Def in Use`|`Inheritance Status`|`Conflict Note`
</step_reference>
## REF_CP-1B_04_SummaryTopSheet.md
<!-- REF_CP-1B_04 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="04" name="Summary / Top-Sheet">
<input>Steps 1-3</input>
<gate>Steps 1-3 complete</gate>

## Instructions
Executive summary. Required rows: Issuer, Period(s), EBITDA Def, Revenue, EBITDA, EBITDA Margin, FCF, Total/Net Leverage, Cash Interest Coverage, Liquidity, Key YoY Variance, Key Credit Observation.

## Output
T4.3: `Row Label`|`Value / Observation`
</step_reference>
## REF_CP-1B_05_FinancialPerformanceTable.md
<!-- REF_CP-1B_05 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="05" name="Financial Performance Table">
<input>CP-1 normalized financials</input>
<gate>Normalized data available</gate>

## Instructions
Multi-period table. 19 lines: Revenue, COGS, Gross Profit, Gross Margin, SG&A, EBITDA, EBITDA Margin, D&A, EBIT, Cash Interest Paid, Cash Taxes Paid, Total/Maint/Growth Capex, WC Change, OCF, FCF, DCF, Net Income.

Apply REF_CP-1B_CalculationDiscipline.md (calculation engine, prohibited calculations, period construction, cash-flow rules) to every calculated cell and variance.

## Output
T4.4: `Line Item`|`Period 1`…`N`|`YoY Change (Abs)`|`YoY Change (%)`|`Analyst Note`
</step_reference>
## REF_CP-1B_06_KPIDashboard.md
<!-- REF_CP-1B_06 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="06" name="KPI Dashboard">
<input>T4.4 + CP-1 KPIs</input>
<gate>Step 5 complete</gate>

## Instructions
Required KPIs: Total Debt/EBITDA, Net Debt/EBITDA, Sr Sec Leverage, EBITDA/Cash Interest, (EBITDA-Capex)/Cash Interest, FFO/Debt, FCF/Debt, FCF Conversion, Gross Margin, EBITDA Margin, Revenue Growth, Liquidity.

## Output
T4.5: `KPI Category`|`Metric Name`|`Period 1`…`N`|`YoY Change`|`Trend Direction`|`Calculation Status`|`Analyst Note`
</step_reference>
## REF_CP-1B_07_VarianceAnalysis.md
<!-- REF_CP-1B_07 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="07" name="Variance Analysis">
<input>T4.4 + T4.5</input>
<gate>≥1 period pair</gate>

## Instructions
Detailed variance for all material metrics. Bases: YoY, sequential, LTM, actual vs base case/guidance/rating-agency. Apply REF_CP-1B_CalculationDiscipline.md period-construction rules (same-period YoY, consecutive sequential, null-propagating LTM/YTD; no mixed annual/quarterly bases without annualization flag).

## Output
T4.6: `Metric`|`Comparison Basis`|`Prior Value`|`Current Value`|`Abs Change`|`% Change`|`Mgmt Driver`|`Analyst Driver`|`Credit Implication`
</step_reference>
## REF_CP-1B_08_CorporateActions.md
<!-- REF_CP-1B_08 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="08" name="Corporate Actions & Comparability">
<input>Sources + T4.4</input>
<gate>Always</gate>
## Instructions
Identify ALL corporate actions: acquisitions, disposals, restructurings, refinancings, one-offs, accounting/perimeter changes, restatements.
## Output
T4.7: `Event`|`Date`|`Description`|`Quantified Impact`|`Comparability Effect`|`Credit Implication`|`Source`
</step_reference>
## REF_CP-1B_09_ComparativeEvaluation.md
<!-- REF_CP-1B_09 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="09" name="Comparative Evaluation">
<input>Prior notes/base case/guidance</input>
<gate>Benchmarks available</gate>

## Instructions
Compare actual vs benchmarks. Label basis explicitly. Skip with statement if none.

## Output
T4.8: `Metric`|`Benchmark Source`|`Benchmark Type`|`Expected Value`|`Actual Value`|`Variance`|`Credit Implication`
</step_reference>
## REF_CP-1B_10_ConflictLog.md
<!-- REF_CP-1B_10 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="10" name="Conflict Log">
<input>Steps 1-9</input>
<gate>Always</gate>

## Instructions
Log ALL conflicts. No conflicts → explicit confirmation.

## Output
T4.9: `Conflict Description`|`Source(s)`|`Metric(s)`|`Period(s)`|`Materiality`|`Resolution Status`|`Downstream Impact`
</step_reference>
## REF_CP-1B_11_MonitoringAssessment.md
<!-- REF_CP-1B_11 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="11" name="Monitoring Assessment">
<input>T4.4-T4.9</input>
<gate>Steps 5-7 complete</gate>

## Instructions
Monitoring: deterioration, improvement, trajectory, covenant proximity, refi triggers, rating thresholds. Each signal evidence-linked.

## Output
T4.10: `Signal Type`|`Metric/Indicator`|`Evidence`|`Severity`|`Credit Implication`|`Recommended Action`
</step_reference>
## REF_CP-1B_12_GapsLimitations.md
<!-- REF_CP-1B_12 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="12" name="Gaps & Limitations Ledger">
<input>Steps 1-11</input>
<gate>Always</gate>
## Instructions
Comprehensive cumulative ledger of ALL gaps from all prior steps.
## Output
T4.11: `Gap Description`|`Affected Metric/Section`|`Affected Period(s)`|`Downstream Impact`|`Severity`|`Recommended Action`
</step_reference>
## REF_CP-1B_13_OverallEarningsView.md
<!-- REF_CP-1B_13 (T2) | 2026-06-02 -->
<step_reference module="CP-1B" step="13" name="Overall Earnings View">
<input>Steps 1-12</input>
<gate>Always</gate>

## Instructions
Module summary: (a) period scope, (b) key findings, (c) material trends, (d) monitoring signals, (e) gaps, (f) downstream readiness.

## Output
Analytical narrative — the module summary closing the canonical `.md` `## Analysis`; the concise completion response carries status, limitations, recommended next command, and the Markdown link only, per CP_AB_EXPORT_SPEC.md.
</step_reference>
## REF_CP-1B_14_ModelWorkbookValidation.md
# REF CP-1B 14 — Model Workbook Validation

Load after the Overall Earnings View on every run. Use CP-1's
stable `metric_id` and `period_id`; do not create synonyms or replacement
canonical values.

## Stable table IDs

- `<!-- table-id: cp1b.model_comparator_register -->`
- `<!-- table-id: cp1b.model_validation_register -->`
- `<!-- table-id: cp1b.addback_validation_register -->`
- `<!-- table-id: cp1b.model_readiness -->`
- `<!-- table-id: cp1b.cp_model_snapshot_fields -->`

## Snapshot field

Columns:
`field_id | value | status | source_id | source_locator | as_of`

Emit exactly one `READY` row with `field_id` =
`historical_performance`. Summarise the source-grounded historical trend,
inflection and key credit-relevant variance in concise workbook-ready prose.
Every value requires a source ID, precise locator and ISO as-of date. It
validates/interprets CP-1 history and does not create replacement numbers.

## Comparator register

Columns:
`metric_id | current_period_id | reference_period_id | comparison_basis | current_value | reference_value | absolute_change | percentage_change | calculation_status | restatement_flag | basis_change_flag | perimeter_change_flag | definition_change_flag`

`comparison_basis` is one of `YOY_SAME_QUARTER`, `SEQUENTIAL`, `YTD_PRIOR`,
`LTM_PRIOR`. A percentage comparison with a null or zero denominator is null
and `Not Calculable`.

## Validation register

Columns:
`metric_id | period_id | cp1_value | cp1b_comparison_value | difference | tolerance | status | explanation | source_or_conflict_ref`

- CP-1 value is authoritative.
- CP-1B comparison value is used only to detect transcription, period,
  restatement, basis, perimeter or definition issues.
- `status` is `PASS`, `WARN` or `BLOCK`.
- Validate reported revenue, EBITDA, adjusted EBITDA, CFO/NCFO, FCF, debt and
  cash.
- A mismatch never silently changes the CP-1 value.

## Add-back validation register

Columns:
`addback_id | period_id | cp1_value | cp1b_comparison_value | difference | tolerance | status | label_match | definition_change_flag | explanation | source_or_conflict_ref`

- Validate every CP-1 issuer-specific `(addback_id, period_id)` exactly once.
- `label_match` confirms the CP-1 issuer label matches the compared disclosure.
- Never replace an issuer label with a generic category, merge two add-backs,
  or substitute a CP-1B comparison value.
- `status` is `PASS`, `WARN` or `BLOCK`; any unresolved missing ID, label
  mismatch, definition change or value mismatch blocks CP-MODEL readiness.
- An explicitly empty CP-1 bridge requires an empty add-back validation
  register and is valid only when EBITDA equals adjusted EBITDA.

## Readiness

Columns:
`downstream_module | status | blocking_metric_ids | blocking_period_ids | conflict_refs | explanation`

Emit one CP-MODEL row. `ready` requires:

- all comparator period IDs exist in CP-1;
- validation has no unresolved `BLOCK`;
- basis, perimeter, restatement and definition changes are either false or
  explicitly reconciled;
- issuer-specific adjusted-EBITDA ID, label and definition differences are
  explained;
- no alternative canonical value was emitted.
## REF_CP-1B_CalculationDiscipline.md
<!-- REF_CP-1B_CalculationDiscipline (T2 Library) | 2026-06-10 | Restored from CP-1B__SUPPORT__Calculation_Period_and_Monitoring_Rules §2.5 -->
<library_reference module="CP-1B" name="Calculation Discipline">
<consumers>REF_CP-1B_05 (Financial Performance); REF_CP-1B_06 (KPI Dashboard); REF_CP-1B_07 (Variance Analysis)</consumers>

# CP-1B Calculation Discipline

## Calculation Engine Rule
All calculations use normalized figures inherited from CP-1. CP-1B does not transform, re-normalize, or re-base CP-1 data. If a calculation requires a figure CP-1 stores as null, the result is null and the limitation is logged.

## Calculation Discipline
- Every calculated value must be reproducible from its stated inputs and formula.
- Formulas must match the CP-1 canonical definitions exactly.
- If any input is null, the result is null — not zero, not estimated, not interpolated.
- Rounding must match the precision established by CP-1 for each metric.
- Period alignment must be exact: do not mix figures from different periods, stubs, or fiscal-year conventions in a single calculation.

## Prohibited Calculations
- Do not estimate missing inputs by interpolation, extrapolation, or averaging.
- Do not apply growth rates from one metric to impute another.
- Do not create new metrics not defined in the CP-1 definition register.
- Do not adjust CP-1 figures for items the analyst considers non-recurring unless CP-1 has already made that adjustment.
- Do not reverse CP-1 normalization adjustments.

## Period Construction Rules
- Year-over-year variance: compare same-period figures (Q3 FY2024 vs Q3 FY2023, or FY2024 vs FY2023).
- Sequential variance: compare consecutive periods (Q3 FY2024 vs Q2 FY2024).
- LTM: most recent full year + current stub − prior-year comparable stub. If any component is null, LTM is null.
- YTD: sum of sub-periods within the current fiscal year. If any sub-period component is null, YTD is null.
- Do not mix annual and quarterly figures in the same variance unless the comparison basis is explicitly annualized and flagged.

## Cash Flow Calculation Rules
- Use cash interest paid and cash taxes paid for cash-flow metrics (not accrued interest expense or total tax expense) unless CP-1 has flagged that cash figures are unavailable.
- Capex uses the CP-1 canonical classification (maintenance vs growth) where available. If disaggregated capex is unavailable, use total capex and flag the limitation.
- Working capital changes follow the CP-1 sign convention.
</library_reference>
