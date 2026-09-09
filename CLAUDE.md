# CLAUDE.md — engineering contract

CAOS turns governed source documents into committee-ready credit conclusions.
This file is the contract. `docs/DECISIONS.md` is the binding record (later
entries override earlier). `docs/SYSTEM_SPEC.md` is the structure,
`docs/IA_SPEC.md` the workspace, `docs/MODEL_BUILDER_SPEC.md` the workbook,
`DESIGN.md` the visual language, `CONTEXT.md` the vocabulary.

Most of this repository is written by an agent. `docs/AI_CODE_QUALITY.md` says
what that costs and which tool stops each failure mode. Read it before your
first commit.

## The eleven invariants (never weaken)

Each gets a named failing test before the code that satisfies it. A change that
makes one pass vacuously is wrong even with a green suite.

1. **Pinned sources only.** Runs execute against the pinned, immutable source
   set. Supplied evidence only; web discovery is structurally absent, not
   disabled. Withdrawal is checked live at every use.
2. **Evidence reads fail closed.** Every `read_evidence` is validated at the
   host boundary and refuses with a typed code. **No text is returned on
   refusal** — not in the exception chain, the delivered set, or the ledger.
3. **The host owns identity.** Provider-claimed frontmatter never survives.
   Checkpointed digests are expectations re-verified against the store.
4. **The bundle is the methodology authority.** Integrity checked on the bytes
   at use. A run pinned to one build never executes under another. **Never edit
   a file that exists upstream** — additions go in new skill folders.
5. **Human gates are digest-bound.** Approval binds the exact reviewed content
   (preview digest + input fingerprint). Single-actor releases are store CAS
   transactions, not interrupts.
6. **Execution is durable and exactly-once.** Resume from accepted attempts,
   never restart. A crash in the commit gap yields one artifact, one charge, one
   terminal event.
7. **Calculation is pure and finite.** Non-finite values and zero denominators
   refused before use. Decimal, never float, on any money path.
8. **Budgets fail closed.** Every ceiling refuses the next operation before
   overspend. No provider call without a reservation.
9. **Module output is the strict canonical envelope.** Bounded schema,
   undeclared fields refused, citations only from delivered evidence.
10. **The route is resolved once and pinned.** The resolved route — closed node
    list, typed edge set, frozen predicates — is digested at the plan gate.
    Execution reads only the pin. Replay from the same pins takes the same path.
    Route *resolution* is a pure function; route *selection* is a pinned input.
11. **Citations are coordinate-anchored.** `{document_sha256, page, bboxes,
    matched_text}`. The host re-locates the quote in its token index and derives
    one rectangle per line the quote covers. A quote it cannot re-locate, or
    cannot locate exactly once, is refused before it reaches the artifact. A
    rectangle never encloses text the quote does not contain.

Standing rules that back them:

- **Wire strictness.** Every JSON success serves a named model, `extra="forbid"`
  both ways. A new field means a model change plus an updated pinned key set.
  One document per section, never per widget.
- **Transactional pairing.** Governed writes commit state + audit event in one
  transaction; run-state transitions commit state + run event in one
  transaction, and no event is inserted without the transition it records —
  proven either by the row lock the transition is taken under or by a
  conditional update whose zero rows mean no event. That is what makes terminal
  events exactly-once.
- **Boundary text.** Every string that can reach pinned state, a revision, a
  frozen payload or an audit event carries `BoundaryText`, never a bare `str`.
  NFC-normalised before the length bound; rejects lone surrogates, Cc controls
  except CR/LF/TAB, and bidirectional override/isolate controls.
- **Auth edge.** Development trusts a role header; production derives role from
  OIDC groups only. Unknown and unauthorized both return 404.
- **Persona is not authority.** The section on screen composes the view and
  grants nothing. Every governed action is checked server-side at commit time.

## Where things live

Paths that exist today, then the ones each phase adds. A map that names a
directory the repository does not have costs more than no map.

- `server/engine/route.py` — `resolve_route`, `dependency_order`, `node_states`,
  `frontier`, `route_digest`, and the host-declared model extension. Typed edges
  from `profile["edges"]`, never from `navigation.dependencies`. Pure: no I/O.
