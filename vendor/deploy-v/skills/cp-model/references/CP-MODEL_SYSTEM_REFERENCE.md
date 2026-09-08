# CP-MODEL System Reference

| Field | Value |
|---|---|
| module_id | CP-MODEL |
| module_name | CreditSnapshotModelWorkbook |
| owned_object | credit_snapshot_model_workbook |
| schema_family | Infrastructure |
| output_class | WORKBOOK_EXPORT |
| required upstream | CP-1, CP-1A, CP-1B, CP-2, CP-2A |
| optional upstream | CP-2G |
| downstream | none |
| construction | clean-sheet, data-driven renderer |
| visible sheets | Credit Snapshot, Model, KPIs |
| hidden sheets | _INPUTS, _MAP, _CHECKS, _AUDIT |

CP-MODEL v3 creates its model and snapshot from validated canonical data. It
does not consume a workbook template, a fixed cell-address manifest, vendor
formulas or a protected manual capital table. CP-1 owns canonical numeric
truth; CP-1B validates it. CP-1A, CP-1B, CP-2 and CP-2A own snapshot text.
CP-2G optionally owns forecast drivers. CP-1C/comparables are not consumed.

The module owns only the new workbook it exports. It fails closed on a missing
or mismatched handoff, unresolved source value, reconciliation failure,
external calculation failure, untracked formula, formula-value mismatch,
output collision or binary reload failure.

The visible workbook is credit-analyst oriented: it preserves every source
segment, EBITDA add-back and debt facility; separates realized and unrealized
add-backs; shows facility name, maturity and contractual cost within stated
security groups; bridges cash flow from Adjusted EBITDA; and presents quarter,
YTD, FY, LTM, PF, Base and Downside views. Growth, profitability, coverage and
senior-secured, senior, total and net leverage sit at the bottom of `Model`.
`KPIs` is reserved for issuer operating measures such as users, RGUs,
connections, backlog and ARPU; it shows an applicability note when none are
supplied.
