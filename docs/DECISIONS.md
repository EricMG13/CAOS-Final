# Decision record

Binding. Later entries override earlier ones. Every entry is dated, states what
was decided, and states the reason — a decision without a reason cannot be
revisited intelligently.

---

## 2026-09-08 §1 — Rebuild rather than refactor

The predecessor tree (29k lines of server code, 35k of tests) is sound in its
invariants and wrong in three structural choices: a precompiled LangGraph per
route, a SQLite/Postgres split, and route resolution built from the catalog's
untyped display list. The first two are removable; the third invalidates every
route the system has ever run. Rebuilding is cheaper than unpicking, and the
invariants transfer intact.

## 2026-09-08 §2 — Runtime DAG follows legacy

The route is resolved from `profile["edges"]` with typed edges
(`REQUIRED`/`CONDITIONAL`/`QA_GATE` blocking, `OPTIONAL`/`ADVISORY` soft until
the source is READY), node states `COMPLETE`/`BLOCKED`/`RESTRICTED`/`RUNNABLE`,
and a frontier of runnable plus restricted. Invariant 10 is not weakened but
re-pinned: the *resolved* route is digested at the gate and execution reads only
the pin.

**Reason.** The predecessor read `navigation.dependencies` — 97 untyped pairs
meant for display — so 25 OPTIONAL and 22 ADVISORY edges were enforced as
mandatory, the single QA_GATE did not gate, and RESTRICTED could not occur.

## 2026-09-08 §3 — No checkpointer

Execution state is the accepted-attempt ledger. Recovery is recomputation of
`node_states`, not restoration of a checkpoint.

**Reason.** A legacy-style route cannot be precompiled, so a graph framework's
checkpoint buys nothing the run store does not already own — and the split
between checkpoint and domain state was the source of most of the
predecessor's recovery machinery.

## 2026-09-08 §4 — PostgreSQL only

One database from the first commit, including run state. No SQLite tier.

**Reason.** Five entries on the predecessor's known-gaps ledger existed only
because of that split.

## 2026-09-08 §5 — CP-PARSE stays a separate host node

The upstream bundle merges CP-PARSE into CP-0. The host keeps them as separate
stage-0 nodes via an `_ALIASES` carve-out, overriding both the new
`superseded_module_ids["CP-PARSE"]` entry and `preparation_stage.runnable:
false`.

**Reason.** CP-PARSE owns the `document_parse_manifest` over the host's own
already-extracted immutable blocks. That object is host territory. Revisit if a
future bundle collapses the two schemas.

**Consequence.** `assemble_authority` must not slice `SKILL.md` on section
markers — the merged skill has dropped `## CP-PARSE runnable profile`, which
would break CP-0 as well as CP-PARSE. CP-PARSE receives the whole CP-0 skill
plus its own reference files.

## 2026-09-08 §6 — Never edit an upstream bundle file

New behaviour goes in new skill folders. New route nodes ride a host-declared
extension mirroring `research_extension`, never a catalog edit.

**Reason.** One Deploy V release changed 175 files including 21 of 22
`SKILL.md`. Every upstream file we touch becomes a permanent merge and moves the
whole-tree pin.

## 2026-09-08 §7 — LibreOffice is required, not optional

`soffice` is the workbook's formula verification engine and is installed in the
worker image. The build fails closed without it.

**Reason.** Reverses an earlier recommendation made before reading
`cp_model_v3/builder.py`. Legacy recalculates through soffice and then validates
the sheet registry, the formula inventory and every computed value against an
independently computed expectation. The predecessor shipped LibreOffice and
never invoked it, so its workbooks were never evaluated at all — a formula
resolving to `#DIV/0!` shipped silently.

## 2026-09-08 §8 — `cash_flow_forecast` and CP-CF

A deterministic forecast calculator, and the module that declares it, both in a
new skill folder.

**Reason.** CP-2G states its roll-forward rules in prose and emits 42 driver
rows; no host code computed the projection, so leverage and coverage were
recomputed deterministically over arithmetic a model performed.

## 2026-09-08 §9 — Coordinate-anchored citations (invariant 11)

A citation is `{document_sha256, page, bbox, matched_text}`, re-located by the
host in its token index.

**Reason.** The predecessor's locators were line ranges over extracted text.
"One click from its evidence" meant one click to a line range, not to a region
on a page.

## 2026-09-08 §10 — Phase 0 toolchain

`uv` compiles and installs every lock. Three locks: `requirements.txt` (runtime,
empty until Phase 1), `requirements-dev.txt` (ruff 0.14.0, mypy 1.18.2,
pytest 9.0.3, resolved for 3.14) and `requirements-security.txt` (bandit 1.7.10,
pip-audit 2.9.0, resolved for 3.12). All three carry `--generate-hashes`;
nothing installs without `--require-hashes`.

pytest is pinned at 9.0.3 rather than 8.4.2 because 8.4.2 carries
PYSEC-2026-1845. A red vulnerability gate is answered by recompiling, not by
waiving (`SYSTEM_SPEC.md` §11) — this is the first instance of that rule.

**Reason.** `uv` resolves and hashes in one step and needs no bootstrap
dependency of its own, so the lock and the installer cannot disagree. The two
interpreter versions are forced by §4 of `docs/AI_CODE_QUALITY.md`.

## 2026-09-08 §11 — A CI job arrives with the code it scans

Phase 0 ships `lint`, `types`, `test`, `security` and `size`. `postgres`,
`model`, `frontend` and `image` are added by Phases 1, 7, 9 and the phase that
introduces the Dockerfile respectively, each with its scan floor.

**Reason.** `docs/REBUILD_PLAN.md` Phase 0 lists `image` among the Phase 0 jobs,
but there is no image to scan and no runtime lock with packages in it; `trivy fs`
over this tree reports every target as *not scanned*. A gate that passes because
it found nothing is precisely the failure §4 of `docs/AI_CODE_QUALITY.md`
forbids, so the job waits for its subject rather than shipping vacuous.

## 2026-09-08 §12 — psycopg 3, and no ORM

`psycopg[binary]` is the only runtime dependency Phase 1 adds. The store is
hand-written SQL against PostgreSQL 16; there is no ORM and no query builder.

**Reason.** The invariants this phase exists to protect are all statements about
exact SQL — `FOR UPDATE` on the run row before allocating `run_events.seq`, a
conditional `UPDATE ... WHERE` whose zero-row result must suppress the event
insert, and `ON CONFLICT DO NOTHING` on a content-addressed digest. An ORM would
put a layer between the invariant and the statement that proves it, and the
predecessor's transactional-pairing bugs are exactly what that layer hides.
`psycopg` 3 gives server-side parameter binding and explicit transaction control
with nothing in between.

