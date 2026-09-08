# Adversarial review — application build contracts

Date: 2026-09-08. Skills: `adversarial-reviewer`, `senior-architect`,
`confidence-review`.

**Scope:** all eleven pre-existing Markdown contract, specification and design
files read in full. The concurrent Phase 0 implementation was inspected initially, then
excluded from changes and this verdict at the user's direction. No application
runtime, vendored methodology bundle or rendered frontend exists in this
checkout to validate. This is a specification review, not runtime qualification.

**Verdict: BLOCK** on treating the specifications as a complete implementation
contract. The open findings below need resolution before their affected phases;
they do not prevent independent store work. Three existing specification files
were corrected. The other task's implementation and Git state were left alone.

Personas ran in order: Saboteur (execution and calculation failure paths), New
Hire (cross-document contracts and phase dependencies), Security Auditor
(authority and trust boundaries). Shared findings are promoted one level, as
the review skill requires. Severity describes the build risk, not a claim that
a deployed vulnerability was observed.

## Critical findings — open

### C1. Provider-call uncertainty has no recovery/accounting contract

**Location:** [System §4](SYSTEM_SPEC.md#4-route-resolution-and-execution),
[System §11](SYSTEM_SPEC.md#11-deployment-and-failure),
[Phase 4](REBUILD_PLAN.md#phase-4--the-frontier-loop).
**Personas:** Saboteur + Security Auditor; WARNING → CRITICAL.

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

## Warnings — open

### W1. CP-0 bootstrap and readiness inputs are not bound to a lifecycle

**Location:** [System §4](SYSTEM_SPEC.md#4-route-resolution-and-execution),
[Decision §5](DECISIONS.md#2026-09-08-5--cp-parse-stays-a-separate-host-node).
**Personas:** New Hire.

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
made explicit. Resolve provider-call recovery and the independent forecast
residual before implementing those boundaries; settle route bootstrap and
obtain the authoritative bundle before the route compatibility work.
