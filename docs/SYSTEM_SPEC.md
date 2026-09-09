# CAOS v2 — system spec

Structure only. Scope and decisions live in `docs/REBUILD_PLAN.md`; the
workspace and its sections live in `docs/IA_SPEC.md`.

---

## 1. Shape

```
                          browser (static export, no Node in prod)
                                     │  HTTPS · SSE
                          ┌──────────┴───────────┐
                          │      API (FastAPI)   │  strict named wire models
                          └──────────┬───────────┘
        ┌──────────────────┬─────────┼──────────┬──────────────────┐
   ingestion          route          │       forecast        deliverable
   + citation       resolution    execution     (CP-CF)       rendering
   anchoring        + pinning       loop            │          + filing
        └──────────────────┴─────────┼──────────────┴──────────────┘
                          ┌──────────┴───────────┐        ┌─────────────┐
                          │    PostgreSQL 16     │        │  blob store │
                          │  domain · runs ·     │        │  CAS, sha256│
                          │  events · audit      │        │  bytes only │
                          └──────────────────────┘        └─────────────┘
                          ┌──────────────────────┐
                          │ methodology bundle   │  vendored, digest-verified
                          │ (Deploy V, read-only)│  on the bytes at use
                          └──────────────────────┘
```

One process, `api`, one instance (`docs/DECISIONS.md` §48). The run loop is the
only long-running work and it runs there; the deliverable renders in the
request. The worker went with the model builds and publication jobs it existed
to poll for.

No worker, no checkpointer, no second database, no message broker.

---

## 2. Storage

PostgreSQL owns everything transactional. Bytes live in a content-addressed
blob store keyed by `sha256`; the database holds the digest, never the bytes.

| Group | Tables |
|---|---|
| Tenancy | `cases`, `case_members`, `users` |
| Evidence | `sources` (read through the `live_sources` view, `docs/DECISIONS.md` §45), `source_sets`, `source_set_members`, `source_blocks`, `source_tokens` |
| Runs | `runs`, `run_routes`, `run_nodes`, `run_attempts`, `run_events`, `budget_ledger` |
| Artifacts | `artifacts`, `snapshots`, `snapshot_members` |
| Deliverable | `deliverable_drafts`, `deliverable_opinions`, `deliverable_publications` |
| Audit | `audit_events`, `audit_chain_heads` |

The target set. `server/store/schema.sql` is what exists; a table arrives there
in the phase that first writes it, and the tables of phases not yet reached are
not there.

Rules that do not bend:

- **Transactional pairing.** A governed write commits state and its audit event
  in one transaction. A run-state transition commits state and its run event in
  one transaction, and no event is inserted without the transition it records —
  proven either by the row lock the transition is taken under or by a
  conditional update whose zero rows mean no event. That is what makes terminal
  events exactly-once.
- **`run_events.seq`** is per-run monotonic, allocated under the run row lock.
- **Append-only** means append-only: `run_events`, `run_attempts`,
  `deliverable_opinions`, `audit_events` have no UPDATE path.
- **`BoundaryText`** on every string that can reach pinned state, a revision, a
  frozen payload or an audit event. NFC-normalised before the length bound;
  rejects lone surrogates, Unicode Cc controls except CR/LF/TAB, and
  bidirectional override/isolate controls. Never a bare `str`.
- **Audit chain.** `audit_events` is hash-chained per case with a
  `audit_chain_heads` lock row. The chain has no external anchor; detect a
  rewrite by comparing a retained package's head with the live head.

### `source_blocks` and `source_tokens`

Blocks are the unit `read_evidence` returns and are one row per block keyed by
`(source_id, block_id)` — not a JSON column on the source row. Tokens are the
coordinate index behind invariant 11 (§5): one row per extracted text run with
its page and rectangle. Tokens are never returned to a module; they exist so the
host can re-locate a quote and refuse one it cannot.

---

## 3. Methodology boundary

The vendored Deploy V bundle is the authority. It is read-only at runtime and
verified on the bytes at use, not at startup only.

