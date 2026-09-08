"""Storage capability modes and the claims each permits.

The mode is the result of what the connector actually returned, never a
configuration assertion. A mode declared unreachable may not be selected, and no
operation it declares may be attempted.

Everything here reads `CREDIT_OS_CAPABILITIES_v1.json`. The claim lists live in
data so they can be tested directly, rather than asserted in prose and checked by
substring.

Standard library only, no repository imports.
"""

from __future__ import annotations

import json
from pathlib import Path

HOST_READ_ONLY = "HOST_READ_ONLY"
ATTACHED_READ_ONLY = "ATTACHED_READ_ONLY"
UNAVAILABLE = "UNAVAILABLE"

# Degradation is one-way. A failed list never re-escalates.
DEGRADATION_ORDER = (HOST_READ_ONLY, ATTACHED_READ_ONLY, UNAVAILABLE)

CAPABILITIES_FILENAME = "CREDIT_OS_CAPABILITIES_v1.json"


class CapabilityError(Exception):
    """A mode was selected or used in a way its declaration forbids."""


class UnreachableMode(CapabilityError):
    """A mode marked reachable:false was selected."""


def _find_capabilities(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    here = Path(__file__).resolve().parent
    for candidate in (
        here / CAPABILITIES_FILENAME,
        here.parent / "references" / CAPABILITIES_FILENAME,
        here.parent.parent / "references" / CAPABILITIES_FILENAME,
        here.parent.parent
        / "Co-Pilot Agents"
        / "CP-OS"
        / "references"
        / CAPABILITIES_FILENAME,
    ):
        if candidate.is_file():
            return candidate
    raise CapabilityError(f"{CAPABILITIES_FILENAME} not found; the package is incomplete")


def load(path: Path | None = None) -> dict:
    return json.loads(_find_capabilities(path).read_text(encoding="utf-8"))


class Capability:
    """One resolved mode, with the operations and claims it allows."""

    def __init__(self, mode: str, declaration: dict) -> None:
        self.mode = mode
        self._declaration = declaration
        if not declaration.get("reachable", False):
            raise UnreachableMode(
                f"{mode} is not reachable in this environment: "
                f"{declaration.get('unreachable_reason', 'no reason recorded')}"
            )

    @property
    def operations(self) -> frozenset[str]:
        return frozenset(self._declaration.get("operations", ()))

    @property
    def has_trusted_state(self) -> bool:
        return bool(self._declaration.get("trusted_state", False))

    def permits(self, operation: str) -> bool:
        return operation in self.operations

    def require(self, operation: str) -> None:
        """Fail closed before attempting an operation the mode does not allow."""
        if not self.permits(operation):
            raise CapabilityError(
                f"{self.mode} does not permit {operation!r}; "
                f"it allows {sorted(self.operations) or 'nothing'}"
            )

    @property
    def may_claim(self) -> tuple[str, ...]:
        return tuple(self._declaration.get("may_claim", ()))

    @property
    def must_not_claim(self) -> tuple[str, ...]:
        return tuple(self._declaration.get("must_not_claim", ()))


def resolve(mode: str, capabilities: dict | None = None) -> Capability:
    """Resolve a named mode, refusing anything declared unreachable."""
    capabilities = capabilities or load()
    modes = capabilities["modes"]
    if mode not in modes:
        raise CapabilityError(f"unknown capability mode: {mode!r}")
    return Capability(mode, modes[mode])


def deployment_mode(capabilities: dict | None = None) -> str:
    capabilities = capabilities or load()
    return capabilities["deployment_mode"]


def degrade(mode: str) -> str:
    """Return the next mode down. Degradation never reverses."""
    if mode not in DEGRADATION_ORDER:
        raise CapabilityError(f"{mode!r} is not part of the degradation ladder")
    index = DEGRADATION_ORDER.index(mode)
    return DEGRADATION_ORDER[min(index + 1, len(DEGRADATION_ORDER) - 1)]


def reachable_modes(capabilities: dict | None = None) -> frozenset[str]:
    capabilities = capabilities or load()
    return frozenset(
        name for name, row in capabilities["modes"].items() if row.get("reachable")
    )


def assert_writes_impossible(capabilities: dict | None = None) -> None:
    """No reachable mode may declare a write.

    A guard against reintroducing a write path by editing the data file. If this
    ever fires, either the environment genuinely gained write access — in which
    case the state design must be revisited deliberately — or someone widened a
    capability without meaning to.
    """
    capabilities = capabilities or load()
    for name, row in capabilities["modes"].items():
        if row.get("reachable") and "write" in row.get("operations", ()):
            raise CapabilityError(
                f"{name} is reachable and declares a write; the HOST_READ_ONLY "
                "architecture assumes no writable location exists"
            )
