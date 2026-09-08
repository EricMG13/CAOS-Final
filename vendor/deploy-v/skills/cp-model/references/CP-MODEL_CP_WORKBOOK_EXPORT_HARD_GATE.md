# CP Workbook Export Hard Gate

Version: 3.0  
Applies only to: `CP-MODEL`

## Identity lock

`WORKBOOK_EXPORT` is valid only for CP-MODEL. It is deployed in Structures A
and B with the same data, renderer, calculation and validation gates.

| Module | Owned object | Permitted file |
|---|---|---|
| CP-MODEL | `credit_snapshot_model_workbook` | `[IssuerID]_CP-MODEL-v3_[FirstPeriod]-[LastPeriod]_[YYYYMMDD].xlsx` |

## Runtime hard gates

1. A file-generation runtime capable of creating, writing and reloading `.xlsx`
   plus LibreOffice/soffice for external recalculation is mandatory.
2. Build from validated canonical handoffs through the typed intermediate model.
   Do not consume a workbook template, a fixed cell map or a prior output.
3. Work in a unique temporary directory and never overwrite an existing output.
4. Export exactly one validated `.xlsx`.
5. Do not emit an analytical Markdown, DOCX or PDF artifact.
6. Return only concise status, limitations and a link to the workbook created.
7. `confidence_score` and `confidence_band` do not apply to this output class.

## Construction hard gates

- Derive visible rows and columns from the validated periods, segments,
  add-backs, debt facilities and optional forecast drivers.
- Preserve every source value and its provenance; never coerce source data to
  satisfy a formula.
- Generate every calculation formula and track it against an independently
  computed expected value.
- Emit `Credit Snapshot`, `Model`, `KPIs`, `_INPUTS`, `_MAP`, `_CHECKS`,
  `_AUDIT` in that order; keep all four control sheets hidden.
- Show every source add-back and debt facility; group debt only by explicitly
  stated security and expose senior-secured, senior and total leverage.
- CP-1C/comparables and any Comps/Data sheet are outside the export contract.

## Fail closed

Do not export when any required upstream owner is not ready, identity/scope
differs, a mandatory mapping is unresolved, a reconciliation fails, a formula
is untracked, recalculation does not produce a cached value, a formula result
differs from its independent expectation, a formula error exists, the output
already exists or binary validation fails. Never group or truncate repeating
schedules to fit a presentation capacity.
