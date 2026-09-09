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
- `server/engine/node.py` — `execute_module`: assemble, ask, validate, anchor,
  store. Nothing is written until every citation has been re-derived.
- `methodology/envelope.py` — the canonical envelope, validated against the
  bundle's own `CP_MODULE_PAYLOAD_BASE.schema.txt`.
- `server/provider.py` — the provider boundary: `ProviderCall`, `Completion`,
  `price_of`, `RecordedProvider` and the live client. Pinned to `claude-opus-5`.
- `server/boundary_text.py`, `server/digests.py`, `server/refusals.py` — the
  types every boundary uses.
- `methodology/bundle.py` — `open_bundle` and `Bundle.read`, the only reader of
  vendored bytes: no-follow handles, hashed against the manifest at every use.
  `methodology/registry.py` — `ModuleSpec`, `reference_files`, `module_spec` and
  `assemble_authority`. The catalog says what is live, the manifest says what its
  bytes are, and `_CARVE_OUTS` is the host's one override.
- `methodology/calculators.py` — `calculator_spec` and `run_calculator`. Host
  selection, work factors, and execution of verified bytes under `-I -S` in a
  private directory.
- `vendor/deploy-v/` — the methodology bundle, read-only and never edited
  (`docs/DECISIONS.md` §6). The gates do not scan it.
- `scripts/` — the five gates `make check` runs.

Arriving with their phase, and not yet present: `models/` — the build and the
workbook renderer (Phase 7); `frontend/` — one workspace, nine sections, static
export (Phase 9).

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
  PR or entered in the ledger below with its reason. SonarQube is the third
  reviewer and analyses without being asked, but it arrives after the PR is open
  and it reads rules rather than intent — it is not a substitute for either pass
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

- **The SAST gate does not scan `tests/`.** `make security` points bandit at
  `$(SEC_TARGETS)` and declares `$(SEC_UNSCANNED) = tests` to `scan_floors.py`,
  which refuses any tracked .py neither list claims -- so the omission is
  declared here rather than merely absent. Pointed at `tests/` as well, bandit
  reports 437 findings: 408 are B101 `assert_used`, because a suite is nothing
  but asserts, and the one HIGH is B613 `trojansource` on
  `test_a_case_id_carrying_a_bidi_override_never_reaches_the_store`, which
  needs a real `\u202e` in the source to prove invariant 2 refuses it. Both are
  the test doing its job, and `make security` fails on any finding, so scanning
  the suite means a skip list that would also mask those checks in `server/`.
  *Upgrade:* scan `tests/` with B101 and B613 skipped, the day a test helper
  does something a scanner should have an opinion about.
- **The vendored bundle carries no licence, and the repository is public.**
  `vendor/deploy-v/` is 349 files and 5.3 MB with no licence file, no copyright
  notice and no provenance statement -- searched for, not assumed. `LICENSE`
  carves it out and says so (`docs/DECISIONS.md` §30), which states this
  repository's position and does not obtain terms for redistributing somebody
  else's bytes from a public repository. Invariant 4 makes the bundle
  authority; it does not make it ours. *Upgrade:* terms from whoever authored
  Deploy V, or a private repository -- the copyright holder's call, and the
  only known gap in this ledger that code cannot close.
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
- **The third reviewer's configuration is not in this tree.** SonarQube Cloud
  analyses this repository automatically and posts `SonarCloud Code Analysis`
  (`docs/DECISIONS.md` §31), which is the property CodeRabbit never had: it runs
  without anyone asking. What follows the repository is one line —
  `.sonarcloud.properties` excluding `vendor/`. The quality gate's conditions,
  the rule set, and whether automatic analysis stays enabled at all are settings
  in SonarQube Cloud that no test here can read, so the gates cannot tell a
  weakened gate from a passing one. `test_nothing_here_starts_a_scanner_of_its_own`
  covers the one failure a commit can cause — a CI scanner job, which would fail
  against a project under automatic analysis and take the build with it.
  *Upgrade:* none available while automatic analysis is the mechanism. Turning
  it off for a CI scanner would put the configuration back in the tree and cost
  a `SONAR_TOKEN` plus a job that has to be kept green; it is a trade, not a
  fix.
- **`.sonarcloud.properties` is unverified from here.** It is the file automatic
  analysis reads — `sonar-project.properties` is the scanner CLI's and is
  ignored — but nothing in this repository can prove the exclusion took effect,
  and a pull-request analysis only reports on the diff, so `vendor/` being
  judged or not judged does not show up on a PR. Its authoritative equivalent is
  the project's Analysis Scope settings in SonarQube Cloud.
  *Upgrade:* read the project's measures once, and set the exclusion in the UI
  instead if the file did nothing.
- **Nothing replaces `.coderabbit.yaml`'s `path_instructions`.** They asked a
  reviewer to flag a float on a money path, a `str(exc)` on a wire response, a
  model without `extra="forbid"`, a synonym for a `CONTEXT.md` term. SonarQube
  runs its own rules and takes no such prompt, so those four now rest on `ruff`
  (BLE, TRY), `check_vocabulary.py`, the named tests and `adversarial-reviewer`
  — where they already rested, since no CodeRabbit review ever ran unasked.
  Invariant-level review is still one model reading its own work.
  *Upgrade:* a custom rule set, or a lint rule per invariant, the day one of
  these is missed in review rather than caught by a test.
