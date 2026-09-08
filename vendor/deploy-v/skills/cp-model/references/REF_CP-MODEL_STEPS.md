Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

Original files, in this bundle: REF_CP-MODEL_A_SourceTemplateGate.md, REF_CP-MODEL_B_PeriodAccountMapping.md, REF_CP-MODEL_C_ModelMath.md, REF_CP-MODEL_D_PreservationExportQA.md

## REF_CP-MODEL_A_SourceTemplateGate.md
# REF CP-MODEL A — Source and Build Gate

## Source gate

Accept only matching canonical Markdown handoffs from CP-1, CP-1A, CP-1B,
CP-2 and CP-2A; CP-2G is optional. Validate:

- common-envelope module identity, issuer, reporting period and analysis date;
- `qa_status: Passed` and CP-MODEL in `downstream_consumers`;
- exact stable table IDs, required headers and controlled identifiers;
- unique keys, complete source IDs/locators/as-of dates and cross-table period
  references;
- CP-1 and CP-1B CP-MODEL readiness;
- absence of any mandatory `BLOCK`.

CP-1B validates but never replaces CP-1 numeric truth. CP-1C is outside the
contract.

## Build gate

The renderer starts from a blank workbook and derives layout from the validated
intermediate model. A workbook template, template attachment, manifest cell map
or previously generated workbook is neither required nor accepted as an input.

Require a callable LibreOffice/soffice engine before rendering. Build in a
unique temporary directory beneath the requested output directory. Probe and
record the engine version, recalculate externally, validate the result, then
publish with exclusive-create semantics. Never overwrite an existing output.

## Source immutability

Every source-owned value retains its owner, source ID, locator, as-of date and
source-file hash. Calculated cells are generated only from declared formulas
and independently verified expectations. The renderer must not manufacture a
source value to make a workbook identity pass.
## REF_CP-MODEL_B_PeriodAccountMapping.md
# REF CP-MODEL B — Data-Driven Period and Account Mapping

The typed intermediate model is the workbook's layout-independent authority.
The renderer records every realised field-to-cell mapping in `_MAP`.

## Snapshot

| Owner | Stable table | Content |
|---|---|---|
| CP-1A | `cp1a.cp_model_snapshot_fields` | issuer, sector/country display, shareholders, transaction and business description |
| CP-1B | `cp1b.cp_model_snapshot_fields` | historical performance narrative |
| CP-2 | `cp2.cp_model_strengths_weaknesses` | ranked strengths and weaknesses |
| CP-2A | `cp2b.cp_model_catalysts` | ranked catalysts / near-term events |

Every rendered statement retains its source ID, locator and as-of date in
`_INPUTS` and as a comment on the visible source cell.

## Periods

- Select the requested latest discrete `QUARTER` periods, with a minimum of
  four and no renderer-defined maximum.
- Include every available reported `FY` period in a separate annual block.
- Require a single currency, unit, accounting basis and entity perimeter across
  the selected scope.
- Do not derive quarters or fiscal years in CP-MODEL; CP-1 must publish the
  canonical period values.
- Build the analysis axis in this order: discrete quarters, comparable YTD,
  reported FY, rolling LTM, PF, Base and Downside, with one narrow blank column
  between each group. Always show prior/current YTD and LTM pairs. The prior
  column is the same-fiscal-quarter prior-year comparator; when its complete
  source window is unavailable, retain a labelled `Not supplied` column and
  leave its values and current-period YoY blank. Do not substitute the
  immediately preceding rolling quarter. Flows sum component quarters;
  balance-sheet and debt values use the ending observation. Reported FY always
  remains source-owned.
- PF uses latest LTM operating flows and current capital structure when no
  separate transaction adjustments are supplied, and is labelled explicitly.
- Base/Downside use CP-2G assumptions when present. If CP-2G is absent, retain
  labelled unavailable case headers and leave the case values blank.

## Repeating schedules

- Render every CP-1 segment in `display_priority` order, including a separate
  corporate/elimination line when present. Use
  `cp1.cp_model_segment_allocation` only to bind each stable segment ID to a
  CP-2G growth-driver slot; never group or reorder the visible segment rows to
  fit slots.
- Render every identified add-back in `display_priority` order. Never merge or
  truncate add-backs. Preserve the source category and separate realized,
  unrealized and not-stated lines and subtotals.
- Render every debt facility with carrying value, classification and maturity
  metadata. Group facilities by the explicitly reported `SECURED`, `UNSECURED`
  or `NOT_STATED` security class and show group subtotals. Never substitute
  principal for carrying value or infer security/seniority from the instrument
  name.
- Accept only explicit seniority values `SUPER_SENIOR`, `SENIOR`,
  `SENIOR_SUBORDINATED`, `SUBORDINATED`, `JUNIOR` or `NOT_STATED`. An unknown
  value blocks the build rather than silently changing senior leverage.
- Reconcile segments to reported revenue, the adjusted EBITDA bridge to
  reported adjusted EBITDA, and facilities to reported total debt for every
  selected period.

