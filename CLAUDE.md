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
- `server/engine/plan.py` — the plan gate. `Plan`, `plan_preview`, `plan_gate`,
  `open_plan_gate` and `approve_plan`: the one place a route is pinned, and only
  against content a person approved (`docs/DECISIONS.md` §33).
- `server/store/` — Postgres owns everything transactional.
  `server/store/schema.sql` is applied whole at startup, with no migrations.
  The write paths are `server/store/runs.py`, `server/store/attempts.py`,
  `server/store/routes.py`, `server/store/gates.py` (digest-bound interrupts),
  `server/store/members.py` (case standing, read where a gate is released),
  `server/store/sources.py` (admission) and `server/store/source_sets.py`
  (pinning); `server/store/events.py` is the one emitter every run event is
  allocated through, and `server/store/blobs.py` is the content-addressed blob
  store.
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
- `make dev` — fails until the first HTTP route exists (Phase 6).
- `make test` — the suite. `make test-model` additionally requires LibreOffice.
- `make check` — lint, types, tests, security, in that order.
- The model job needs `soffice` on PATH. Without it the workbook build fails
  closed by design (`MODEL_BUILDER_SPEC.md` §5) — a green model suite with
  soffice absent is a vacuous pass.

## Known gaps (honest ledger)

Every accepted limitation gets an entry here with its reason and its upgrade
path, in the same breath as the code that creates it. An empty ledger on a
system this size means nobody looked.

An entry that defers to *a slice* — the extraction slice, the ingestion slice,
the run surface, the API layer — defers to the current phase, the lowest whose
exit test does not pass. `docs/REBUILD_PLAN.md` lists under that phase what the
exited phases still owe, each with the test it owes (`docs/DECISIONS.md` §38).

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
- **The third reviewer's scope is now editable by the agent it reviews.**
  `docs/DECISIONS.md` §41 moved the analysis from SonarQube Cloud's own side
  into the `sonarqube` CI job, because automatic analysis imports no coverage
  report and there is no setting that changes that. §31's property is spent:
  `sonar.sources`, `sonar.exclusions` and the coverage path are in
  `sonar-project.properties`, in the same pull request they judge. An agent that
  wanted a clean analysis could narrow the source list in the diff under review.
  What still stands: the quality gate's conditions remain in SonarQube Cloud, so
  the *verdict* is not in the tree even though the *scope* is; and three tests
  hold the scope — `test_the_analysis_claims_every_tracked_python_file`,
  `test_the_coverage_floor_measures_what_the_analysis_reads`, and
  `test_exactly_one_job_submits_the_analysis`. Each of those a determined author
  could edit in the same diff, which is the difference between a control and a
  speed bump, and is why this is a ledger entry rather than a footnote.
  *Upgrade:* none available in this repository. A scope that the code's author
  cannot edit means a scanner nobody here configures, and that is the
  arrangement §41 gave up to obtain a coverage metric. The alternative worth
  having is a branch ruleset condition on the analysis' own reported scope,
  which SonarQube Cloud does not offer today.
- **Two analysis configurations exist, and which one is live is not readable
  from here.** `.sonarcloud.properties` is automatic analysis' and
  `sonar-project.properties` is the scanner's; the switch between them is a
  setting in SonarQube Cloud (`docs/DECISIONS.md` §41). While both exist,
  `test_both_analysis_configurations_declare_the_same_scope` keeps their sources,
  tests, Python version and exclusions identical, so whichever is being read says
  the same thing. What no test here can tell is *which*, so a coverage report is
  either imported or silently absent depending on a setting this tree cannot see.
  *Upgrade:* delete `.sonarcloud.properties` in the commit that confirms the
  `sonarqube` job is posting the check — which is a person reading the checks on
  a pull request, not a test.
- **The check name under CI analysis is unverified.** `SonarCloud Code Analysis`
  is a required check on `main`, bound to the SonarQubeCloud app
  (`docs/DECISIONS.md` §34), and it was the name posted under *automatic*
  analysis. Nothing in this repository can read the ruleset or the check name,
  and nothing tried the CI-submitted path before §41, so whether the app posts
  the same name is not known here. If it does not, the required check never
  reports and blocks every merge — §14's hazard, from the direction §34 did not
  cover — until someone edits the ruleset to the new name.
  *Upgrade:* read the checks on the first pull request that runs the
  `sonarqube` job, and the first analysis on `main` after it merges. This is
  the one entry in this ledger with a deadline rather than a phase.