- **Registry** (`methodology/registry.py`) is the only seam. One `ModuleSpec` per
  live module: `module_id`, execution mode, `skill_slug`, `reference_files`,
  `max_output_tokens`, `derived_projections`, `source_mode`, `plan_approval`.
  The live set and each module's files are derived from the catalog and the
  manifest, never written out (`docs/DECISIONS.md` §24); which calculator a
  module may select is a rule, not a field (§25). The host's one declaration
  is `_CARVE_OUTS`: CP-PARSE (§5).
- **Calculators** are host-owned. Only a `(module_id, calculator_id)` pair the
  host declares can select code; the calculator and its helper module are read
  through no-follow file handles and digest-checked; work factors are bounded
  per calculator. A module asks for a calculation; it never supplies the code.
- **Pin.** A run records the bundle build id and digest. A run pinned to one
  build never executes under another. Never edit a file that exists upstream
  (`DECISIONS.md` §6). Host additions go in new skill folders and require a
  dated decision entry and regenerated manifests; they are part of the pinned
  build and are verified at use too.
- **Provider frontmatter never survives.** Whatever a module claims about its
  own identity, period, module id or digests is an expectation the host
  re-verifies against the store.

---

## 4. Route resolution and execution

The full argument is `docs/DECISIONS.md` §2. The contract:

```python
# resolution — pure, no I/O
resolve_route(catalog, profile_id, selection_id, *,
              module_order=None,        # CP-0's plan, or None for the whole pathway
              research_brief=None,      # appends CP-DR at stage 99
              predicates=None,          # freezes CONDITIONAL edges
             ) -> ResolvedRoute         # nodes (dependency order), typed edges, predicates

# pinning — at the plan gate, once
pin_route(run_id, resolved) -> route_digest      # row in run_routes, digest in run_events

# state — recomputed from accepted attempts, never stored; readiness is read
# from the accepted CP-0 artifact, never passed in (docs/DECISIONS.md §18)
node_states(route, accepted) -> {route_node_id: COMPLETE|BLOCKED|RESTRICTED|RUNNABLE}
frontier(route, accepted)    -> [route_node_id]   # RUNNABLE + RESTRICTED
```

An `expected_upstream_digests` in the first draft of this block had no consumer
and was never built; it is dropped rather than left as a promise
(`docs/DECISIONS.md` §38).

Edge types and their meaning are the bundle's, read from `profile["edges"]`:
`REQUIRED`, `CONDITIONAL`, `QA_GATE` block; `OPTIONAL`, `ADVISORY` degrade to
`RESTRICTED` — unless the source's readiness is `READY` or
`READY_WITH_LIMITATIONS`, in which case they block.

The execution loop:

```python
while ready := frontier(route, attempts, readiness):
    await gather(*(run_node(n) for n in ready))  # one attempt row per node per try
```

- `run_node` reserves budget, resolves the provider, executes, validates the
  envelope, verifies citations, and commits the accepted attempt with its
  `artifact_sha256` — state and event in one transaction.
- Recovery is recomputation: on start, `node_states` over the surviving attempt
  rows tells the engine exactly what remains. There is nothing to restore.
- A node parked on a digest-bound interrupt (source-set pinning, research-plan
  approval) is `BLOCKED` on a host predicate, not a special engine state.

**Route coverage.** 18 pathways across two profiles: `FULL_CREDIT_32` (10,
2–19 nodes) and `LITE_CREDIT_22` (8). The catalog is the route set; adding one
is a catalog read.

---

## 5. Evidence and citation

Ingestion is the only way bytes enter a case. Web discovery is structurally
absent — there is no code path to it.

1. Admit or refuse the whole pack in one transaction. Store bytes at
   `sha256`; extract text with page and rectangle per token; pack blocks
   (one per line while small, bounded line groups once not, splitting a line at
   the group width rather than giving it a block of its own).
2. Classify, propose dispositions, select a route. Every one of these is a
   **labelled machine suggestion**. Issuer, document types, periods,
   dispositions and route are never taken from the browser and never from an
   instruction found inside a document.
3. Pin a source-set version. Version allocation locks the case row before
   reading the current version.

`read_evidence` is validated at the host boundary and fails closed with a typed
refusal. **No text is ever returned on refusal** — not in the exception chain,
not in the delivered set, not in the ledger.

