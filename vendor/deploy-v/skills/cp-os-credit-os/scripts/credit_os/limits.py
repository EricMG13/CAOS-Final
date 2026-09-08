"""Governed ceilings and the cumulative refresh budget.

Extracted from the deleted `safe_io` module. The ceilings are unchanged; only
what they are charged against moved, from filesystem reads to connector
operations.

One budget spans an entire refresh — listing, stability, reads, decode and
parsing. It is never reset between phases. A shared pass may avoid re-reading
bytes, but may not reset the counter to obtain one.

Standard library only, no repository imports.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

LIMITS_FILENAME = "CREDIT_OS_RUNTIME_LIMITS_v1.json"


class BudgetExceeded(Exception):
    """The cumulative refresh budget ran out."""


def _find_limits(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    here = Path(__file__).resolve().parent
    for candidate in (
        here / LIMITS_FILENAME,
        here.parent / "references" / LIMITS_FILENAME,
        here.parent.parent / "references" / LIMITS_FILENAME,
        here.parent.parent / "Co-Pilot Agents" / "CP-OS" / "references" / LIMITS_FILENAME,
    ):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"{LIMITS_FILENAME} not found; the package is incomplete")


def load_limits(path: Path | None = None) -> dict:
    return json.loads(_find_limits(path).read_text(encoding="utf-8"))["limits"]


def settle_seconds(path: Path | None = None) -> float:
    return float(load_limits(path)["stability_settle_seconds"])


@dataclass
class Budget:
    """One cumulative refresh budget."""

    max_bytes: int
    max_entries: int
    max_seconds: float
    _bytes: int = 0
    _entries: int = 0
    _seen: set = field(default_factory=set)
    _started: float | None = None

    @classmethod
    def from_limits(cls, limits: dict | None = None) -> "Budget":
        limits = limits or load_limits()
        return cls(
            max_bytes=limits["bytes_per_refresh"],
            max_entries=limits["entries_per_run_folder"],
            max_seconds=limits["refresh_wall_time_seconds"],
        )

    def start(self) -> None:
        if self._started is None:
            self._started = time.monotonic()

    def charge_bytes(self, count: int) -> None:
        self.start()
        self._bytes += count
        if self._bytes > self.max_bytes:
            raise BudgetExceeded(
                f"refresh byte budget exhausted: {self._bytes} > {self.max_bytes}"
            )
        self.check_time()

    def charge_entry(self, name: str | None = None) -> None:
        """Charge one distinct entry inspected this refresh.

        Deduplicated by name. The ceiling is "entries inspected per run folder",
        not "listing calls": a stability pass re-lists the same folder, and
        charging it twice would make any folder over half the cap impossible to
        refresh at all — the same failure the per-entry settle wait had.
        """
        self.start()
        if name is not None:
            if name in self._seen:
                self.check_time()
                return
            self._seen.add(name)
        self._entries += 1
        if self._entries > self.max_entries:
            raise BudgetExceeded(
                f"refresh entry budget exhausted: {self._entries} > {self.max_entries}"
            )
        self.check_time()

    def check_time(self) -> None:
        self.start()
        assert self._started is not None
        elapsed = time.monotonic() - self._started
        if elapsed > self.max_seconds:
            raise BudgetExceeded(
                f"refresh wall-time budget exhausted: {elapsed:.1f}s > {self.max_seconds}s"
            )

    @property
    def spent_bytes(self) -> int:
        return self._bytes

    @property
    def spent_entries(self) -> int:
        return self._entries
