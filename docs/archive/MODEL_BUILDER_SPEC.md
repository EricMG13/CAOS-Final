> **Archived 2026-09-09 under `docs/DECISIONS.md` §48.** Not in the build.
> Kept verbatim for a build that brings the workbook back. What that build
> needs, measured in §48: `libreoffice-calc` in the image (436 MB, 167
> packages), the model extension placing CP-MODEL at stage 101 with the
> `CP-CF → CP-MODEL` edge, a worker process for the recalculation, and a
> per-calculator dependency set for `openpyxl`. The bundle code it renders and
> verifies with -- `vendor/deploy-v/skills/cp-model/` -- is still vendored and
> pinned. Section references below are to the documents as they stood before
> §48; the appendix carries what those documents said.

# Model Builder — legacy parity spec

CP-MODEL v3 is the reference implementation. The rebuild's Model Builder must
**look and function like it**. This document is the parity contract; where it
and any other document disagree, this one wins for the workbook.

Source of truth: `skills/cp-model/` in the vendored Deploy V bundle —
`SKILL.md` (the export hard gate), `scripts/cp_model_v3/builder.py`,
`workbook.py`, `calculations.py`, `domain.py`.

---

## 1. The finding that drives this document

The old CAOS tree does **not** function like legacy, and the gap is not
cosmetic.

| | Legacy CP-MODEL v3 | Old CAOS tree |
|---|---|---|
| Cells | Real Excel formulas, tracked by `FormulaExpectation` | Formula strings written, never evaluated |
| Verification | Recalculate through LibreOffice, reopen twice (formula view + value view), validate sheet registry, formula inventory, and **every computed value** against an independently computed expectation | `_assert_workbook_semantics` reopens with `data_only=False` and compares what was written against what was intended |
| Publish | `os.link` / `O_EXCL` — refuses to overwrite | `workbook.save(path)` |
| Provenance | Every source value carries its refs as a cell comment | Bold row 1, freeze `A2` |
| Sheets | Seven, fixed order, four hidden | Created ad hoc from tab payloads |

So a formula that computes the wrong number, or resolves to `#DIV/0!` or
`#REF!`, ships silently today. Legacy catches it before publication.

**This reverses the earlier recommendation to drop LibreOffice.** In legacy,
soffice is not a dead alternate export path — it is the formula verification
engine (`builder.py::_resolve_soffice`, `_recalculate`,
`_validate_recalculated`). The worker image keeps it, and the build fails
closed without it: *"LibreOffice/soffice is required to recalculate and
validate formulas."*

---

## 2. Output contract

- Exactly one validated `.xlsx`. No Markdown, DOCX or PDF from this module.
- Filename `[IssuerID]_CP-MODEL-v3_[FirstPeriod]-[LastPeriod]_[YYYYMMDD].xlsx`.
- Never overwrite an existing output — publish exclusively (`os.link`, falling
  back to `O_WRONLY|O_CREAT|O_EXCL`), and refuse rather than clobber.
- Work in a unique temporary directory; publish only after validation passes.
- `confidence_score` and `confidence_band` do not apply to this output class.
- Return concise status, limitations and a link. Nothing else.

## 3. Sheets — seven, in this order

| # | Sheet | Visible | Contents |
|---|---|---|---|
| 1 | `Credit Snapshot` | yes | Issuer identity, capital structure, headline credit metrics |
| 2 | `Model` | yes | The spread: periods as columns, line items as rows, formulas in the analysis columns |
| 3 | `KPIs` | yes | Derived ratios and operating KPIs |
| 4 | `_INPUTS` | **hidden** | The typed IR values as written, one row per `(metric_id, period_id)` |
| 5 | `_MAP` | **hidden** | `MappingRecord` — every cell address to its IR key |
| 6 | `_CHECKS` | **hidden** | `SemanticCheck` rows: check_id, status, period, actual, expected, difference, tolerance, detail |
| 7 | `_AUDIT` | **hidden** | Source paths, source hashes, limitation flags, upstream validation warnings, engine version |

The sheet registry is validated after recalculation. A missing, extra or
reordered sheet is a refusal.

## 4. Construction rules

- **Derive, never template.** Visible rows and columns come from the validated
  periods, segments, add-backs, debt facilities and optional forecast drivers.
  Do not consume a workbook template, a fixed cell map, or a prior output.