`postgres:16-alpine` is pinned by digest
`sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685` in CI;
a tag alone is not a pin.

## 2026-09-08 §13 — Merges go through `make merge`

`make merge PR=<n>` runs `gh pr checks` before `gh pr merge` and stops on
anything not green. No new script: `gh pr checks` already exits non-zero when a
check fails or is still pending.

**Reason.** PR #1 merged with the size gate red at 983 lines because nothing
stopped it. At the time nothing could: branch protection and rulesets are both
refused on a private repository on GitHub's free plan. That has since been
resolved -- see §14 -- and `make merge` is now a local convenience rather than
the only control.

`--delete-branch` is deliberately absent. Deleting a base branch **closes** the
pull requests stacked on it rather than retargeting them; that is what happened
to PR #3, which had to be reopened as #5.

## 2026-09-08 §14 — The repository is public, and `main` has a ruleset

Ruleset `main gates`, active on the default branch: `lint`, `types`, `test`,
`security` and `size` are required status checks, and branch deletion and
non-fast-forward pushes are refused.

**Reason.** Overrides §13's premise. Making the repository public lifted the
Pro-only restriction on rulesets, so the gates are enforced by the platform
rather than by whoever remembers to run `make merge`. `postgres` is not yet in
the required set because no job of that name exists on `main`; it is added with
the store PR that introduces it, since a required check that never reports
blocks every merge.

## 2026-09-08 §15 — A citation carries one rectangle per line, not one rectangle

`bbox` becomes `bboxes`: one rectangle for each line the quote covers. Every
`source_tokens` row carries the layout region and the line it belongs to,
assigned by the extractor, and a match may run within a line or continue onto
the next line of the same region -- never across a gutter.

`region` rather than `block`: `CONTEXT.md` already spends `block` on the unit
`read_evidence` returns, and `source_blocks` is keyed by a `block_id` that means
something else entirely. One spelling for two concepts is the defect that
glossary exists to prevent, and `check_vocabulary.py` cannot see it -- it catches
a synonym for a term, not a term used for two things.

**Reason.** The singular `bbox` cannot describe a quote that wraps, and every
covenant worth citing wraps. Building the enclosing rectangle instead was
verified to accept `"net debt"` spanning a two-column gutter -- a phrase not on
the page -- and to return, for a quote crossing a line break, a rectangle
enclosing two words that were never quoted. Either makes "one click from its
evidence" false, which is the defect the rebuild exists to escape
(`DECISIONS.md` §9).

PDF highlight annotations use QuadPoints, a list of quads, for exactly this
reason. Line identity comes from the extractor because separating two columns
that share a y-band is layout analysis; a threshold in the anchoring path would
be a heuristic on the evidence boundary.

## 2026-09-08 §16 — `BoundaryText` covers identifiers, not document text

Governed identifiers -- `case_id`, `node_id` -- are `BoundaryText` at the store
boundary, and every digest is checked against `[0-9a-f]{64}` before it is used
as a key or a path. Document-derived text (`Block.text`, `Token.text`) is not
`BoundaryText` and will be handled by the extractor instead.

**Reason.** `BoundaryText` existed, was tested thoroughly, and was called from
nowhere: an adversarial review found `grep -rn BoundaryText server/` returned
only its own module. An invariant with a type nothing constructs is decoration.

The split is deliberate. Refusing a whole document because it contains U+202B
would refuse legitimate Arabic and Hebrew filings, which is the wrong answer for
a credit system that reads what issuers actually publish. The identifier path
has no such tension: nothing legitimate names a case with a bidirectional
override. Document text needs a narrower rule -- strip the control, keep the
document, keep the coordinates -- and that belongs where extraction happens,
under its own decision entry, not bolted onto a type meant for host-authored
strings.

## 2026-09-08 §17 — The Deploy V bundle is vendored at build `a43cb903`

`vendor/deploy-v/`, copied verbatim from the user-supplied package, minus `.git`
and `.DS_Store`. 349 files, 5.3 MB. Build id
`a43cb903ca2751f79e77b6da71f6ea131b8462a32e1b549d65fd0f67389d185f`, from the
bundle's own `DEPLOY_V_INTEGRITY_v1.json`; the host does not mint an identity
for something that ships with one.

`tests/test_bundle_pin.py` hashes every file the manifest covers and asserts the
facts the specification rests on. Every one verified against these bytes:

| Claim | Source | Found |
|---|---|---|
| typed edges live in `profile["edges"]` | `DECISIONS.md` §2 | `catalog.profiles.*.edges` |
| 25 OPTIONAL, 22 ADVISORY, one QA_GATE | `DECISIONS.md` §2 | exactly, plus 44 REQUIRED |
| `navigation.dependencies` is 97 untyped pairs | `DECISIONS.md` §2 | 97, no `type` key on any |
| 18 pathways across two profiles | `SYSTEM_SPEC.md` §4 | 10 FULL + 8 LITE |
| CP-PARSE superseded by CP-0 | `DECISIONS.md` §5 | `absorbed_by: CP-0` |
| `preparation_stage.runnable: false` | `DECISIONS.md` §5 | exactly |
| `research_extension` at stage 99 | `SYSTEM_SPEC.md` §4 | `route_stage: 99` |

**Two corrections to how the specification reads, not to what it says.**

`profile["edges"]` means the profile inside
`skills/cp-os-credit-os/references/CREDIT_OS_V_MODULE_CATALOG_v2.json`, not the
profile in `CP_DEPLOY_V_EXECUTION_PROFILES_v1.json`. Both files have a
`profiles` key and only one has edges; the execution-profiles file points at the
catalog through `pathway_execution.source`. Anyone reading `profile["edges"]`
and opening the wrong file finds nothing, which is one step from reading
`navigation.dependencies` instead -- the predecessor's exact defect.

**The catalog declares no CONDITIONAL edge at all.** `CONTEXT.md` lists
`CONDITIONAL` as a blocking edge type and `SYSTEM_SPEC.md` §4 has
`resolve_route` freezing predicates for it. Zero edges of that type exist in
either profile, so predicate freezing has nothing to act on against this build.
The type stays implemented -- it is the bundle's vocabulary and a later build may
use it -- but no test can exercise it with real data, and `CLAUDE.md` says so.

