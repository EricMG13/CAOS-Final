# CP-DR | Deep Research Contract Schema
# Version: 1.0 | 2026-07-21

## Identity

| Field | Value |
|---|---|
| module_id | CP-DR |
| module_name | DeepResearch |
| module_type | Analytical — issuer or sector research |
| owned_object | research_dossier |
| layer | none — positioned by the research brief |

## Required input

The canonical brief contains `schema`, `mode`, `run_id`, `scope_type`, `scope_key`, `subject_name`, `decision_context`, `as_of_date`, `time_horizon`, `exclusions`, `source_mode`, `budget`, `authorization_basis` and a bounded `questions` list. Linked research additionally binds `cp0_sha256` and `authority_sha256`, and requires current CP-0 plus named predecessors. Standalone research has no CP-0 requirement.

## Required output-envelope extension

| Field | Type / enum |
|---|---|
| research_mode | `linked` or `standalone` |
| scope_type | `issuer` or `sector` |
| scope_key | non-empty scalar used in filenames |
| subject_name | non-empty string |
| research_question | non-empty string |
| source_mode | `supplied_only`, `web_only`, or `hybrid` |
| approved_plan_hash | `sha256:` plus 64 lowercase hex characters |
| coverage_score | integer 0–100 |
| research_status | `Complete`, `Complete with Gaps`, or `Blocked` |
| research_stop_reason | `coverage_satisfied`, `budget_exhausted`, `sources_exhausted`, `blocked`, or `user_stopped` |

For issuer scope, `issuer_name` and `issuer_id` may also be supplied. They are not required for sector scope. `qa_status: Blocked` remains the fail-closed projection gate and caps confidence at 39.

## Artifacts

| Artifact | Filename | Rule |
|---|---|---|
| canonical Markdown handoff | `[ScopeKey]_CP-DR_[YYYYMMDD].md` | Sole analytical output; author and validate fail-closed |

The handoff uses the six canonical H2 headings. New CP-SR outputs are prohibited; prior CP-SR reports may appear only in the source registry with historical provenance.

## Routing

The run-specific brief names factual predecessors and selected canonical receiving owners. No retired aliases or fixed late layer. Require TDR.1 / cpdr.questions, TDR.2 / cpdr.evidence and TDR.3 / cpdr.findings, plus cpdr.adoptions in each receiver. Exact fields and validation are defined in `../../cp-os-credit-os/references/CP_DR_RESEARCH_BRIEF_V1.md`.
