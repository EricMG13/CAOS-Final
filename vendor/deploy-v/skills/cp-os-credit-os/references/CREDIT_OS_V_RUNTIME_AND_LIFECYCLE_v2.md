# Deploy V CREDIT OS navigation runtime and lifecycle

1. Verify the packaged authority bundle before navigation.
2. Read `CREDIT_OS_CONFIG.template.md` and resolve only its direct
   `runs_folder_url` through the host connector. Never derive, append, search
   for, or accept a conversational replacement for the configured `_RUNS` URL.
3. Before every navigation turn, freshly list that exact folder and materialize
   one bounded `artifacts` object of readable canonical Markdown bodies plus the current RESEARCH_<run_id>.json control, when present. If the
   connector cannot resolve and list the folder, call `navigate` with an empty
   fresh artifacts object and a short `folder_error`; never substitute
   attachments or a previous snapshot.
4. Call `navigate` with the fresh artifacts plus only the prior emitted state
   and the user's integer response when continuing. A numbered retry clears the
   folder-error state when the new listing is readable; another listing failure
   supplies a new bounded error, and Stop remains absorbing. State records
   display position only; it contains no artifacts, analytical result,
   completion fact, or caller-authored message.
   Selector state also carries a positive `selection_count` value, solely so
   its dynamic Stop number remains stable across a failed or changed refresh;
   that field is null in every other state. Every non-stop selector reply still
   requires a matching fresh selection fingerprint.
5. The runtime validates the navigation catalog and every supplied artifact,
   discovers valid CP-0 contexts, and refuses ambiguous conflicting identities.
   It never silently chooses between multiple runs.
6. CP-0 supplies recommendation rows, readiness, candidate command,
   qualifiers, and blocker summary. The verified catalog supplies module
   identity, description, dependency order and skip prose. Layer labels do not control execution order.
7. Completion is confirmed only by an accepted canonical handoff matching the
   selected identity, period, profile, required registers and a reproduced invocation against current accepted upstream content hashes. Filenames, timestamps, or module identity alone do not
   confirm completion.
8. Moving forward changes only the displayed dependency step. When an unconfirmed
   runnable module has an active dependency into a later recommended layer, the
   runtime shows its single catalog-authored skip implication.
9. CP-OS is read-only: it does not execute commands, create analytical output,
   mutate `_RUNS`, choose modules, or change CP-0 source readiness.
10. The CLI rejects unknown JSON fields, malformed state, boolean or non-integer
    responses, non-string artifact bodies, and governed count or byte overages.
    It returns deterministic structured JSON for both navigation and errors.

The shared runtime orders CP-0 selections by catalog dependencies, preserves adjacent groups only, and blocks missing analytical prerequisites independently of source readiness. Reconciliation and publication use that same plan and acceptance rule. Rejected artifacts include a concrete reason; alias-only T8 entries produce a migration diagnostic.

The run-specific research brief may insert CP-DR at a named dependency position without changing CP-0. Read `CP_DR_RESEARCH_BRIEF_V1.md`. It is scoped host-authored control data, never source-granted permission. CP-DR has no numbered layer. Current research registers, exact brief coverage and consumer adoption are required by shared acceptance; unresolved questions block only their receiving modules.