Gates do not scan `vendor/`: it is authority we never edit (§6), so a vocabulary
or coverage finding inside it names something no PR is allowed to fix. `ruff`,
`mypy` and both identifier gates exclude it, and the CI size gate already did.

## 2026-09-08 §18 — There is no bootstrap cycle; readiness is an artifact

Resolves W1 of `docs/ADVERSARIAL_REVIEW.md`.

**The route resolves before any node runs.** `resolve_route` takes
`(profile_id, selection_id)`, both chosen by the analyst at run creation. The
bundle settles this itself: `CP0_PROFILE_ANCHOR_CONTRACT_v1.md` says "CP-0 is the
first, zero-upstream invocation" and "the profile is immutable within a run;
source content cannot change it". CP-0 is the first node *of* the pinned route,
not a precondition for having one. Its `module_order` is an optional narrowing
recorded in the pin, never a re-resolution.

**`source_readiness` stops being a parameter.** `node_states(route, accepted)`
derives readiness from the accepted CP-0 artifact in the attempt ledger it
already reads. This is the whole of W1's second half: there is no separate state
whose persistence was unstated, because there is no separate state. Recovery
stays recomputation (§3) and a crash leaves nothing to restore.

**Withdrawal never touches the route.** Invariant 1 checks withdrawal live at
every use while invariant 10 pins the route once, and both hold because
withdrawal is a predicate in `read_evidence` -- already the only path to bytes.
A withdrawn source makes its consumer fail or carry a limitation through edges
that already exist. The pin is never rewritten.

**Checked and not a problem.** CP-0's schema appears to carry a fourth readiness
value, `READY_FOR_MODEL_ROUTE`. It does not: that is
`SOURCE_READY_FOR_MODEL_ROUTE`, the `status` of a separate
`model_route_source_assessment` object scoped `SOURCE_SUFFICIENCY_ONLY`. Source
readiness is `READY`, `READY_WITH_LIMITATIONS`, `BLOCKED`, as the spec says.

## 2026-09-08 §19 — `make merge` checks for the flag, not for a `gh` version

The target refuses a `gh` whose `pr merge` has no `--match-head-commit`, rather
than one whose version string is not an exact match. `GH_VERSION := 2.100.0` is
removed.

**Reason.** The pin refused every `gh` but one, including the 2.96.0 on the
machine that has to run it, and would have refused each release after 2.100.0 as
well. A version string is a proxy; the flag is the thing the target depends on,
and an older `gh` without it already fails closed on an unknown flag.

`tests/test_merge_gate.py` drives the target against a stub `gh` that refuses
`pr merge`, because nothing watched it when it merged PR #6 by accident.

## 2026-09-08 §20 — The run row lock, not a conditional update

`commit_terminal` reads the run state under `SELECT ... FOR UPDATE` and returns
before writing anything when the state is not RUNNING. The standing rule in
`CLAUDE.md` and `docs/SYSTEM_SPEC.md` named the conditional update as *the*
mechanism; both now state the guarantee -- no event without the transition it
records -- and admit either proof.

**Reason.** The lock is already load-bearing for `run_events.seq`, allocated as
`max(seq) + 1` and safe only because two callers cannot read the same sequence.
Under that lock the state read is authoritative, so `AND state = 'RUNNING'` on
the UPDATE is a branch that cannot be taken and a rowcount check that cannot
fail. A review read the module docstring rather than the code and reported the
mechanism as missing; the wording was what was wrong, and the docstring is
fixed. `docs/REBUILD_PLAN.md` still records the original plan and is left
alone: it is the plan of record, and this entry overrides it.

## 2026-09-08 §21 — Provider-call recovery: the attempt row is the call identity

Resolves C1 of `docs/ADVERSARIAL_REVIEW.md`, due before Phase 4.

The failure it names: reserve budget, the provider completes and bills, the
process dies before the accepted-attempt commit. Recovery finds no artifact and
retries, knowing neither whether the first call completed nor what it cost.

**The attempt row is written and committed before the provider is called**, and
it carries its reservation. That row is the durable call identity; there is no
second identifier to keep in step with it.

**An attempt with a reservation and no accepted artifact is INDETERMINATE, and
its reservation is not released.** Unknown usage keeps its reserved exposure.
Releasing it would let a crash convert a real charge into free budget, which is
the direction that overspends.

**A retry is a new attempt with its own reservation.** No provider idempotency
is assumed; without a verified idempotency contract a retry is a new operation
and must be budgeted as one.

**"One charge" means one `budget_ledger` entry per accepted attempt.** Provider
billing may exceed the ledger, and the difference is exactly the indeterminate
reservations -- which are rows, visible and countable. The ledger never claims
to know what a vendor billed.

**The API process owns run execution and startup recovery. The worker owns model
builds and publication jobs only.** `SYSTEM_SPEC.md` §1 gives the worker those
two jobs and §4 requires startup recovery without saying whose; this settles it.
One instance of each, so there is no contention to arbitrate.

**Phase 4 owes three tests**: a crash after remote completion and before local
acceptance; the same with no provider idempotency; and concurrent reservations
at the ceiling, which must refuse rather than overspend.

## 2026-09-08 §22 — The forecast residual compares the model's assertion to the host's arithmetic

Resolves C2 of `docs/ADVERSARIAL_REVIEW.md`, due before Phase 7.

The review's point stands: reusing the closing-balance expression as its own
expectation always produces zero, even when a component was omitted from both
sides. The residual needs an independently derived side.

**It already exists upstream.** CP-2G's payload requires
`debt_liquidity_rollforward`, and `REF_CP-2G_STEPS.md` says "reconcile opening
balances to the prior closing period and log any residual" and asks that cash
and debt "roll forward without an unexplained material residual". The model
asserts the balances; `cash_flow_forecast` recomputes them from components.

    residual = model-asserted closing balance − host-computed closing balance

Per case-period, once for debt and once for cash, in the statement currency.
Positive means the model asserted more than its own components support.

**The host declares what it reads from that array.** The bundle requires
`debt_liquidity_rollforward` but types it `{"type": "array"}` with no item
schema, so its contents are unspecified upstream. The host's input contract
names the fields it needs -- case, period, opening and closing debt and cash --
which is a host-side declaration and not an upstream edit (§6).

**A period the array omits is unavailable, not reconciled.** Falling back to the
computed value as its own expectation is precisely the zero-residual defect.

Phase 7 owes a worked input with a known non-zero residual and the downstream
unavailability it propagates.

## 2026-09-08 §23 — The model extension places CP-MODEL as well as CP-CF

