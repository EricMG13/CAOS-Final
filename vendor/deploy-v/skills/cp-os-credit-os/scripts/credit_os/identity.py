"""CREDIT OS identity generation and validation.

CP-OS generates every identifier it writes. User text never becomes a path
component, and a user-supplied identifier is never authority — it may only
select an already enumerated resource.

This module is import-clean: standard library only, no repository imports, so it
survives projection into the installed package.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import unicodedata
from datetime import datetime, timezone

RUN_ID = re.compile(r"^COS-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{32}$")
ATTEMPT_ID = re.compile(r"^ATT-[A-Z0-9-]{2,16}-[0-9a-f]{16}$")
ROUTE_NODE_ID = re.compile(r"^RN-[A-Z0-9_]{2,48}-[0-9]{2}-CP-[A-Z0-9]{1,8}$")
MODULE_ID = re.compile(r"^CP-[A-Z0-9]{1,8}$")
SELECTION_ID = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
INTAKE_SELECTION_IDS = frozenset({"GUIDED_INTAKE", "STANDALONE_INTAKE"})
STANDALONE_SELECTION = re.compile(r"^STANDALONE_[A-Z0-9_]{1,52}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

ATTEMPT_SUFFIX_LENGTH = 16

# Categories that let a display string lie about what it is: Cc/Cf cover control
# and formatting characters including the bidirectional overrides, Cs surrogates,
# Co private use, Cn unassigned.
_UNSAFE_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Cn"})


class IdentityError(ValueError):
    """A value failed a frozen identity grammar."""


def require_intake_selection(selection_id: str) -> str:
    """Accept only the two universal pre-CP-0 intake selections."""
    if selection_id not in INTAKE_SELECTION_IDS:
        raise IdentityError(
            "intake selection must be GUIDED_INTAKE or STANDALONE_INTAKE"
        )
    return selection_id


def standalone_selection_id(module_id: str) -> str:
    """Compose a standalone selection from an already validated module ID.

    This low-level helper intentionally does not decide eligibility.  Callers
    must select the module from the generated catalogue before invoking it.
    """
    if not MODULE_ID.fullmatch(module_id):
        raise IdentityError(f"not a module ID: {module_id!r}")
    selection = "STANDALONE_" + module_id.replace("-", "_")
    if not STANDALONE_SELECTION.fullmatch(selection):
        raise IdentityError(f"standalone selection exceeds its frozen grammar: {selection!r}")
    return selection


def new_run_id(*, now: datetime | None = None) -> str:
    """Generate a run ID: UTC stamp plus 128 bits of entropy.

    Generated once, at first run, and rendered into the CP-0 bootstrap envelope.
    CP-0 echoes it into its handoff, which then anchors the run — under
    HOST_READ_ONLY there is nowhere to reserve or persist it, so the artifact is
    the record. A run ID lost before CP-0 is run simply means starting again;
    nothing was stored.
    """
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return f"COS-{moment.strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(16)}"


def derive_attempt_id(
    *, run_id: str, route_node_id: str, module_id: str, ordinal: int = 1
) -> str:
    """Derive an attempt ID: ATT-<module_id>-<hex16>.

    Deterministic, not random. Under HOST_READ_ONLY there is nowhere to persist a
    generated value, so a random attempt ID would be unrecoverable the moment the
    session ended and no later session could verify an artifact's echo against it.

    Deriving from (run_id, route_node_id, ordinal) lets a returning session
    recompute the same identifier from the artifacts alone. `ordinal` starts at 1
    and increments only on an explicit user-declared rerun.
    """
    require(RUN_ID, run_id, "run_id")
    require(ROUTE_NODE_ID, route_node_id, "route_node_id")
    if not MODULE_ID.match(module_id):
        raise IdentityError(f"not a module ID: {module_id!r}")
    if not isinstance(ordinal, int) or ordinal < 1:
        raise IdentityError(f"attempt ordinal must be a positive integer: {ordinal!r}")
    seed = "\x00".join((run_id, route_node_id, str(ordinal))).encode("utf-8")
    return f"ATT-{module_id}-{hashlib.sha256(seed).hexdigest()[:ATTEMPT_SUFFIX_LENGTH]}"


def split_attempt_id(attempt_id: str) -> tuple[str, str]:
    """Return (module_id, suffix).

    Anchored on the fixed 16-character lowercase-hex suffix. The middle class
    contains '-', so splitting on the last separator is not reliable.
    """
    if not ATTEMPT_ID.match(attempt_id):
        raise IdentityError(f"not an attempt ID: {attempt_id!r}")
    body = attempt_id[len("ATT-") :]
    module_id, suffix = body[: -(ATTEMPT_SUFFIX_LENGTH + 1)], body[-ATTEMPT_SUFFIX_LENGTH:]
    return module_id, suffix


def route_node_id(selection_id: str, stage: int, module_id: str) -> str:
    """Compose the stable identifier for one executable occurrence."""
    if not SELECTION_ID.match(selection_id):
        raise IdentityError(f"not a selection ID: {selection_id!r}")
    if not MODULE_ID.match(module_id):
        raise IdentityError(f"not a module ID: {module_id!r}")
    if not 0 < stage < 100:
        raise IdentityError(f"stage out of range: {stage}")
    return f"RN-{selection_id}-{stage:02d}-{module_id}"


def require(pattern: re.Pattern[str], value: object, label: str) -> str:
    """Validate an identifier against a frozen grammar, or fail closed."""
    if not isinstance(value, str):
        raise IdentityError(f"{label} must be a string, got {type(value).__name__}")
    if not pattern.match(value):
        raise IdentityError(f"{label} does not match its frozen grammar: {value!r}")
    return value


def is_safe_component(value: str) -> bool:
    """True only for a value that could not misbehave as a path component.

    This is a display and comparison guard. It is deliberately *not* the reason
    paths are safe — CP-OS generates every path it writes, and no external value
    ever becomes one.
    """
    if not value or len(value) > 64:
        return False
    if value != unicodedata.normalize("NFC", value):
        return False
    if any(unicodedata.category(ch) in _UNSAFE_CATEGORIES for ch in value):
        return False
    if value in {".", ".."} or value.startswith("."):
        return False
    return all(ch.isascii() and (ch.isalnum() or ch in "._-") for ch in value)


def sanitize_display(value: str, *, limit: int = 200) -> str:
    """Make untrusted text safe to render inside a labelled explanation.

    Normalizes, strips control and bidirectional characters, caps length, and
    escapes Markdown. The result can never create an option, command, path,
    link or state transition — it is only ever shown.
    """
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFC", value)
    text = "".join(
        ch for ch in text if unicodedata.category(ch) not in _UNSAFE_CATEGORIES
    )
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    # Underscore is deliberately absent. Escaping it mangles almost every real
    # filename (ACME_CP-1_20260802.md) to prevent emphasis, and emphasis is
    # cosmetic — it cannot create an option, command, path or link. The escaped
    # set is the characters that can: link and code syntax, pipes that forge
    # table cells, and angle brackets.
    for char in ("\\", "`", "*", "[", "]", "<", ">", "|", "#"):
        text = text.replace(char, "\\" + char)
    return text