- **`sonar-project.properties` is verified by the project's analysis warnings,
  and by nothing in this tree.** An earlier version of the analysis config
  declared only `sonar.exclusions`, and SonarQube Cloud's *Analysis warnings*
  said what that cost: `sonar.tests` unset, so SonarPython found test-shaped
  files and ran production rules on none of them — 29 files under neither rule
  set; and `sonar.python.version` unset, so every rule was evaluated against all
  of Python 3 at once. Both are declared, and the warnings are the only place
  either could have been noticed: a pull-request analysis reports on the diff,
  so a rule that never ran shows up as nothing rather than as a finding.
  The same holds for the `vendor/` exclusion, which no test here can prove took
  effect. What the suite pins is that the *file* says the right thing —
  `sonar.sources` and `sonar.tests` between them claim every tracked .py,
  `sonar.python.version` matches the type gate's interpreter, and the coverage
  path matches what the suite writes. Whether SonarQube read it is a question
  only SonarQube answers. Under §41 a pull request's own analysis does read this
  file, which is one thing automatic analysis could not do — the scanner runs
  from the branch, so an ignored key shows up on the pull request that
  introduced it rather than only after merge.
  *Upgrade:* read the analysis warnings on the first pull request that runs the
  `sonarqube` job. The authoritative equivalent, if the file is ever ignored
  wholesale, is the project's Analysis Scope settings.
- **Nothing replaces `.coderabbit.yaml`'s `path_instructions`.** They asked a
  reviewer to flag a float on a money path, a `str(exc)` on a wire response, a
  model without `extra="forbid"`, a synonym for a `CONTEXT.md` term. SonarQube
  runs its own rules and takes no such prompt, so those four now rest on `ruff`
  (BLE, TRY), `check_vocabulary.py`, the named tests and `adversarial-reviewer`
  — where they already rested, since no CodeRabbit review ever ran unasked.
  Invariant-level review is still one model reading its own work.
  *Upgrade:* a custom rule set, or a lint rule per invariant, the day one of
  these is missed in review rather than caught by a test.
- **Coverage is measured and imported; no percentage is enforced here.**
  `docs/DECISIONS.md` §41 closed the gap that said no coverage reached the
  analysis at all. What replaced it is narrower: `scan_floors.py --cobertura`
  refuses a report that measured nothing or that left out a tracked file, which
  is a floor on the report's *completeness* and not on its *number*. Nothing in
  this tree fails a build at 12% — the only condition that does is the quality
  gate's, in SonarQube Cloud, where it applies to new code and where this
  repository cannot read it. So a change that lowers overall coverage merges
  green as long as the lines it adds are covered.
  *Upgrade:* `--cov-fail-under` with a number, the day somebody is prepared to
  defend one. It is deliberately not set to today's figure: a floor picked to
  match what happens to pass is a floor that has never refused anything.
- **Coverage counts the tests that ran, and CI runs the suite twice.** The
  `test` job writes the report and the `postgres` job re-runs part of the suite
  without writing one, so a race proven only in the second job counts as
  uncovered. Harmless to the number's direction — it understates rather than
  overstates — but it means the figure is not "what this suite exercises".
  *Upgrade:* combine the two reports with `coverage combine`, if the second job
  ever holds a path the first does not.
- **A fork's pull request cannot run the analysis.** `SONAR_TOKEN` is a
  repository secret and is not exposed to workflows from forked repositories, so
  the `sonarqube` job fails there and the required check never reports. Every
  pull request in this repository to date is from a branch in the repository
  itself, so this has never happened. *Upgrade:* a `pull_request_target` split,
  the day an outside contributor opens one — which is a change to how untrusted
  code is run in CI and needs its own decision entry.

**Phase 6.**

- **`test_every_exit_test_of_an_exited_phase_exists` checks that a plan-named
  test was written, not that it passes.** Passing is the suite's job, and a
  named test that skips — `test_the_live_provider_returns_a_completion` without
  a credential — counts as written. It refuses the failure three phases had, a
  phase exited on a test nobody wrote; it cannot refuse a phase exited on a
  test that skips. *Upgrade:* refuse a skipped exit test, the day CI holds a
  credential to run the live one.
- **No node is BLOCKED on a gate.** The plan gate opens one and releases one,
  so `open_gate` and `approve_gate` now have a real caller -- but `node_states`
  never consults `gate_released`, so `SYSTEM_SPEC.md` §4's "BLOCKED on a host
  predicate" is still a shape nothing takes. A run whose gate is open is
  RUNNABLE at its first node exactly as if it were not. *Upgrade:* the slice
  that runs the loop against a pinned route, which is the first code with a
  frontier to hold back.