`SYSTEM_SPEC.md` §6.2 says the host-declared model extension appends CP-CF with
a synthesised `REQUIRED` edge `CP-CF → CP-MODEL`. It does not say who places
CP-MODEL, and nothing else can: in the pinned catalog CP-MODEL is
`route_eligible: true` but `navigable: false`, and it appears in **no** pathway's
node list. The same is true of CP-MEMO.

The extension therefore appends both -- CP-CF at stage 100, CP-MODEL at 101,
mirroring CP-DR's stage 99 -- and the `CP-CF → CP-MODEL` edge has a node to
point at. No pathway node list is edited (§6).

**Reason.** The catalog separates *route-eligible* from *navigable*: a module
may be placed in a route without being an analyst-selectable step. CP-MODEL is
exactly that, so a host extension is the only mechanism that can place it, and
§6.2 already establishes host-declared extensions as legitimate.

A pathway missing any owner is refused during resolution, before pinning, rather
than dropping the edge or running CP-CF without an input it reads. Three FULL
pathways carry all three owners; `COVENANT_REFINANCING` carries CP-1 and CP-4
but no CP-2G and is refused, which is what `test_model_extension_refuses_
missing_owner` asserts.

## 2026-09-09 §24 — The catalog says what is live; the manifest says what its bytes are

`SYSTEM_SPEC.md` §3 reads as though `ModuleSpec.reference_files` is written out
per module. It is derived instead, from two sources with two different jobs.

**The live set is the catalog's `modules` list**, plus the one host carve-out.
It is not the manifest's folder list. The bundle ships 25 skill folders and the
catalog declares 24 modules; the extra folder is `cp-os-credit-os`, whose
`references/` hold `CREDIT_OS_V_MODULE_CATALOG_v2.json` — the routing catalog
itself. A live set taken from folder layout makes `CP-OS` a module and hands a
model the map that routes it, which inverts invariant 4's direction of
authority. `test_the_os_skill_folder_is_not_a_live_module` is the guard.

**The file set is an allowlist**: `SKILL.md`, the module's own `references/`
where the suffix is `.md`, `.txt` or `.json`, and root `CANON_SHARED.md`. Not a
denylist naming `scripts/` and `agents/`. One Deploy V release changed 175 files
(§6); a rule naming what to exclude admits every directory the next release
invents. `scripts/` is calculator code the host selects and never puts in a
prompt (`SYSTEM_SPEC.md` §3), and `CANON_SHARED.md` is in because 23 of 25
`SKILL.md` instruct the module to open it and a module has no filesystem.

**Reason.** Twenty-five hand-written file lists drift from the bundle in one
direction only: a new upstream reference file is silently withheld from the
module that ships with it, and nothing fails. Derivation cannot drift, because
the manifest that names the files is the manifest that pins their bytes.

**Consequence.** The host keeps exactly one declaration, `_CARVE_OUTS`, and it
is CP-PARSE (§5). Everything else about a module's identity comes from the
bundle, verified at use.

## 2026-09-09 §25 — A module may select a calculator its own folder ships

`SYSTEM_SPEC.md` §6.1 shows `_CALCULATORS` as a table keyed by
`(module_id, calculator_id)`. Taken literally that is 25 rows at this build:
`credit_metrics` ships in three skill folders and `confidence_score` in
twenty-two.

The host declares a rule instead. A calculator id is declared once, with its
transitive helper set; a module may select it when its **own** skill folder
ships `scripts/<calculator_id>.py`, and never otherwise.

**Reason.** The rule is stronger than the list, not weaker. It refuses exactly
what §3 is protecting — a module reaching into another module's scripts — and it
cannot drift from the bundle, whereas twenty-five hand-written rows go stale the
first time upstream moves a script. The host still owns selection: a calculator
nobody declared cannot be selected however many folders ship it, and a declared
calculator with no work factor is refused rather than run unbounded.

**Consequence.** `ModuleSpec` gains no `calculators` field. The pair-keyed
lookup was the only thing that needed one, and two sources of truth for which
calculator a module may run is the defect the registry exists to prevent.

## 2026-09-09 §26 — Calculators run under `-I -S`, on copied bytes

Verified: with the host's own interpreter, a child started with no flags or with
`-I` alone can `import psycopg` — the store's driver, and therefore a socket to
the store. `-S` is what removes site-packages from its path.

The bytes are read through the digest-checked path, written into a private
`TemporaryDirectory` (mode 0700), and executed there. What runs is what was
hashed, rather than a path that was hashed a moment earlier. `-I` implies `-P`,
which costs nothing because the vendor scripts put their own folder on
`sys.path` themselves.

stdout goes to a file, never a pipe: nothing can deadlock on a full buffer, and
the size is known before a byte enters this process. A timeout kills the whole
process group, so a calculator's own children die with it.

**Reason.** The boundary's premise is that a module never supplies code. A
calculator that can reach the host's installed packages makes that premise
false, and only a flag stands between the two.
## 2026-09-09 §27 — "No migrations" is enforced at startup, not assumed

`server/store/schema.sql` opened by claiming that a file applied in full at
startup makes drift impossible. It does not. Verified against PostgreSQL 16:

    CREATE TABLE IF NOT EXISTS t (a int);
    CREATE TABLE IF NOT EXISTS t (a int, b text);

leaves `t` with column `a` only — no error, no warning. Adding a *new* table to
the file works exactly as the file intends; changing an *existing* one silently
does nothing, and a long-running instance keeps the old shape while the file
says otherwise. CLAUDE.md's ledger recorded the case that works and not the case
that does not.

**`apply_schema` now compares and refuses.** It applies the file a second time
into an empty schema created for the comparison, describes both schemas from
`pg_catalog` — columns with type, nullability, identity and default;
constraints; indexes; triggers — and raises `SchemaDrifted` naming what differs
if the two sets are not equal. This is the §11 posture: refuse before acting.

**Postgres parses the file, not us.** The alternative was a SQL parser in
Python deciding what `schema.sql` declares, which is a second implementation of
DDL semantics that can disagree with the first. Applying the file to an empty
schema is the same authority answering the question about itself.

**A schema that was empty before the file was applied is not compared.** There
is nothing for it to have drifted from, and the comparison costs a second full
apply — which every test would otherwise pay for a state it cannot reach. A
first boot skips it; every restart after it pays for one.

**Refusing, not repairing.** A mismatch is reconciled by hand. Generating the
`ALTER TABLE` would be a migration engine, which is the thing §12's no-ORM
decision and this file's shape exist to avoid.

## 2026-09-09 §28 — The Anthropic SDK, not raw HTTP

