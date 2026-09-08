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
  transaction, and every event insert rides a conditional update — zero rows
  updated, no event. That is what makes terminal events exactly-once.
- **Boundary text.** Every string that can reach pinned state, a revision, a
  frozen payload or an audit event carries `BoundaryText`, never a bare `str`.
  NFC-normalised before the length bound; rejects lone surrogates, Cc controls
  except CR/LF/TAB, and bidirectional override/isolate controls.
- **Auth edge.** Development trusts a role header; production derives role from
  OIDC groups only. Unknown and unauthorized both return 404.
- **Persona is not authority.** The section on screen composes the view and
  grants nothing. Every governed action is checked server-side at commit time.

## Where things live

- `engine/route.py` — `resolve_route`, `dependency_order`, `node_states`,
  `frontier`. Typed edges from `profile["edges"]`, never from
  `navigation.dependencies`.
- `engine/runtime.py` — the frontier loop. No checkpointer: recovery is
  recomputation from the accepted-attempt ledger.
- `storage/` — Postgres owns everything transactional; bytes are content-
  addressed in the blob store.
- `methodology/` — bundle verification, the registry (the only seam for adding
  or upgrading a module), and the calculator execution boundary.
- `models/` — the build, and the workbook renderer that must match
  `docs/MODEL_BUILDER_SPEC.md`.
- `frontend/` — one workspace, nine sections, static export.

## Rules of work

- **Test first.** The failing test names the invariant or the behaviour. This is
  the single highest-value control against the +75 % logic-error rate.
- **One concern per PR.** If the diff grows a second concern, split it.
- **Never log document-derived text.** Log the typed code, never `str(exc)`.
- **No new dependency without a dated decision entry.** Locks are fully pinned
  and hashed; the image and CI install with `--require-hashes`.
- **A scanner that scanned nothing is a failure**, not a pass.
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
- **`check_tested.py` matches a name as a whole word anywhere in the suite's
  bytes,** docstrings and comments included. It catches the definition no test
  mentions, not the definition whose test asserts nothing. *Upgrade:* resolve
  references through the AST once the suite is large enough for the false
  negatives to matter.
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
- **CodeRabbit reviews nothing while PRs are stacked.** It is installed and
  live, reading `.coderabbit.yaml`, but auto-review is skipped on any PR whose
  base is not the default branch — and each phase stacks on its predecessor to
  stay under the 800-line size gate. `docs/AI_CODE_QUALITY.md` §2 counts it as
  the third reviewer; on a stacked PR it is absent. *Upgrade:* `@coderabbitai
  review` per stacked PR, or merge each phase to `main` before opening the
  next so the base is the default branch.
**Phase 3.**

- **`pin_route` does not exist yet.** `route_digest` computes what the plan gate
  will pin, and nothing writes it to `run_routes` or reads execution from a pin.
  Resolution is pure and replayable; the pin that makes invariant 10 binding is
  the gate slice. *Upgrade:* the next slice, with the run surface.
- **The model extension is not built.** `CP-CF` rides a host-declared extension
  with synthesised `REQUIRED` edges from CP-1, CP-2G and CP-4
  (`SYSTEM_SPEC.md` §6.2), and `test_cp_cf_waits_for_all_required_owners` and
  `test_model_extension_refuses_missing_owner` are unwritten. *Upgrade:* the
  next slice.

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
- **Append-only is enforced by trigger on `run_events` alone.**
  `run_attempts`, `deliverable_opinions`, `model_revisions` and `audit_events`
  are equally append-only in the spec. *Upgrade:* each carries the same
  `refuse_rewrite` trigger in the phase that creates it.
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
