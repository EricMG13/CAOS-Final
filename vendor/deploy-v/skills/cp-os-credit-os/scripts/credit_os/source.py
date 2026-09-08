"""Read-only artifact source over a connector-resolved folder.

Replaces `safe_io`. There is no filesystem here: the connector mediates every
access and CREDIT OS constructs no paths, which removes symlinks, hardlinks,
special files, traversal and path-swap races from the threat model entirely.

What replaces them is size-before-bytes and a stability window. Rejecting a file
on its listed size before requesting content is strictly better than the local
design, which had to begin reading to discover how large something was.

The host supplies two callables — one to list, one to read. Nothing here knows
what a OneDrive connector is, which is also what makes it testable.

Standard library only, no repository imports.
"""

from __future__ import annotations

import hashlib
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Iterable

from .capability import Capability
from .limits import Budget, BudgetExceeded  # noqa: F401  (re-exported for callers)

# Names that cannot be an artifact we issued, whatever else they are.
_UNSAFE_NAME_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Cn"})


class SourceError(Exception):
    """A listing or read failed, or returned something unusable."""


class Unstable(SourceError):
    """The entry changed across the stability window."""


@dataclass(frozen=True)
class Entry:
    """One listed item. `token` is the connector's version marker if it has one."""

    name: str
    size: int
    token: str | None = None
    handle: object = None  # opaque connector reference; never a path we build

    def identity(self) -> tuple:
        return (self.name, self.size, self.token)


@dataclass
class ReadResult:
    data: bytes
    entry: Entry
    sha256: str


@dataclass
class Listing:
    entries: list[Entry] = field(default_factory=list)
    rejected: list[tuple[str, str]] = field(default_factory=list)

    def names(self) -> list[str]:
        return [e.name for e in self.entries]


def _reject_name(name: str) -> str | None:
    if not name or name in (".", ".."):
        return "empty or dot name"
    if "/" in name or "\\" in name:
        return "separator in a listed name"
    if any(unicodedata.category(ch) in _UNSAFE_NAME_CATEGORIES for ch in name):
        return "control or bidirectional character in name"
    if name != unicodedata.normalize("NFC", name):
        return "name is not NFC-normalised"
    if len(name) > 255:
        return "name exceeds 255 characters"
    return None


class ReadOnlySource:
    """A folder CREDIT OS can list and read, and can never write.

    `lister` returns an iterable of `Entry`. `reader` takes an `Entry` and a byte
    ceiling and returns at most that many bytes. Both are supplied by the host.
    """

    def __init__(
        self,
        *,
        capability: Capability,
        lister: Callable[[], Iterable[Entry]],
        reader: Callable[[Entry, int], bytes],
        limits: dict,
        budget: Budget | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        capability.require("list")
        capability.require("read")
        self.capability = capability
        self._lister = lister
        self._reader = reader
        self.limits = limits
        self.budget = budget or Budget.from_limits(limits)
        self._sleep = sleep

    # -- listing ------------------------------------------------------------

    def list(self) -> Listing:
        """List the folder, rejecting unusable names before anything is read."""
        listing = Listing()
        try:
            raw = list(self._lister())
        except Exception as exc:  # connector failures are data, not crashes
            raise SourceError(f"listing failed: {exc}") from exc

        seen: dict[str, str] = {}
        for entry in raw:
            self.budget.charge_entry(entry.name)
            reason = _reject_name(entry.name)
            if reason:
                listing.rejected.append((entry.name, reason))
                continue
            # Case-folded collision: on a case-insensitive store these are one
            # file, and silently taking the last one loses evidence.
            key = entry.name.casefold()
            if key in seen:
                listing.rejected.append(
                    (entry.name, f"case-folded duplicate of {seen[key]!r}")
                )
                continue
            seen[key] = entry.name
            listing.entries.append(entry)
        return listing

    # -- reading ------------------------------------------------------------

    def _ceiling_for(self, name: str) -> int:
        lowered = name.lower()
        if lowered.endswith(".xlsx"):
            return self.limits["xlsx_outer_file_bytes"]
        if lowered.endswith(".zip"):
            return self.limits["zip_outer_file_bytes"]
        return self.limits["markdown_or_control_file_bytes"]

    def read(self, entry: Entry) -> ReadResult:
        """Read one entry, checking its listed size before requesting bytes."""
        ceiling = self._ceiling_for(entry.name)
        if entry.size > ceiling:
            raise SourceError(
                f"{entry.name}: listed size {entry.size} exceeds its {ceiling}-byte "
                "ceiling; refused without fetching"
            )
        self.budget.charge_bytes(entry.size)
        try:
            data = self._reader(entry, ceiling + 1)
        except Exception as exc:
            raise SourceError(f"{entry.name}: read failed: {exc}") from exc

        if len(data) > ceiling:
            raise SourceError(
                f"{entry.name}: returned more than its {ceiling}-byte ceiling"
            )
        if len(data) != entry.size:
            # The listing and the content disagree — the file changed, or the
            # connector is lying. Either way it is not a stable read.
            raise Unstable(
                f"{entry.name}: listed {entry.size} bytes, read {len(data)}"
            )
        return ReadResult(data=data, entry=entry, sha256=hashlib.sha256(data).hexdigest())

    def read_text(self, entry: Entry) -> str:
        """Decode strictly. A decode failure is a rejection, not a repair."""
        result = self.read(entry)
        try:
            return result.data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SourceError(f"{entry.name}: not valid UTF-8") from exc

    # -- stability ----------------------------------------------------------

    def stable_set(self, entries: list[Entry]) -> tuple[list[Entry], list[Entry]]:
        """Split entries into (stable, unstable) using one global settle window.

        Pass A takes the identity of every candidate, one shared wait follows,
        then pass B re-lists and compares. A per-entry wait would need
        `entries * settle` seconds inside a refresh ceiling that is far smaller —
        for a full folder that is several minutes against a one-minute budget, so
        a run could never be refreshed at all.

        Where the connector exposes a version token the comparison uses it. Where
        it does not, size and name are all that is available from a listing, so
        callers requiring certainty must compare content digests across two reads
        and charge both.
        """
        before = {e.name: e.identity() for e in entries}
        self._sleep(float(self.limits["stability_settle_seconds"]))
        self.budget.check_time()

        after = {e.name: e.identity() for e in self.list().entries}
        stable, unstable = [], []
        for entry in entries:
            if after.get(entry.name) == before[entry.name]:
                stable.append(entry)
            else:
                unstable.append(entry)
        return stable, unstable

    def read_stable(self, entry: Entry) -> ReadResult:
        """Read an entry twice and require identical content.

        Used where the connector exposes no version token. Both reads are charged
        to the budget — a stability guarantee that costs nothing is not one.
        """
        first = self.read(entry)
        if entry.token is not None:
            return first
        second = self.read(entry)
        if first.sha256 != second.sha256:
            raise Unstable(f"{entry.name}: content changed between two reads")
        return second