- **No coverage reaches the analysis.** Nothing emits a coverage report and
  automatic analysis imports none, so the quality gate's coverage condition has
  no metric to evaluate; the `SonarCloud Code Analysis` check on PR #41 passed
  reading 0.0% on new code. Adding coverage is a new dependency and therefore a
  decision entry and a lock recompile, which is a different concern from this
  one. *Upgrade:* the slice that first wants a coverage floor.

**Phase 5.**

- **The registry declares identity and folders, not execution.** `ModuleSpec`
  carries `module_id`, `skill_slug` and `reference_files`. `SYSTEM_SPEC.md` §3
  also lists execution mode, `max_output_tokens`, `calculators`,
  `derived_projections`, `source_mode` and `plan_approval`; nothing reads any of
  them yet, and a field no caller reads is a field no test can constrain.
  *Upgrade:* each arrives with the slice that reads it — `calculators` with the
  calculator boundary, the rest with the provider boundary.
- **No run records the build it ran under.** `Bundle.build_id` is read and
  `Authority` carries it, and no `runs` column holds it, so "a run pinned to one
  build never executes under another" is enforced nowhere. Nothing executes a
  module yet, so there is no execution to refuse. *Upgrade:* the slice that runs
  CP-1, which is the first caller with a run to bind.
- **Three `references/` workbooks are authority the host does not deliver.**
  CP-3 has two and CP-6 one, all `.xlsx`. `reference_files` allowlists `.md`,
  `.txt` and `.json` because authority reaches a module as prompt text, so a
  module whose reference is a workbook is given everything except that.
  `test_a_binary_reference_is_not_delivered_as_text` pins the set at three.
  *Upgrade:* the slice that gives a module a non-text attachment, if one ever
  needs to; otherwise a decision that these three are host-side inputs.
- **`MANIFEST_SHA256` refuses an accident, not an author.** It is the only
  cover for `DEPLOY_V_INTEGRITY_v1.json`, which is the one vendored file no
  manifest entry covers — verified by
  `test_the_manifest_is_the_only_uncovered_vendored_file`. It stops a partial
  edit, a bad merge and a corrupt checkout. Anyone with commit rights edits the
  constant and `vendor/` in one commit. *Upgrade:* a signature over the bundle
  from a key this repository does not hold, which is a supply-chain decision
  rather than a code one.
- **Nothing bounds the size of an assembled authority.** CP-OS aside, the
  largest module reads its `SKILL.md`, up to 20 reference files and the 48 KB
  shared canon on every call, with no ceiling and no cache. Invariant 8 says
  every ceiling refuses before overspend; assembly has none because nothing
  downstream has a token budget to overspend yet. *Upgrade:* with
  `max_output_tokens` and the provider boundary.
- **`execute_module` opens the bundle twice** -- once directly and once inside
  `assemble_authority` -- about 2.6 ms per node. Verification at use is the
  point, so the duplicate is honest rather than wrong. *Upgrade:* pass the
  open bundle down, when a node call is worth 1.3 ms.
- **A malformed `document_sha256` in a citation refuses as `DIGEST_INVALID`,**
  from `checked_digest`, rather than a citation-shaped code. Public-safe
  either way; it names the wrong layer. *Upgrade:* when the refusal codes
  reach a surface a person reads.
- **The loop and `execute_module` have not met.** `run_route` still takes an
  arbitrary `Executor` and prices every node at a flat 1.00; `execute_module`
  computes a real charge from reported usage and no loop calls it.
  *Upgrade:* Phase 6, with the run surface.
- **`max_output_tokens` is one constant for every module.** `SYSTEM_SPEC.md`
  §3 puts it on `ModuleSpec`; no module has needed a different ceiling yet.
  *Upgrade:* the first module that does.
- **`artifacts.node_id` still carries two spellings.** `execute_module` works
  in route node ids throughout, which settles what the loop writes, and
  `commit_terminal` is still exercised with module ids. Changing that is a
  separate concern from this slice. *Upgrade:* Phase 6, unchanged.
- **No live provider call has ever run.** Every provider test drives the real
  SDK against a mock transport, which is a real check of the request body and
  the refusal mapping and is not a check that the API accepts the combination
  of `thinking: adaptive` and `output_config.effort` this host sends. The one
  test that would prove it, `test_the_live_provider_returns_a_completion`, is
  `-m live_provider` and skips without a credential; none was available in the
  environment that wrote it. *Upgrade:* run it once with a key.
- **A credential means an environment variable, not an `ant` profile.** The SDK
  would resolve a profile from disk; honouring it would let a developer's
  machine spend money in a suite meant to be free (`docs/DECISIONS.md` §28).
  A machine with a profile and no environment variable gets no live provider.
  *Upgrade:* an explicit opt-in variable, if anyone wants profiles.
