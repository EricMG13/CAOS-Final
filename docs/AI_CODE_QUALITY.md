# AI code quality — controls

Most of this repository will be written by an AI agent. CodeRabbit's *State of
AI vs Human Code Generation* (470 PRs: 320 AI-co-authored, 150 human-only)
measured what that does to a codebase: **10.83 issues per AI PR against 6.45 for
human-only**, ~1.7× overall. The study stands whatever tool ends up reading the
diffs here; §2 records why it is no longer CodeRabbit.

This document maps each measured failure mode to a control that is enforced by
a tool, not by intention. A control nobody runs is not a control.

---

## 1. The measured failure modes, and what stops each

| Failure mode | Measured | Control | Enforced by |
|---|---|---|---|
| **Logic & correctness** | +75 % | Test-first for every calculator, state transition and money path. A failing test exists before the implementation. | `superpowers:test-driven-development`; CI refuses a PR whose new public function has no test |
| **Readability** | 3× | Function length and complexity ceilings; a rewrite pass on non-trivial functions before commit | `ruff` (C901, PLR0912/0913/0915); `rewrite-tournament` skill post-edit |
| **Error handling** | ~2× | Typed refusals only. No bare `except`, no `except Exception` without re-raise, no `str(exc)` reaching a log or a wire response | `ruff` (BLE, TRY); the observability test that drives a sentinel document through real ingestion |
| **Security** | 2.74× | Static analysis with a scan floor, dependency audit, secret scan. An image scan and a route-level actor matrix that drives every endpoint as nine different actors arrive with the Dockerfile and the first HTTP route | `bandit` (pinned 3.12 — see §4) + `scan_floors.py`, `pip-audit`, `gitleaks`; Trivy and the actor-matrix test are owed by `REBUILD_PLAN.md` Phases 7 and 6 |
| **Formatting** | 2.66× | Formatter runs on write, not on review | `ruff format` in a `PostToolUse` hook and in CI; `prettier` in the hook, and in CI with the frontend (Phase 9) |
| **Naming inconsistency** | ~2× | One glossary. Every domain term in `CONTEXT.md`; a check that new identifiers do not introduce a synonym for an existing term | `CONTEXT.md` + `scripts/check_vocabulary.py` |
| **Concurrency & dependencies** | ~2× | No new dependency without a dated decision entry. Fully pinned, hashed locks. Every governed race proven on two independent Postgres connections | `--require-hashes` in CI and the image, `pip-audit`, `test_postgres_races.py` |
| **Performance — excessive I/O** | **~8×** | A declared I/O budget per request path, asserted in tests. N+1 detection on every list endpoint | `scripts/io_budget.py --assert` + `test_io_budget_read_evidence` |
| **Critical/major severity** | 1.4–1.7× | Two independent review passes before merge: self-doubt enumeration, then hostile review. The hostile pass is the gate — it must find something, and each finding is either fixed or entered in the known-gaps ledger | `confidence-review` then `adversarial-reviewer`, both before the PR is opened; `SonarCloud Code Analysis` on every PR (§2) |
| **Overall volume** | 1.7× | Small PRs. One concern per PR, hard cap on changed lines | CI size gate |

**Excessive I/O deserves its own note.** It is the largest single multiple in
the report (~8×) and the old CAOS tree had exactly this defect: evidence blocks
lived in one JSON column, so `read_evidence` parsed every block of a source on
every call — 17 ms per read at the ceiling, ~1.4 s per run. `SYSTEM_SPEC.md` §2
fixes the shape (`source_blocks` keyed by `(source_id, block_id)`); the I/O
budget test is what stops it coming back.

---

## 2. Repository controls

### `.claude/settings.json`

- **`PostToolUse` on Write|Edit** → `ruff format` + `ruff check --fix` for
  Python, `prettier` for TS/CSS. Formatting never reaches review.
- **`PreToolUse` on Bash** → refuse `git push --force`, `git commit --no-verify`,
  and any `pip install` outside the hashed lock.

No `Stop` hook. An earlier draft described one that ran the changed-file tests;
it was never written, and a control this document names is one a reader
believes exists.

### Pre-commit

`ruff`, `ruff-format`, `gitleaks`, `check-added-large-files`,
`check-merge-conflict`, and the vocabulary check.

### CI jobs

Running: `lint` · `types` · `test` · `postgres` (two-connection races) ·
`security` (bandit + pip-audit + gitleaks) · `size` · `sonarqube`. Arriving with
their subjects (`docs/DECISIONS.md` §11): `model` (LibreOffice recalculation —
`MODEL_BUILDER_SPEC.md` §8) and `image` (Trivy, fixable HIGH/CRITICAL) in
Phase 7, `frontend` (lint, tsc, unit, build, a11y, workbench smoke) in Phase 9.

`sonarqube` is the third reviewer, and it is the one job that does not decide
its own verdict: it submits the analysis, and `SonarCloud Code Analysis` —
posted by SonarQube Cloud's GitHub App — carries the quality gate's answer. It
was deliberately absent until `docs/DECISIONS.md` §39; the paragraph below says
what changed and what it cost.

### Review

Three reviewers with different blind spots.

