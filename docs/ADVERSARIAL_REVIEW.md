# Adversarial review — application build contracts

Date: 2026-09-08. Skills: `adversarial-reviewer`, `senior-architect`,
`confidence-review`.

**Scope:** all eleven pre-existing Markdown contract, specification and design
files read in full. The concurrent Phase 0 implementation was inspected initially, then
excluded from changes and this verdict at the user's direction. No application
runtime, vendored methodology bundle or rendered frontend exists in this
checkout to validate. This is a specification review, not runtime qualification.

**Verdict: BLOCK** on treating the specifications as a complete implementation
contract. *(All four open findings were closed on 2026-09-08 -- see the status
line under each. The verdict is left as written; the record is the point.)* The open findings below need resolution before their affected phases;
they do not prevent independent store work. Three existing specification files
were corrected. The other task's implementation and Git state were left alone.

Personas ran in order: Saboteur (execution and calculation failure paths), New
Hire (cross-document contracts and phase dependencies), Security Auditor
(authority and trust boundaries). Shared findings are promoted one level, as
the review skill requires. Severity describes the build risk, not a claim that
a deployed vulnerability was observed.

## Critical findings — both resolved

### C1. Provider-call uncertainty has no recovery/accounting contract

**Location:** [System §4](SYSTEM_SPEC.md#4-route-resolution-and-execution),
[System §11](SYSTEM_SPEC.md#11-deployment-and-failure),
[Phase 4](REBUILD_PLAN.md#phase-4--the-frontier-loop).
**Personas:** Saboteur + Security Auditor; WARNING → CRITICAL.
**Status:** resolved 2026-09-08, `docs/DECISIONS.md` §21. The attempt row is the durable call identity, committed before the provider call; an indeterminate reservation keeps its exposure; a retry is a new operation; the API process owns run recovery.

The concrete failure is: reserve budget, the provider completes and bills the
call, then the API process dies before the accepted-attempt commit. Recovery
finds no accepted artifact and retries. Recomputing the frontier does not tell
the host whether the first external call completed or how much it cost. The
spec never says how that outstanding reservation is retained, reconciled or
charged, or whether "one charge" means a host ledger entry or provider billing.
The existing commit-gap guarantee does not settle this earlier failure window.

Before Phase 4, define the durable call identity and pending-reservation
recovery policy. Unknown usage must keep its reserved exposure; a retry needs
its own reservation unless a verified provider idempotency contract makes it
the same operation. Define which process owns and resumes runs: §1 assigns
only model/publication jobs to the worker while §4 requires startup recovery.
Require a crash test after remote completion but before local acceptance,
including the no-idempotency case and concurrent reservations at the ceiling.
No provider-specific idempotency capability was assumed. The underlying retry
ambiguity is documented in [AWS's idempotent API guidance](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).

### C2. Forecast residual has no defined independent comparator

**Location:** [System §6.1](SYSTEM_SPEC.md#61-cash_flow_forecast--the-deterministic-forecast-calculator).
**Personas:** Saboteur + New Hire; WARNING → CRITICAL.
**Status:** resolved 2026-09-08, `docs/DECISIONS.md` §22. CP-2G's required `debt_liquidity_rollforward` is the independent side: residual = model-asserted closing balance minus host-computed closing balance.

The spec defines equations that compute closing debt and cash, then requires
an explicit non-zero residual to detect reconciliation failures. It does not
define the residual equation, units, sign convention or independent quantity
against which those computed balances reconcile. Reusing the closing-balance
expression as its own expectation always produces zero, even if a cash-flow
component was omitted from both calculations.

Before Phase 7, specify the independently derived sides of each reconciliation,
where their inputs come from, and how they map to the displayed residual. Add a
worked input with a known non-zero residual and expected downstream
unavailability. The plan now names the required regression tests; they are
future exit checks, not tests implemented by this review. No financial formula
was invented to fill this gap.

## Warnings — both resolved

### W1. CP-0 bootstrap and readiness inputs are not bound to a lifecycle

**Location:** [System §4](SYSTEM_SPEC.md#4-route-resolution-and-execution),
[Decision §5](DECISIONS.md#2026-09-08-5--cp-parse-stays-a-separate-host-node).
**Personas:** New Hire.
**Status:** resolved 2026-09-08, `docs/DECISIONS.md` §18. There is no bootstrap cycle -- the bundle's own anchor contract settles it -- and readiness is read from CP-0's accepted artifact rather than passed in.

`resolve_route` can consume CP-0's plan, but CP-0 is itself a runnable route
node and execution is required to read a route pinned once. The optional
whole-pathway default provides one possible path; the plan-driven bootstrap
path remains unspecified. Likewise, `source_readiness` is an input to frontier
recovery with no stated persisted source, although it changes whether soft
edges block. Live withdrawal must still refuse use without rewriting route pins.

Before Phase 3, define the preparation run/gate sequence and the provenance of
readiness. Trace an intake through CP-PARSE, CP-0, approval, pinning and restart,
and assert that recovery cannot reinterpret the approved route. This is an
unresolved contract, not evidence that a particular bootstrap implementation
is broken.

### W2. The authoritative bundle cannot be checked from this checkout

**Location:** [System §3](SYSTEM_SPEC.md#3-methodology-boundary),
[Model Builder introduction](MODEL_BUILDER_SPEC.md).
**Personas:** New Hire.
**Status:** resolved 2026-09-08, `docs/DECISIONS.md` §17. The bundle is vendored at build `a43cb903` and every claim in §2 and §5 is asserted against its bytes.

The referenced Deploy V catalog, schemas, calculator source and workbook
renderer are absent, and no acquisition location or expected bundle digest is
recorded here. Consequently, the 18-pathway claim, CP-PARSE alias compatibility,
six canonical artifact inputs and workbook parity cannot be verified. Obtain
the exact immutable bundle and record its acquisition/pin before the Phase 3
catalog tests; a made-up catalog cannot prove compatibility with the authority.
This review does not claim those external facts are wrong.

## Findings corrected in the specifications

| Finding | Severity / personas | Correction |
|---|---|---|
| One successful period per case satisfied forecast completeness, even with the rest of the requested horizon missing. | CRITICAL; Saboteur + Security Auditor | System §6.1 requires the exact non-empty requested case-period set, no duplicates/extras, and no unavailable periods. Explicitly unavailable ratios remain allowed. Phase 7 gains coverage and propagation exit checks. |
| CP-CF reads CP-1 and CP-4, but its stated incoming extension edge named only CP-2G. Those edges alone permit execution before covenant terms are available. | CRITICAL; Saboteur + Security Auditor | System §6.2 declares every required artifact owner and refuses extended routes with missing owners. Phase 3 gains ordering and missing-owner exit checks. Actual catalog closure remains subject to W2. |
| One snapshot for the entire screen conflicts with Book comparing multiple cases, each owning its own accepted snapshot. | CRITICAL; Saboteur + New Hire | IA §5 binds one snapshot per case and keeps the shared comparison basis separate. Phase 9 gains a two-case stale-response exit check. |
| System §3 allowed editing the bundle with a decision entry despite the binding prohibition on upstream edits. | WARNING; New Hire + Security Auditor (NOTE promoted) | The exception now applies only to additions in new skill folders; all added bytes remain pinned and verified. |
| Copying "base tabs" did not distinguish model data from prior workbook sheets, which the workbook contract forbids reusing. | WARNING; New Hire | System §6 specifies immutable model-table data reuse followed by fresh IR rendering, recalculation and validation. Phase 7 gains an overlay exit check. |
| The frontier example passes a generator as one `gather` argument. | WARNING; Saboteur | Expanded coroutine arguments. The original raises `TypeError`; the corrected example awaits both nodes. |
| Production role/standing checks had no explicit phase exit requirement. | WARNING; Security Auditor | The first HTTP route must arrive with its actor matrix and tests for forged role headers, private 404s and revoked membership at commit. This schedules the existing authority rules. |

## Notes

- Aligned the registry path with `CLAUDE.md` (`methodology/registry.py`).
- Corrected the phase count to eleven (0–10) and paper text to dark ink on cream.
- Existing sensible constraints remain: PostgreSQL only, no checkpointer,
  no extra navigation surface, host-owned calculations, no upstream edits,
  coordinate-anchored citations and required LibreOffice recalculation.
- No new dependencies, application code, UI or speculative infrastructure.
  No commits, staging, merges, publishing or messages to the other task.

## Confidence review and verification

Least confident about: scope isolation, changed acceptance/dependency contracts,
and whether the remaining promises have sufficient inputs to be implemented.
The checks below separate corrected defects from verified properties; C1, C2,
W1 and W2 remain open for the reasons and next steps given above.

1. **Scope isolation:** compared the diff with the current checkout. Only the
   three specification files and this review were changed by this review.
2. **Forecast boundary:** reproduced a two-period request for which the old
   completeness condition accepts only the first period. The correction keeps
   null ratios with reasons distinct from absent/unavailable periods.
3. **CP-CF ordering:** evaluated the originally stated edge set with only CP-2G
   accepted; CP-CF is released while CP-4 is absent. Explicit dependencies close
   that gap without modifying upstream files. Bundle-wide compatibility is open.
4. **Snapshot identity:** checked Book's accepted-only comparison and the
   cross-case stale-response rule together. The correction preserves one visible
   identity for each case; it does not permit two snapshots of the same case.
5. **Overlay authority:** checked the revised wording against Model Builder
   §§4–5; deriving, recalculating and validating each workbook remain mandatory.
6. **Executable example:** ran the old and corrected frontier expressions with
   Python 3.14. The old form fails with `TypeError`; the corrected form returns
   both node results. Verified again against the expression in the edited file.
7. **Document checks:** `git diff --check` and relative Markdown-link checks
   pass (18 links across 12 Markdown files). The exact-horizon rule refuses
   missing, duplicate and extra periods; the revised edge set waits for all
   three input owners. These are specification probes, not application tests.
   No runtime qualification, live-provider or workbook-parity claim is made.
8. **Rewrite tournament:** skipped: changes are documentation and a one-line
   example correction; no non-trivial application function was changed.

## Summary

Seven specification defects were corrected and their applicable exit checks
made explicit. All four open findings were closed on 2026-09-08: the bundle was
vendored and pinned (W2), route bootstrap was settled by the bundle's own anchor
contract (W1), provider-call recovery was given a contract (C1), and the
forecast residual was given an independently derived side (C2). Each carries a
status line above and a dated entry in `docs/DECISIONS.md`.

---

# Review 2 — the build plan against the tree

Date: 2026-09-09. Skill: `adversarial-reviewer`, then `confidence-review`.

**Scope:** `docs/REBUILD_PLAN.md`, `docs/SYSTEM_SPEC.md`, `docs/DECISIONS.md`
§1–34, `docs/AI_CODE_QUALITY.md`, `docs/INITIALISATION_PROMPT.md`,
`docs/IA_SPEC.md`, `docs/MODEL_BUILDER_SPEC.md`, this file, `README.md`,
`CONTEXT.md` and `DESIGN.md` — each read in full and checked against the tree
on `main` at `01884c7`: 32 modules, 31 test files, the CI workflow, the hooks
and the pre-commit configuration. Every claim below was verified by reading the
code or by grep, not inferred from the documents. The first review read
specifications with no code to hold them to; this one had six phases of code.

**Verdict: BLOCK** on the plan as it stood. Three findings were promoted to
critical by being caught from two postures. Every finding below carries a
status line; all were addressed on 2026-09-09 in the same branch, and the
verdict is left as written for the same reason as the first.

## Critical findings — all resolved

### C1. SDK-internal retries are provider calls without a reservation

**Location:** `server/provider.py`, `docs/DECISIONS.md` §21 and §28.
**Personas:** Saboteur + Security Auditor; WARNING → CRITICAL.
**Status:** fixed. `live_client()` builds the client with `max_retries=0`,
`test_the_live_client_never_retries_on_its_own` reads it back, and
`docs/DECISIONS.md` §37 reconciles §21 with §28.

`live_provider_or_none` built `anthropic.Anthropic()` with the SDK default of
two retries (read from the locked 1.4.0, not recalled). On a 408, 409, 429, 5xx
or connection error the SDK re-sent the request under the one attempt row and
the one reservation — the failure §21 closed, reintroduced inside one call. The
provider suite disables SDK retries on its mock client, so the path production
ran was the one path no test ran.

### C2. Withdrawal — half of invariant 1 — had no phase

**Location:** `docs/REBUILD_PLAN.md`; `IA_SPEC.md` §4.2; `docs/DECISIONS.md` §18.
**Personas:** Security Auditor + Saboteur; promoted.
**Status:** scheduled, not built. Phase 6 owes
`test_a_withdrawn_source_refuses_the_read_and_reopens_the_gate`; the column,
the `read_evidence` predicate and the plan-gate re-open are Phase 6 work under
`docs/DECISIONS.md` §38.

No phase bullet named it, no column existed, and `grep withdraw` found comments
only, while Phase 2 — the `read_evidence` phase — was exited. A source admitted
in error stayed readable by every future run of a set that pinned it, and the
pin is immutable by design.

### C3. The mandatory reading order carried overridden contracts

**Location:** `docs/INITIALISATION_PROMPT.md`; `docs/REBUILD_PLAN.md` Phases
0, 3, 5; `docs/SYSTEM_SPEC.md` §2, §3, §4, §6.1, §6.2; `README.md`.
**Personas:** New Hire + Saboteur; promoted.
**Status:** fixed. The prompt reads `docs/DECISIONS.md`; every overridden line
named below is corrected in place with a citation; `docs/DECISIONS.md` §38
reverses §20's "left alone"; `test_every_exit_test_of_an_exited_phase_exists`
holds the plan to the standard `test_the_map_is_true.py` held `CLAUDE.md` to.

The prompt read five files "in full" and never the binding record, while §20
said the plan was deliberately left stale. A session following it would have
built: `active_incoming` and `expected_upstream_digests` (never existed);
`_ALIASES` (code is `_CARVE_OUTS`, §24); an `image` job (§11);
`node_states(route, attempts, source_readiness)` (§18 removed the parameter);
`ModuleSpec.calculators` (§25: no such field); a `_CALCULATORS` table (§25
replaced it with a rule); §6.2 without CP-MODEL's placement (§23); a README
saying no application code existed. Correcting §6.1 surfaced one more: it bound
`cash_flow_forecast` to CP-2G as well as CP-CF, which §25 makes impossible
without editing an upstream folder. CP-CF is now its only caller.

## Warnings — all resolved

| Finding | Personas | Status |
|---|---|---|
| **W1.** Exit tests passed without the phase's deliverable — Phase 2 had no extractor, Phase 4 a stub executor at a flat price, Phase 5 a recorded provider — and the ledger deferred each gap to a "slice" the plan never named, so "start at the lowest phase whose exit test does not pass" walked past all three. | Saboteur | Rule added to the plan and to `docs/DECISIONS.md` §38: the current phase owes what an exited phase did not ship, listed under it with the test it owes. Phase 6 lists the five. The ledger's "slice" is defined as that phase. The map test refuses a later phase starting before an earlier one's tests exist. |
| **W2.** The audit chain was Phase 8, after six phases of governed writes; `audit_events` did not exist, and a plan approval — a human decision — committed without one. | Security Auditor | Phase 6 owes `audit_events`, `audit_chain_heads` and `test_a_governed_write_commits_its_audit_event_or_nothing`; Phase 8 builds the package over the chain rather than the chain. |
| **W3.** Commit-time authority was bound to "the first HTTP route", but the commit is `approve_gate`, which exists and checks nothing about the approver. A check at the request is what §8 says is not enough. | Security Auditor | Standing rule rewritten: the phase that first commits a human decision ships the standing check inside the store call; the HTTP phase ships identity derivation. `test_membership_revocation_refuses_commit` and `case_members` are Phase 6's. |
| **W4.** Phase 10 had no runnable exit test, and `ORCHESTRATION_PROOF` appeared nowhere else — not in any document, not in the bundle. | Saboteur | Both words defined in the plan; two named exit tests. |
| **W5.** `AI_CODE_QUALITY.md` named controls that did not exist: a `Stop` hook, `run_sec_audit.py`, `test_dependency_pins.py`, `test_io_budget.py`, Trivy in CI, `prettier` in CI. | New Hire | Each struck or bound to the phase that owes it; the CI job list says which jobs run and which arrive. |
| **W6.** No phase owned the `worker` process, the Dockerfile, the `image` job, or the per-calculator dependency set the ledger says `-S` cannot survive in Phase 7. | New Hire | Phase 7 bullets, with `test_a_calculator_sees_only_its_declared_dependencies`. |

## Notes — all resolved

- `docs/INITIALISATION_PROMPT.md` said "ten phases" of eleven, and restated
  seven rules under a rationale that said it would restate none — one of which,
  "never float", contradicted §6.1's deliberate float in existing calculators.
  It now defers to `CLAUDE.md` for all of them.
- Plan Phase 6 listed `/run/` rendering, a Phase 9 section. Reworded.
- `server/provider.py`'s price constants carried no source or date. Annotated:
  first-party list price for `claude-opus-5`, published 2026-06-24.

## Confidence review and verification

Least confident about: whether disabling SDK retries loses a retry the host
needed; whether the plan rule for owed work can be satisfied by writing the
test's name and never the test; whether any corrected line still disagrees
with the code.

1. **Retries:** measured rather than recalled. The real SDK from the lock,
   driven through `provider_using` at a mock wire answering 500: three
   requests under the default, one under `max_retries=0`. Nothing in the loop
   relied on the SDK retrying, because the loop has never called the SDK. A
   second seam surfaced while checking: `live_client` was public and skipped
   the credential guard, so a direct caller would have let the SDK read an
   `ant` profile from disk. The guard moved into `live_client`, and the
   credential test now asserts on both.
2. **A named test is not a written test:** `_owed` counts a test as written
   when `def test_…` exists, so a name alone satisfies nothing; and a test that
   is written but skips does satisfy it — entered in the `CLAUDE.md` ledger
   under Phase 6 with its upgrade.
3. **Corrected lines against the code:** `node_states(route, accepted)` and
   `frontier(route, accepted)` are the signatures in `server/engine/route.py`;
   `_CARVE_OUTS` is the name in `methodology/registry.py`; `route_digest` and
   `dependency_order` exist and `active_incoming` does not; no `_CALCULATORS`
   table exists; the CI workflow defines `lint`, `types`, `test`, `postgres`,
   `security` and `size` and nothing else; `.claude/settings.json` has no
   `Stop` hook.
4. **The synthetic map test** fails when a lower phase's test is missing and
   passes when only the current phase's is, so the rule is the one intended
   rather than the one that happens to pass today.
5. **Rewrite tournament:** skipped. The code changed is two test helpers and a
   one-line client factory, which the skill excludes.
6. **Gates:** `make lint`, `make types`, `make test` against the local store
   (361 passed, the live-provider test skipped), `make security`, and
   `test_decision_record` over §37–§38 — all green.

## Summary

The plan's phase-exit discipline is real and the first review's findings were
closed properly, but §28 undid C1 in code the suite deliberately did not
exercise, and withdrawal, the audit chain and commit-time authority had no
phase because the plan and the ledger used different units of work. The retry
is closed in code; the rest is scheduled under Phase 6 by a rule that stops it
being walked past again.