- **Nothing constructs a `Plan`.** `open_plan_gate` and `approve_plan` are
  reached only from tests. Nothing chooses a pathway, decides whether the model
  extension applies, or renders the preview to a person -- the plan gate binds
  those choices and does not make them, and `plan_preview` returns text rather
  than anything a person would read on a screen. *Upgrade:* the run surface,
  which is the first caller with an analyst in front of it.
- **The plan gate binds a source set nothing checks for withdrawal.** Invariant
  1 says withdrawal is checked live at every use, and the plan preview is a use:
  it shows a person the documents a run will read. Nothing implements withdrawal
  anywhere -- there is no column, no check in `read_evidence`, and no path that
  sets one -- so this is inherited rather than created here, and it is named
  here because this is the first surface that puts a document list in front of
  someone. *Upgrade:* the slice that adds withdrawal, which has to reach the
  plan gate and `read_evidence` together.
- **The `RESEARCH_PLAN` gate has no caller.** `GateKind` declares it and
  `docs/REBUILD_PLAN.md` Phase 6 names research-plan approval beside source-set
  pinning; CP-DR's brief has no gate, so only `SOURCE_SET` is ever opened.
  *Upgrade:* the slice that resolves a route with a research brief, which is
  the first one with a plan to approve.
- **`approve_plan` assumes it opens the outermost transaction.** It opens one
  so the release and the pin commit together, and inside a caller's transaction
  `connection.transaction()` degrades to a SAVEPOINT: the pair stays atomic
  relative to that caller, and is not durable when `approve_plan` returns.
  Identical in shape to `commit_terminal`'s and `apply_schema`'s assumptions
  below, and it gets the same answer for the same reason. *Upgrade:* refuse a
  non-idle connection at entry, with the slice that fixes all three.
- **An approval checks case standing, not global role.** `approve_gate` reads
  `case_members` under the run row lock and refuses a release by anyone who is
  not `APPROVER` or `ADMIN` on the run's case, holding the row `FOR SHARE` so a
  revocation waits for the release rather than landing inside it
  (`docs/DECISIONS.md` §39). `SYSTEM_SPEC.md` §8 wants global role rechecked
  there too, and nothing derives one: there is no served identity, so the
  store call is handed an approver's name and can check only what the store
  holds about it. *Upgrade:* identity derivation with the first HTTP route,
  which is what turns a header or an OIDC group into a role the call can be
  handed.
- **`case_members` is current membership, with no history and no guard.** A
  grant, a change of standing and a revocation each rewrite the row in place,
  and nothing records who did it or when the previous standing ended; the
  audit chain that would is owed by this phase. A raw `DELETE` on the table is
  a revocation nobody made, and a raw `UPDATE` a grant nobody gave. *Upgrade:*
  `audit_events`, with `test_a_governed_write_commits_its_audit_event_or_nothing`,
  which makes a membership change a governed write.
- **There is no `users` table.** `SYSTEM_SPEC.md` §2 lists one under tenancy.
  `member_id` is the same text an approval records in `approved_by`, and
  nothing yet joins it to a person. *Upgrade:* identity derivation, which is
  the first thing with a person to record.
- **Granting and revoking standing check nothing about who is doing it.**
  `grant_membership` and `revoke_membership` take no actor: any caller holding
  a connection can make anyone `ADMIN` on any case, or strip a case's last
  `ADMIN`, and then release its gate through the check this slice added. The
  release is guarded and the thing that confers the standing to release is
  not, which is a privilege-escalation path the moment a route wraps either
  call. It is not closed here because the rule that closes it is intake's:
  who a case's first member is follows from who admitted it, and
  `admit_source` and `start_run` still mint cases with no authority check
  (Phase 1, below). Guarding the grant with an `ADMIN` check and leaving that
  bootstrap open would be the asymmetry the release entry refused. *Upgrade:*
  identity derivation and intake authority together, with the actor matrix --
  `test_a_grant_needs_admin_standing_on_the_case`.
- **At the store, an unknown run and an unauthorised one are different
  codes.** `lock_run` refuses `RUN_NOT_FOUND` before the case is known, so
  `STANDING_INSUFFICIENT` can only follow it, and a caller with no standing
  anywhere can tell a run that exists from one that does not. `SYSTEM_SPEC.md`
  §8 collapses both into one 404 at an edge that does not exist yet, and
  nothing here pins that it will. *Upgrade:* the first HTTP route, with
  `test_unauthorised_case_is_private_404`.