`anthropic==1.4.0` enters `requirements.in`, bringing 14 transitive packages
(`httpx2`, `pydantic`, `anyio`, `truststore` and their dependencies) into a
fully hashed lock. `pip-audit` is clean over the recompiled locks.

**Reason.** One `POST /v1/messages` is forty lines of `urllib`, and that was the
first instinct. It is the wrong one: the SDK owns retry and backoff on 429 and
5xx, typed exception classes the refusal mapping switches on, streaming
assembly, and the request shapes that change under us — `budget_tokens` became
`effort`, `output_format` became `output_config.format`, and a hand-rolled
client would have carried each stale shape until something broke in production.
The bundled Claude API reference is explicit that a Python project uses the
official SDK and does not reach for raw HTTP because it feels lighter.

**Two departures from the SDK's own defaults**, both recorded here because both
look like omissions otherwise.

*No server-side `fallbacks`.* The SDK recommends enabling them on
`claude-opus-5` so a policy refusal is retried on another model. A run here is
bound to a provider identity (`REBUILD_PLAN.md` Phase 10). A silent switch mid-run
would make two replays of one pinned route incomparable and an accepted artifact
unattributable, which is a larger loss than a refused node. `stop_reason ==
"refusal"` becomes `PROVIDER_REFUSED`.

*A credential means an environment variable.* The SDK also resolves an `ant`
profile from disk. Honouring that would let a developer's machine spend money in
a suite that is meant to be free and offline, and would make
`test_a_live_call_needs_a_credential_and_says_so` pass or fail depending on
whose laptop ran it.

**Consequence.** `pytest -m live_provider` is the only test in this repository
that spends money, and it skips without a credential. Everything else drives the
real SDK against a mock transport, which is what caught `ParsedMessage` having
no `_request_id` — a crash on every live call that `mypy` could not see.

## 2026-09-09 §29 — The envelope is the bundle's schema; citations are the host's

`CP_MODULE_PAYLOAD_BASE.schema.txt` already declares the canonical envelope:
thirteen required fields, closed enums for `output_class`, `qa_status` and
`confidence_band`, and `additionalProperties: false`. That last line *is*
invariant 9. The host validates against that file, read through `Bundle.read`
and therefore digest-checked at use.

**Not against a model copied from it.** A hand-written `pydantic` model would be
a second declaration of one contract, free to drift from the authority it
paraphrases — and it is the drift, not the schema, that admits an undeclared
field. `jsonschema==4.26.0` enters the locks (4 transitive packages) rather than
a hand-rolled validator: `additionalProperties` getting subtly wrong is exactly
the failure invariant 9 exists to prevent, and the Lite base already uses
`$ref`, `$defs` and `allOf`, which is a spec to implement rather than a subset.

**Where the schema stops, the host starts.** The base types `evidence_trace`
only as an object. Citations are host territory (invariant 11), so the shape
inside it is declared here: `evidence_trace.citations` is a list of
`{document_sha256, page, matched_text}` — exactly those three keys. A claim
carrying `bboxes` is refused rather than ignored, because a module supplying its
own rectangles is a module asserting where its quote sits, and the host derives
that.

**Consequence.** `delivered_evidence` is finally read. `read_evidence` records
what a node was handed; `_anchor` refuses a citation naming anything else, which
closes the half of invariant 9 that anchoring alone never could — the other
document is in the same case, in the same pinned set, and carries the same
sentence, so only the ledger can tell the two apart.

## 2026-09-09 §30 — All rights reserved, because the bundle is not ours to license

**Decided.** `LICENSE` states proprietary terms — no grant — and carves
`vendor/deploy-v/` out of them explicitly.

**Why not an open-source licence.** The repository is public and vendors 5.3 MB
of `deploy-v` verbatim. MIT or Apache-2.0 at the root would assert terms over
those bytes too, and invariant 4 says the bundle is upstream authority this
repository never edits — it certainly cannot relicense it. A permissive licence
here would be a claim the copyright holder is not in a position to make, and the
carve-out is the whole reason the file has to exist rather than be omitted.

**Why write anything at all.** An unlicensed public repository is already all
rights reserved, so this grants and removes nothing. What it removes is the
ambiguity a reader resolves by guessing, and it is the only place the carve-out
can be stated. §6 says the bundle is never edited; it does not say the
repository has no rights in it.

**What this does not settle.** The bundle ships no licence file, no copyright
notice and no provenance statement — searched, not assumed. Redistributing it
from a public repository rests on terms nobody here has seen. That is a gap in
the ledger, not a decision, and `CLAUDE.md` carries it.

**Reversible.** Moving to an open-source licence is the copyright holder's
decision, and it needs the bundle's terms settled first.

## 2026-09-09 §31 — SonarQube replaces CodeRabbit as the third reviewer

`.coderabbit.yaml` is deleted. SonarQube Cloud's automatic analysis takes its
place: the GitHub App reads the repository from its own side and posts the
`SonarCloud Code Analysis` check on every pull request, whose conclusion is the
quality gate's verdict. `.sonarcloud.properties` excludes `vendor/`. Nothing
else about it lives in this tree.

**Reason.** CodeRabbit never reviewed anything here unprompted. Its answer on
PR #20 was *"does not receive automatic reviews because it has fewer than 10
stars"*; on PR #41 it was *"Draft PRs are not automatically reviewed by
default"*. Two different reasons, one outcome, and `@coderabbitai review` posted
by `github-actions[bot]` on PR #22 was never answered — so the ask needed a
human every time. The property `docs/AI_CODE_QUALITY.md` §2 wanted from a third
reviewer was independence, and what it had instead was `confidence-review` and
`adversarial-reviewer`, one model in two postures.

**And no `sonarqube` CI job.** The first version of this change added one, with
a credential guard that refused to let the analysis be skipped inside a green
job. It was wrong twice over. Automatic analysis was already enabled and already
passing on PR #41 before the job ran, so the reviewer needed no wiring at all;
and automatic analysis and a CI scanner are **mutually exclusive** — with the
former on, a scanner against the same project fails and fails the build, so the
job could never have gone green even with the `SONAR_TOKEN` it was waiting for.
`sonar-project.properties` is the scanner CLI's file and is ignored by automatic
analysis, so it configured nothing while it existed; `gitleaks` also read the
`sonar.projectKey` in it as a generic API key and failed the `security` gate.
`test_nothing_here_starts_a_scanner_of_its_own` refuses all of it, because the
next agent to read §11 will reach for the same job.

