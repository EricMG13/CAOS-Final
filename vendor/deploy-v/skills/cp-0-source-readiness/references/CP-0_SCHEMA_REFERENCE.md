<!-- CP-0 Schema Reference | v3.1 | 2026-08-04 -->
<schema_reference module="CP-0" tier="3">
# CP-0 source-readiness schema

Stable identity: `module_id=CP-0`, `module_name=SourceReadiness`, `owned_object=source_readiness_register`. The internal preparation phase owns `document_parse_manifest` within CP-0.

## Core objects

| ID | Object | Purpose |
|---|---|---|
| T1 | Input Gate | objective, issuer, period, same-run preparation validation and validation status |
| T2 | Source Register | original authority plus active-representation quality and usability |
| T3 | Source Hierarchy | source class, authority rule, presence and missing minimum |
| T4 | Content-to-Module Map | active representation, evidence demand and readiness effect |
| T5 | Gaps/Conflicts | gaps, conflicts, severity, affected modules and remediation |
| T6 | Evidence Trace | evidence ID, original source, active representation and locator |
| T7 | Master Index State | run, upstream preparation, outputs, warnings and consumers |
| T8 | Recommended Run Command Sheet | live host ID, candidate command, safe exact command, upstream handoff and active source attachments |

## Readiness invariants

- same-run preparation validation, inventory coverage, hashes, package validation and representation uniqueness pass before readiness begins.
- Readiness consumes the frozen same-run preparation catalog; changed sources return to preparation before readiness.
- A blocked preparation has no content fallback; changed or absent sources return to the internal preparation phase.
- Authority belongs to the original source; extraction confidence and fidelity belong to the active representation.
- Each consumer receives an objective-specific readiness status and limitation, not a pack-level source-count proxy.
- T8 uses canonical live navigable host IDs only; CP-X, CP-PARSE, retired aliases, CP-MODEL, CP-MEMO and CP-DR are never recommendation rows.
- Every T8 row carries `candidate_command`; non-runnable rows retain `exact_command=DO NOT RUN`.
- A downstream handoff launched from T8 retains the selected CP-0 `run_id` in `upstream_artifacts_used`.

## CP-MODEL boundary

CP-0 may emit only `SOURCE_READY_FOR_MODEL_ROUTE`, `assertion_scope=SOURCE_SUFFICIENCY_ONLY`, required analytical route `[CP-1, CP-1A, CP-1B, CP-2, CP-2A]`, optional `[CP-2G]`, and `cp_model_input_contract=NOT_EVALUATED`. Never route directly to CP-MODEL.

## Analysis sections

Readiness conclusion; validated preparation lineage; source authority and coverage; content-to-module map; gaps/conflicts; downstream readiness; recommended commands; Master Index; QA.

## QA and export

Canonical `[IssuerID]_CP-0_[YYYYMMDD].md` is the only CP-0 handoff. Preserve the canonical YAML plus six H2 sections in `CP_AB_EXPORT_SPEC.md`; retain T1-T8 losslessly in the analytical appendix. Validated prepared packages remain supporting evidence for the one CP-0 handoff.
</schema_reference>