- **Preserve every source value and its provenance. Never coerce source data to
  satisfy a formula.** If a formula and a source disagree, the workbook records
  the variance; it does not adjust the source.
- **Show every source add-back and every debt facility.** Group debt only by
  explicitly stated security. Expose senior-secured, senior and total leverage.
- CP-1C comparables and any Comps/Data sheet are outside this contract.
- Fail closed when a required upstream owner is not ready, or identity/scope
  does not match.

## 5. Formula integrity — the loop that must exist

```
render(IR) -> (draft.xlsx, [FormulaExpectation])
  |
  +-- every generated formula records an independently computed expected value
  |
recalculate(draft.xlsx) via soffice          # headless, timeout-bounded
  |
validate(recalculated.xlsx, expectations):
  - _validate_sheet_registry(formula_book, value_book)
  - _enumerate_formula_cells(formula_book, value_book)
  - _validate_formula_inventory(cells, tracked)   # no untracked formula, none missing
  - _validate_formula_values(value_book, tracked) # computed == expected
  |
publish_exclusive(recalculated.xlsx, destination)
```

Four independent failures, each its own refusal:

| Failure | Meaning |
|---|---|
| `WORKBOOK_RECALC_UNAVAILABLE` | soffice absent or non-zero exit |
| `WORKBOOK_SHEET_REGISTRY_INVALID` | sheet set or order wrong, or hidden flags wrong |
| `WORKBOOK_FORMULA_UNTRACKED` | a formula cell with no expectation, or an expectation with no cell |
| `WORKBOOK_FORMULA_MISMATCH` | computed value ≠ expected value |

`WORKBOOK_FORMULA_MISMATCH` names the sheet, address, expected and actual. It
never ships a workbook.

## 6. Look — the visual contract

The workbook is a credit analyst's spread, not a data dump.

- **Title** 16pt bold on each visible sheet; **section headers** banded across
  the used width.
- **Number formats**: `MONEY_FORMAT` for currency, `PERCENT_FORMAT` for ratios
  expressed as percentages, `CHECK_FORMAT` for reconciliation rows. Multiples
  (`5.68x`) carry their own format.
- **Check rows are filled pale green** when they reconcile, and carry the
  variance when they do not.
- **Spacer columns** separate quarterly, annual, LTM, pro-forma and forecast
  column groups; the analysis layout computes them from the column set.
- **Date header row** formatted `dd-mmm-yy`.
- **Freeze panes** so the row labels and the period header stay on screen.
- **Every source value cell carries a comment** containing its source refs and
  the owning module (`_comment(provenance, owner)`). This is "every number one
  click from its evidence" inside the workbook itself, and it survives the file
  leaving the system.

## 7. On-screen Model Builder

The `/model/` section renders the same object, not a different one.

- The worksheet view is the `Model` sheet's row and column structure, with the
  same groups, spacers and number formats.
- Selecting a cell shows its formula in the formula bar — the **workbook's**
  formula, not a re-derivation — plus its `_MAP` key and its provenance.
- `_CHECKS` is a first-class view: check id, status, actual, expected,
  difference, tolerance. A failing check is visible on screen before anyone
  downloads anything.
- The projection view (`IA_SPEC.md` §4.6) is the forecast columns of the same
  sheet, with the residual column from `cash_flow_forecast`.
- Download serves the validated file with its legacy filename. A build whose
  validation failed has no download.

## 8. Parity tests

These are contract tests, not unit tests. Each names the legacy behaviour it
pins.

1. `test_sheet_registry_order_and_visibility` — seven sheets, exact order, four
   hidden.
2. `test_every_formula_is_tracked` — formula cell set == expectation set.
3. `test_recalculated_values_match_expectations` — drives a real soffice
   recalculation over a fixture IR; any drift fails.
4. `test_recalc_unavailable_fails_closed` — soffice removed from PATH ⇒
   `WORKBOOK_RECALC_UNAVAILABLE`, no file published.
5. `test_publish_refuses_to_overwrite` — a second publish to the same path
   refuses.
6. `test_source_cells_carry_provenance_comments` — every cell written from a
   `SourceNumber` has a comment naming its refs.
7. `test_source_values_are_never_coerced` — a source that disagrees with a
   formula produces a variance row, not an edited source.