**Consequence.** The controls visible in this repository are one line narrower
than a CI job would have been: analysis scope is `.sonarcloud.properties`, and
the quality gate, the rule set and the schedule are settings in SonarQube Cloud
that no test here can read.

That is not only a cost. Most of this repository is written by an agent, and a
scanner configured from the tree would put the reviewer's scope and gate in the
same diff as the code under review — editable by its author. Automatic analysis
cannot be reached from a commit at all, which is the independence
`docs/AI_CODE_QUALITY.md` §2 said the review control was missing, and it is the
same reasoning §14 used to move the other gates off `make merge` and onto a
platform ruleset. What it does not cover is a gate *loosened* rather than
disabled: a relaxed condition still reports green.

§14's answer applies to the check: `SonarCloud Code Analysis` joins the `main`
ruleset's required checks once it has reported on `main`, which is what makes a
disabled analysis block every merge instead of passing silently.

## 2026-09-09 §32 — A gate is two tables: a re-openable ask and a once-only release

Invariant 5 wants an approval bound to the exact reviewed content, and
`docs/REBUILD_PLAN.md` Phase 6 wants the release to be a CAS transaction. One
table with a nullable `decision`, released by a conditional UPDATE, would satisfy
both readings of `SYSTEM_SPEC.md` §2 and is what the shape suggests. It is not
what was built.

**Decided.** `run_gates` holds what a person is being asked to approve and is
re-openable while undecided. `run_gate_approvals` holds the release, is
append-only, and its primary key `(run_id, kind)` *is* the compare-and-set. The
approval row is copied from the gate row by the insert's own `SELECT`, so what
it records is what the store held rather than what a caller claimed.

**Reason.** The two halves have opposite requirements. The ask must move: a
source is withdrawn, a plan is re-derived, and saying so is the point of
re-opening a gate. The decision must not move at all. Splitting them lets the
release carry `refuse_rewrite` and its TRUNCATE guard -- so
`test_every_table_that_refuses_a_rewrite_also_refuses_a_truncate` covers it with
no new machinery -- while the ask keeps the UPDATE path it needs. A single table
could carry neither guard, and an approval a raw statement can rewrite is not an
approval. The cost is that `run_gates` itself is unguarded at the store; that is
in the known-gaps ledger with its upgrade.

**Two digests, not one.** `preview_sha256` is the bytes a person read.
`input_fingerprint` is what those bytes were rendered from. Content that renders
identically over different inputs -- a withdrawn source contributing no visible
line, an ordering the renderer normalises away -- is different content, and the
fingerprint is what refuses it.

**Consequence.** Every run event is now allocated by one emitter,
`server/store/events.py`, which takes the run row lock itself. `run_events.seq`
was safe only by accident before: `commit_terminal` held that lock for its own
reasons and `pin_route` was serialised by `run_routes_pkey`. Gate events are the
first path with neither, and two concurrent inserts collided on
`run_events_pkey` -- verified by removing the lock and watching
`test_concurrent_emitters_allocate_distinct_sequences` fail with exactly that
constraint name. `SYSTEM_SPEC.md` §10 already asked for one emitter; this is it,
and `test_only_the_emitter_inserts_a_run_event` is what keeps it the only one.

**Lock ordering, checked rather than assumed.** `emit` takes the run row
`FOR UPDATE`, and `pin_route` calls it *after* inserting into `run_routes` --
which has already taken KEY SHARE on that same run row through its foreign key.
That is a lock upgrade, and a lock upgrade behind a queued waiter is the classic
deadlock. It was measured on this PostgreSQL rather than reasoned about: a
holder of KEY SHARE upgrades to FOR UPDATE with another transaction already
queued for FOR UPDATE, and neither aborts. The shape that would deadlock is two
transactions *both* upgrading, and nothing reaches it: a second concurrent
`pin_route` collides on `run_routes_pkey` during the index insert, before its
foreign key trigger fires, so it never holds KEY SHARE at all; `accept` takes
KEY SHARE and never upgrades; and both gate paths take the run row lock first
and so never hold KEY SHARE before it. `pin_route` is therefore left as it is.
A new path that writes a child row of `runs` and then emits should take the run
row lock first, which is what both gate paths do.

## 2026-09-09 §33 — The release and the pin are one call, not two

`approve_plan` releases the plan gate and pins the route in a single
transaction it opens itself. The obvious alternative -- `approve_gate`, then a
separate `pin_route` when the caller is ready -- was written first and thrown
away.

**Reason.** Two calls can disagree. Release the plan a person read, then pin a
different route, and the store afterwards holds an approval row for one thing
and a pin for another, with nothing saying which was on screen. That is exactly
the failure invariant 5 exists to prevent, reintroduced one layer above the
mechanism that prevents it. Making them one call means the route that gets
pinned is the route the digests were computed over, by construction rather than
by the caller remembering. `test_approving_a_plan_that_is_not_the_one_on_screen_pins_nothing`
is what holds it, and `test_a_pin_that_fails_takes_the_release_down_with_it`
holds the other direction: the release is written first, so a pin that refuses
has to take it back.

**Consequence.** `approve_plan` is the only caller of `pin_route`, which closes
the Phase 3 ledger entry that had nothing pinning. It also means the plan gate
is where the model extension stops being a test-only argument: `Plan.route`
carries whatever `resolve_route` produced and the fingerprint digests it, so an
approval of a plan without the model effect cannot release a run that builds
one.

**The two digests, and why neither is enough.** `preview_sha256` is over the
text a person reads -- case, pathway, document digests, module ids in the order
they will run. `input_fingerprint` is over what that text was rendered from,
and it carries the two things a reader cannot see: the source-set version and
the route digest. Re-pinning the same documents allocates a new version whose
preview is byte-identical, so the preview digest alone would let an approval of
version 3 release a run bound to version 4. The route digest is in the
fingerprint rather than the preview for the same reason in reverse: the preview
names modules, because a route node id is an internal spelling and a person
approving a plan should not be asked to read one.

## 2026-09-09 §34 — Every gate the CI runs is a required check

`main gates` requires all seven: `lint`, `types`, `test`, `postgres`,
`security`, `size` and `SonarCloud Code Analysis`. The last is bound to the
SonarQubeCloud app rather than *Any source*; the six Actions jobs are not.

**Reason.** §14 fixed five and deferred `postgres` because no job of that name
existed on `main` yet — "a required check that never reports blocks every
merge". It has existed since the store phase, and it is the only gate that
proves the governed races on two independent connections, which
`docs/AI_CODE_QUALITY.md` §1 names against the ~2× concurrency defect rate. It
ran and reported on every pull request and stopped none of them.

