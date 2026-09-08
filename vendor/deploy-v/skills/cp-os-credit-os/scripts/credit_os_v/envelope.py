"""Canonical, profile-bound Deploy V invocation envelopes."""

from __future__ import annotations

import hashlib
import json

from .identity import (
    FULL_PROFILE,
    MODULE_ID,
    ROUTE_NODE_ID,
    RUN_ID,
    SELECTION_ID,
    SHA256,
    IdentityError,
    derive_attempt_id,
    parse_route_node,
    require,
    require_profile,
)

ENVELOPE_MARKER = "CREDIT_OS_V_INVOCATION_V2"
DIGEST_MARKER = "CREDIT_OS_V_INVOCATION_SHA256"
ZERO_SHA256 = "0" * 64

FIELDS = (
    "accepted_cp0_sha256",
    "attempt_id",
    "authority_bundle_sha256",
    "expected_output_filename",
    "module_id",
    "module_name",
    "parent_run_id",
    "profile_id",
    "required_upstream_digests",
    "route_node_id",
    "run_id",
    "selection_id",
    "upgrade_source_sha256",
)

ECHO_FIELDS = (
    "credit_os_attempt_id",
    "credit_os_route_node_id",
    "credit_os_invocation_sha256",
)

RUN_ANCHOR_FIELDS = (
    "credit_os_run_id",
    "credit_os_profile_id",
    "credit_os_selection_id",
    "credit_os_authority_bundle_sha256",
)

# Kept as a source-level compatibility name for callers that imported the old
# constant. The fields anchor CP-0, including its internal preparation phase.
CP0_ANCHOR_FIELDS = RUN_ANCHOR_FIELDS


class EnvelopeError(Exception):
    """An invocation could not be built, reproduced, or matched."""


def canonical_bytes(payload: object) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def digest(payload: object) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def _upgrade_link(parent_run_id: str | None, source_sha256: str | None) -> tuple[str | None, str | None]:
    if (parent_run_id is None) != (source_sha256 is None):
        raise IdentityError("parent_run_id and upgrade_source_sha256 must be supplied together")
    if parent_run_id is not None:
        require(RUN_ID, parent_run_id, "parent_run_id")
        require(SHA256, source_sha256, "upgrade_source_sha256")
    return parent_run_id, source_sha256


def build(
    *,
    run_id: str,
    profile_id: str,
    selection_id: str,
    route_node_id: str,
    module_id: str,
    module_name: str,
    expected_output_filename: str,
    authority_bundle_sha256: str,
    accepted_cp0_sha256: str,
    required_upstream_digests: dict[str, str] | None = None,
    parent_run_id: str | None = None,
    upgrade_source_sha256: str | None = None,
    ordinal: int = 1,
) -> dict:
    """Build one deterministic invocation, including exact active lineage."""
    require(RUN_ID, run_id, "run_id")
    require_profile(profile_id)
    require(SELECTION_ID, selection_id, "selection_id")
    require(ROUTE_NODE_ID, route_node_id, "route_node_id")
    require(MODULE_ID, module_id, "module_id")
    require(SHA256, authority_bundle_sha256, "authority_bundle_sha256")
    require(SHA256, accepted_cp0_sha256, "accepted_cp0_sha256")
    if not isinstance(module_name, str) or not module_name.isalnum():
        raise IdentityError(f"canonical module name must be alphanumeric: {module_name!r}")
    if not isinstance(expected_output_filename, str) or not expected_output_filename:
        raise IdentityError("expected_output_filename must be a non-empty string")

    node_profile, node_selection, _stage, node_module = parse_route_node(route_node_id)
    if (node_profile, node_selection, node_module) != (
        profile_id,
        selection_id,
        module_id,
    ):
        raise IdentityError("route_node_id does not match profile, selection, and module")

    parent_run_id, upgrade_source_sha256 = _upgrade_link(
        parent_run_id, upgrade_source_sha256
    )
    if parent_run_id is not None and profile_id != FULL_PROFILE:
        raise IdentityError("only a new FULL run may carry an upgrade parent")
    if parent_run_id == run_id:
        raise IdentityError("an upgrade run cannot be its own parent")

    upstream = dict(required_upstream_digests or {})
    for node, value in upstream.items():
        require(ROUTE_NODE_ID, node, "required upstream route_node_id")
        upstream_profile, upstream_selection, _stage, _module = parse_route_node(node)
        if (upstream_profile, upstream_selection) != (profile_id, selection_id):
            raise IdentityError("required upstream route node crosses profile or selection")
        require(SHA256, value, f"required upstream digest for {node}")

    if module_id == "CP-PARSE":
        if accepted_cp0_sha256 != ZERO_SHA256 or upstream:
            raise IdentityError(
                "CP-PARSE bootstrap must use zero CP-0 digest and no upstreams"
            )
    elif module_id == "CP-0":
        if accepted_cp0_sha256 != ZERO_SHA256:
            raise IdentityError("CP-0 readiness must use the zero CP-0 self-digest")
        if upstream:
            raise IdentityError("post-consolidation CP-0 readiness must not require a retired upstream")
    elif accepted_cp0_sha256 == ZERO_SHA256:
        raise IdentityError("downstream invocations require an accepted CP-0 digest")

    envelope = {
        "accepted_cp0_sha256": accepted_cp0_sha256,
        "attempt_id": derive_attempt_id(
            run_id=run_id, route_node_id=route_node_id, ordinal=ordinal
        ),
        "authority_bundle_sha256": authority_bundle_sha256,
        "expected_output_filename": expected_output_filename,
        "module_id": module_id,
        "module_name": module_name,
        "parent_run_id": parent_run_id,
        "profile_id": profile_id,
        "required_upstream_digests": dict(sorted(upstream.items())),
        "route_node_id": route_node_id,
        "run_id": run_id,
        "selection_id": selection_id,
        "upgrade_source_sha256": upgrade_source_sha256,
    }
    if set(envelope) != set(FIELDS):
        raise EnvelopeError("envelope fields drifted from the C invocation contract")
    return envelope