8. `test_filename_matches_legacy_pattern`.
9. `test_debt_grouped_only_by_stated_security` — no inferred grouping.
10. `test_screen_formula_equals_workbook_formula` — the formula bar and the
    `_MAP`-addressed cell agree.

A green suite with soffice absent is a vacuous pass. CI installs LibreOffice
for the model job and asserts the engine version is recorded in `_AUDIT`.

---

## Appendix — what the other documents said before §48

### `docs/SYSTEM_SPEC.md` §6

## 6. Model

One model effect per pathway. Full Credit builds the complete model from the six
canonical artifacts. Every other pathway resolves through the nearest validated
Full Credit ancestor: its build re-verified by recomputation, the accepted run's
calculation records re-executed, one `pathway_effects` entry on a byte-identical
copy of the base model-table payloads under the overlay's own input fingerprint.
This reuses validated data, not workbook sheets or a prior `.xlsx`. Every
workbook is rendered from the resulting typed IR and recalculated and validated
afresh, as required by `MODEL_BUILDER_SPEC.md` §§4–5.

- Calculation is pure and finite. Non-finite values and zero denominators are
  refused before use.
- Every build carries `source_lineage`: one row per pinned source with intake
  disposition, consumers, citing artifacts, model tables and binding. A `used`
  relevant document bound to nothing is `MODEL_SOURCE_LINEAGE_INCOMPLETE` and
  never READY.
- The expression language ported from the AI Studio build (`docs/DECISIONS.md` §8)
  is a registry calculator. It parses `$M`, `x`, `%`, `bps`, `IF/THEN/ELSE`,
  `MIN`/`MAX`/`SUM`/`HAIRCUT`, evaluates against pinned artifacts server-side,
  and attaches the lineage of every operand to the result. It never evaluates in
  the browser and never reads anything but the pinned snapshot.

Builds are claimed CAS-bound; a `BUILDING` row a dead worker left behind is
requeued at the next worker start. Exports take the same claim — one worker
today, but the claim is not optional.

### `docs/IA_SPEC.md` §4.6

### 4.6 Model — `/model/`

The build, its worksheet, assumptions, scenarios, tornado and one-way
sensitivity, revisions and rebase preview. Source lineage is a first-class view:
one row per pinned source, its consumers and its bindings. An incomplete
lineage blocks READY and says which source is bound to nothing.

The projection is a view here, not a separate section: per case-period, the
operating, investing and financing lines, the debt and cash roll-forward, and
**the residual as its own column**. A period whose residual exceeds tolerance
renders unavailable with its reason, and every later period in that case
renders unavailable too — never as zero growth, and never silently balanced.
Each projected figure carries the driver that produced it and that driver's
evidence, so the passport contract (§4.4) holds for forecast cells exactly as
it does for actuals.

### `docs/REBUILD_PLAN.md` Phase 7

## Phase 7 — Model build and the workbook

`docs/MODEL_BUILDER_SPEC.md` in full. This is the phase where "looks like
legacy" is either true or not.

- Typed IR from the six canonical artifacts; overlay resolution for the other
  pathways; `source_lineage` per pinned source.
- Renderer: seven sheets in order, four hidden, real formulas, every formula
  tracked by a `FormulaExpectation`, provenance comments on source cells.
- Recalculate through soffice; validate registry, inventory and every computed
  value; publish exclusively.
- `cash_flow_forecast` calculator and CP-CF (`SYSTEM_SPEC.md` §6.1–6.2).
- The `worker` process, its Dockerfile with soffice in it, and the `image` job
  with its scan floor (`docs/DECISIONS.md` §11).
- A per-calculator dependency set: `-S` holds for the stdlib calculators and
  not for `cp_model_v3` or `cp_memo` —
  `test_a_calculator_sees_only_its_declared_dependencies`.

**Exit:** the ten parity tests in `MODEL_BUILDER_SPEC.md` §8, with LibreOffice
present. `test_recalc_unavailable_fails_closed` proves the suite is not vacuous.
`test_forecast_complete_requires_every_requested_period` refuses a missing,
duplicate, extra or unavailable case-period; a full horizon with an explicitly
unavailable zero-denominator ratio remains valid. An independently wrong
residual and forward propagation are exercised by
`test_forecast_residual_is_not_forced_to_zero` and
`test_forecast_unavailability_propagates`.
`test_overlay_renders_from_ir_without_reusing_a_workbook` protects the overlay
boundary in `SYSTEM_SPEC.md` §6.