**Why the third reviewer is bound to its app and the six are not.** A check is
matched by name, so *Any source* accepts that name from any actor. For
`SonarCloud Code Analysis` that would undo the argument §31 rests on — a
reviewer the author of the code cannot weaken. The six Actions jobs are
declared in `.github/workflows/ci.yml`, so whoever can edit the workflow already
controls them; binding the source buys nothing they do not already concede.

**Consequence.** The hazard now runs the other way. §14 worried about a
required check that never reports; the same break arrives by renaming a job,
which silently makes its check unreportable and blocks every merge until the
ruleset is edited to match. `test_every_required_check_is_a_job_the_ci_still_defines`
refuses the rename. Nothing here can read the ruleset, so the test pins this
entry's list against the workflow rather than against GitHub.

## 2026-09-09 §35 — A plan never severs a blocking edge into a module it keeps

**Decided.** `module_order` may drop modules from a pathway (§18); it may not
drop one that a kept module reaches through a REQUIRED, CONDITIONAL or QA_GATE
edge. `resolve_route` refuses such a plan with `ROUTE_NOT_RESOLVABLE` before
anything is pinned.

**Why.** Narrowing filters the edge set to the surviving modules, so keeping
CP-2 and dropping CP-1 — which CP-2 REQUIRES — resolved to a CP-2 that was
RUNNABLE with nothing to read. Reproduced against the pinned catalog. A blocking
edge is the catalog saying a module cannot run without that input; a plan that
deletes the edge does not make the input unnecessary, it makes the gap
invisible.

**What §18 said and did not say.** "Narrows, never adds" ruled out invention. It
was silent on severance, and the code read the silence as permission.

**Soft edges are not covered.** Dropping the source of an OPTIONAL or ADVISORY
edge removes the edge too, so its target runs RUNNABLE rather than RESTRICTED
and carries no limitation forward. That is a lesser loss and a separate
decision; it is noted here so it is not mistaken for one already made.

## 2026-09-09 §36 — Readiness is read from the CP-0 artifact, and CONDITIONAL exists

**Decided.** `accepted_attempts` reads CP-0's readiness from its accepted
artifact at `runtime_output.readiness_summary.overall_readiness`, the field
`CP-0__SourceReadiness__payload.schema.txt` declares. An accepted CP-0 artifact
that does not carry one of its four values is refused `ENVELOPE_INVALID`.

**Why this and not a column.** §18 already decided it: readiness is derived
from the accepted CP-0 artifact, and there is no separate state. The loop then
built every `Accepted` without one, so the hardening rule — OPTIONAL and
ADVISORY block once the source is READY — held in tests that hand-constructed
`Accepted(readiness=...)` and nowhere else. Reading the artifact is what §18
described; a column would be the separate state it ruled out, and one that
`artifacts` has no rewrite guard on.

**§18 was wrong about the enum.** It said source readiness is READY,
READY_WITH_LIMITATIONS, BLOCKED. The schema's `overall_readiness` also carries
CONDITIONAL. It is accepted as a value and does not harden: hardening turns
soft inputs into blocking ones on the strength of a source that is ready, and
a conditional source is not that. The enum is copied into `loop.py` because
the schema file is not JSON Schema and cannot be validated against.

**Consequence.** `run_route` and `accepted_attempts` take a `BlobStore`. The
frontier is still recomputation and nothing else: on restart the loop reads the
artifact CP-0 actually produced.

## 2026-09-09 §37 — Host retries are the only retries

The live client is built with `max_retries=0`. The SDK's default is 2, and it
retries a 408, 409, 429, 5xx or connection error by re-sending the request.

**Reason.** §21 rules that a retry is a new attempt with its own reservation
and that no provider idempotency is assumed. §28 listed "the SDK owns retry and
backoff on 429 and 5xx" among the reasons to take the SDK, and never reconciled
the two: an SDK retry is a second provider call under the one attempt row and
the one reservation, invisible to the ledger -- C1 of
`docs/ADVERSARIAL_REVIEW.md`, reintroduced one layer below the fix. The
provider suite disables SDK retries on its mock client and so never ran the
path production ran. Measured on the locked SDK against a mock wire: one 500
on a streamed call is three requests under the default and one under zero.
`test_the_live_client_never_retries_on_its_own` reads the setting back from
the client the host builds, and `live_client` is also where the credential
guard now lives, so a caller reaching past `live_provider_or_none` cannot let
the SDK read an `ant` profile from disk (§28).

**Consequence.** A 429 or a 5xx is `PROVIDER_UNAVAILABLE` on the first try,
and the attempt is INDETERMINATE with its reservation kept, as §21 says. When a
retry is worth having, it is the loop's, reserved as a new attempt.

## 2026-09-09 §38 — The plan is kept true, and the current phase owes what exited phases did not ship

Two findings of the second adversarial review (`docs/ADVERSARIAL_REVIEW.md`),
both in the documents rather than the code.

**Overridden text is corrected in place.** §20 left `docs/REBUILD_PLAN.md`
untouched as "the plan of record" and let the entry override it. As a policy
that produced a plan naming two functions that never existed
(`active_incoming`, `expected_upstream_digests`), a registry table by a name
§24 had replaced, a CI job §11 had deferred, a spec whose `node_states`
signature §18 had changed and whose calculator table §25 had replaced -- and
`docs/INITIALISATION_PROMPT.md` did not have this record in its reading order
at all. A session following that prompt would build what a decision had
removed. From here an entry that overrides the plan or a spec is written back
into them with a citation, the prompt reads this record, and
`test_every_exit_test_of_an_exited_phase_exists` holds the plan to the standard
`test_the_map_is_true.py` already held `CLAUDE.md` to.

**The current phase owes what an exited phase did not ship.** Phase 2 was
exited without an extractor, Phase 4 without a priced provider call, Phase 5
without a live one, and each ledger entry deferred the gap to "a slice" the
plan never names -- so "start at the lowest phase whose exit test does not
pass" walked past all three. An exited phase is not reopened. Its unshipped
deliverable is listed under the current phase with the test it owes, and that
test is part of the current phase's exit. The ledger's "slice" means that
phase.

**Reason.** Both are the defect the map test was written for: a document an
agent must read that names something the repository does not have. The plan is
the one document that decides what gets built next, so it is where drift costs
most. Overrides §20's "left alone".

## 2026-09-09 §39 — Coverage moves the analysis into CI, and §31's independence is spent

