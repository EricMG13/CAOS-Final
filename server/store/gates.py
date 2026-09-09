"""Digest-bound interrupts: what a person approves, and what that binds.

Invariant 5. An approval binds the exact reviewed content, and a single-actor
release is a store CAS transaction rather than an interrupt the engine parks
inside. A node waiting on one is `BLOCKED` on a host predicate --
`gate_released` -- not on a special engine state (`docs/SYSTEM_SPEC.md` §4).

Two digests, because one is not enough. `preview_sha256` is the bytes a person
read. `input_fingerprint` is what those bytes were rendered from, so content
that happens to render identically over different inputs -- a withdrawn source
that contributed no visible line, an ordering the renderer normalises away -- is
still different content and is still refused.

The gate itself is re-openable while undecided: the content underneath it moves,
and saying so is the point. What never moves is a decision, so the release lives
in its own append-only ledger whose primary key is the CAS.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from server.boundary_text import BoundaryText
from server.digests import checked_digest
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.events import EventKind, emit, lock_run


class GateKind(StrEnum):
    """The interrupts `docs/REBUILD_PLAN.md` Phase 6 names, and no others."""

    SOURCE_SET = "SOURCE_SET"
    RESEARCH_PLAN = "RESEARCH_PLAN"


@dataclass(frozen=True, slots=True)
class Gate:
    """One interrupt, named by the content it asks about."""

    run_id: str
    kind: GateKind
    preview_sha256: str
    input_fingerprint: str


def open_gate(store: Store, gate: Gate) -> bool:
    """Park the run on this gate. True when the gate moved, False on a replay.

    Re-opening on new content is ordinary: the source set was re-pinned, the
    plan was re-derived. Re-opening a gate a person has already released is not,
    because the asked content and the released content would then disagree with
    only the approval row saying which was reviewed.
    """
    content = _content(gate)
    with store.transaction():
        lock_run(store, run_id=gate.run_id)
        released = _released_content(store, gate)
        if released is not None:
            if released == content:
                return False
            raise Refusal(RefusalCode.GATE_ALREADY_DECIDED)
        moved = store.execute(
            "INSERT INTO run_gates (run_id, kind, preview_sha256, input_fingerprint)"
            " VALUES (%s, %s, %s, %s)"
            " ON CONFLICT (run_id, kind) DO UPDATE"
            "    SET preview_sha256 = EXCLUDED.preview_sha256,"
            "        input_fingerprint = EXCLUDED.input_fingerprint,"
            "        opened_at = now()"
            "  WHERE (run_gates.preview_sha256, run_gates.input_fingerprint)"
            "     IS DISTINCT FROM"
            "        (EXCLUDED.preview_sha256, EXCLUDED.input_fingerprint)",
            (gate.run_id, gate.kind.value, *content),
        )
        if moved.rowcount == 0:
            # The gate already holds exactly this content. The run is known --
            # `lock_run` refused it otherwise -- so there is nothing else a
            # skipped write can mean, and a replay must not emit a second event.
            return False
        emit(store, run_id=gate.run_id, kind=EventKind.GATE_OPENED)
    return True


def approve_gate(store: Store, gate: Gate, *, approver: BoundaryText) -> bool:
    """Release the gate against the content the approver reviewed.

    True on the release, False on a replay of it. The insert selects the gate
    row only while it still holds exactly the reviewed digests, so zero rows
    written means no release and no event -- the conditional write
    `docs/SYSTEM_SPEC.md` §2 accepts as proof of the pairing. The primary key is
    what makes it once: a second release finds the row already there.
    """
    content = _content(gate)
    with store.transaction():
        lock_run(store, run_id=gate.run_id)
        released = store.execute(
            "INSERT INTO run_gate_approvals"
            " (run_id, kind, preview_sha256, input_fingerprint, approved_by)"
            " SELECT run_id, kind, preview_sha256, input_fingerprint, %s"
            "   FROM run_gates"
            "  WHERE run_id = %s AND kind = %s"
            "    AND preview_sha256 = %s AND input_fingerprint = %s"
            " ON CONFLICT (run_id, kind) DO NOTHING",
            (approver.value, gate.run_id, gate.kind.value, *content),
        )
        if released.rowcount == 0:
            return _replayed(store, gate, content)
        emit(store, run_id=gate.run_id, kind=EventKind.GATE_APPROVED)
    return True


def gate_released(store: Store, *, run_id: str, kind: GateKind) -> bool:
    """The host predicate a parked node is `BLOCKED` on until it holds."""
    found = store.execute(
        "SELECT 1 FROM run_gate_approvals WHERE run_id = %s AND kind = %s",
        (run_id, kind.value),
    ).fetchone()
    return found is not None


def _replayed(store: Store, gate: Gate, content: tuple[str, str]) -> bool:
    """Why nothing was written: a replay, a gate that moved, or no gate at all.

    Only a refused release pays for these reads, and each answer is a different
    thing to tell a person: their decision already stands, what they read is no
    longer what would execute, or there is nothing to approve.
    """
    released = _released_content(store, gate)
    if released is not None:
        if released == content:
            return False
        raise Refusal(RefusalCode.APPROVAL_CONTENT_CHANGED)
    if _open_content(store, gate) is None:
        raise Refusal(RefusalCode.GATE_NOT_OPEN)
    raise Refusal(RefusalCode.APPROVAL_CONTENT_CHANGED)


def _content(gate: Gate) -> tuple[str, str]:
    """The two digests an approval binds, checked before either is used."""
    return checked_digest(gate.preview_sha256), checked_digest(gate.input_fingerprint)


def _open_content(store: Store, gate: Gate) -> tuple[str, str] | None:
    found = store.execute(
        "SELECT preview_sha256, input_fingerprint FROM run_gates"
        " WHERE run_id = %s AND kind = %s",
        (gate.run_id, gate.kind.value),
    ).fetchone()
    return (str(found[0]), str(found[1])) if found is not None else None


def _released_content(store: Store, gate: Gate) -> tuple[str, str] | None:
    found = store.execute(
        "SELECT preview_sha256, input_fingerprint FROM run_gate_approvals"
        " WHERE run_id = %s AND kind = %s",
        (gate.run_id, gate.kind.value),
    ).fetchone()
    return (str(found[0]), str(found[1])) if found is not None else None
