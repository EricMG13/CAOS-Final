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

## 2026-09-08 §16 — `BoundaryText` covers identifiers; document text is handled
at extraction

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