## Growth, credit metrics and operating KPIs

- Render total-revenue, adjusted-EBITDA and every business-unit growth rate
  with the compact `YoY` suffix.
- For discrete quarters, growth means year over year against the same fiscal
  quarter and is blank until a comparable quarter exists.
- For reported fiscal years, growth means year over year against the prior
  reported fiscal year and is blank until a comparable year exists.
- Put growth, profitability, leverage, coverage, cash-conversion and working-
  capital credit metrics at the bottom of `Model`, including senior-secured,
  senior, total and net leverage.
- Create `KPIs` for every build, but populate it only from
  `cp1.operating_kpi_schedule`. Group rows by business unit and category. If
  the optional schedule is absent, show an applicability note; never substitute
  financial ratios.

## Accounts and forecast

Use CP-1 cash-paid interest and tax metrics, not expenses. Retain CP-1 signs for
cash flows. Calculate FFO `Other` only as the disclosed residual in REF C.

When CP-2G is present, its three Base and three Downside periods drive formulas
using the latest PF revenue mix, margins and cash-flow ratios. Keep CP-2G
assumption values and lineage on hidden control sheets; do not display a
forecast-assumption block on the analyst-facing `Model` worksheet.
The direct CP-2G interface has three division-growth slots; a scenario build
with more than three unallocated CP-1 business-unit series blocks rather than
silently leaving additional units flat.
## REF_CP-MODEL_C_ModelMath.md
# REF CP-MODEL C — Model Math

CP-MODEL writes calculation formulas and separately computes expected results
from the typed intermediate model. A workbook is valid only when every cached
formula result matches its independent expected value within the declared
tolerance.

## Historical identities

- Revenue = sum of rendered segment rows when a segment schedule is available;
  otherwise use the source-owned reported revenue.
- Gross Profit = Revenue + COGS.
- EBIT = Gross Profit + OPEX (including D&A).
- EBITDA = EBIT + D&A.
- Adjusted EBITDA = EBITDA + every identified add-back.
- FFO Other = CFO − Change in Working Capital − Adjusted EBITDA − Cash Interest
  − Cash Leases − Cash Taxes.
- FFO = Adjusted EBITDA + Cash Interest + Cash Leases + Cash Taxes + FFO Other.
- CFO (calculated) = FFO + Change in Working Capital.
- CFO reconciliation = CFO (reported) − CFO (calculated).
- FCF = CFO + Capex & Intangible Investment.
- NCF = FCF + acquisitions/disposals + net debt issuance/repayment +
  net equity issuance/repurchase + dividends + other investing/financing.
- Total debt = sum of debt-facility carrying values.

Cash interest, leases, taxes, capex, dividends and other outflows retain CP-1's
canonical signs. A missing required value is blocking; CP-MODEL never inserts a
plug other than the disclosed FFO residual.

The visible cash-flow bridge follows this exact order: Adjusted EBITDA; Cash
Interest Paid; Cash Lease Payments; Cash Taxes Paid; FFO Other; Funds From
Operations; Change in Working Capital; CFO Calculated; CFO Reported; CFO
Reconciliation; Capex & Intangible Investment; Free Cash Flow; and the
remaining investing/financing lines through Net Cash Flow.

## Ratios and annuals

Growth = current value / comparable value − 1. Quarterly growth uses the same
fiscal quarter in the prior year; annual growth uses the prior reported fiscal
year. Total revenue, adjusted EBITDA and each business unit use this convention.

Every analysis column carries two independent links:

- `growth_comparison_column_id` is used only by visible `YoY` formulas. It points
  to the exact same-quarter prior-year column for a quarter, the exact
  prior-year aggregate for current YTD/LTM, and the prior reported fiscal year
  for FY. It is null when that exact comparable period is unavailable. For a
  forecast case year, it points to the prior year in the same case; year one may
  point to PF only when PF is an exact comparable twelve-month base, otherwise
  its YoY remains blank.
- `rollforward_column_id` is used only to calculate PF/Base/Downside values. The
  first Base and Downside year rolls from PF; each later year rolls from the
  preceding year in the same case. This link never supplies a YoY denominator.

The deprecated `comparison_column_id`, if accepted during the compatibility
window, must equal `growth_comparison_column_id` and is ignored by forecast
roll-forward calculations. A renderer must not substitute a nearby column for
either link.

- Senior secured debt = sum of facilities explicitly classified both senior
  and secured.
- Senior debt = sum of facilities explicitly classified `SUPER_SENIOR` or
  `SENIOR`, whether secured or unsecured.
- Total debt = sum of every debt-facility carrying value, including facilities
  whose security or seniority is not stated.
- Senior secured leverage = senior secured debt / applicable adjusted EBITDA.
- Senior leverage = senior debt / applicable adjusted EBITDA.
- Total leverage = total debt / applicable adjusted EBITDA.
- Net leverage = (total debt − cash and equivalents) / applicable adjusted
  EBITDA.

