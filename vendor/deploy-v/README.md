# Deploy V

Deploy V provides 25 physical skills for enterprise leveraged-finance credit analysis and governed publication.

## Deployment

Folder grounding via a saved Copilot memory prompt, not native Cowork install -- ground a conversation on this package's root folder (the one directly containing `skills/`, `CANON_SHARED.md`, and the retrieval index), then follow `DEPLOY_V_COPILOT_MEMORY_PROMPT.md`.

## Verify

Run `python3 -B verify_package.py`. It checks every packaged file's hash and size,
the baseline digest, routing and launcher build IDs, identical shared helpers,
runtime authority pins, Python syntax, ten helper self-checks, the CP-MODEL input
validator self-test, and the review regressions in `tests/`. Verification is read-only.

For exporter integration checks, install the dependencies declared by CP-MODEL
and CP-MEMO, plus `pdftoppm`, then run `python3 -B verify_package.py --integration`.
This exercises native rasterization at 9, 10, and 100 pages, including rejection
of unsafe page paths. A live Microsoft 365 launch still requires the acceptance
tests in the launcher documents.

This is the distributed package; the upstream build system and its full test
suite are not included. After intentional local edits, use
`python3 -B verify_package.py --refresh --integration`. Refresh copies shared
helpers from the canonical skill listed in `SHARED` in that script, runs checks,
and regenerates the manifest, baseline, integrity hashes, routing build ID, and
launcher facts. Edit the listed canonical helper, not an arbitrary duplicate.
Refresh alone never rewrites runtime authority pins. After reviewing intentional contract changes, use `python3 -B verify_package.py --rebuild-authorities --refresh --integration` to rebuild the local bundle explicitly and verify the complete package. Unavailable upstream-only provenance components remain pinned; the local rebuild is recorded as such.

The build ID hashes canonical JSON containing the routing fields (excluding
the ID itself), integrity skill records, and root source hashes. Root and test
files have separate integrity records, including the finalized launcher text.
Bytecode and symlinks are rejected as distribution drift.

## Contents

25 physical skills under `skills/`. `CP_DEPLOY_V_RETRIEVAL_INDEX_v1.json` is the retrieval authority and carries routing fields only -- module IDs, aliases and entry paths -- because it is read on every dispatch; per-file hashes live beside it in `DEPLOY_V_INTEGRITY_v1.json`. `DEPLOY_V_MANIFEST.json` and `DEPLOY_V_BASELINE.json` are regenerated from this exact tree.

### Execution order and reruns

The numbered layer on a module is a display grouping, not an execution order. CP-0 freezes the effective source set and selected work; the shared dependency plan then runs each producer before the consumers that use its accepted handoff. Reconciliation, navigation and memo publication use that same plan. A module may be shown in an earlier layer after a dependency-driven return, and it still runs at the current route occurrence with its current upstream hashes.

Rerun the affected module and its downstream dependents when any of these occur:

- CP-0 changes its source inventory, profile, selection, readiness, or accepted handoff.
- A required upstream handoff is missing, stale, rejected, or has a changed content hash.
- A later module identifies a factual gap that requires new source extraction or changes a blocked source gate.
- A late CP-5/CP-6 challenge creates a new bounded research question.

An ordinary late question does not rewrite CP-0 or restart unrelated branches. Preserve the run anchor, create or revise the bounded CP-DR brief, and rerun the named research consumer plus its dependents. The runtime reports the exact blocker instead of asking the user to rerun every module.

### Physical modules and aliases

Every command ID resolves to one physical `SKILL.md`. The current owners are:

| Alias IDs | Physical owner |
| --- | --- |
| `CP-PARSE` | `CP-0` |
| `CP-2C` | `CP-1A` |
| `CP-1E` | `CP-1D` |
| `CP-2B` | `CP-2A` |
| `CP-2F` | `CP-2E` |
| `CP-3A`, `CP-3B` | `CP-3` |
| `CP-4A`, `CP-4B`, `CP-4D` | `CP-4` |
| `CP-5A` | `CP-5` |
| `CP-6A` | `CP-6` |
| `CP-L20`, `CP-L23`, `CP-L30`, `CP-L40` | `CP-L10` |

Aliases are retrieval names, not separate implementations or extra workflow steps. On every launch, resolve the requested ID against the current `CP_DEPLOY_V_RETRIEVAL_INDEX_v1.json`, require exactly one match, then read that owner's current `SKILL.md`. A stale, inaccessible, missing, or ambiguous index stops dispatch; do not scan sibling folders or use cached skill text as a fallback. An alias-only CP-0 selection is a migration error and must be replaced with its canonical owner while preserving the user's qualifiers.

### Launch checklist

1. Ground the host on the package root containing `skills/`, `CANON_SHARED.md`, and the retrieval index.
2. Reopen the current retrieval index and verify its `build_id` before each launch.
3. Resolve the exact command or alias to one physical owner and report the normalized command and current skill path.
4. For a routed issuer run, start from the current accepted CP-0 context; for standalone CP-DR, use its complete brief without manufacturing CP-0.
5. If a handoff is rejected, follow its concrete reason and rerun only the affected dependency path.

The URL-bound launcher adds the same checks for a connector-backed folder and requires the connector-returned package and skill URLs to remain current. See `DEPLOY_V_COPILOT_MEMORY_PROMPT_URL_BOUND.md` when stable folder URLs are available; otherwise use the folder-grounded prompt.

CP-3 always uses the maintained Sector RV workbook inside the enterprise
environment and assumes it is current and relevant. It resolves the selected or
configured enterprise reference, or finds it through the available enterprise
connector, without freshness/relevance or source-permission confirmation.
`REF_CP-3_Sector_RV.xlsx` is an intentionally empty deployment placeholder;
enterprise loan data is not distributed here. Example screenshots explain the
layout and are not a replacement market source. No local copy is needed. Keep
source dates and row citations; actual missing enterprise values remain data gaps.

The other two bundled reference workbooks contain sample portfolio data. Supply
portfolio-specific constraints and exposures for mandate checks and numeric
sizing. Missing portfolio inputs limit those decisions while supported loan RV
and security-selection analysis continue.

## CP-DR in the workflow

CP-DR is an optional physical research module with no fixed numbered layer. A run-specific research brief inserts it after named factual prerequisites and before affected consumers, including late questions without rewriting CP-0. Its three required registers lock question coverage and evidence; receivers must explicitly accept, reject or qualify each finding. Unresolved answers block only their assigned consumers. Revisions are conservative at dossier/batch level. Standalone issuer/sector research remains available without CP-0. See `skills/cp-os-credit-os/references/CP_DR_RESEARCH_BRIEF_V1.md` for the brief, placement and validation commands.
