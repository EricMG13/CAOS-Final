# CP Workbook Export Specification

Version: 3.0  
Output class: `WORKBOOK_EXPORT`

## Common contract

Every run validates canonical handoffs, builds a typed layout-free model,
creates a new workbook, forces external recalculation, validates all formula
results and publishes one `.xlsx`. The workbook is the sole analytical artifact
and handoff.

Required payload fields are defined by
`./CP-MODEL_CP_WORKBOOK_EXPORT_PAYLOAD_BASE.schema.txt`.

## Workbook structure

Expected worksheets, in order:

1. `Credit Snapshot` — visible narrative and latest credit overview
2. `Model` — visible dynamic quarterly, annual and optional forecast model
3. `KPIs` — visible business-unit operating measures such as users, RGUs,
   connections, backlog, churn and ARPU when applicable; financial and credit
   metrics remain at the bottom of `Model`
4. `_INPUTS` — hidden source values and provenance
5. `_MAP` — hidden realised semantic-to-cell map
6. `_CHECKS` — hidden reconciliation and semantic results
7. `_AUDIT` — hidden renderer, engine and source hashes

There is no shared reference workbook or pre-authored cell-address manifest.

## Cell classes

| Class | Meaning |
|---|---|
| SNAPSHOT_SOURCE | canonical CP-1A/CP-1B/CP-2/CP-2A text |
| HISTORICAL_SOURCE | canonical CP-1 period, segment, add-back or facility value |
| CALCULATED_FORMULA | generated formula with independent expected value |
| FORECAST_SOURCE | optional canonical CP-2G driver |
| LABEL | renderer-owned presentation text |

## Validation

Before returning a file:

- validate each handoff and every required table/key/source locator;
- validate segment/revenue, EBITDA/add-back, cash-flow and debt identities;
- validate every source value is represented in the provenance ledger;
- externally recalculate with LibreOffice/soffice and record its version;
- require each formula cell to be tracked and have a cached result;
- compare each cached result to the independent expected value;
- reject all formula error values and unexpected sheet states;
- reload formula and data-only views before exclusive publication.

CP-MODEL is a terminal exporter and has no downstream analytical consumer.