**The gate is `adversarial-reviewer`, run before every PR is opened.** It is not
advisory: each of its three personas must produce a finding, and every finding
is either fixed in the PR or written into the CLAUDE.md known-gaps ledger with
its reason. A pass that produced nothing means it was not run.

**SonarQube is the third, and it is the only one that is not this model.**
`confidence-review` and `adversarial-reviewer` are one model reading its own
work in two postures; the persona structure buys back some independence and is
not the same thing as a second opinion. SonarQube's rule engine was written by
people who never saw this repository, which is exactly the property the review
control was missing — see `docs/DECISIONS.md` §31.

**It runs from CI, and it did not always.** Until `docs/DECISIONS.md` §39 the
analysis ran from SonarQube Cloud's own side, which meant the agent writing this
repository could not narrow the reviewer reading it — the independence §2 had
been missing. That ended for one reason: **automatic analysis imports no
coverage report.** The quality gate's coverage condition had no metric to judge,
and no setting fixes it, because coverage reaches a SonarQube Cloud project
through a scanner or not at all. So the `sonarqube` job submits the analysis and
hands it `coverage.xml`; the GitHub App still posts `SonarCloud Code Analysis`,
whose conclusion is the quality gate's verdict.

The cost is real and is in the CLAUDE.md ledger: `sonar.sources`, the exclusions
and the coverage path now sit in the tree, editable in the pull request they
judge. The verdict does not — the gate's conditions stay in SonarQube Cloud.
What guards the scope is `test_the_analysis_claims_every_tracked_python_file`,
`test_the_coverage_floor_measures_what_the_analysis_reads` and
`test_exactly_one_job_submits_the_analysis`, each of which an author could also
edit. That is a weaker arrangement than the one it replaced, bought for a
coverage number the gate can actually evaluate.

**The predecessor could not run unasked at all.** CodeRabbit declined every PR
here — *"does not receive automatic reviews because it has fewer than 10
stars"* on #20, *"Draft PRs are not automatically reviewed by default"* on #41 —
and honoured `@coderabbitai review` only from a human, never from a workflow, so
no automation in this repository could produce a review. A control nobody runs
is not a control.

Analysis scope follows the repository: `sonar-project.properties` excludes
`vendor/`, so the bundle we never edit is not judged, and names the three source
directories every tracked `.py` outside `tests/` falls under. The check belongs
in the `main` ruleset for the reason §14 gives. Two cases remain uncovered: a
quality gate loosened rather than switched off, and — since §39 — a scope
narrowed in the diff under review.

The measured value of the arrangement so far, on the two changes it reviewed
before this: CodeRabbit contributed two docstrings to #20; the adversarial pass
over that same merged change found the assertion in
`test_every_table_that_refuses_a_rewrite_also_refuses_a_truncate` was half
blind, and two tables with no guard at all (#24). Both had already passed
`make check`.

---

## 3. Skills enabled for this repository

| Skill | When |
|---|---|
| `superpowers:test-driven-development` | before implementing any feature or fix |
| `superpowers:systematic-debugging` | before proposing a fix for any failure |
| `confidence-review` | after writing code, before declaring done |
| `rewrite-tournament` | after a non-trivial function, before commit |
| `adversarial-reviewer` | before merging anything touching a governed path |
| `ponytail-review` | when a diff grows past its concern |
| `superpowers:verification-before-completion` | before reporting completion |

---

## 4. Two gates that must not be "tidied"

**bandit is pinned to Python 3.12.** bandit 1.7.10 reaches for the
`ast.Constant.s` alias newer interpreters no longer provide; under 3.14 it skips
every server file and exits 0 — a green SAST gate that scanned nothing. The step
asserts the JSON report carries no parse errors and covers the whole server, so
a naive version bump fails loudly.

**A scanner that skipped a file is a failure.** `scan_floors.py` holds three
floors, and they catch different things. `--no-parse-errors` is what catches the
interpreter failure above: under 3.14 bandit still lists all 29 files in
`metrics` with their line counts, and files the 26 it choked on under `errors` —
so a coverage count would pass it. `--cover DIR…` names the directories the scan
was pointed at and refuses a report that does not account for each tracked .py
under them by name, plus a target holding no tracked .py at all, so a mistyped
directory cannot quietly expect nothing. `--unscanned DIR…` names what is
deliberately left out, and between the two every tracked .py in the repository
has to be claimed: a source package a later phase adds cannot go unscanned
without somebody saying so. This applies to every scanning gate this
repository runs, and since `docs/DECISIONS.md` §39 that includes the coverage
report: `scan_floors.py --cobertura` reads `coverage.xml` through the same
floors, because a file missing from a coverage report is not a file at zero per
cent — it raises the percentage of every file that is there. The third reviewer
is no longer the exception it could not reach, now that this tree declares the
scope it reads (§2).

---

## 5. What these controls do not fix

The report's root causes include "AI lacking local business logic" and "poor
adherence to repository idioms". No linter detects a plausible-looking credit
calculation that is wrong. That is what the methodology bundle, the calculator
boundary and the qualification corpus are for — and why the invariants in
`CLAUDE.md` are non-negotiable rather than advisory.