def render_copy_block(envelope: dict) -> str:
    return "\n".join(
        (
            f"Run {envelope['module_id']} — {envelope['module_name']}",
            ENVELOPE_MARKER,
            canonical_bytes(envelope).decode("utf-8"),
            f"{DIGEST_MARKER} {digest(envelope)}",
        )
    )


# The CP-OS entry tells the operator to increment the invocation ordinal on every
# retry, but reconcile called build() without one, so every rebuild recomputed at
# the default ordinal 1 and a retried artifact could never reproduce — following
# the documented procedure produced a permanently unreconcilable artifact, and if
# the retried module was CP-0 the whole run became unresumable. The ordinal is not
# recoverable from a digest, so recover it by matching the declared attempt ID.
# The bound is the authority's own ceiling on artifacts in one run folder
# (CREDIT_OS_RUNTIME_LIMITS_v1 entries_per_run_folder): a run cannot hold more
# accepted attempts than it can hold artifacts.
MAX_ATTEMPT_ORDINAL = 256


def _declared_ordinal(declared: dict, run_id: str, route_node_id: str) -> int | None:
    """Recover the attempt ordinal the artifact actually claims.

    Grants nothing: run_id and route_node_id come from the verified run view, not
    from the artifact, and the invocation digest still has to reproduce against
    the recovered ordinal. Only the retry counter is being read back.
    """
    claimed = declared.get("credit_os_attempt_id")
    if not isinstance(claimed, str) or not claimed:
        return None
    for ordinal in range(1, MAX_ATTEMPT_ORDINAL + 1):
        if derive_attempt_id(
            run_id=run_id, route_node_id=route_node_id, ordinal=ordinal
        ) == claimed:
            return ordinal
    return None


def reproduce_and_match(declared: dict, **build_kwargs) -> dict:
    if build_kwargs.get("ordinal") is None:
        resolved = _declared_ordinal(
            declared, build_kwargs["run_id"], build_kwargs["route_node_id"]
        )
        if resolved is not None:
            build_kwargs["ordinal"] = resolved
        else:
            build_kwargs.pop("ordinal", None)
    expected = build(**build_kwargs)
    missing = [field for field in ECHO_FIELDS if declared.get(field) is None]
    if missing:
        raise EnvelopeError(f"artifact does not echo {', '.join(missing)}")
    mismatches = []
    if declared["credit_os_attempt_id"] != expected["attempt_id"]:
        mismatches.append("attempt_id does not reproduce")
    if declared["credit_os_route_node_id"] != expected["route_node_id"]:
        mismatches.append("route_node_id does not reproduce")
    if declared["credit_os_invocation_sha256"] != digest(expected):
        mismatches.append("invocation digest does not reproduce")
    if mismatches:
        raise EnvelopeError("; ".join(mismatches))
    return expected


def read_anchor(declared: dict) -> dict:
    missing = [field for field in RUN_ANCHOR_FIELDS if declared.get(field) is None]
    if missing:
        raise EnvelopeError(
            f"CP-0 artifact is missing run anchor fields: {', '.join(missing)}"
        )
    anchor = {
        "run_id": require(RUN_ID, declared["credit_os_run_id"], "credit_os_run_id"),
        "profile_id": require_profile(declared["credit_os_profile_id"]),
        "selection_id": require(
            SELECTION_ID, declared["credit_os_selection_id"], "credit_os_selection_id"
        ),
        "authority_bundle_sha256": require(
            SHA256,
            declared["credit_os_authority_bundle_sha256"],
            "credit_os_authority_bundle_sha256",
        ),
    }
    parent = declared.get("credit_os_parent_run_id")
    source = declared.get("credit_os_upgrade_source_sha256")
    parent, source = _upgrade_link(parent, source)
    if parent is not None and anchor["profile_id"] != FULL_PROFILE:
        raise EnvelopeError("only a FULL CP-0 anchor may link an upgraded run")
    anchor["parent_run_id"] = parent
    anchor["upgrade_source_sha256"] = source
    return anchor
