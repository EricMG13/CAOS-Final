# Rebuild plan

Eleven phases (0–10). Each has an exit test — a named, runnable check that fails
before the phase and passes after. A phase is not done because the code exists;
it is done when its exit test passes and the prior phases' tests still pass.

Order is chosen so the thing most likely to be wrong is built earliest, when it
is cheapest to change. The predecessor reached 29k lines of server code before
anyone noticed its route resolution read the wrong table.

---

## Phase 0 — Repository and gates

Before any application code. The controls in `docs/AI_CODE_QUALITY.md` must
exist before the code they govern.

- `pyproject.toml` with hashed, fully pinned locks; `Makefile`;
  `.claude/settings.json` with the format and guard hooks.
- CI: `lint · types · test · security · image`. Pre-commit with ruff, gitleaks,
  the vocabulary check.
- SonarQube Cloud bound to the repository (DECISIONS.md §30).
- `scripts/check_vocabulary.py`, `scripts/io_budget.py`, `scripts/scan_floors.py`.

**Exit:** an empty PR that adds one unformatted, unnamed, untested function is
refused by CI for all four reasons separately.

## Phase 1 — Store, events, boundary text

- Postgres schema in full at startup. Blob store, content-addressed.
- `run_events` with per-run monotonic `seq` under the run row lock.
- Transactional pairing: state + event, on a conditional update.
- `BoundaryText`; typed refusal codes with no vendor or filesystem detail.

**Exit:** `test_terminal_event_is_exactly_once` — a simulated crash in the
commit gap yields one artifact, one charge, one terminal event.
`test_boundary_text_rejects_bidi_override`.

## Phase 2 — Ingestion, tokens, evidence

- Admit a pack or refuse it, in one transaction. Extract text with page and
  rectangle per token into `source_tokens`. Pack `source_blocks` keyed by
  `(source_id, block_id)`.
- Source-set versioning under the case row lock.
- `read_evidence`: validated at the boundary, fails closed, returns no text on
  refusal.
- Citation anchoring: re-locate `matched_text` at the stated page, derive the
  rectangle, refuse what cannot be located.

**Exit:** `test_evidence_refusals_return_no_text` over the whole argument
surface; `test_uncitable_quote_is_refused_before_artifact`;
`test_io_budget_read_evidence` (the ~8× I/O failure mode — one read is one
row fetch, not a whole-source parse).

## Phase 3 — Route resolution

The phase the predecessor got wrong. Build it before anything depends on it.

- Read `profile["edges"]`. Implement `dependency_order`, `active_incoming`,
  `node_states`, `frontier`, `expected_upstream_digests`.
- Soft edges harden when the source is READY.
- Research and model route extensions, host-declared, no catalog edit.
- `resolve_route` pure; `pin_route` at the gate.

**Exit:** `test_optional_edge_does_not_block`,
`test_optional_edge_blocks_when_source_ready`,
`test_qa_gate_blocks_cp6_until_cp5_accepted`,
`test_restricted_node_runs_and_carries_limitation`,
`test_resolved_route_is_pinned_and_replays_identically`,
`test_cp_cf_waits_for_all_required_owners`,
`test_model_extension_refuses_missing_owner`.

## Phase 4 — The frontier loop

- `while frontier(...)`: run ready nodes concurrently, one attempt row per try.
- Recovery is recomputation from accepted attempts. No checkpointer.
- Budget reservation before any provider call; reconciliation after.

**Exit:** `test_recovery_is_recomputation` — kill mid-run, restart, the run
completes without restarting completed nodes and without a checkpoint file.
Plus the three the provider-call contract owes (`docs/DECISIONS.md` §21):
`test_crash_after_remote_completion_keeps_its_reservation`,
`test_a_retry_without_provider_idempotency_reserves_again` and
`test_concurrent_reservations_at_the_ceiling_refuse`.

## Phase 5 — Methodology boundary and one module end to end

- Bundle verification on the bytes at use; `assemble_authority` **without**
  SKILL.md slicing; per-module `authority_digest`.
- Registry with `_ALIASES`, including the CP-PARSE carve-out and its wiring test.
- Calculator execution boundary with host-owned selection and work factors.
- CP-1 running against a real provider, producing a canonical envelope.

**Exit:** `test_authority_bytes_mismatch_refuses`;
`test_cp1_produces_canonical_envelope_with_anchored_citations`.

## Phase 6 — Gates and the run surface

- Digest-bound interrupts: source-set pinning, research-plan approval.
- Acceptance as a CAS transaction.
- SSE tail with `Last-Event-ID`; membership rechecked per event.
- `/run/` renders node states with their reasons, and the one QA_GATE reads as
  a gate.

**Exit:** `test_approval_binds_the_exact_reviewed_content`;
`test_sse_closes_after_terminal_delivery`.

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

## Phase 8 — Publication

- CP-MEMO: ten fixed sections, editorial boundary enforced, conflicts preserved,
  one `.docx`, never overwriting.
- Publication gate: inventory → draft → per-page visual QA → publish.
- Opinion on the exact revision; freeze; filing refusing the signer and the
  freezer; detached receipt; hash-chained audit; verifiable package.

**Exit:** `test_publish_refused_until_every_page_passes`;
`test_filing_refuses_the_opinion_signer`;
`test_audit_package_verifies_with_stdlib_alone`.

## Phase 9 — The workspace

`docs/IA_SPEC.md` in full. Nine sections, one word each, static export.

- The four chrome bands on every section; the nine-section rail with counts and
  one-line state; served role read-only beside it.
- Analysis, Book (metric passport, ten fields), Model (projection with the
  residual column), Committee (CP-MEMO and its gate).
- Every decision state rendered distinctly.

**Exit:** `npm run a11y` and `npm run test:workbench` green on three engines;
`test_passport_contract` asserts all ten fields on an actual and on a projected
cell.
`test_book_binds_one_snapshot_per_compared_case` compares two issuers and
refuses a late response carrying a different snapshot for either one.

## Phase 10 — Qualification

- The corpus harness, the answer keys, the matrix.
- A verdict is bound to provider identity, corpus digest, build, date, expiry
  and reviewer.

**Exit:** a host-control binding reads `ORCHESTRATION_PROOF`, never `QUALIFIED`.
Live qualification remains an external input until the credential and the
analyst approvals exist.

---

## Standing rules across all phases

- Test first. The failing test names the invariant.
- One concern per PR.
- A new limitation gets a `CLAUDE.md` known-gaps entry in the same PR that
  creates it.
- No new dependency without a dated `DECISIONS.md` entry.
- Never edit an upstream bundle file.
- The first phase exposing an HTTP route also ships the actor matrix for that
  route. `test_production_never_trusts_role_header`,
  `test_unauthorised_case_is_private_404` and
  `test_membership_revocation_refuses_commit` enforce `SYSTEM_SPEC.md` §8;
  production identity and commit-time authority checks do not wait for the
  workspace or qualification phases.

## What is deliberately not in the plan

A checkpointer. A second database. A message broker. An admin UI. Multi-instance
deployment. Each is a decision entry away if it earns its place; none is
scaffolded ahead of need.