A citation is `{document_sha256, page, bboxes, matched_text}`. The host
re-locates `matched_text` in `source_tokens` at the stated page and derives one
rectangle per line the quote covers -- the same shape as a PDF highlight's
QuadPoints, and for the same reason: selected text wraps. A single enclosing
rectangle would cover text the quote does not contain, which is the predecessor's
line-range defect wearing coordinates.

Every token carries the layout region and the line it belongs to, assigned by
the extractor. A region is a column or a paragraph; it is not a `block`, which
is the unit `read_evidence` returns. Matching joins tokens within a line and
continues only onto the next line of the same region, so a quote cannot be
assembled across a column gutter: the two columns are different regions and the
phrase never forms. A quote it cannot re-locate, or cannot locate exactly
once, is refused before it reaches the artifact. Citations may only name evidence
actually delivered to that node.

---

## 6. Forecast

The forward model is CP-CF's accepted artifact: a projection the host computes
from module-authored drivers, read in the Model section (`IA_SPEC.md` §4.6).
The workbook build that stood here — one model effect per pathway, overlays,
`source_lineage`, the expression-language calculator — went with CP-MODEL
(`docs/DECISIONS.md` §48; archived in `docs/archive/MODEL_BUILDER_SPEC.md`).
Calculation is pure and finite: non-finite values
and zero denominators are refused before use.

### 6.1 `cash_flow_forecast` — the deterministic forecast calculator

The gap this closes: CP-2G states its roll-forward rules in prose and emits 42
driver rows, but no calculator computes the projection. Leverage and coverage
are recomputed deterministically *over* arithmetic the model performed. This
calculator moves the arithmetic to the host and leaves CP-2G doing what needs a
model — choosing drivers, with rationale and evidence.

**Binding.** `cash_flow_forecast` is declared once, with its helper set and its
work factor, and its code ships in `scripts/` of the host-added CP-CF folder.
Under `docs/DECISIONS.md` §25 a module selects a calculator only when its own
folder ships the script, so CP-CF is the only caller: CP-2G's folder is upstream
and gains no file (§6.2). An earlier draft bound the pair to CP-2G as well,
which §25 makes impossible without an upstream edit.

**Inputs** (model-authored, host-validated before any code is selected):

| Field | Meaning |
|---|---|
| `opening` | `debt_by_facility[]`, `cash`, `as_of_period_id` — from the last CP-1 actual |
| `periods[]` | `period_id`, `fiscal_year`, `case`, `days` — ordered, one row per case-period |
| `drivers[]` | CP-2G's `cp_model_forecast_drivers` rows, `status` included |
| `contractual` | `amortisation[]`, `maturities[]`, `coupons[]` per facility |
| `policy` | `cash_sweep_pct`, `min_cash`, `revolver_limit`, `fx` |
| `tolerance` | reconciliation tolerance, default `Decimal("0.001")` |

**Output.** Per case-period: `operating` (revenue, ebitda, margin, cfo),
`investing` (capex, acquisitions_disposals), `financing` (cash interest, cash
taxes, distributions, issuance, contractual and optional repayment), `fcf`,
`debt` (opening, pik, capitalised_interest, fx_perimeter, closing), `cash`
(opening, closing, accessible), `residual`, `metrics` (gross and net leverage,
interest coverage, fcf_to_debt, liquidity_runway_periods), and
`unavailable_reason`. Plus a `checks[]` list of `SemanticCheck` records in the
shape `cp_model_v3/calculations.py` defines.

**The two identities it computes**, taken verbatim from CP-2G's calculation
controls:

```
closing_debt = opening_debt + issuance + pik + capitalised_interest
             − contractual_repayment − optional_repayment ± fx_perimeter

closing_cash = opening_cash + cfo − capex − cash_interest − cash_taxes
             − distributions ± financing_investing
```

**Invariants.**

1. **Decimal only, end to end.** JSON has no decimal type, so every numeric in
   the input carries as a **string** and is parsed with `Decimal(str)`. A JSON
   float in a numeric field is `METHODOLOGY_INPUT_INVALID`, not a silent
   coercion — binary floating point cannot represent a cent. Output numerics
   are strings too. The module contains no `float`, matching
   `cp_model_v3/calculations.py`, which has zero `float(` calls.
   This is stricter than the existing calculators, which accept JSON numbers;
   the difference is deliberate and is the one place the new calculator does
   not simply copy the incumbent contract.
