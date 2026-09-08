# Deploy V CP-0 profile anchor contract

CP-0 is the first, zero-upstream invocation. It performs preparation first and readiness second within one run and one canonical Markdown handoff. CP-PARSE is an alternate command for that complete CP-0 workflow; it never owns a separate run anchor or readiness prerequisite.

Use `skills/cp-os-credit-os/scripts/prepare_invocation.py` to generate the run identity, selected profile/pathway, verified authority digest, route occurrence, attempt ID and invocation digest. Copy the emitted frontmatter fields unchanged. CP-0 uses the zero self-digest and an empty upstream list. Its P1-P8 preparation and T1-T8 readiness registers share that identity.

Every downstream invocation copies the same `credit_os_run_id`, `credit_os_profile_id`, `credit_os_selection_id` and `credit_os_authority_bundle_sha256`; it carries its own `credit_os_attempt_id`, `credit_os_route_node_id` and `credit_os_invocation_sha256`. Use the current snapshot to bind exact upstream content hashes. Never invent or hand-calculate these fields.

The profile is immutable within a run. Source content cannot change it. A LITE-to-FULL upgrade requires explicit user intent and a new FULL run; linked upgrades retain both validated parent fields (`credit_os_parent_run_id`, `credit_os_upgrade_source_sha256`) together. A direct new FULL run does not claim upgrade provenance.