- `server/engine/loop.py` — the frontier loop. No checkpointer: recovery is
  recomputation from the accepted-attempt ledger.
- `server/store/` — Postgres owns everything transactional.
  `server/store/schema.sql` is applied whole at startup, with no migrations.
  The write paths are `server/store/runs.py`, `server/store/attempts.py`,
  `server/store/routes.py`, `server/store/sources.py` (admission) and
  `server/store/source_sets.py` (pinning);
  `server/store/blobs.py` is the content-addressed blob store.
- `server/evidence/` — `server/evidence/reads.py` is `read_evidence`, the only
  way a module sees a document; `server/evidence/citations.py` re-locates a
  quote and derives its rectangles.
- `server/boundary_text.py`, `server/digests.py`, `server/refusals.py` — the
  types every boundary uses.
- `vendor/deploy-v/` — the methodology bundle, read-only and never edited
  (`docs/DECISIONS.md` §6). The gates do not scan it.
- `scripts/` — the five gates `make check` runs.

Arriving with their phase, and not yet present: `methodology/` — bundle
verification at use, the registry, the calculator boundary (Phase 5);
`models/` — the build and the workbook renderer (Phase 7); `frontend/` — one
workspace, nine sections, static export (Phase 9).

## Rules of work

- **Test first.** The failing test names the invariant or the behaviour. This is
  the single highest-value control against the +75 % logic-error rate.
- **One concern per PR.** If the diff grows a second concern, split it.
- **Never log document-derived text.** Log the typed code, never `str(exc)`.
- **No new dependency without a dated decision entry.** Locks are fully pinned
  and hashed; the image and CI install with `--require-hashes`.
- **A scanner that scanned nothing is a failure**, not a pass.
- **Adversarial pass before every PR.** `confidence-review`, then
  `adversarial-reviewer`, before the PR is opened. Each finding is fixed in the
  PR or entered in the ledger below with its reason. This is the third
  reviewer; CodeRabbit is not available on demand
  (`docs/AI_CODE_QUALITY.md` §2).
- **Regenerate, don't hand-maintain.** Inventories and ledgers are emitted from
  the suite. The previous tree carried ~500 KB of hand-written governance
  markdown; do not repeat that.

## Running

- `make venv` — the two toolchains. `make lock` — recompile every lock.
- `make dev` — fails until the first HTTP route exists (Phase 1).
- `make test` — the suite. `make test-model` additionally requires LibreOffice.
- `make check` — lint, types, tests, security, in that order.
- The model job needs `soffice` on PATH. Without it the workbook build fails
  closed by design (`MODEL_BUILDER_SPEC.md` §5) — a green model suite with
  soffice absent is a vacuous pass.

## Known gaps (honest ledger)

Every accepted limitation gets an entry here with its reason and its upgrade
path, in the same breath as the code that creates it. An empty ledger on a
system this size means nobody looked.

**Phase 0.**

- **No `image` CI job.** There is no Dockerfile and no runtime lock with
  packages in it, so Trivy would report every target as *not scanned*
  (`docs/DECISIONS.md` §11). *Upgrade:* the phase that adds the Dockerfile adds
  `trivy image` with `--exit-code 1` on fixable HIGH/CRITICAL and a scan floor
  asserting a non-empty target list.
- **`check_tested.py` matches a name as a whole word anywhere the suite names
  an identifier,** with no scope resolution. The haystack is `NAME` tokens only,
  so a comment, a docstring or a string literal no longer counts -- two
  definitions passed on prose alone before it did (`Node`, `accept`). What it
  still cannot tell apart is one identifier from another that spells the same:
  an unrelated import, a local variable, an attribute on some other object. It
  catches the definition no test mentions, not the definition whose test asserts
  nothing. *Upgrade:* resolve references to the symbol they bind, once the suite
  is large enough for the false negatives to matter.
- **A test file that does not tokenise crashes `check_tested.py`** with an
  unhandled `TokenError` rather than a typed refusal. Fail-closed, and the same
  shape as `check_vocabulary.py`'s `ast.parse`. `make lint` runs `ruff check`
  first, so the `make check` path never reaches it -- but a standalone run has
  no such guard, and `tests/test_phase0_gates.py` drives the script directly.
  *Upgrade:* a typed refusal naming the file, the day a gate is run anywhere a
  traceback is not a fine answer.
