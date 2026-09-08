# CP-L40 Schema Reference

## Identity

`CP-L40 | LiteLegalStructureCapacityScreen | lite_legal_structure_capacity_screen | Nested | CANONICAL_MARKDOWN | SCREENING_ONLY`

Covered owner notation: CP-4 | CP-4B | CP-4A. Leakage notation: CP-4 | CP-4B.

## Canonical topics

| Topic ID | Label | Exact source owners | Default FULL upgrade owner |
|---|---|---|---|
| `CONTROLLING_DOCUMENT_AVAILABILITY` | Controlling-document availability | CP-4 | CP-4 |
| `PROTECTION_WEAKNESS_FLAGS` | Protection and weakness flags | CP-4 | CP-4 |
| `ENTITY_GUARANTEE_COLLATERAL` | Entity, guarantee, and collateral coverage | CP-4B | CP-4B |
| `LEAKAGE_PRIMING_FLAGS` | Leakage and priming flags | CP-4, CP-4B | CP-4B |
| `CAPACITY_AVAILABILITY` | Capacity availability | CP-4A | CP-4A |
| `PRESSURE_POINT_UPGRADE_PRIORITY` | Pressure point and upgrade priority | CP-4A | CP-4A |

Each topic appears exactly once. Source owners and upgrade IDs are limited to CP-4, CP-4B, and CP-4A.

## Required tables

| ID | Name | Exact columns |
|---|---|---|
| `TL40.1` | Source and Scope Gate | subject_identity; source_ref; source_owner_module; as_of_or_period; scope_status; topics_supported; limitation |
| `TL40.2` | Topic Allocation Register | topic_id; topic_label; source_owner_modules; materiality; evidence_status; disposition; priority_rank; summary; source_refs; upgrade_module_ids |
| `TL40.3` | Decision Screen | screen_item; assessment; evidence; credit_transmission; screening_implication; confidence; source_refs |
| `TL40.4` | Gaps and Upgrade Register | topic_id; trigger; missing_inputs; decision_impact; required_source; target_full_module_id; expected_owned_object; blocking_for_full_decision |

`TL40.3` requires an `OVERALL` row. No FULL table ID is part of this schema.

## Runtime output

Required common fields: `decision_scope`, `execution_basis`, `screen_status`, `screen_conclusion`, `source_scope_gate`, `topic_allocation`, `cross_topic_synthesis`, `upgrade_plan`, and `gaps_conflicts`. Optional execution telemetry may be supplied without a prescribed budget.

Required CP-L40 fields: `screening_posture`, `decision_screen`, `gap_upgrade_register`, and `table_inventory`.

`screening_posture` is exactly `LOWER_CONCERN | WATCH | HEIGHTENED_CONCERN | MIXED | INSUFFICIENT_INFORMATION`. Runtime output rejects unknown properties and `exact_capacity` explicitly.

## Authority and QA

The artifact cannot own legal advice, definitive interpretation, covenant aggressiveness, structural-priority ranking, exact capacity/headroom, compliance, or recovery dollars. Validate exact document/source identity, topics and owners, evidence trace, qualitative dispositions, affirmative immateriality evidence, gap detail, upgrades, posture, table inventory, and canonical artifact identity. Output depth and length are evidence-proportionate and uncapped by this authority.

## Export

Author exactly one validated canonical Markdown handoff under `../../../CANON_SHARED.md § CP_AB_EXPORT_SPEC.md`; no alternate analytical export.
