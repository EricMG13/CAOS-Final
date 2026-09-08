# CP-L23 Schema Reference

## Identity

`CP-L23 | LiteLiquiditySensitivityScreen | lite_liquidity_sensitivity_screen | Nested | CANONICAL_MARKDOWN | SCREENING_ONLY`

Covered owner notation: CP-2D | CP-2E | CP-2G.

## Canonical topics

| Topic ID | Label | Exact source owners | Default FULL upgrade owner |
|---|---|---|---|
| `ACCESSIBLE_LIQUIDITY_USES` | Accessible liquidity and uses | CP-2D | CP-2D |
| `WORKING_CAPITAL_CAPEX_CASH_BURN` | Working capital, capex, and cash burn | CP-2D | CP-2D |
| `RATES_HEDGES` | Rates and hedges | CP-2E | CP-2E |
| `FX_COMMODITY_INFLATION` | FX, commodity, and inflation | CP-2E | CP-2E |
| `BASE_DOWNSIDE_TRAJECTORY` | Base and downside trajectory | CP-2G | CP-2G |
| `BREAKPOINTS_REFINANCING` | Breakpoints and refinancing | CP-2D, CP-2E, CP-2G | CP-2G |

Each topic appears exactly once. Source owners and upgrade IDs are limited to CP-2D, CP-2E, and CP-2G.

## Required tables

| ID | Name | Exact columns |
|---|---|---|
| `TL23.1` | Source and Scope Gate | subject_identity; source_ref; source_owner_module; as_of_or_period; scope_status; topics_supported; limitation |
| `TL23.2` | Topic Allocation Register | topic_id; topic_label; source_owner_modules; materiality; evidence_status; disposition; priority_rank; summary; source_refs; upgrade_module_ids |
| `TL23.3` | Decision Screen | screen_item; assessment; evidence; credit_transmission; screening_implication; confidence; source_refs |
| `TL23.4` | Gaps and Upgrade Register | topic_id; trigger; missing_inputs; decision_impact; required_source; target_full_module_id; expected_owned_object; blocking_for_full_decision |

`TL23.3` requires an `OVERALL` row. No FULL table ID is part of this schema.

## Runtime output

Required common fields: `decision_scope`, `execution_basis`, `screen_status`, `screen_conclusion`, `source_scope_gate`, `topic_allocation`, `cross_topic_synthesis`, `upgrade_plan`, and `gaps_conflicts`. Optional execution telemetry may be supplied without a prescribed budget.

Required CP-L23 fields: `screening_posture`, `decision_screen`, `gap_upgrade_register`, and `table_inventory`.

`screening_posture` is exactly `ADEQUATE_SCREEN | WATCH | PRESSURED | MIXED | INSUFFICIENT_INFORMATION`. Runtime output rejects unknown properties and `twelve_month_liquidity_bridge` explicitly.

## Authority and QA

The artifact cannot own a 12-month bridge, months-to-empty calculation, full forecast or scenario engine, assumed facility/hedge access, silent plug, or CP-MODEL table. Validate topic identity and owners, evidence trace, accessibility limitations, gap detail, affirmative immateriality evidence, upgrade coverage, four-table inventory, and canonical artifact identity. Output depth and length are evidence-proportionate and uncapped by this authority.

## Export

Author exactly one validated canonical Markdown handoff under `../../../CANON_SHARED.md § CP_AB_EXPORT_SPEC.md`; no alternate analytical export.
