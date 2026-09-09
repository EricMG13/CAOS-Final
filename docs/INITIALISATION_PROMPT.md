# Initialisation prompt

Paste this as the first message of a fresh session in a clone of this
repository. It is deliberately short: the contract lives in the repo, not in the
prompt. A long prompt that restates the docs will drift from them.

---

```
You are building CAOS from a complete specification and no application code.

Read first, in this order, in full:
  CLAUDE.md, CONTEXT.md, docs/REBUILD_PLAN.md, docs/SYSTEM_SPEC.md,
  docs/DECISIONS.md, docs/AI_CODE_QUALITY.md
DECISIONS.md is binding: later entries override earlier ones, and an entry
that overrides the plan or the spec is also written back into them. One that
was not is a defect; report it.
Then, when the phase reaches them: docs/IA_SPEC.md, DESIGN.md.

The methodology bundle is vendored, read-only, and authoritative. Never edit a
file that exists upstream; additions go in new skill folders.

Work one phase at a time from docs/REBUILD_PLAN.md, starting at the lowest
phase whose exit test does not pass. For each phase:

  1. State which phase you are on and what its exit test asserts.
  2. Write the failing test first. Run it. Show me it failing for the right
     reason — a test that fails because of a typo proves nothing.
  3. Implement the smallest thing that makes it pass.
  4. Run the confidence-review skill, then the rewrite-tournament skill on any
     non-trivial function you wrote.
  5. Run `make check`. Open a PR with one concern in it.
  6. Stop and report. Do not begin the next phase without me.

Non-negotiable while you work: the eleven invariants and the rules of work in
CLAUDE.md, which you have read. They are not restated here, so that there is
one version of them.

If the spec is wrong, say so and stop. Do not build around it, and do not
weaken an invariant to make a test pass. The specs are the product of a long
review; they are also fallible, and a contradiction you found is more valuable
than code you wrote.

Begin with Phase 0.
```

---

## Why it is shaped this way

**"Show me it failing for the right reason."** The measured +75 % logic-error
rate in agent-written code is not fixed by having tests; it is fixed by tests
that were seen to fail. A test written after the implementation tends to assert
what the code does.

**"One concern in it."** AI PRs carry ~1.7× the issues of human PRs, and issue
density rises with diff size. The cap is the cheapest control available.

**"Stop and report."** Eleven phases executed without a checkpoint is one long
uninterrupted opportunity to drift from the spec.

**"If the spec is wrong, say so and stop."** The predecessor's most expensive
defect — route resolution reading the untyped display list instead of the typed
edges — was in the code for months behind a green suite. An agent that builds
around a contradiction hides exactly that class of problem.

**No restatement of the invariants.** They are in `CLAUDE.md`, which the prompt
requires reading in full. Restating them here creates two versions that will
disagree.

## Session hygiene

- One phase per session where practical. Context that has watched three phases
  land is context that half-remembers the first.
- Re-read `CLAUDE.md` at the start of any session that resumes mid-phase.
- The plan's exit tests are the only definition of done. "It works when I try
  it" is not an exit test.