- **`check_tested.py` sees module-level definitions only.** A method is covered
  through the class that holds it. *Upgrade:* descend into classes when a
  governed path first puts logic on a method.
- **`check_vocabulary.py` enforces 9 of the 33 synonyms `CONTEXT.md` lists.**
  The other 24 carry an ordinary technical meaning here — `file`, `state`,
  `version`, `response` — and each is exempt with a stated reason in
  `NOT_ENFORCED`. The check refuses to run if `CONTEXT.md` and that list drift
  apart. *Upgrade:* enforce an exempt synonym the day it is actually misused.
- **The two identifier gates read Python only.** TypeScript identifiers are
  unchecked. *Upgrade:* Phase 9, with the frontend.
- **`io_budget.py --assert` enforces only that some `server/api/` module
  declares an `IO_BUDGET`.** It keys on the route directory, not on `server/`:
  a store module has no request path and no round-trip budget to declare.
  *Upgrade:* Phase 2 raises the floor to one budget per request path, with
  `test_io_budget_read_evidence`.
- **`make dev` fails.** There is no API or worker until the first HTTP route.
- **CodeRabbit never auto-reviews, and the ask cannot be automated.** It is
  installed and live, reading `.coderabbit.yaml`, but it declines every PR here
  with *"does not receive automatic reviews because it has fewer than 10
  stars"* — its own words on PR #20, whose base was `main`. The stacked-base
  rule is real and `base_branches` covers it, but it was never why this
  repository saw no reviews. `@coderabbitai review` does start one, in under a
  minute, when a person posts it (PR #20). The same comment posted by
  `github-actions[bot]` from a workflow was ignored for nine minutes and never
  answered (PR #22), so CodeRabbit does not honour a bot author and no workflow
  in this repository can make the request. `docs/AI_CODE_QUALITY.md` §2 counts
  it as the third reviewer beside `confidence-review` and
  `adversarial-reviewer`; **on every PR to date it is absent unless a human
  types `@coderabbitai review`.** `adversarial-reviewer` is the gate in its
  place, which costs the independence CodeRabbit had: two of the two remaining
  reviewers are the same model in different postures, and no tool with genuinely
  different weights reads this repository unless somebody asks for one.
  *Upgrade:* 10 stars, or a plan whose auto-review does not gate on them. A
  workflow driven by a personal access token would also work and is not worth a
  long-lived credential for this.

**Phase 4.**

- **Nodes run one at a time.** `SYSTEM_SPEC.md` §4 gathers the frontier
  concurrently; that waits for a provider call worth overlapping and for a store
  that can be awaited -- psycopg here is synchronous. Correctness does not
  depend on it: the frontier is recomputed each pass either way.
- **A node failure aborts the run rather than being retried.** `SYSTEM_SPEC.md`
  §11 says a crash mid-node loses the attempt and the next pass retries the
  node. Today the executor's exception propagates out of `run_route`. Retrying
  instead makes a stalled loop possible -- a node that fails forever leaves the
  frontier unchanged -- so the retry and the no-progress guard land together.
  *Upgrade:* with the provider boundary in Phase 5.
- **The loop never ends the run.** No node marks `runs.state` COMPLETE and no
  terminal event is emitted; `commit_terminal` exists and the loop does not call
  it. *Upgrade:* Phase 6, with the run surface.
- **`artifacts.node_id` carries a route node id from the loop and a module id
  from `commit_terminal`'s tests.** One column, two spellings, which is the
  defect `CONTEXT.md` exists to prevent. Nothing yet forces either.
  *Upgrade:* Phase 6, when the terminal path and the loop meet.
- **One flat price per node.** `_price()` returns `Decimal("1.00")` until a
  provider quotes a real one. It is both the reservation and the ceiling for
  that call: a charge above it is refused, so a provider cannot bill past what
  the budget agreed to.
**Phase 3.**

- **Nothing calls `pin_route` yet.** The pin exists and is binding once written,
  but no gate writes it: `pin_route` is reached only from tests, and no execution
  path reads `pinned_route`. Invariant 10 holds for anything that pins, and
  nothing pins. *Upgrade:* Phase 6's plan gate, and Phase 4's loop reading the
  pin instead of a passed-in route.
- **CP-CF is a route node with no module behind it.** The extension places it
  and the edges gate it, but no skill folder, calculator or registry entry
  exists yet, so a route carrying CP-CF resolves and cannot execute.
  *Upgrade:* Phase 5, which owns the registry and the calculator boundary, and
  the `cash_flow_forecast` work in `docs/DECISIONS.md` §8.
- **Nothing selects the model extension.** `resolve_route(..., model_extension=
  True)` is reached only from tests; no gate decides when a pathway gets its
  model effect. *Upgrade:* Phase 6's plan gate.

- **No CONDITIONAL edge exists in the pinned bundle.** `CONTEXT.md` lists it as
  a blocking edge type and `resolve_route` freezes predicates for it, but the
  catalog at build `a43cb903` declares zero of them (`docs/DECISIONS.md` §17).
  The code path will be written and cannot be exercised against real data.
  *Upgrade:* a bundle that uses the type, or a decision to drop it.
- **The bundle is verified at rest, not at use.** `tests/test_bundle_pin.py`
  hashes the vendored tree against its own manifest; nothing yet re-checks the
  bytes when a module is loaded, and no run records the build it ran under.
  *Upgrade:* Phase 5, which owns `assemble_authority` and the per-module
  `authority_digest`.

**Phase 1.**

- **`commit_terminal` assumes it opens the outermost transaction.** Called
  from inside a caller's transaction, `connection.transaction()` degrades to a
  SAVEPOINT: the writes are not durable when it returns, and the run row lock
  is held until the outer commit. Nothing asserts this. *Upgrade:* refuse a
  non-idle connection at entry, when the API layer brings real callers.
- **The schema holds the five tables Phase 1 writes,** not all of
  `SYSTEM_SPEC.md` §2. "In full at startup" is read as *one file applied
  whole, with no migrations* rather than *every future table exists now*;
  tables nothing writes cannot have their columns checked by a test.
  *Upgrade:* each phase adds its own tables to the same file.
- **Append-only is enforced on the four tables that exist.** `run_events`,
  `source_sets`, `source_set_members` and `delivered_evidence` each refuse
  UPDATE, DELETE and TRUNCATE. `run_attempts`, `deliverable_opinions`,
  `model_revisions` and `audit_events` are equally append-only in the spec and
  are not yet created. *Upgrade:* each carries both `refuse_rewrite` triggers in
  the phase that creates it, and
  `test_every_table_that_refuses_a_rewrite_also_refuses_a_truncate` fails until
  it does.
- **`artifacts` and `budget_ledger` refuse nothing.** Invariant 6 promises one
  artifact, one charge and one terminal event per run; only the event is
  guarded. `TRUNCATE budget_ledger` succeeds, and so does an UPDATE that
  rewrites a charge. `SYSTEM_SPEC.md` §2 does not list either table as
  append-only, so this is a spec question rather than a missing trigger --
  but a money ledger that can be rewritten is worth deciding on deliberately.
  `test_every_table_that_refuses_a_rewrite_also_refuses_a_truncate` cannot
  catch it: the query polices tables already wired to `refuse_rewrite`, so a
  table with no trigger at all is invisible to it. *Upgrade:* decide whether
  either is append-only, and if so give it both triggers.
- **The triggers stop an accident, not the application role.** The store
  connects as the owner of its own tables, so `ALTER TABLE delivered_evidence
  DISABLE TRIGGER ALL` followed by `TRUNCATE` succeeds -- verified. No
  least-privilege role exists; dev, CI and the tests all connect as `postgres`.
  The guards are worth having, and what they buy is a careless statement
  refused, not an untrusted caller contained. *Upgrade:* a role that owns no
  table and holds no TRUNCATE grant, in the phase that first deploys the store
  somewhere real.
- **Refusal is proven behaviourally for `run_events` only.** `source_sets`,
  `source_set_members`, `delivered_evidence` and `run_attempts` are covered
  structurally -- the pairing test asserts each carries both triggers, and
  `run_events` proves the shared `refuse_rewrite` function actually raises. A
  DELETE against the other four touches zero rows in a fresh schema, so it
  succeeds whether the trigger is there or not; a behavioural test needs a
  populated fixture per table. *Upgrade:* the slice that gives those tables
  real fixtures.
- **The identifier gates see only what git tracks.** A file added but not yet
  staged is invisible to `check_vocabulary.py` and `check_tested.py`, so
  `make check` can pass over code neither has read. *Upgrade:* stage before
  running the gates -- or have them scan the working tree and subtract
  .gitignore, which is what `git ls-files` was chosen to avoid re-deriving.
- **`check_vocabulary.py` cannot see a term used for two things.** It catches a
  synonym for a `CONTEXT.md` term, not one spelling carrying two concepts -- a
  layout `block_id` on `source_tokens` and the `block_id` of `source_blocks`
  passed it cleanly until a human read them together. *Upgrade:* unclear that a
  checker can do this; the control is review.
- **A quote must align to whole extracted tokens, and must not be hyphenated
  across a line.** A PDF that breaks `leverage` into `lever-` and `age` yields
  two tokens, and a module quoting `leverage` is refused. *Upgrade:*
  de-hyphenate at extraction, in the slice that adds real PDF extraction.
- **Citation anchoring is proven against a synthetic token index.** No real
  PDF has been extracted, so nothing shows that an extractor's blocks and
  lines are the ones this logic assumes. *Upgrade:* the extraction slice adds
  a real document fixture and re-runs these tests against it.
- **`delivered_evidence` is recorded and not yet read.** `read_evidence` writes
  what each node was handed, but `anchor_citation` still checks only the case,
  so a module can cite a document it was never delivered. Invariant 9 is half
  built: the ledger exists, the check does not. *Upgrade:* the next slice, which
  binds anchoring to the delivered set.
- **`admit_source` and `start_run` both mint a `cases` row.** Tenancy is
  created as a side effect, with no authority check at the boundary.
  *Upgrade:* the ingestion slice, where intake authority is decided.
- **Document-derived text is not `BoundaryText`.** `Block.text` and
  `Token.text` reach pinned state unvalidated; identifiers and digests do not
  (`docs/DECISIONS.md` §16). A document carrying a bidirectional override is
  stored as given. *Upgrade:* the extraction slice strips the control rather
  than refusing the document.
- **Nothing bounds the size of anything ingested.** Token text, block text,
  blob payloads and tokens per page are all unbounded, and `IO_BUDGET` counts
  round-trips rather than rows -- so one dense page is unbounded memory per
  citation. Invariant 8 says every ceiling refuses before overspend; the
  ingestion path has no ceilings. *Upgrade:* the extraction slice, which is the
  first code that knows how large a real document is.
- **Blocks are accepted as given.** Nothing checks that a block's page exists
  in the source, that blocks cover the document, or that they respect the size
  rule in `SYSTEM_SPEC.md` §5 (one per line while small, bounded line groups
  once not). *Upgrade:* the extraction slice, which is what produces them.
- **A source set can be pinned to sources from a single case only, and nothing
  yet reads it.** `read_evidence` is what makes a pinned set mean something.
  *Upgrade:* the next slice.
- **A source admitted with no tokens is accepted.** Every citation against it
  is then refused, which is correct but late; a scanned document with no text
  layer should be refused at intake. *Upgrade:* the ingestion slice.
- **A run's terminal event is the only event kind.** `RUN_COMPLETED` is
  written; failure and node-level transitions are not. *Upgrade:* Phase 4,
  with the frontier loop that produces them.
- **`run_events.seq` is allocated by `coalesce(max(seq), 0) + 1` with nothing
  serialising two allocators.** Today no two can run at once, but by accident
  rather than by design: `commit_terminal` holds the run row `FOR UPDATE`, and
  every `run_events` insert takes a KEY SHARE lock on that same row through the
  foreign key, so any other writer blocks behind it -- while `pin_route` is
  serialised against itself by the `run_routes` primary key. Two KEY SHARE
  holders are compatible with *each other*, so the first event kind emitted from
  a path holding neither guard gives two writers the same `seq` and a raw
  `run_events_pkey` violation -- verified: two concurrent inserts of an
  invented kind collide exactly so. *Upgrade:* the phase that emits node-level
  events allocates `seq` under the run row lock, with a two-connection test.
