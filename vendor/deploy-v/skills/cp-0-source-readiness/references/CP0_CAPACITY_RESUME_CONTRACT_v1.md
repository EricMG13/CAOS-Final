<!-- CP-0 Deploy V Capacity & Resume Contract | v1.0 | 2026-08-04 -->
<cp0_capacity_resume_contract deployment="V" module="CP-0" enforcement="hard">
# CP-0 capacity, batching and resume contract

This contract is injected only into the generated Deploy V CP-0 package. It is
binding whenever the complete triage set cannot be parsed safely within one
execution window. It changes neither CP-0's module identity nor its output
ownership: `module_id=CP-0` remains the sole analytical handoff identity.
For `IN_PROGRESS` and `READY_FOR_FINALIZATION` only, this narrower Deploy V
gate supersedes the shared runbook's ordinary requirement that every pipeline
run emit canonical Markdown; final or blocked readiness remains governed below.

## Capacity preflight

After inventory and frozen triage, but before extraction, record the immutable
logical `run_id`, the SHA-256 of the ordered original-source inventory, the
host/tool limits used for planning, the selected parse-job count and the
estimated bytes/pages/work units. Classify the plan as `SINGLE_WINDOW`,
`MULTI_WINDOW` or `BLOCKED`. A limit may come from the host, the parsing tool or
a labelled conservative default, but every active limit must be a positive
integer and its source must be recorded.

Page count and file size are capacity inputs, never evidence-value proxies.
Triage remains downstream-aware: short controlling documents may outrank large
appendices, and unique lender presentations retain their narrative requirement.

## Deploy V runtime payload addendum

The shared CP-0 payload remains unchanged for Deploys A/B. Deploy V validates
these additional required runtime fields:

| Location | Required contract |
|---|---|
| `pipeline.execution_state` | `IN_PROGRESS`, `READY_FOR_FINALIZATION`, `FINALIZED` or `BLOCKED` |
| `capacity_plan` | command-safe `run_id` (`[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`), frozen `source_set_sha256` and `batch_plan_sha256`, `limit_source`, recognized positive-integer limits (`max_source_bytes`, `max_batch_bytes`, `max_batch_pages`, `max_batch_sources`, `max_execution_seconds`, `max_work_units`), estimates, `capacity_outcome`, required-job count, planned-batch count and `all_required_jobs_terminal` |
| `parse_batches[]` | contiguous `BATCH-NNN`, sequence, status, logical source IDs and non-empty auditable work boundaries |
| `checkpoint` | matching run/source/batch-plan identities, managed `checkpoint_path`, positive sequence, state/previous hashes, exact completed batches, next batch and exact resume command |
| `parse_jobs[]` extension | `batch_ids`, positive `work_unit_count`, bounded `completed_work_unit_count`; status also permits `QUEUED`/`IN_PROGRESS`, with `coverage_status=PENDING` |
| `representation_catalog[]` extension | parse status also permits `QUEUED`/`IN_PROGRESS`; pending rows have no active or selected content |
| `readiness_summary.finalized` | true only for `FINALIZED` or `BLOCKED` |

The Deploy V CP-0 validator is the executable authority for cross-row alignment,
source-set hashing, checkpoint reconciliation and state-transition gates.

## Deterministic parse work

Create a complete ordered batch plan before the first parse. Each batch has a
stable `BATCH-NNN` ID, sequence, status, source IDs and auditable work boundaries
(page, slide, sheet/range, clause or section). Every selected parse source occurs
in at least one batch. A single oversized source may span several execution
batches, but its prepared artifact is not selected until its work units are
reassembled and fidelity/coverage QA reaches a terminal result.

Parse jobs and execution batches use `QUEUED`, `IN_PROGRESS`, `COMPLETE`,
`DEGRADED` or `BLOCKED`. `COMPLETE`, `DEGRADED` and `BLOCKED` are terminal.
Pending work has no active content representation and supplies no readiness
content. A required parse never silently falls back to the original.

Execution batches are not evidence ZIP batches. Evidence ZIPs remain final,
reconciled supporting packages and keep one source's complete output set
together; do not emit them while the logical run is in progress.

## Checkpoint and resume

After every execution batch, atomically persist a checkpoint in the managed run
workspace. It records `run_id`, source-set SHA-256, monotonic checkpoint sequence,
state SHA-256, previous-checkpoint SHA-256, completed batch IDs, next batch ID and
the exact resume command. Reject a resume if the run ID, source-set hash,
checkpoint chain, original hashes or batch plan differs from the frozen values.
The resume command must match the grammar below in full—with no suffix—and its
absolute checkpoint path must resolve inside the managed run workspace.

For pending parse work, the exact command starts:

`Run CP-0 [mode: parse_only] [run_id: <run_id>] [resume_from: <checkpoint>]`

After all required parse jobs are terminal, finalization occurs in the same
execution window when capacity permits. Otherwise persist `READY_FOR_FINALIZATION`
and return:

`Run CP-0 [mode: readiness_only] [run_id: <run_id>] [resume_from: <checkpoint>]`

Managed artifacts and checkpoint state pass directly between phases. The user
does not copy derivatives back into a source folder or reattach them.

## Readiness gate

The logical run state is `IN_PROGRESS`, `READY_FOR_FINALIZATION`, `FINALIZED` or
`BLOCKED`.

- `IN_PROGRESS`: at least one required parse job is queued or running. Return
  only progress, limitations and the exact CP-0 resume command. Emit no canonical
  CP-0 analytical handoff, model-route assertion or downstream module command;
  readiness remains `CONDITIONAL`.
- `READY_FOR_FINALIZATION`: all required parse jobs are terminal, but readiness
  has not been frozen. Return only the exact CP-0 readiness-only command.
- `FINALIZED`: every required parse is terminal, batch/checkpoint reconciliation
  passes, the effective-source catalog is frozen and the canonical CP-0 Markdown
  may be emitted with downstream readiness.
- `BLOCKED`: execution cannot continue safely or a required terminal parse is
  blocked. Any required blocked parse forces this logical state. Surface the
  exact gap/remediation and issue no executable downstream command.

`DEGRADED` is terminal only when the prepared representation remains usable and
every limitation and downstream effect is explicit. Otherwise use `BLOCKED`.
CP-0 still may assert only source sufficiency for the CP-MODEL route and never
`CP_MODEL_INPUT_READY`.
</cp0_capacity_resume_contract>