For quarterly columns, applicable adjusted EBITDA and other flow metrics use
latest-twelve-month values once four quarters are available. Annual columns use
the reported fiscal-year flow. Gross margin, adjusted EBITDA margin, interest
coverage, FCF/debt, capex/revenue, cash conversion and DSO/DSI/DPO are
formula-owned. Undefined or inapplicable ratios remain blank; they are never
source values.

Reported annual periods are rendered from CP-1 values, not rebuilt from
quarterly sums. Any reported-FY-to-quarter reconciliation status and basis
difference is preserved in the checks ledger.

YTD and LTM flow rows sum discrete component quarters; their balance, debt and
period-end operating KPI rows use the final component quarter. YTD leverage and
FCF/debt annualize the applicable flow by `365 / day_count`. Rate operating
KPIs (for example ARPU or churn) remain blank in derived columns unless CP-1
publishes the aggregate directly. A directly published rate remains visible on
the KPI worksheet even when the corresponding financial YTD/LTM window cannot
be reconstructed; only the financial Model column remains `Not supplied`.

YTD and LTM are displayed as prior/current pairs. Their growth rows use the
compact `YoY` suffix. Current YTD compares only with the complete YTD aggregate
ending in the same fiscal quarter one year earlier; current LTM compares only
with the complete twelve-month window ending in the same fiscal quarter one
year earlier. The prior record has no growth comparator of its own. It remains
visibly labelled but unavailable, and current YoY remains blank, when the exact
comparison window is not supplied.

## Forecast drivers

PF uses the latest four-quarter flows and current period-end capital structure
when no explicit transaction adjustment is available.

`cp1.cp_model_segment_allocation` is the sole binding between CP-1 stable
segment IDs and CP-2G `DIVISION_1..3` growth drivers. Each allocation row is one
active slot, has a non-empty `component_segment_ids` list, and every source
segment occurs in exactly one list. Omitted slots are inactive. The allocation
changes only driver assignment: every original source segment remains a
separate visible row and receives the growth rate of its assigned slot.

For each Base/Downside case period, CP-2G must supply a numeric `READY` growth
driver with complete lineage for every active slot. Inactive slots remain
`NOT_APPLICABLE` with null values and are never converted to zero. A missing or
`NOT_APPLICABLE` driver for an active slot makes that case period, and every
later period depending on it, unavailable. The case period is available only
when all active-slot growth drivers and all other required case-period drivers
are ready.

Base and Downside segment revenue applies the assigned CP-2G growth rate to the
column named by `rollforward_column_id`: PF for year one and the preceding year
in the same case thereafter. COGS, OPEX, D&A, cash leases, cash taxes, working
capital, FFO Other, capex and working-capital balances roll at their PF
revenue/COGS ratios; identified add-backs and facility debt carry from PF; cash
rolls through NCF; and CP-2G supplies acquisitions, equity, dividends and other
financing flows. All such cells are formulas with independently calculated
expectations. CP-2G values remain formula-linked to hidden `_INPUTS` records so
lineage is retained without a visible forecast-assumption section.
## REF_CP-MODEL_D_PreservationExportQA.md
# REF CP-MODEL D — Recalculation, Export and QA

## Required checks

- every required handoff passes its common and module-specific contract;
- selected period scope, basis, currency, unit and perimeter are consistent;
- segment revenue, EBITDA, adjusted EBITDA, cash flow and debt identities pass
  for every selected quarter and annual period where applicable;
- every source-owned visible value appears in `_INPUTS` with provenance;
- every realised visible field mapping appears in `_MAP`;
- every semantic validation appears in `_CHECKS`;
- visible sheet order is exactly `Credit Snapshot`, `Model`, `KPIs`;
- `_INPUTS`, `_MAP`, `_CHECKS` and `_AUDIT` exist in order and are hidden;
- every formula is tracked and has a cached result after external recalculation;
- no formula result is an Excel/LibreOffice error value;
- every formula result matches the independent calculation expectation;
- the saved binary reloads successfully in formula and value modes.

An omitted optional CP-2G handoff is allowed. Every unresolved mandatory
mismatch blocks export.

## Audit sheets

- `_INPUTS`: owner, field, period, visible target, value and provenance.
- `_MAP`: realised semantic field-to-cell mapping and cell class.
- `_CHECKS`: independent check ID, PASS/BLOCK status and detail.
- `_AUDIT`: renderer version/hash, calculation engine and SHA-256 for every
  handoff.

Hidden control sheets are an audit mechanism, not a confidentiality boundary.
Workbook recipients can unhide them or inspect the OOXML package. Never place
credentials, secrets or source content that is not authorised for every
intended recipient in `_INPUTS`, `_MAP`, `_CHECKS` or `_AUDIT`; distribute the
workbook under the most restrictive handling requirement of its sources. Sheet
hiding must never be described as encryption or access control.

## Export

Publish exactly one new file:
`[IssuerID]_CP-MODEL-v3_[FirstPeriod]-[LastPeriod]_[YYYYMMDD].xlsx`.

Validate the temporary binary before publication. Use exclusive creation so a
concurrent or pre-existing output can never be overwritten.
