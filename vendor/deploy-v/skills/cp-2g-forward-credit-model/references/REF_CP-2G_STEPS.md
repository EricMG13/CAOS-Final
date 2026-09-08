Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

Original files, in this bundle: REF_CP-2G_A_SourceGate.md, REF_CP-2G_B_AssumptionAndDefinitionLock.md, REF_CP-2G_C_ForecastEngine.md, REF_CP-2G_D_ScenariosAndBreakpoints.md, REF_CP-2G_E_CreditHandoff.md, REF_CP-2G_F_OutputAndQA.md

## REF_CP-2G_A_SourceGate.md
# CP-2G A — Source and identity gate

Require CP-1 canonical financials for the same issuer and anchored reporting period. Record module ID, run ID, reporting period, source status and confidence. Re-anchor revenue, EBITDA, CFO, capex, FCF, cash, debt, interest and liquidity directly to CP-1; do not copy values from a narrative summary when a table value exists.

Lock issuer identity, consolidated perimeter, finance-company perimeter where applicable, fiscal calendar, currency/unit, actual/estimate cut-off and forecast horizon. A changed entity perimeter requires a separate bridge. If CP-1 is missing, Blocked, materially stale or mismatched, stop rather than manufacture a forecast base.

CP-1B may contribute earnings trajectory and guidance deltas; CP-2 may contribute business drivers and risks; CP-2E may contribute macro/FX sensitivities. These inputs do not override CP-1 metric definitions without a recorded definition conflict.

## REF_CP-2G_B_AssumptionAndDefinitionLock.md
# CP-2G B — Assumption and definition lock

Classify every forecast input as `source_fact`, `management_guidance`, `external_consensus`, `user_assumption`, `calculated`, or `analyst_judgment`. Store exact source and locator or name the user instruction. Do not relabel an analyst estimate as consensus or management guidance.

At minimum consider revenue volume/price/mix, margin, working capital, restructuring costs, capex, cash taxes, cash interest, leases, dividends/distributions, acquisitions/disposals, debt amortisation, refinancing terms, minimum cash and revolver availability. Use null rather than zero when unsupported.

Maintain separate definition IDs for reported EBITDA, CP-1 normalized EBITDA, covenant EBITDA and agency-adjusted metrics. The forward model normally uses CP-1 definitions; downstream modules may recalculate using their governing definitions.

## REF_CP-2G_C_ForecastEngine.md
# CP-2G C — Forecast engine

Build the shortest model that answers the credit question while covering the full refinancing horizon. Prefer eight quarters plus three annual periods when evidence supports quarterly granularity. Avoid false precision when only annual guidance exists.

For each case and period calculate operating results, CFO, capex, FCF, cash interest, debt issuance/repayment, closing debt/cash, accessible liquidity, leverage and coverage. Show formulas or formula IDs. Reconcile opening balances to the prior closing period and log any residual.

Debt and cash flows must respect entity perimeter. Never net securitised or matched-funding finance-company debt against industrial cash. Do not count restricted, trapped or operationally required cash as accessible without support. Do not assume undrawn revolvers are available when covenant or borrowing-base conditions are unknown.

## REF_CP-2G_D_ScenariosAndBreakpoints.md
# CP-2G D — Scenarios and breakpoints

The base case is the most evidence-supported path, not management's most favourable presentation. Upside and downside cases change named operating or financing drivers and preserve all unchanged assumptions. A severe case is optional and must not be disguised as the ordinary downside.

For every scenario show the first period in which liquidity, coverage, covenant headroom, refinancing feasibility or minimum cash becomes constrained. Identify the causal driver, not only the resulting leverage number. Test at least one disconfirming case against the central thesis.

Do not assign case probabilities unless sourced or user-approved. If weights are used, retain the unweighted cases and show the weighting source. Never average conflicting scenarios to conceal uncertainty.

## REF_CP-2G_E_CreditHandoff.md
# CP-2G E — Credit handoff

Summarise the direction and timing of deleveraging or releveraging, the peak funding requirement, minimum liquidity, refinancing dependency and the two or three assumptions that dominate the result. State which conclusions change across cases.

Handoff ownership:

- CP-2 consumes the forecast profile for integrated credit synthesis.
- CP-2A consumes driver breakpoints and stress transmission.
- CP-2D consumes near-term sources/uses and minimum-liquidity periods.
- CP-2H consumes forecast metrics for rating-trigger headroom.
- CP-3/3D consume refinancing needs and scenario credit metrics.

CP-2G does not issue formal ratings, choose securities, determine legal capacity or make portfolio recommendations.

## REF_CP-2G_F_OutputAndQA.md
# CP-2G F — Output and QA

Required QA tests:

1. Upstream issuer/run/period identity is anchored.
2. Every material assumption has a class, case, period, source/rationale and unit.
3. Opening and closing cash/debt roll forward without an unexplained material residual.
4. FCF, leverage and coverage definitions remain continuous across periods and cases.
5. Industrial/company and finance-company perimeters remain separate.
6. Downside changes named drivers and exposes the earliest breakpoint.
7. Nulls are not converted to zero and unsupported precision is removed.
8. No rating, legal conclusion, security recommendation or probability is fabricated.
9. Markdown contract validation and semantic/numerical checks pass.

The canonical Analysis section contains tables T2H.1–T2H.9. Evidence Trace holds formula/evidence lineage. Gaps & Conflicts names unresolved inputs and affected cases. QA Validation reports pass/fail for each test and the resulting status.

## Optional CP-MODEL driver interface

Append on every run:

`<!-- table-id: cp2g.cp_model_forecast_drivers -->`

Columns:
`driver_id | slot_id | case | period_id | fiscal_year | value | unit | assumption_id | status | source_id | source_locator | as_of`

Emit exactly three consecutive fiscal years for both `BASE` and `DOWNSIDE`.
The first year is no earlier than the latest CP-1 actual fiscal year. If the
latest actual year includes a directly reported FY period, the first forecast
year is no earlier than the following fiscal year.
For every case/period emit:

- `division_growth` for each of `DIVISION_1`, `DIVISION_2`, `DIVISION_3`,
  unit `PERCENT_DECIMAL`;
- `acquisitions_disposals`, `net_equity_issue_repay`, `dividends_paid` and
  `other_investing_financing` with blank `slot_id`, unit `CURRENCY_MM`.

`DIVISION_1..3` resolve only through CP-1's
`cp1.cp_model_segment_allocation`; CP-2G must never infer the mapping from
segment display order. Slots unused by the issuer may be `NOT_APPLICABLE`.

`status` is `READY` or `NOT_APPLICABLE`. A ready value requires an assumption
ID, source ID, precise locator and ISO as-of date. A not-applicable row has a
blank value and remains blank in the workbook. CP-MODEL does not consume upside
drivers. A missing active division-growth value makes that case period and its
dependent later periods unavailable; it is never interpreted as zero growth.