- **Nobody has ruled on independence at the plan gate.** `open_gate` takes no
  actor -- the host parks the run; a person does not -- so the store cannot
  say who derived the plan, and an `APPROVER` or `ADMIN` may release it
  whoever that was. `SYSTEM_SPEC.md` §7 wants filing to refuse the opinion's
  signer and its freezer; nothing says whether the plan gate wants the same,
  and a rule nobody wrote is not one this slice should invent. *Upgrade:* a
  decision entry, and Phase 8's independence check if the answer is yes.
- **A `run_id` that is not a UUID escapes as a psycopg error, not a refusal.**
  Every store signature takes `run_id: str` and every `runs` lookup compares it
  to a `uuid` column, so a malformed id raises `InvalidTextRepresentation`
  carrying the offending string rather than `RUN_NOT_FOUND`. Caller input, not
  document text, so nothing governed leaks -- but `SYSTEM_SPEC.md` §8 wants an
  unknown run and an unauthorized one to be indistinguishable, and an
  unparseable one is neither. `lock_run` inherits the shape rather than
  introducing it. *Upgrade:* the run surface, where a path parameter is parsed
  once and a bad one is the same private 404 as any other unknown run.
- **`run_gates` carries no rewrite guard.** It needs the UPDATE path the
  re-open uses, so `refuse_rewrite` would refuse the one thing the table exists
  to allow. A raw `UPDATE` therefore moves the asked content under a person who
  is mid-review, and a raw `DELETE` removes an undecided gate -- a released one
  is held by the approval ledger's foreign key. `open_gate` refuses both under
  the run row lock; the store does not, and
  `test_every_table_that_refuses_a_rewrite_also_refuses_a_truncate` cannot see
  it, because that query polices tables already wired to `refuse_rewrite`.
  *Upgrade:* a second guard function permitting only the undecided re-open,
  with the catalogue test taught to police it as it polices the first.
- **A gate event does not say which gate.** `GATE_OPENED` and `GATE_APPROVED`
  carry no kind. That follows `SYSTEM_SPEC.md` §9 -- the client never reads
  event payloads, an event name triggers a refetch -- and it means the event
  ledger records when a gate moved but not which of the two it was. The
  approval ledger says that for a release; nothing says it for an opening.
  *Upgrade:* the SSE slice, if the run view cannot answer it from `run_gates`.
- **`emit` assumes it is inside a transaction, and nothing asserts it.** On an
  autocommit connection `lock_run` takes a row lock that is released before the
  insert runs, so the sequence it allocated is not the sequence it keeps --
  which is the collision the lock exists to prevent, reintroduced by the
  caller. Every caller today opens one. Same shape as `commit_terminal`'s and
  `apply_schema`'s assumptions below, and it gets the same answer for the same
  reason; `require_standing` shares it, since its `FOR SHARE` is released with
  the transaction it was taken in. *Upgrade:* refuse a connection in autocommit
  at entry, with the slice that fixes all four -- the API layer, which is what
  brings callers this file did not write.

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

- **`pin_route` has a gate, and `pinned_route` still has no reader.**
  `approve_plan` is what writes the pin, so invariant 10's "digested at the plan
  gate" is now a thing that happens. What still does not happen is execution
  reading it: `run_route` calls `pinned_route`, and nothing calls `run_route`
  outside its own tests. *Upgrade:* the slice that runs the loop against a
  pinned route.
- **CP-CF is a route node with no module behind it.** The extension places it
  and the edges gate it, but no skill folder, calculator or registry entry
  exists yet, so a route carrying CP-CF resolves and cannot execute.
  *Upgrade:* Phase 5, which owns the registry and the calculator boundary, and
  the `cash_flow_forecast` work in `docs/DECISIONS.md` §8.
- **The model extension is bound but still not chosen.** `Plan.route` carries
  whatever `resolve_route(..., model_extension=...)` produced, and the plan gate
  digests it, so approving a plan without the model effect cannot release a run
  that builds one -- `test_the_model_extension_is_part_of_what_is_approved`.
  What is still missing is anything that *decides* the flag: every caller is a
  test. *Upgrade:* the run surface, with the rest of plan construction.

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
  passed it cleanly until a human read them together. `source_set_members`
  and `case_members` are the second instance: the first holds documents, the
  second people, and `CONTEXT.md` gives *membership* to the case, so the older
  table is the one misnamed. Renaming it is its own slice. *Upgrade:* unclear
  that a checker can do this; the control is review.
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
