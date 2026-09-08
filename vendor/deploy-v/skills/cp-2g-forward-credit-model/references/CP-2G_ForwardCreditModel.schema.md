# CP-2G Forward Credit Model schema

On every run the canonical Markdown also includes
the complete `cp2g.cp_model_forecast_drivers` stable table defined in REF F.

## Required analysis tables

| ID | Table | Required fields |
|---|---|---|
| T2H.1 | Source and identity gate | source_id, upstream module/run/period, status, locator, limitation |
| T2H.2 | Historical-to-base bridge | metric, historical actual, LTM/base, adjustment, basis, evidence_id |
| T2H.3 | Assumption register | assumption_id, driver, case, period, value/range, unit, class, source, rationale |
| T2H.4 | Forward operating model | period, case, revenue, EBITDA, margin, CFO, capex, FCF, evidence/assumption IDs |
| T2H.5 | Debt and liquidity roll-forward | period, case, opening debt/cash, issuance, repayment, interest, closing debt/cash, accessible liquidity |
| T2H.6 | Credit metrics | period, case, gross/net leverage, coverage, FCF/debt, liquidity runway, definition IDs |
| T2H.7 | Scenario and breakpoint matrix | driver shock, first break, period, liquidity/covenant/refinancing consequence, recovery action |
| T2H.8 | Deleveraging and monitoring handoff | case, trajectory, target/date, dependency, trigger, downstream module |
| T2H.9 | Gaps and conflicts | item, conflict/gap, affected case/period, model impact, required evidence |

## Calculation controls

- Closing debt = opening debt + issuance/PIK/capitalised interest − contractual and optional repayments ± supported FX/perimeter movements.
- Closing cash = opening cash + CFO − capex − cash interest/taxes/distributions ± supported financing/investing movements.
- FCF definitions must be explicit and inherited from CP-1 unless a labelled alternative is necessary.
- Net leverage uses accessible cash only; finance-company and industrial/company debt and cash remain separate.
- A balancing residual is never silently forced to zero.

## Contextual CP-MODEL driver table

On every run, runtime output and canonical
Markdown must include `cp2g.cp_model_forecast_drivers` with columns:

`driver_id | slot_id | case | period_id | fiscal_year | value | unit | assumption_id | status | source_id | source_locator | as_of`

Emit exactly three consecutive fiscal years for `BASE` and `DOWNSIDE`. The
first forecast year is no earlier than the latest CP-1 actual fiscal year; when
the latest actual year contains a directly reported FY period, forecasting
starts no earlier than the following fiscal year. Each
case/period contains `division_growth` rows for `DIVISION_1..3` and the four
non-division flow drivers defined in REF F: seven rows per case/period and 42
rows in total. Division slots resolve only through
`cp1.cp_model_segment_allocation`; display order is never a mapping.

Allocation rows define active slots. Every active slot must be `READY`, numeric
and fully sourced for every case/period. An inactive slot is
`NOT_APPLICABLE` with a null value. Missing or `NOT_APPLICABLE` data for an
active slot makes that case period and its dependent later periods unavailable;
it must never be interpreted as zero growth. A case period is consumable only
when all active slots and every other required driver are ready.

## Completion gate

`Complete` requires a reconciled base case, at least one downside case, traceable assumptions, debt/cash roll-forwards and credit-metric continuity. `Complete with Gaps` is permitted when named, bounded assumptions remain. Missing canonical history, identity mismatch or an unreconciled material model break is `Blocked`.
