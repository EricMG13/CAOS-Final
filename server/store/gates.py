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

Authority is checked here too, because here is where the decision commits
(`docs/SYSTEM_SPEC.md` §8). A request can check standing when it arrives; only
the releasing transaction can check it at the moment the release is written,
and between the two a membership can be revoked.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from server.boundary_text import BoundaryText
from server.digests import checked_digest
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.events import EventKind, emit, lock_run
from server.store.members import Standing, require_standing

# The standings that may clear an interrupt. A reader or a writer is shown the
# plan and does not decide it.
_MAY_RELEASE = frozenset({Standing.APPROVER, Standing.ADMIN})


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

    A replay is answered before the run's state is read. Recovery replays every
    gate, and a run that has since left RUNNING still holds the ask it was
    parked on; only a *new* ask needs a RUNNING run. Everything is read under
    the run row lock, so an ask that differs from the one held is written
    without a second look.
    """
    content = _content(gate)
    with store.transaction():
        _, state = lock_run(store, run_id=gate.run_id)
        released = _released_content(store, gate)
        if released is not None:
            if released == content:
                return False
            raise Refusal(RefusalCode.GATE_ALREADY_DECIDED)
        if _asked_content(store, gate) == content:
            return False
        _require_running(state)
        store.execute(
            "INSERT INTO run_gates (run_id, kind, preview_sha256, input_fingerprint)"
            " VALUES (%s, %s, %s, %s)"
            " ON CONFLICT (run_id, kind) DO UPDATE"
            "    SET preview_sha256 = EXCLUDED.preview_sha256,"
            "        input_fingerprint = EXCLUDED.input_fingerprint,"
            "        opened_at = now()",
            (gate.run_id, gate.kind.value, *content),
        )
        emit(store, run_id=gate.run_id, kind=EventKind.GATE_OPENED)
    return True


def approve_gate(store: Store, gate: Gate, *, approver: BoundaryText) -> bool:
    """Release the gate against the content the approver reviewed.

    True on the release, False on a replay of it. Everything is read under the
    run row lock, in this order, and the order is the point:

    A release that already stands, on exactly this content, is reported before
    anything is checked. Recovery replays the identical call, and the approver
    may have lost their standing since -- what revocation takes away is the
    next decision, not the one that committed.

    Then the approver's standing on the run's case, held `FOR SHARE` so a
    revocation waits for this transaction rather than landing inside it. Every
    other refusal comes after it -- a release on other content, a run that has
    left RUNNING, a gate that moved or was never opened -- so what an outsider
    learns from any call but the exact replay is the one thing: they have no
    standing here.

    Then the insert, which selects the gate row only while it still holds
    exactly the reviewed digests, so zero rows written means no release and no
    event -- the conditional write `docs/SYSTEM_SPEC.md` §2 accepts as proof
    of the pairing. The lock is what makes the release once; the primary key
    is the store's own word for it, kept so a second row can never be written.
    """
    content = _content(gate)
    with store.transaction():
        case_id, state = lock_run(store, run_id=gate.run_id)
        released = _released_content(store, gate)
        if released == content:
            return False
        require_standing(
            store, case_id=case_id, member_id=approver, allowed=_MAY_RELEASE
        )
        if released is not None:
            raise Refusal(RefusalCode.APPROVAL_CONTENT_CHANGED)
        _require_running(state)
        written = store.execute(
            "INSERT INTO run_gate_approvals"
            " (run_id, kind, preview_sha256, input_fingerprint, approved_by)"
            " SELECT run_id, kind, preview_sha256, input_fingerprint, %s"
            "   FROM run_gates"
            "  WHERE run_id = %s AND kind = %s"
            "    AND preview_sha256 = %s AND input_fingerprint = %s"
            " ON CONFLICT (run_id, kind) DO NOTHING",
            (approver.value, gate.run_id, gate.kind.value, *content),
        )
        if written.rowcount == 0:
            # Only a refused release pays for the read that tells the two apart.
            if _asked_content(store, gate) is None:
                raise Refusal(RefusalCode.GATE_NOT_OPEN)
            raise Refusal(RefusalCode.APPROVAL_CONTENT_CHANGED)
        emit(store, run_id=gate.run_id, kind=EventKind.GATE_APPROVED)
    return True


def gate_released(store: Store, *, run_id: str, kind: GateKind) -> bool:
    """The host predicate a parked node is `BLOCKED` on until it holds."""
    found = store.execute(
        "SELECT 1 FROM run_gate_approvals WHERE run_id = %s AND kind = %s",
        (run_id, kind.value),
    ).fetchone()
    return found is not None


def _require_running(state: str) -> None:
    """A run that has left RUNNING has no decision left to take."""
    if state != "RUNNING":
        raise Refusal(RefusalCode.RUN_NOT_RUNNING)


def _content(gate: Gate) -> tuple[str, str]:
    """The two digests an approval binds, checked before either is used."""
    return checked_digest(gate.preview_sha256), checked_digest(gate.input_fingerprint)


def _asked_content(store: Store, gate: Gate) -> tuple[str, str] | None:
    """What the gate currently asks a person to approve; None if never opened."""
    found = store.execute(
        "SELECT preview_sha256, input_fingerprint FROM run_gates"
        " WHERE run_id = %s AND kind = %s",
        (gate.run_id, gate.kind.value),
    ).fetchone()
    return (str(found[0]), str(found[1])) if found is not None else None


def released_gate(store: Store, *, run_id: str, kind: GateKind) -> Gate | None:
    """The gate as it was released, or None while it is undecided.

    A decision replays as itself. A caller re-deriving a gate's content after
    the release -- recovery replaying a plan gate over a set that has since
    lost a source -- asks for this first, so what it replays is the decision a
    person made rather than a content the store would rightly refuse to move.
    """
    found = store.execute(
        "SELECT preview_sha256, input_fingerprint FROM run_gate_approvals"
        " WHERE run_id = %s AND kind = %s",
        (run_id, kind.value),
    ).fetchone()
    if found is None:
        return None
    return Gate(run_id, kind, str(found[0]), str(found[1]))


def _released_content(store: Store, gate: Gate) -> tuple[str, str] | None:
    released = released_gate(store, run_id=gate.run_id, kind=gate.kind)
    if released is None:
        return None
    return released.preview_sha256, released.input_fingerprint