2. **Chained, asserted.** `opening[n+1] == closing[n]` per case, checked rather
   than assumed. A break is `FORECAST_CHAIN_BROKEN`.
3. **The residual is explicit and never forced to zero.** This is CP-2G's own
   rule made executable: if `abs(residual) > tolerance`, the period is
   `unavailable` and says so.
4. **Unavailability propagates forward.** A period that cannot be computed makes
   every later period in that case unavailable. It is never read as zero growth
   — also CP-2G's rule.
5. **Non-finite values and zero denominators are refused before use**
   (invariant 7). Leverage against zero EBITDA is `null` with a reason, never
   an infinity.
6. **Pure.** No I/O, no clock, no randomness. Same inputs, byte-identical output.

**Work factor**, host-enforced in `_enforce_work_factor` before the vendor
script's own guards, so a looser script can never widen what model-authored
input may cost:

```
MAX_FORECAST_PERIODS    = 40     # ten years quarterly
MAX_FORECAST_CASES      = 6
MAX_FORECAST_FACILITIES = 40
periods × cases × (1 + facilities) ≤ 100_000
```

**`calculation_output_complete`**: `status == "complete"`, the requested
`(case, period_id)` set is non-empty, and the output contains every requested
pair exactly once, with no extra pairs. Every requested period has finite
closing debt, finite closing cash and a non-empty `metrics`. An explicitly
unavailable period makes the calculation incomplete; it and its reason still
appear in the output, with unavailability propagated forward. One successful
period cannot stand in for the requested horizon. A ratio that is `null` with
the zero-denominator reason allowed above is not itself a missing period.

**Refusals** — typed, public-safe, no vendor or filesystem detail:
`METHODOLOGY_INPUT_INVALID`, `FORECAST_CHAIN_BROKEN`,
`FORECAST_RESIDUAL_UNRECONCILED`, `FORECAST_DRIVER_NOT_READY`.

### 6.2 CP-CF — CashFlowEngine, and the no-edit rule

**The rule.** We never edit a file that exists upstream. One Deploy V release
changed 175 files including 21 of 22 `SKILL.md`; every upstream file we touch
becomes a permanent merge and moves the whole-tree pin. Additions live in new
folders under `skills/`, which upstream will never write to. Invariant 4's
preference — "behaviour changes ride wrappers or registry entries where they
can" — is satisfied as closely as a new calculator permits, because calculator
code must be bundle-resident and verified at use.

The id follows the host/utility convention — `CP-DR`, `CP-MODEL`, `CP-MEMO` —
not the numbered families. `CP-2CF` would read as a sub-module of CP-2 absorbed
by it, which is the opposite of what this is.

**Why a new module and not a wider CP-2G.** CP-2G's contract is fixed upstream
at seven drivers × three fiscal years × BASE and DOWNSIDE — 42 rows, three
divisions, annual only. A complete cash flow model needs quarterly periods,
more than two cases, per-facility contractual detail and covenant-period
testing. Widening CP-2G means editing upstream. CP-CF carries the wider
contract; CP-2G is left untouched as the annual base case and remains the
driver author.

**What CP-CF does.** It is an agent module whose job is explicitly *not*
arithmetic: it authors the driver set, the contractual schedule and the policy
(sweep, minimum cash, revolver behaviour, FX) from CP-1 actuals, CP-2G's
drivers and CP-4's covenant terms, each with evidence — then declares
`cash_flow_forecast` and reports what the calculator returned. Its handoff
carries the projection, the residual per period, and the first covenant breach
period per case.

**Route placement without editing the catalog.** Reuse the mechanism legacy
already has for CP-DR: a host-declared model extension, mirroring
`profile["research_extension"]`, appends CP-CF at stage 100 with synthesised
`REQUIRED` edges `CP-1 → CP-CF`, `CP-2G → CP-CF` and `CP-4 → CP-CF`. These
name every artifact owner CP-CF reads, including the covenant terms; CP-2G
completing alone does not release CP-CF. An extended route missing a required
owner is refused during resolution, before pinning, rather than dropping the
edge or running with missing inputs. No upstream pathway node list is edited,
and the extension is part of the resolved route that gets pinned at the gate
(§4), so replay is unaffected. `docs/DECISIONS.md` §23 had the extension place
CP-MODEL at 101 as well; §48 does not place it.

