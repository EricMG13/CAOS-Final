# CP-L30 Schema Reference

## Identity

`CP-L30 | LiteMarketRecoveryOpportunityScreen | lite_market_recovery_opportunity_screen | Nested | CANONICAL_MARKDOWN | SCREENING_ONLY`

Covered owner notation: CP-3D | CP-3A | CP-3. Compensation notation: CP-3D | CP-3. Downside notation: CP-3A | CP-3.

## Canonical topics

| Topic ID | Label | Exact source owners | Default FULL upgrade owner |
|---|---|---|---|
| `DATED_MARKET_SNAPSHOT` | Dated market snapshot | CP-3D | CP-3D |
| `CURVE_COMPARABLE_COMPENSATION` | Curve and comparable compensation | CP-3D, CP-3 | CP-3D |
| `LIQUIDITY_TECHNICALS` | Liquidity and technicals | CP-3D | CP-3D |
| `STRUCTURAL_RECOVERY_PROTECTION` | Structural and recovery protection | CP-3A | CP-3A |
| `DOWNSIDE_LME_EXPOSURE` | Downside and LME exposure | CP-3A, CP-3 | CP-3A |
| `INTEGRATED_SCREENING_POSTURE` | Integrated screening posture | CP-3D, CP-3A, CP-3 | CP-3 |

Each topic appears exactly once. Source owners and upgrade IDs are limited to CP-3D, CP-3A, and CP-3.

## Required tables

| ID | Name | Exact columns |
|---|---|---|
| `TL30.1` | Source and Scope Gate | subject_identity; source_ref; source_owner_module; as_of_or_period; scope_status; topics_supported; limitation |
| `TL30.2` | Topic Allocation Register | topic_id; topic_label; source_owner_modules; materiality; evidence_status; disposition; priority_rank; summary; source_refs; upgrade_module_ids |
| `TL30.3` | Decision Screen | screen_item; assessment; evidence; credit_transmission; screening_implication; confidence; source_refs |
| `TL30.4` | Gaps and Upgrade Register | topic_id; trigger; missing_inputs; decision_impact; required_source; target_full_module_id; expected_owned_object; blocking_for_full_decision |

`TL30.3` requires an `OVERALL` row. No FULL table ID is part of this schema.

## Runtime output

Required common fields: `decision_scope`, `execution_basis`, `screen_status`, `screen_conclusion`, `source_scope_gate`, `topic_allocation`, `cross_topic_synthesis`, `upgrade_plan`, and `gaps_conflicts`. Optional execution telemetry may be supplied without a prescribed budget.

Required CP-L30 fields: `screening_posture`, `decision_screen`, `gap_upgrade_register`, and `table_inventory`.

`screening_posture` is exactly `ESCALATE_FOR_FULL_SELECTION | MONITOR | DEPRIORITIZE | INSUFFICIENT_INFORMATION`. Runtime output rejects unknown properties and `buy_sell_hold` explicitly.

## Authority and QA

The artifact cannot own Buy/Sell/Hold, a preferred instrument, fair value, security rank, composite score, recovery value, or position size. Validate exact security/date/source basis, six topics and owners, evidence trace, qualitative dispositions, gap/immutability evidence, upgrade coverage, posture, table inventory, and canonical artifact identity. Output depth and length are evidence-proportionate and uncapped by this authority.

## Export

Author exactly one validated canonical Markdown handoff under `../../../CANON_SHARED.md § CP_AB_EXPORT_SPEC.md`; no alternate analytical export.
