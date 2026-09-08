"""Profile-qualified identity helpers for the Deploy V CREDIT OS runtime."""

from __future__ import annotations

import hashlib
import re

from credit_os.identity import MODULE_ID, RUN_ID, SHA256, IdentityError, new_run_id

FULL_PROFILE = "FULL_CREDIT_32"
LITE_PROFILE = "LITE_CREDIT_22"
PROFILE_IDS = frozenset({FULL_PROFILE, LITE_PROFILE})

PROFILE_ID = re.compile(r"^(?:FULL_CREDIT_32|LITE_CREDIT_22)$")
SELECTION_ID = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
ROUTE_NODE_ID = re.compile(
    r"^RN-(FULL_CREDIT_32|LITE_CREDIT_22)-"
    r"([A-Z][A-Z0-9_]{2,63})-([0-9]{2})-(CP-[A-Z0-9]{1,8})$"
)
ATTEMPT_ID = re.compile(r"^ATT-CP-[A-Z0-9]{1,8}-[0-9a-f]{16}$")


def require(pattern: re.Pattern[str], value: object, label: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise IdentityError(f"{label} does not match its frozen grammar: {value!r}")
    return value


def require_profile(profile_id: object) -> str:
    return require(PROFILE_ID, profile_id, "profile_id")


def route_node_id(
    profile_id: str, selection_id: str, stage: int, module_id: str
) -> str:
    """Return the stable ID for one module occurrence in one profile route."""
    require_profile(profile_id)
    require(SELECTION_ID, selection_id, "selection_id")
    if not isinstance(stage, int) or isinstance(stage, bool) or not 0 < stage < 100:
        raise IdentityError(f"stage out of range: {stage!r}")
    require(MODULE_ID, module_id, "module_id")
    return f"RN-{profile_id}-{selection_id}-{stage:02d}-{module_id}"


def parse_route_node(value: object) -> tuple[str, str, int, str]:
    text = require(ROUTE_NODE_ID, value, "route_node_id")
    match = ROUTE_NODE_ID.fullmatch(text)
    assert match is not None
    return match.group(1), match.group(2), int(match.group(3)), match.group(4)


def derive_attempt_id(*, run_id: str, route_node_id: str, ordinal: int = 1) -> str:
    """Derive a resumable attempt ID from the immutable run occurrence."""
    require(RUN_ID, run_id, "run_id")
    _profile, _selection, _stage, module_id = parse_route_node(route_node_id)
    if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1:
        raise IdentityError(f"attempt ordinal must be a positive integer: {ordinal!r}")
    seed = "\x00".join((run_id, route_node_id, str(ordinal))).encode("utf-8")
    return f"ATT-{module_id}-{hashlib.sha256(seed).hexdigest()[:16]}"


__all__ = [
    "ATTEMPT_ID",
    "FULL_PROFILE",
    "LITE_PROFILE",
    "MODULE_ID",
    "PROFILE_ID",
    "PROFILE_IDS",
    "ROUTE_NODE_ID",
    "RUN_ID",
    "SELECTION_ID",
    "SHA256",
    "IdentityError",
    "derive_attempt_id",
    "new_run_id",
    "parse_route_node",
    "require",
    "require_profile",
    "route_node_id",
]