- **The loop still prices every node at 1.00.** `price_of` computes the real
  charge from reported usage and nothing calls it: `server/engine/loop.py`
  keeps `_price()`. *Upgrade:* the slice that runs CP-1, which is the first
  caller with a `Completion` to price.
- **A calculator's stdout is bounded in memory, not on disk.** `_captured`
  writes the child's stdout to a file and refuses on `st_size` before reading a
  byte, so the host cannot be OOMed. Nothing bounds what the child writes to
  that file first, so a runaway calculator can fill the temp filesystem within
  its 30-second ceiling. *Upgrade:* `RLIMIT_FSIZE` on the child — deliberately
  not taken now, because `preexec_fn` is the only stdlib way to set it and its
  fork-safety caveats do not belong in what becomes a threaded API process.
- **The sandbox is `-I -S`, a scrubbed environment, a private cwd and a process
  group kill.** It stops the child reaching the host's installed packages —
  verified, and `-I` alone does not — but it is not a sandbox: no seccomp, no
  network namespace, no memory limit. A calculator can still open a socket using
  the standard library. The mitigation is that the code is pinned, read-only and
  digest-checked at use. *Upgrade:* a real jail, if a calculator ever runs
  anything but bundle-resident code.
- **`-S` will not survive Phase 7.** It works because every calculator declared
  today is standard-library only. The bundle ships `scripts/requirements.txt`
  and `CP-MEMO_requirements.txt`, so `cp_model_v3` and `cp_memo` have
  third-party dependencies and will need site-packages the host chooses.
  *Upgrade:* a per-calculator dependency set, resolved by the phase that first
  declares one.
- **Existing calculators take JSON floats.** Invariant 7 wants Decimal on any
  money path; `credit_metrics` computes in float, as `SYSTEM_SPEC.md` §6.1
  records deliberately. The host refuses non-finite input via `allow_nan=False`
  on the way in and takes the vendor's numbers as given on the way out.
  *Upgrade:* `cash_flow_forecast`, which is Decimal end to end by contract.
- **Vendored authority text is not `BoundaryText`.** `Bundle.read` checks the
  digest and that the bytes decode as UTF-8, nothing more, and that text goes
  straight into a prompt. `docs/DECISIONS.md` §16 rules on identifiers and on
  document text; vendored authority is a third category nobody has ruled on. A
  bidirectional override in an upstream markdown file is delivered as written.
  Trusting it follows from invariant 4 — the bundle *is* the authority — but it
  is a decision nobody has made rather than one that has been made.
  *Upgrade:* a decision entry either way, in the slice that first sends
  authority to a provider.
- **CP-CF has no skill folder.** `_CALCULATORS`, `cp-cf-cash-flow-engine` and
  the calculator boundary are the next slice; a route carrying CP-CF still
  resolves and still cannot execute.

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
- **A drifted store is refused at startup, not repaired.** `CREATE TABLE IF NOT
  EXISTS` is a no-op on a table that already exists, so *adding* a table to
  `schema.sql` works and *widening* one silently does not. `apply_schema`
  applies the file a second time into an empty schema and refuses a store whose
  columns, constraints, indexes or triggers differ (`docs/DECISIONS.md` §27).
  What it does not do: a schema that was **empty** before the file was applied
  is not compared at all -- there is nothing to have drifted from, and the
  comparison costs a second full apply; a mismatch is reconciled by a
  hand-written `ALTER TABLE`, because generating one is a migration engine; it
  reads the whole schema `search_path` resolves to, so an object some other
  thing owns there -- an extension's table in `public` -- reads as drift rather
  than as unrelated; and it needs CREATE on the database to make the schema it
  compares against, which a least-privilege role would have to be granted.
  *Upgrade:* the phase that first deploys the store somewhere real, which is
  where an extension, a second owner or that role could appear.

- **`apply_schema` needs a transaction, and nothing asserts it.** The file is
  applied before the comparison can be made, so the caller's rollback is what
  un-applies a store the check then refuses. On an autocommit connection the
  refusal arrives *after* the store was changed -- the opposite of
  `SYSTEM_SPEC.md` §11 -- and a failure part-way leaves the comparison schema
  and a moved `search_path` behind. Same shape as `commit_terminal`'s
  assumption above, and it gets the same answer for the same reason: no caller
  outside the suite exists yet. *Upgrade:* refuse a connection in autocommit at
  entry, when the API layer brings real callers.

- **Two processes applying the schema at once can refuse each other.** The
  comparison reads the live schema while another instance may be half way
  through applying the same file, and a partial read is drift. `SYSTEM_SPEC.md`
  §11 runs one `api` and one `worker`, which is two processes. *Upgrade:* a
  `pg_advisory_xact_lock` around the apply, in the phase that first starts both.

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
- **The identifier gates and the SAST floor see only what git tracks.** A file
  added but not yet staged is invisible to `check_vocabulary.py`,
  `check_tested.py` and `scan_floors.py --cover`, so `make check` can pass over
  code none of them has read. bandit walks the filesystem rather than the index,
  so it does scan that file and its findings still fail the gate; what the floor
  cannot do is *require* it to have been scanned. *Upgrade:* stage before
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
