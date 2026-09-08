# CP-L10 Schema Reference

## Identity

`CP-L10 | LiteFinancialChangeScreen | lite_financial_change_screen | Nested | CANONICAL_MARKDOWN | SCREENING_ONLY`

Covered owner notation: CP-1 | CP-1B.

## Canonical topics

| Topic ID | Label | Exact source owners | Default FULL upgrade owner |
|---|---|---|---|
| `SOURCE_BASIS` | Source and basis | CP-1, CP-1B | CP-1 |
| `EARNINGS_MARGIN_CHANGE` | Earnings and margin change | CP-1B | CP-1B |
| `CASH_CONVERSION` | Cash conversion | CP-1, CP-1B | CP-1B |
| `LEVERAGE_COVERAGE` | Leverage and coverage | CP-1, CP-1B | CP-1B |
| `LIQUIDITY_MATURITIES` | Liquidity and maturities | CP-1, CP-1B | CP-1 |
| `KPI_COMPARABILITY` | KPI and comparability quality | CP-1, CP-1B | CP-1B |

Each topic appears exactly once. Source owners and upgrade IDs are limited to CP-1 and CP-1B.

## Required tables

| ID | Name | Exact columns |
|---|---|---|
| `TL10.1` | Source and Scope Gate | subject_identity; source_ref; source_owner_module; as_of_or_period; scope_status; topics_supported; limitation |
| `TL10.2` | Topic Allocation Register | topic_id; topic_label; source_owner_modules; materiality; evidence_status; disposition; priority_rank; summary; source_refs; upgrade_module_ids |
| `TL10.3` | Decision Screen | screen_item; assessment; evidence; credit_transmission; screening_implication; confidence; source_refs |
| `TL10.4` | Gaps and Upgrade Register | topic_id; trigger; missing_inputs; decision_impact; required_source; target_full_module_id; expected_owned_object; blocking_for_full_decision |

`TL10.3` requires an `OVERALL` row. No FULL table ID is part of this schema.

## Runtime output

Required common fields: `decision_scope`, `execution_basis`, `screen_status`, `screen_conclusion`, `source_scope_gate`, `topic_allocation`, `cross_topic_synthesis`, `upgrade_plan`, and `gaps_conflicts`. Optional execution telemetry may be supplied without a prescribed budget.

Required CP-L10 fields: `screening_posture`, `decision_screen`, `gap_upgrade_register`, and `table_inventory`.

`screening_posture` is exactly `IMPROVING | STABLE | DETERIORATING | MIXED | INSUFFICIENT_INFORMATION`. Runtime output rejects unknown properties and `canonical_financial_history` explicitly.

## Authority and QA

The artifact cannot own canonical numeric history, normalized financials, CP-1 definitions, CP-1B stable tables, or CP-MODEL fields. Validate six unique topics, qualitative dispositions, source trace, affirmative immateriality evidence, structured gap detail, upgrade coverage, the four-table inventory, exact filename identity, canonical headings, and provisional confidence. Output depth and length are evidence-proportionate and uncapped by this authority.

## Export

Author exactly one validated canonical Markdown handoff under `../../../CANON_SHARED.md § CP_AB_EXPORT_SPEC.md`; no alternate analytical export.
