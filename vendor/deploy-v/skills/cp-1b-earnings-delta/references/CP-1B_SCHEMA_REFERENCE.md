<!-- CP-1B Schema Reference (T3) | 2026-06-02 -->
`cp1b.cp_model_snapshot_fields` contains the single source-grounded
`historical_performance` workbook field on every run.

## CP-MODEL projection profile

The CP-MODEL profile, emitted on every run, comprises
`cp1b.model_comparator_register`, `cp1b.model_validation_register`,
`cp1b.addback_validation_register`, `cp1b.model_readiness` and
`cp1b.cp_model_snapshot_fields`. The snapshot columns are `field_id | value |
status | source_id | source_locator | as_of` and contain exactly one `READY`
`historical_performance` row. These projections validate and interpret CP-1;
they never overwrite CP-1 numeric authority or substitute for the 15 required
analytical tables.

## Required Tables (15)
| ID | Table | Key Columns |
|----|-------|-------------|
| T4.1 | Source Classification Register | Source File Name, Document Type, Period Coverage, Evidence Quality Tier, Analytical Use, Limitations |
| T4.2 | Definition Inheritance | Metric Name, CP-1 Canonical Def, CP-1 Formula, EBITDA Def in Use, Inheritance Status, Conflict Note |
| T4.3 | Summary / Top-Sheet | Row Label, Value/Observation (13 rows) |
| T4.4 | Financial Performance | Line Item, Period 1…N, YoY Abs/%, Analyst Note (19 lines) |
| T4.5 | KPI Dashboard | KPI Category, Metric, Period 1…N, YoY Change, Trend, Calc Status, Note |
| T4.6 | Variance Register | Metric, Basis, Prior/Current, Abs/%, Mgmt/Analyst Driver, Credit Implication |
| T4.7 | Corporate Actions | Event, Date, Description, Impact, Comparability Effect, Credit Implication, Source |
| T4.8 | Comparative Evaluation | Metric, Benchmark Source/Type, Expected/Actual, Variance, Credit Implication |
| T4.9 | Conflict Log | Conflict, Sources, Metrics, Periods, Materiality, Resolution, Downstream Impact |
| T4.10 | Monitoring Assessment | Signal Type, Metric, Evidence, Severity, Credit Implication, Action |
| T4.11 | Gaps & Limitations | Gap, Affected Metric, Periods, Downstream Impact, Severity, Action |
| T4.12 | Model Comparator Register | metric_id, current/reference period IDs, basis, values, changes, status, comparability flags |
| T4.13 | Model Validation Register | metric_id, period_id, CP-1 value, comparison value, difference, tolerance, status, explanation |
| T4.14 | Add-back Validation Register | addback_id, period_id, CP-1/comparison values, tolerance, status, label/definition checks |
| T4.15 | Model Readiness | downstream module, status, blocking metric/period IDs, conflicts, explanation |

## QA Checklist
- [ ] CP-1 defs inherited/confirmed  - [ ] All 15 tables present on every run  - [ ] Calcs traceable  - [ ] Content distinctions maintained  - [ ] No def switching  - [ ] Variance bases explicit  - [ ] Gaps cumulative in T4.11  - [ ] CP-1/CP-1B keyed values and issuer-specific add-backs validated without override  - [ ] Numeric Confidence Score (0–100) + band emitted per CP_CONFIDENCE_SCORE.md  - [ ] Canonical Markdown valid; the Markdown handoff pass view-appropriate parity  - [ ] Null ≠ zero

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
