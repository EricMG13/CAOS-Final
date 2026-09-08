# CP-MODEL Schema Reference

Central payload:
`CP-MODEL__CreditSnapshotModelWorkbook__payload.schema.txt`

## Workbook contract

Renderer-created visible sheets, in order:

1. `Credit Snapshot`
2. `Model`
3. `KPIs`

Renderer-created hidden sheets, in order:

4. `_INPUTS`
5. `_MAP`
6. `_CHECKS`
7. `_AUDIT`

No workbook template or pre-authored cell manifest participates in the build.
The realised workbook map is emitted into `_MAP` for each run.

## Required runtime records

- `quarter_periods`: unique selected CP-1 discrete quarters; at least four.
- `annual_periods`: every available CP-1 `FY` period, possibly empty.
- `analysis_columns`: ordered renderer axis comprising `QUARTER`, `YTD`, `FY`,
  `LTM`, `PF`, `BASE` and `DOWNSIDE` column records. Each record retains its
  component periods, ending balance period, growth-comparison column,
  forecast-roll-forward column and case. The deprecated
  `comparison_column_id` remains an alias of `growth_comparison_column_id` for
  one compatibility release. YTD and LTM each contain prior/current records;
  unavailable prior comparators are
  explicit records with `available=false`, not fabricated values.
- `formulas_validated`: number of formula cached values compared to the
  independent calculation model.
- `semantic_checks`: number of independently evaluated reconciliation checks.
- `renderer_sha256`: hash of the renderer source used for the build.
- `calculation_engine`: exact external recalculation engine/version.
- `source_manifest`: required/optional upstream artifact and validation status.

`qa_status` is `Passed` only when no blocking check exists, the externally
recalculated workbook reloads, every formula is tracked and matches its
independent expected value, all control sheets are hidden, and publication is
exclusive.

Output:
`[IssuerID]_CP-MODEL-v3_[FirstPeriod]-[LastPeriod]_[YYYYMMDD].xlsx`.
