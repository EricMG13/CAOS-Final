# CP-L20 Schema Reference

## Identity

`CP-L20 | LiteFundamentalCreditScreen | lite_fundamental_credit_screen | Nested | CANONICAL_MARKDOWN | SCREENING_ONLY`

Covered owner notation: CP-2 | CP-2C | CP-2F. Joint policy notation: CP-2 | CP-2C.

## Canonical topics

| Topic ID | Label | Exact source owners | Default FULL upgrade owner |
|---|---|---|---|
| `BUSINESS_DURABILITY` | Business durability | CP-2 | CP-2 |
| `MARGIN_FCF_RESILIENCE` | Margin and FCF resilience | CP-2 | CP-2 |
| `LEVERAGE_REFINANCING_CONTEXT` | Leverage and refinancing context | CP-2 | CP-2 |
| `GOVERNANCE_SPONSOR_BEHAVIOR` | Governance and sponsor behavior | CP-2C | CP-2C |
| `FINANCIAL_POLICY_CAPITAL_ALLOCATION` | Financial policy and capital allocation | CP-2, CP-2C | CP-2C |
| `ESG_TRANSITION` | ESG and transition transmission | CP-2F | CP-2F |

Each topic appears exactly once. Source owners and upgrade IDs are limited to CP-2, CP-2C, and CP-2F.

## Required tables

| ID | Name | Exact columns |
|---|---|---|
| `TL20.1` | Source and Scope Gate | subject_identity; source_ref; source_owner_module; as_of_or_period; scope_status; topics_supported; limitation |
| `TL20.2` | Topic Allocation Register | topic_id; topic_label; source_owner_modules; materiality; evidence_status; disposition; priority_rank; summary; source_refs; upgrade_module_ids |
| `TL20.3` | Decision Screen | screen_item; assessment; evidence; credit_transmission; screening_implication; confidence; source_refs |
| `TL20.4` | Gaps and Upgrade Register | topic_id; trigger; missing_inputs; decision_impact; required_source; target_full_module_id; expected_owned_object; blocking_for_full_decision |

`TL20.3` requires an `OVERALL` row. No FULL table ID is part of this schema.

## Runtime output

Required common fields: `decision_scope`, `execution_basis`, `screen_status`, `screen_conclusion`, `source_scope_gate`, `topic_allocation`, `cross_topic_synthesis`, `upgrade_plan`, and `gaps_conflicts`. Optional execution telemetry may be supplied without a prescribed budget.

Required CP-L20 fields: `screening_posture`, `decision_screen`, `gap_upgrade_register`, and `table_inventory`.

`screening_posture` is exactly `SUPPORTIVE | BALANCED | PRESSURED | MIXED | INSUFFICIENT_INFORMATION`. Runtime output rejects unknown properties and `committee_memo` explicitly.

## Authority and QA

The artifact cannot own the full CP-2 synthesis, a scorecard, a governance or sponsor score, an ESG score, a legal conclusion, a formal rating, or an instrument recommendation. Validate the exact topics and owners, evidence trace, qualitative dispositions, affirmative immateriality evidence, gap detail, upgrade coverage, table inventory, canonical Markdown identity, and provisional confidence. Output depth and length are evidence-proportionate and uncapped by this authority.

## Export

Author exactly one validated canonical Markdown handoff under `../../../CANON_SHARED.md § CP_AB_EXPORT_SPEC.md`; no alternate analytical export.
