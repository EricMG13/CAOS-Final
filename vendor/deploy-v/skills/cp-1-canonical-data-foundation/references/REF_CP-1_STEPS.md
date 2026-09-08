Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-1_AntiPatterns.md, REF_CP-1_Discipline.md, REF_CP-1_Workflow.md.

Original files, in this bundle: REF_CP-1_01_FileGateSourceValidation.md, REF_CP-1_02_EntityPeriodScope.md, REF_CP-1_03_Normalization.md, REF_CP-1_04_IncomeStatementCoverage.md, REF_CP-1_05_CashFlowStatementCoverage.md, REF_CP-1_06_BalanceSheetCoverage.md, REF_CP-1_07_NormalizedFinancialsTable.md, REF_CP-1_08_DerivedPeriodConstruction.md, REF_CP-1_09_CalculationRegisterKPIBuild.md, REF_CP-1_10_DefinitionConflictRegister.md, REF_CP-1_11_EvidenceRiskCreditAnalysis.md, REF_CP-1_12_CoverageGateDownstreamReadiness.md, REF_CP-1_13_ModelWorkbookInterface.md, REF_CP-1_AntiPatterns.md, REF_CP-1_Discipline.md, REF_CP-1_Workflow.md

## REF_CP-1_01_FileGateSourceValidation.md
<!-- REF_CP-1_01_FileGateSourceValidation (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1" step="1" name="File Gate & Source Validation">
<input>User-provided source files + CP-0 registry (if available).</input>
<gate priority="critical">No financial sources → **BLOCKED.** Do not proceed.</gate>

## Detailed Instructions
1. Inventory all source files: name, type, period coverage, currency, unit, perimeter, accounting basis, evidence quality tier.
2. Evidence hierarchy: Tier 1 (Audited FS) > 2a (Unaudited w/ auditor) > 2b (w/o) > 2c (Lender/sponsor) > 2d (Rating) > 3a (Internal) > 3b (External).
3. Assess material sufficiency for IS + CFS + BS + KPIs. Flag downstream impact if insufficient.
4. Record analytical use and limitations per source.
5. Source-first discipline: complete before any extraction.

## Output — T4.1 Source Register
`Source File Name` | `Document Type` | `Period Coverage` | `Currency` | `Unit` | `Perimeter` | `Accounting Basis` | `Evidence Quality Tier` | `Analytical Use` | `Limitations`

## Warnings
- Do NOT classify from filenames alone — inspect content.
- Do NOT proceed if no financial sources available.
</step_reference>
## REF_CP-1_02_EntityPeriodScope.md
<!-- REF_CP-1_02_EntityPeriodScope (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1" step="2" name="Entity/Period Scope Register">
<input>T4.1 Source Register + source document content.</input>
<gate>Source-supported only. No entity inference from filenames.</gate>

## Detailed Instructions
1. Establish issuer entity scope: issuer name (legal entity), borrower, guarantor group, restricted group. Note ambiguity.
2. Establish all reporting periods: annual, interim, quarterly. Record FY end, stub/short periods.
3. Record reporting basis: currency, unit, consolidation perimeter, accounting basis.
4. Cross-reference against Source Register — ensure all sources mapped to entities and periods.

## Output — T4.2 Entity Period Key Register
`Entity Name` | `Entity Role` | `Fiscal Year End` | `Reporting Currency` | `Reporting Unit` | `Consolidation Perimeter` | `Accounting Basis` | `Available Periods`

## Warnings
- Entity names from content, not filenames. Flag ambiguity.
- If consolidation perimeter differs across sources, flag — affects Step 3.

**Subsequent events:** the reporting period ends at the balance-sheet date. Scan every source for events after that date (subsequent-events note, dividends declared, refinancings, buybacks, disposals) → flagged Subsequent Events entry with the event date in T4.2 warnings; never blended into period figures (Canon Core item 7).
</step_reference>
## REF_CP-1_03_Normalization.md
<!-- REF_CP-1_03_Normalization (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1" step="3" name="Normalization">
<input>T4.1 + T4.2 + raw financial data from sources.</input>
<gate>Source data available for at least one period.</gate>

## Detailed Instructions
1. Establish canonical basis: single currency (with FX rates + source), single unit, single perimeter, single accounting basis.
2. Record every adjustment: what, source file, type, before/after, rationale, affected periods.
3. Flag incomplete normalization — carry figure with limitation marker.
4. Once established, basis applies to ALL subsequent steps. Currency/unit switching = **prohibited**.

## Output — T4.3 Normalization Register
`Adjustment Description` | `Source File` | `Adjustment Type` | `Before Value` | `After Value` | `Rationale` | `Affected Periods`

## Warnings
- Currency/unit switching after normalization is **PROHIBITED**.
- Unresolvable accounting basis differences must be flagged, not silently chosen.
</step_reference>
## REF_CP-1_04_IncomeStatementCoverage.md
<!-- REF_CP-1_04_IncomeStatementCoverage (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1" step="4" name="Income Statement Coverage">
<input>Normalized source data (Step 3 basis).</input>
<gate>Always executes. If IS data unavailable, produce empty table + log all gaps.</gate>

## Detailed Instructions
1. Extract + normalize full IS for every available period on Step 3 basis.
2. Required line items (null + gap where unavailable):
   Revenue | COGS | Gross Profit | SGA | Other Operating | EBITDA (Reported) | EBITDA (Adjusted) | D&A | EBIT | Interest Expense (Total/Cash) | Interest Income | Other Non-Operating | PBT | Tax (Total/Cash) | Net Income | Exceptionals | SBC
3. Each item: source file, period, currency, unit, value, evidence tier.
4. EBITDA not stated → derive from components `[Calculated]`. Insufficient → null.
5. Populate Financial Statement Coverage entries for IS.

## Output — T4.4 Income Statement
`Line Item` | `Period 1` … `Period N`

## Warnings
- Do NOT fabricate missing items. Non-derivable = null + gap.
- EBITDA definition conflicts → log BOTH reported and adjusted for Step 10.
</step_reference>
## REF_CP-1_05_CashFlowStatementCoverage.md
<!-- REF_CP-1_05_CashFlowStatementCoverage (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1" step="5" name="Cash Flow Statement Coverage">
<input>Normalized source data (Step 3 basis).</input>
<gate>Always executes. If CFS unavailable, produce empty table + log gaps.</gate>

## Detailed Instructions
1. Extract + normalize full CFS for every available period.
2. Required line items:
   OCF (before/after WC) | WC Change | Capex (Maint/Growth/Total) | FCF (Levered/Unlevered) | Dividends | Acquisitions | Disposals | Debt Issuance/Repayment | Equity Issuance/Buyback | Net Cash Change | Cash Taxes Paid | Cash Interest Paid
3. Same source-tracing and null-storage rules as Step 4.

## Output — T4.5 Cash Flow Statement
`Line Item` | `Period 1` … `Period N`

## Warnings
- Capex split rarely disclosed. Null for sub-categories; carry Total Capex. Flag CP-2 impact.
- Cash Interest Paid (CFS) may differ from Interest Expense Cash (IS). Distinguish carefully.
</step_reference>
## REF_CP-1_06_BalanceSheetCoverage.md
<!-- REF_CP-1_06_BalanceSheetCoverage (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1" step="6" name="Balance Sheet Coverage">
<input>Normalized source data (Step 3 basis).</input>
<gate>Always executes. If BS unavailable, produce empty table + log gaps.</gate>

## Detailed Instructions
1. Extract + normalize full BS at each reporting date.
2. Required line items:
   Cash & Equivalents | Restricted Cash | ST Investments | Trade Receivables | Inventories | Other CA | Total CA | PP&E (Net) | Goodwill | Other Intangibles | Other NCA | Total Assets | ST Debt | Current Portion LTD | Trade Payables | Other CL | Total CL | Senior Secured Debt | Senior Unsecured Debt | Subordinated Debt | Total Debt | Pension/Lease Obligations | Other NCL | Total Liabilities | Shareholders' Equity | Minority Interests | Total Equity
3. Same source-tracing and null-storage rules.

## Output — T4.6 Balance Sheet
`Line Item` | `Period 1` … `Period N`

## Warnings
- Debt classification by seniority **critical for CP-3**. Not disclosed → null. Do NOT estimate.
- Pension/lease obligations separated from financial debt where possible.

**Non-debt funding liabilities:** a material non-debt, non-interest-bearing liability funding operations (customer deposits / deferred revenue / supplier finance) is credit-relevant working-capital float — flag in T4.6 warnings (size, trend, refund/performance obligation), carry to Step 11 as a named story; never ordinary payables (Canon Core item 8). Also scan the filing's subsequent-events note here.
</step_reference>
## REF_CP-1_07_NormalizedFinancialsTable.md
<!-- REF_CP-1_07_NormalizedFinancialsTable (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1" step="7" name="Normalized Financials Table">
<input>T4.4 IS + T4.5 CFS + T4.6 BS.</input>
<gate>At least one of Steps 4–6 produced data.</gate>

## Detailed Instructions
1. Produce consolidated cross-statement table — IS, CFS, BS across all periods.
2. All figures on Step 3 normalization basis. No re-extraction from sources.
3. Consolidation only — no new data, no modifications.
4. Cross-check internal consistency:
   - Net Income (IS) vs. equity movements (BS)
   - Operating + investing + financing → Net Change in Cash (CFS)
   - Opening vs. closing BS positions vs. period flows
   - Flag material reconciliation differences as gaps

## Output — T4.7 Normalized Financials
`Line Item` | `Statement Source` (IS/CFS/BS) | `Period 1` … `Period N`

## Warnings
- Figures must match Steps 4–6 exactly. Discrepancy = normalization error.
- Cross-statement reconciliation failures → log with materiality assessment.
</step_reference>
## REF_CP-1_08_DerivedPeriodConstruction.md
<!-- REF_CP-1_08_DerivedPeriodConstruction (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1" step="8" name="LTM/YTD/Derived Period Construction">
<input>T4.7 Normalized Financials.</input>
<gate priority="critical">Sub-period data must exist. Missing component → null. Do NOT estimate.</gate>

## Detailed Instructions
1. LTM = Most recent full-year + Current stub − Prior-year comparable stub.
2. YTD constructed where applicable.
3. **Derived Period Rule (CRITICAL):** ALL sub-period components must be available. Missing one = null for entire derived figure.
4. Record all constructions: component sources, formula, calculation status, limitations.
5. Ensure sub-period comparability. Mismatched stubs → Not Comparable.

## Output — T4.8 Constructed Period Register
`Metric Name` | `Derived Period Type` | `Full-Year Component` | `Current Stub` | `Prior-Year Stub` | `Derived Value` | `Calculation Status` | `Source Files` | `Limitations`

## Warnings
- Partial LTM/YTD = **PROHIBITED**. One missing component → entire figure = null.
- Mismatched stub periods → derivation invalid.
</step_reference>
## REF_CP-1_09_CalculationRegisterKPIBuild.md
<!-- REF_CP-1_09_CalculationRegisterKPIBuild (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1" step="9" name="Calculation Register & KPI Build">
<input>T4.7 Normalized Financials + T4.8 Constructed Period Register.</input>
<gate>Normalized data available for at least some periods.</gate>

## Detailed Instructions
1. Calculate all canonical KPIs where inputs available:
   - **Leverage:** Debt/EBITDA, Net Debt/EBITDA, Sr Sec/EBITDA
   - **Coverage:** EBITDA/Cash Int, (EBITDA−Capex)/Cash Int, FFO/Debt
   - **Cash Flow:** FCF, FCF Conversion (FCF/EBITDA), DCF
   - **Liquidity:** Cash+Undrawn Committed, Liquidity/Debt
   - **Margin:** Gross %, EBITDA %, EBIT %, Net Income %
   - **Growth:** Revenue %, EBITDA %
2. Full audit trail per KPI: name, formula, numerator (value+source), denominator (value+source), period, currency, unit, value, calc status, evidence tier, limitations.
3. Calculation status (8 values): `Verified` | `Calculated` | `Estimated` | `Proxy` | `Not Calculable` | `Partial` | `Conflicted` | `Not Available`
4. Populate KPI Dashboard with trend direction and analyst notes.

## Output — T4.9 Calculation Register
`Metric Name` | `Formula` | `Numerator Value` | `Numerator Source` | `Denominator Value` | `Denominator Source` | `Period` | `Currency` | `Unit` | `Calculated Value` | `Calculation Status` | `Evidence Quality Tier` | `Limitations`

## Output — T4.10 KPI Dashboard
`KPI Category` | `Metric Name` | `Period 1…N` | `Trend Direction` | `Analyst Note`

## Warnings
- Null input → KPI = Not Calculable. Do NOT estimate missing inputs.
- Use only canonical 8-value calculation status.
</step_reference>
## REF_CP-1_10_DefinitionConflictRegister.md
<!-- REF_CP-1_10_DefinitionConflictRegister (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1" step="10" name="Definition Conflict Register">
<input>All outputs from Steps 1–9.</input>
<gate>Always executes. No conflicts → explicit alignment confirmation.</gate>

## Detailed Instructions
1. Review all metrics: issuer def vs. canonical? Sources disagree? Definition changed across periods?
2. Log each conflict: metric, canonical def, issuer def, source, periods, materiality (quantify), downstream modules, resolution.
3. Common conflict areas:
   - **EBITDA** — add-backs, exclusions, management vs. audited
   - **Debt** — leases, pensions, drawn facilities
   - **FCF** — levered vs. unlevered, WC inclusion
   - **Capex** — capitalized items, maint vs. growth
   - **Net Debt** — restricted cash, ST investments
4. No conflicts → "No definition conflicts identified across [N] metrics and [M] sources."
5. Supports Definition Inheritance Model for downstream modules.

## Output — T4.11 Definition Conflict Register
`Metric Name` | `Canonical Definition` | `Issuer-Reported Definition` | `Source of Conflict` | `Periods Affected` | `Materiality` | `Downstream Modules Affected` | `Resolution / Recommendation`

## Warnings
- Silent definition acceptance is NOT valid. Log conflicts OR confirm alignment.
- EBITDA adjustments = most common conflict source in leveraged finance.

**Multi-figure events (binding):** one economic event with different figures across statements (e.g. debt extinguishment: P&L charge vs CF add-back vs CF cash paid) → extract ALL, label statement roles, ONE register row explaining the differences. Silent selection = fabrication-class violation (Canon Core item 6). **Debt basis:** carrying-value vs gross-principal divergence is always a register row (both figures + locators).
</step_reference>
## REF_CP-1_11_EvidenceRiskCreditAnalysis.md
<!-- REF_CP-1_11_EvidenceRiskCreditAnalysis (Tier 2) | 2026-06-02 | rev 2026-06-26: narrative = canonical Markdown `## Analysis` → projected Markdown handoff §3 -->
<step_reference module="CP-1" step="11" name="Evidence-to-Risk-to-Credit Analysis">
<input>All tables from Steps 1–10. T4.10 KPI Dashboard as primary reference.</input>
<gate>At least one KPI from Step 9. No KPIs → data-quality narrative only.</gate>

## Detailed Instructions
1. Apply the required analytical chain to every material finding:
   **Evidence** → **Risk Mechanic** → **Credit Implication**
2. Cover analytical dimensions:
   - Leverage trajectory — Debt/EBITDA, Net Debt/EBITDA trends, drivers
   - Coverage trends — Interest coverage evolution, FFO/Debt trajectory
   - Cash-flow quality — FCF conversion, WC dynamics, capex intensity
   - Liquidity adequacy — Cash + undrawn vs. near-term obligations
   - Data-quality risks — Source quality, coverage gaps, normalization limitations
   - Definition risks — Conflicts creating comparability uncertainty
   - Key gaps — Most material gaps and their credit implications
3. Synthesis only — no new data extraction. All evidence must trace to prior tables.
4. Every statement issuer-specific. No generic credit commentary.

## Output
Analytical narrative — part of the canonical `.md` `## Analysis`, structured by analytical dimension. Chat carries only concise completion status and the Markdown link.

## Warnings
- Do NOT introduce new financial figures. All numbers must trace to prior tables.
- Do NOT produce generic or boilerplate credit commentary.

**Required stories where present:** the Step-06 float (Evidence: size/trend → Risk Mechanic: funds ops ahead of delivery, demand shock converts to outflow → Credit Implication: liquidity/leverage quality); Step-02 Subsequent Events (date, effect, why excluded from period figures); Step-10 multi-figure events (which figure serves which purpose).
</step_reference>
## REF_CP-1_12_CoverageGateDownstreamReadiness.md
<!-- REF_CP-1_12_CoverageGateDownstreamReadiness (Tier 2) | 2026-06-02 | rev 2026-06-26: output assembly → Markdown handoff+canonical Markdown self-authored export -->
<step_reference module="CP-1" step="12" name="Coverage Gate & Downstream Readiness">
<input>All outputs from Steps 1–11. Complete gap inventory.</input>
<gate>Always executes. Final quality gate before output assembly.</gate>

## Detailed Instructions
1. Consolidate ALL gaps from ALL prior steps into Gaps & Validation Warnings.
2. Assess CP-1 output sufficiency for each requested downstream consumer:
   | Consumer | Type | Key CP-1 Dependencies |
   |----------|------|----------------------|
   | CP-1B | Analytical | Normalized financials, entity scope |
   | CP-1C | Analytical | Normalized financials, period coverage |
   | CP-2 | Analytical | All KPIs, calculation register, FCF build |
   | CP-2A | Analytical | Cash flow metrics, liquidity data |
   | CP-2D | Analytical | Earnings quality metrics |
   | CP-3 | Analytical | Debt classification, capital structure |
   | CP-3C | Analytical | Debt schedule, maturity profile |
   | CP-4 | Analytical | Covenant-relevant metrics, EBITDA definitions |
   | CP-4A | Analytical | Covenant compliance calculations |
   | CP-5 | Infra | Structured data for database |
   | CP-5A | Infra | Full data set |
   | CP-MODEL | Workbook extension | T4.14–T4.19 complete; stable IDs; source locators; no BLOCK reconciliation |
3. Per consumer: Readiness Status (Ready / Ready with Limitations / Not Ready), gaps, actions.
4. After this step → load SCHEMA_REFERENCE.md and author validated canonical `[IssuerID]_CP-1_[YYYYMMDD].md` per `../../../CANON_SHARED.md § CP_AB_EXPORT_SPEC.md` (YAML envelope + canonical H2 headings). `IssuerID` is the exact front-matter `issuer_id`; `YYYYMMDD` is `analysis_date` without hyphens. Do not create alternate analytical exports.
5. **Audit Appendix contents (relocated from ACTIVE_PROMPT 2026-07-11)** — the single Audit Appendix in Markdown/export holds ALL audit items as sub-sections with tables intact, mapped to CP-1's own output tables: Source Gate / Readiness, Gap Ledger (T4.12), Evidence Trace, Source Registry (T4.1), QA Validation findings (severity-tagged), Definition Conflict Register (T4.11), Limitation Flags, Downstream Consumers (T4.13).

## Output — T4.12 Gaps & Validation Warnings
`Gap Description` | `Affected Line Item or Metric` | `Affected Period(s)` | `Downstream Impact` | `Severity` | `Recommended Action`

## Output — T4.13 Downstream Readiness Matrix
`Downstream Module` | `Readiness Status` | `Gaps or Limitations` | `Recommended Actions`

## Warnings
- Every gap from every prior step must appear in T4.12. Cumulative — no omissions.
- Downstream Readiness must cover every requested consumer, and always carries a
  CP-MODEL row whether or not CP-MODEL was requested. CP-MODEL status
  uses `ready`, `partial`, `blocked` or `not_applicable`; the workbook exporter
  accepts only `ready`.
</step_reference>
## REF_CP-1_13_ModelWorkbookInterface.md
# REF CP-1 13 — Model Workbook Interface

Load on every run. These tables sit inside the existing canonical
Markdown envelope and do not create a second artifact.

## Stable table IDs

Place each comment immediately before its Markdown table:

- `<!-- table-id: cp1.model_period_register -->`
- `<!-- table-id: cp1.model_account_register -->`
- `<!-- table-id: cp1.segment_revenue_schedule -->`
- `<!-- table-id: cp1.cp_model_segment_allocation -->` (required with CP-2G
  when operating segments are present)
- `<!-- table-id: cp1.operating_kpi_schedule -->` (optional when applicable)
- `<!-- table-id: cp1.adjusted_ebitda_bridge -->`
- `<!-- table-id: cp1.debt_facility_register -->`
- `<!-- table-id: cp1.model_reconciliation_register -->`
- `<!-- table-id: cp1.downstream_readiness -->`

## Period register

Columns:
`period_id | fiscal_year | fiscal_quarter | period_type | start_date | end_date | day_count | audit_status | currency | unit | accounting_basis | entity_perimeter | source_id | source_locator | component_period_ids`

- `period_type`: `QUARTER`, `YTD`, `FY`, `LTM`, `PERIOD_END`.
- Direct reported discrete quarter has priority.
- Calculate Q2 as H1−Q1 and Q3 as 9M−H1 only when direct quarters are absent.
- Reported unaudited Q4 remains independent. Calculate Q4 as FY−9M only when
  no reported Q4 exists, and label it `CALCULATED`.
- Direct reported FY is not replaced by a sum of quarters.
- Flow LTM = latest FY + current YTD − prior comparable YTD.
- Balance-sheet LTM means the latest period end.
- A derived period with a missing component is null.

## Account register

Columns:
`metric_id | period_id | value | sign_convention | value_class | calculation_status | source_id | source_locator | conflict_refs | limitation_refs`

Controlled metric IDs:

`revenue`, `cogs`, `gross_profit`, `opex_including_da`, `ebit`,
`depreciation_amortization`, `ebitda`, `adjusted_ebitda`,
`cash_interest_paid`, `cash_lease_payments`, `cash_taxes_paid`, `cfo_ncfo`,
`working_capital_change`, `capex_and_intangible_investment`,
`acquisitions_disposals`, `net_debt_issue_repay`,
`net_equity_issue_repay`, `dividends_paid`, `other_investing_financing`,
`net_cash_change`, `cash_and_equivalents`, `rcf_commitment`, `rcf_drawn`,
`senior_secured_debt`, `unsecured_debt`, `total_debt`,
`net_accounts_receivable`, `inventory`, `accounts_payable`,
`pretax_income`, `income_tax_expense`, `effective_tax_rate`.

Cash interest and cash tax mean cash paid, not accrued expense. `cfo_ncfo`
accepts reported CFO, OCF, NCFO or net cash provided by operating activities.
Use the canonical sign convention: inflows/positive balances positive and
outflows negative. Do not emit the model's FFO `Other` residual as a sourced
metric.

## Segment, EBITDA and debt registers

Segment columns:
`segment_id | segment_name | segment_type | display_priority | period_id | revenue | status | source_id | source_locator`

Adjustment columns:
`addback_id | addback_label | addback_classification | realization_status | display_priority | period_id | value | status | source_definition | source_id | source_locator`

Segment and adjustment registers are issuer-specific repeating schedules, not
fixed template slots:

- emit one stable `segment_id` per identified business unit and one row per
  applicable period; retain exact issuer labels and order by
  `display_priority`;
- `segment_type` is `OPERATING_SEGMENT` or `CORPORATE_ELIMINATION`;
  operating-segment priorities must be unique. Corporate/elimination remains
  separate from operating business-unit rows and has at most one row per
  period; aggregate source elimination lines before emitting that row;
- emit one stable `addback_id` per separately identified add-back and one row
  per applicable period; retain the exact upstream `addback_label`; add-back
  priorities must be unique;
- `addback_classification` is one of `RESTRUCTURING`, `SBC`, `COST_SAVINGS`,
  `RUN_RATE`, `SYNERGY`, `TRANSACTION_COSTS`, `OTHER_EXPLICIT`;
- `realization_status` is independently one of `REALIZED`, `UNREALIZED` or
  `NOT_STATED`. Do not infer realization from the nature classification. Split
  an item into stable IDs when only part has been realized;
- classification supports analysis but never replaces the issuer label or
  permits different add-backs to be merged;
- `source_definition` records the issuer's definition or scope. Every
  `OTHER_EXPLICIT` line must be source-supported and is never a plug;
- do not manufacture empty slots. If the issuer explicitly reports no
  add-backs, emit an empty bridge and reconcile Adjustments to zero.
- if no business-unit revenue schedule is disclosed, emit an empty segment
  table and an explained `WARN` segment reconciliation with null calculated
  value; do not imply a zero segment sum.

CP-MODEL renders the canonical segment schedule dynamically. The forecast-slot
allocation has columns:

`slot_id | slot_label | component_segment_ids`

- emit this allocation only when CP-2G is supplied and the canonical segment
  schedule is non-empty; map every stable `segment_id` exactly once to
  `DIVISION_1`, `DIVISION_2` or `DIVISION_3`;
- use the allocation only to bind CP-2G division-growth drivers. It never
  changes presentation order, merges source segments or reduces the rendered
  schedule;
- multiple segments may share a driver slot, but every segment remains a
  separately identified row in the workbook;
- `display_priority` is presentation-only and never determines forecast
  economics.

Operating KPI columns:
`kpi_id | kpi_label | business_unit | kpi_category | display_priority | period_id | value | unit | value_type | status | source_id | source_locator`

- this optional schedule contains operating measures such as users,
  subscribers, RGUs, connections, backlog, homes passed, churn and ARPU; it
  must not duplicate revenue, EBITDA, leverage or other financial ratios;
- `value_type` is `PERIOD_END`, `PERIOD_FLOW` or `RATE`. Period-end values use
  the last component observation, flows may be summed, and rates are shown
  only where directly sourced rather than averaged;
- preserve definition/perimeter breaks with a new stable `kpi_id`. Never join
  non-comparable series or manufacture backlog/N/A values as zero.

Debt columns:
`facility_id | facility_name | period_id | facility_type | carrying_value | principal | drawn_amount | commitment | secured_status | seniority | currency | margin_or_coupon | maturity_date | lease_classification | source_id | source_locator`

Model debt totals use carrying values. Principal and commitment are retained
separately and are not substitutes. When instrument-level carrying values are
not disclosed, retain the disclosed principal or translated balance on each
named facility and add the separately disclosed aggregate financing-cost,
discount or premium amount as a `DEBT ADJUSTMENT` row. Only that adjustment row
may be negative. Every row requires `facility_name`, currency, interest cost or
an explicit `Not stated`/`Not applicable`, maturity or an explicit `Not stated`/
`Not applicable`, `source_id` and `source_locator`.

Use the controlled `secured_status`, `seniority` and `lease_classification`
values from the CP-1 schema. `NOT_STATED` is not affirmative evidence of a
security or ranking: retain the row in the transparent other/not-stated debt
bucket and exclude it from secured or senior subtotals unless that specific
classification is sourced. Do not infer security or ranking from the
instrument name merely to make the workbook ready.

## Reconciliation and readiness

Reconciliation columns:
`check_id | period_id | check_type | reported_value | calculated_value | difference | tolerance | status | explanation | source_refs`

Required checks include segment revenue to reported revenue, EBITDA bridge,
adjusted EBITDA bridge at exact `addback_id` granularity, CFO identity, debt
totals, NCF to cash movement and
reported FY to quarterly sum. A reported-FY difference can be `WARN` when
audited and unaudited bases differ and the explanation is explicit. It is not
silently forced to zero.

Readiness columns:
`downstream_module | status | missing_metric_ids | conflict_refs | explanation`

Emit exactly one CP-MODEL row. It is `ready` only when all required period and
account keys are unique, at least four discrete quarters have a complete
debt-facility carrying-value schedule, every selected quarter reconciles for
revenue and total debt, all referenced periods exist, required source locators
are present and no mandatory reconciliation is `BLOCK`.

Segment readiness distinguishes non-disclosure from incompleteness:

- a genuinely undisclosed schedule is an empty table, with an explained
  `WARN`/null segment reconciliation for every applicable period; it may remain
  CP-MODEL-ready for historical consolidated modelling, but CP-2G division
  slots must all be `NOT_APPLICABLE` and no allocation table is emitted;
- once any source segment is emitted, every selected discrete quarter must
  contain the complete stable segment set and at least four such quarters are
  required; a missing segment row, null segment value or partial disclosed
  schedule blocks readiness.

The number of quarters, segments, add-backs and facilities is not a
presentation-capacity readiness constraint.
## REF_CP-1_AntiPatterns.md
<!-- REF_CP-1 AntiPatterns (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-1" name="Anti-Patterns — Recognize and Avoid">

Worked examples for CP-1 conduct. Load alongside the CP-1 workflow; the prohibited-behaviors and citation rules in the ACTIVE_PROMPT remain authoritative.

## Anti-Patterns — Recognize and Avoid
❌ Silent reconciliation:
*"EBITDA was EUR 120m in FY2023."*
→ Source A says EUR 120m. Source B says EUR 115m. Conflict not disclosed.

✅ Properly handled:
*"EBITDA (reported) was EUR 120m per audited FS (Source: AR 2023, p. 45). Management-adjusted EBITDA was EUR 115m per LP (Source: LP, p. 12). Conflict logged in Definition Conflict Register. Audited FS figure used as canonical (Tier 1)."*

---
❌ Data fabrication:
*"Capex was approximately EUR 30m based on industry norms."*
→ No capex figure in any source.

✅ Properly handled:
*"Capex: null [Not Available — not disclosed in provided sources]. Gap: Downstream impact on CP-2 FCF build = Not Calculable."*

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
- **Tone:** Institutional credit-analytical. No marketing, no equity-advocacy.
- **Tables are the deliverable, the conclusion is the entry point:** Tabular data remains the complete analytical deliverable and is preserved unchanged below the analytical appendix heading. Narrative supports and never replaces it, but the module-owned conclusion is rendered first so a reader reaches the answer before the registers.
- **Exact figures:** Source precision. No rounding without disclosure.
- **No filler:** Every sentence must carry analytical content or source reference.

</reference>
## REF_CP-1_Discipline.md
<!-- REF_CP-1_Discipline (T2 support) | 2026-07-11 | relocated from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-1" name="Prohibited Behaviors — Full Binding List">

Full prohibited-behaviors table relocated from ACTIVE_PROMPT; the 4 highest-risk rows kept inline in the ACTIVE_PROMPT `<prohibited_behaviors>` block remain authoritative and enforced identically to the rows below — this file is the complete reference, not a relaxed version.

## Prohibited Behaviors (relocated from ACTIVE_PROMPT 2026-07-11)
| Condition | Action |
|-----------|--------|
| Unsupported financial assertion | Must cite source file + locator — no bare claims |
| Conflicting source definitions | Do **NOT** reconcile silently — log in Definition Conflict Register |
| Missing financial data | Store **null** + log gap — do **NOT** fabricate or infer |
| Promotional / equity-optimism language | **Prohibited** — creditor-focused institutional tone only |
| Definition change (canonical → issuer) | Flag + log in Definition Conflict Register — do NOT silently adopt |
| Running text where table is required | Produce the **table** — tables are the primary deliverable |
| Currency/unit switching after normalization | **Prohibited** — once basis set in Step 3, it applies everywhere |

## Separation Discipline — Four Categories (relocated from ACTIVE_PROMPT 2026-07-11)
| # | Category | Rule | Label |
|---|----------|------|-------|
| 1 | Source Data | Directly extracted from source doc with citation | Source citation required |
| 2 | Normalized Data | Adjusted via Step 3 normalization with audit trail | [Normalized] + Normalization Register ref |
| 3 | Calculated / Derived | Computed from source or normalized data via formula | [Calculated] + formula + Calculation Register ref |
| 4 | Analyst Judgement | Interpretation, inference, or qualitative assessment | [Analyst Judgement] |
Every figure must be classifiable. Mixed content must be decomposed and labelled.

## Citation Rules (relocated from ACTIVE_PROMPT 2026-07-11)
| Condition | Action |
|-----------|--------|
| Figure supported by source | Cite exact filename + locator (page, table, note) |
| Figure not in any source | Store null + log gap — do NOT estimate |
| Sources conflict on a figure | Log both values in Conflict Register — do NOT reconcile |
| Figure derived from calculation | Cite inputs + formula in Calculation Register |
| Source is draft / incomplete | State limitation + downstream impact |
| Null or missing value | Store null — **null ≠ zero** unless source explicitly states zero |
**Source-first discipline:** Source Register (Step 1) must be complete before any extraction.

</reference>
## REF_CP-1_Workflow.md
<!-- REF_CP-1_Workflow (T2 support) | 2026-07-11 | relocated from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-1" name="Workflow — Full Table">

Full step table relocated from ACTIVE_PROMPT; the compact step list + REF pointers in the ACTIVE_PROMPT `<workflow>` block remain authoritative for step ordering and gating.

## Workflow (relocated from ACTIVE_PROMPT 2026-07-11)
> **For each step:** load the corresponding `REF_CP-1_{NN}_{Name}.md` file.
> Load `./CP-1_SCHEMA_REFERENCE.md` during export/QA.

| Step | Name | Ref File | Gate | Output Tables |
|------|------|----------|------|---------------|
| 1 | File Gate & Source Validation | REF_CP-1_01_FileGateSourceValidation | No financial sources → BLOCKED | T4.1 Source Register |
| 2 | Entity/Period Scope | REF_CP-1_02_EntityPeriodScope | Source-supported only | T4.2 Entity Period Key |
| 3 | Normalization | REF_CP-1_03_Normalization | Source data available | T4.3 Normalization Register |
| 4 | Income Statement | REF_CP-1_04_IncomeStatementCoverage | Always (gaps logged) | T4.4 IS + FS Coverage |
| 5 | Cash Flow Statement | REF_CP-1_05_CashFlowStatementCoverage | Always (gaps logged) | T4.5 CFS |
| 6 | Balance Sheet | REF_CP-1_06_BalanceSheetCoverage | Always (gaps logged) | T4.6 BS |
| 7 | Normalized Financials | REF_CP-1_07_NormalizedFinancialsTable | ≥1 of Steps 4-6 produced data | T4.7 Consolidated |
| 8 | LTM/YTD/Derived Periods | REF_CP-1_08_DerivedPeriodConstruction | Sub-period data; missing → null | T4.8 Constructed Period Reg |
| 9 | Calculation & KPI Build | REF_CP-1_09_CalculationRegisterKPIBuild | Normalized data available | T4.9 Calc Reg + T4.10 KPI |
| 10 | Definition Conflicts | REF_CP-1_10_DefinitionConflictRegister | Always (confirm or log) | T4.11 Def Conflict Reg |
| 11 | Evidence→Risk→Credit | REF_CP-1_11_EvidenceRiskCreditAnalysis | ≥1 KPI from Step 9 | Analytical narrative |
| 12 | Readiness Assessment | REF_CP-1_12_CoverageGateDownstreamReadiness | Always | T4.12 Gaps + T4.13 Readiness |

**Requested downstream consumers:** the routing-approved analytical and QA
consumers plus canonical-only CP-MODEL when invoked. For CP-MODEL, load
`REF_CP-1_13_ModelWorkbookInterface.md` and include T4.14–T4.19 before final
readiness.

</reference>

## Binding discipline

These rules are per-module applications of the Canon Core items they cite.

**Subsequent-events note:** the balance-sheet review includes the filing's subsequent-events disclosure; post-balance-date items surface as flagged Subsequent Events entries per Step 02.