`sonar-project.properties` is added and a `sonarqube` job submits the analysis
with `SONAR_TOKEN`; `pytest-cov` writes `coverage.xml` from the suite, and
`sonar.python.coverage.reportPaths` is what the scanner reads it by. Overrides
§31.

**`.sonarcloud.properties` stays until the switch-over is done, and that is not
a hedge.** The first version of this change deleted it in the same commit, on
the reasoning that a file automatic analysis reads is dead once the analysis is
CI-based. It is not dead until somebody turns automatic analysis off in
SonarQube Cloud's settings, which no commit can do — so between the merge and
that click, deleting it does not remove a configuration nobody reads. It removes
the only configuration anybody is reading, leaving the live analysis with no
`vendor/**` exclusion, no test classification and no Python version, judging 147
vendored files no pull request is allowed to fix. Both files therefore exist for
one transition, saying the same thing, held together by
`test_both_analysis_configurations_declare_the_same_scope`, and the second is
deleted by the commit that confirms the `sonarqube` job is posting the check.

**Reason.** SonarQube Cloud's automatic analysis imports no coverage report. The
quality gate has had a coverage condition with no metric to evaluate since the
day it was enabled -- the check on PR #41 passed reading 0.0% on new code, and
the CLAUDE.md ledger has carried that as a known gap ever since. There is no
setting that fixes it: coverage reaches a SonarQube Cloud project through a
scanner or it does not reach it at all, and a scanner cannot run against a
project under automatic analysis (§31 established that the hard way). So the
choice was coverage or automatic analysis, not both.

**What it costs, stated plainly.** §31's argument was that an analysis
unreachable from a commit cannot be narrowed by the agent whose code it reads,
and that argument is now spent. `sonar.sources`, `sonar.exclusions` and the
coverage path sit in the tree, in the same pull request they judge, editable by
their author -- exactly the property §31 declined. The quality gate's conditions
remain in SonarQube Cloud, so what moved is scope, not verdict.

Three things are put in the way of a narrowed scope, and none of them is the
platform:

- `test_the_analysis_claims_every_tracked_python_file` already refused a source
  list that dropped a package; it now reads this file instead of the old one.
- `scan_floors.py --cobertura` refuses a coverage report that measured nothing
  or that left out a tracked file under its targets. A file absent from the
  report is not a file at zero per cent -- it raises the percentage of
  everything else, which is the one way a coverage number lies rather than
  simply being low. `test_the_coverage_floor_measures_what_the_analysis_reads`
  holds its target list to `sonar.sources`.
- `test_exactly_one_job_submits_the_analysis` keeps the count at one, which is
  what §31's mutual exclusion becomes once the scanner is the analysis.

**The third reviewer's first finding was on the floor itself, and it took three
analyses to read.** The quality gate on the pull request that introduced this
entry failed on *C Security Rating on New Code*, and the analysis is on a host
the environment that wrote this could not reach, so the finding was guessed at
twice before a person opened the dashboard. Both guesses were wrong, and both
changes stayed:

- `cobertura_metrics` had used `xml.etree.ElementTree.fromstring` under a
  `# nosec B314`, on the reasoning that coverage.py writes the file one step
  earlier. The guess was that SonarPython's S2755 had said the same as bandit.
  It had not, but a suppression that only one scanner honours is not worth
  carrying: Cobertura puts `filename` on `<class>` and on no other element, so
  the floor reads the report as text with one regex, and a regex that misread it
  would name a measured file as unmeasured, which fails closed. No parser, no
  suppression, no `defusedxml`.
- `.sonarcloud.properties` had been deleted; the guess was that the analysis,
  left without its `vendor/**` exclusion, was judging the bundle. It was not the
  finding either, but it was a real regression for the whole transition, and
  the paragraph above is the result.

The finding was path traversal: `parse_args` to `args.report` to
`args.report.read_text`, a CLI argument reaching the filesystem with no
containment. The sink pre-dated this change — `main` had read the report that
way since the gate was written — and this change touched the line, which moved
a latent finding into new code. That is how a new-code gate works and it is not
a complaint: a line you rewrite is yours. `report_within` now resolves the path
and refuses one that does not lie under the directory the gate was invoked in,
before anything is read. A scanner report is a build output of the tree being
scanned, so that is the only place one is ever read from, and the Makefile and
CI both run the gate from the repository root. The check is spelled
`os.path.realpath` and `startswith` rather than `Path.resolve` and
`is_relative_to` because that is the sanitizer shape the rule documents, and
whether the analyzer recognises the pathlib spelling is not known here.

What this cost is a lesson worth the entry: an analysis this repository cannot
read is an analysis it cannot fix without a person in the loop. Two cycles
were spent on inference, and the finding was on the dashboard the whole time.

One more, found while pinning the fix. The mutation checks that backed this
change's tests were first run under `pytest -q` on top of the `-q` already in
`addopts`, and `-qq` prints no `N passed` line — so a harness that grepped for
one reported every mutation as caught, whether it was or not. "A scanner that
scanned nothing is a failure" applies to the scaffolding around a test as much
as to the gates; the checks were redone keyed on the exit code, with the
unmutated tree proven green first, and the separator in `report_within` was
the case that showed it: `"/base-secret/x".startswith("/base")` is true, and
only a sibling-directory input makes the trailing separator load-bearing.

That is weaker than an analysis nobody here can reach, and it is what buys a
coverage metric. The honest summary is that this repository traded an
independent scope for a measured one.

**The dependency.** `pytest-cov==7.1.0`, and `coverage==7.16.0` beneath it, into
`requirements-dev.in` and the hashed lock. It is a development dependency: no
runtime path imports it, and `requirements.in` is untouched.

**The secret exemption.** `gitleaks` reads `sonar.projectKey=EricMG13_CAOS-Final`
as a generic API key -- entropy 4.14, measured on 8.24.3 -- and failed the
`security` gate on it once already (§31). `.gitleaks.toml` exempts that exact
string, by `regexTarget = "match"` and not by path, so the file it sits in is
still scanned for everything else. A project key is in the query string of every
dashboard URL the check posts; the credential is `SONAR_TOKEN`, which is a
repository secret and is exempted nowhere.

**What this entry does not settle.** Whether SonarQube Cloud posts the same
`SonarCloud Code Analysis` check under CI analysis as it did under automatic
analysis. That check is required on `main` (§34), so if the name changes, the
required check stops reporting and blocks every merge until the ruleset follows
-- §14's hazard, arriving from the direction §34 did not cover. Nothing in this
repository can read the ruleset or the check name, so this is verified by
watching the first analysis on `main` and not before. The ledger carries it.