---

## 7. Deliverable

The host renders the deliverable from the frozen snapshot (`IA_SPEC.md` §4.8
for the surface; `docs/DECISIONS.md` §48 for why it is not CP-MEMO's `.docx`,
whose contract is archived in `docs/archive/REPORT_BUILDER_SPEC.md`):

- Exactly one HTML file, never overwriting. It prints to paper (`DESIGN.md`);
  no PDF, deck, dashboard or workbook deliverable.
- The accepted artifacts in route order, every figure carrying its citation
  (§5), then the analyst's narrative and the module provenance index.
- The render originates nothing, structurally: it is a function of frozen
  bytes, so there is no editorial boundary to police. Both sides of an
  unresolved conflict, `Restricted` and `SCREENING_ONLY` qualifications reach
  the page as the artifacts carry them.

Around it, the host's own chain: the analyst signs an opinion on the exact saved
revision (expected-head CAS); freeze refuses without a current sign-off and
refuses a narrative asserting an uncited figure; filing refuses the opinion
signer and the freeze actor (`APPROVER_NOT_INDEPENDENT`) and writes an immutable
detached receipt. The approved bytes always read `PENDING APPROVAL`.

The audit package is verifiable with the standard library alone and re-renders
the export from the frozen payload.

---

## 8. Identity and authority

- Development trusts a role header. Production derives role from OIDC groups
  only; a client role header never escalates.
- Unknown runs and unauthorized runs return the same 404.
- Case standing (`READER`/`WRITER`/`APPROVER`/`ADMIN`) and global role are
  separate and both are rechecked at commit time, not only at request time.
- **Persona is not authority.** The workspace section a user is looking at
  composes the view and grants nothing (`IA_SPEC.md` §2).

---

## 9. Wire

Every JSON success serves a *named* model. `extra="forbid"` both directions.
New field means a model change plus an updated pinned key set in the contract
test. One carve-out only: SSE and binary downloads are not JSON. A first draft
also carved out service-owned envelopes for the model and publication services;
they went with those services (`docs/DECISIONS.md` §48).

One document per section, not per widget — the per-widget query pattern is what
produced the open-envelope carve-outs in the current tree.

Run progress reaches the browser as SSE over `run_events` with `Last-Event-ID`
resume. Membership is rechecked before each event; the stream closes once a
terminal run is fully delivered, and tails close after five minutes for edge
reauthentication. The client never reads event payloads — an event name triggers
a refetch.

---

## 10. Observability

Structured JSON on stdout, standard library only. Run and node transitions
(all of them through one emitter), typed refusals, provider call start and
finish, budget reserve and reconcile, gate interrupts, startup recovery,
intake dispositions.

**Never log source text, evidence block text, module output, prompts, or
anything a document produced.** Log the typed code, never the exception string.
Every string, including nested mapping keys, is redacted and truncated. The ban
is to be enforced by a test that drives a sentinel document through real
ingestion and a real agent node; nothing in the tree logs yet, and the test
arrives with the first logger (`docs/DECISIONS.md` §45).

---

## 11. Deployment and failure

Single instance of `api`, one PostgreSQL, one blob store, one reverse proxy.
Request ceilings are per instance and the instance ceiling is enforced, not
assumed.

`GET /api/health` serves liveness and readiness on one strict model — store,
bundle, blob store — 200 when all hold, 503 otherwise. The
probes really run, at most once per TTL, on a shared background task with a
deadline. The route skips auth and the rate ceiling.

Failure posture, in order of preference: refuse before acting; if acting,
commit exactly once; if uncertain, recompute rather than restore.

- A crash mid-node loses the attempt, not the run. The next pass recomputes
  `frontier` and retries the node.
- A crash in the commit gap yields one artifact, one charge, one terminal event.
- Every ceiling refuses the next operation before overspend. No provider call
  without a reservation.
- Dependencies are fully pinned and hashed; the image and CI install with
  `--require-hashes`. A red vulnerability gate is answered by recompiling, not
  by waiving.
