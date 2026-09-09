"""A human gate binds the exact content that was reviewed (invariant 5).

The hazard is the interval between rendering a preview and approving it. A
source is withdrawn, a plan is re-derived, and the bytes a person read stop
being the bytes that would execute. An approval that names only the run would
commit the new content under the old decision, which is how a governed system
quietly stops being governed.

So an approval carries what was reviewed -- the preview digest and the input
fingerprint -- and the release is a store CAS transaction against those two.
Nothing is written when they no longer match, and no event without the
transition it records (`docs/SYSTEM_SPEC.md` §2).
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.events import EventKind, LockedRun, emit, lock_run, require_running
from server.store.gates import (
    Gate,
    GateKind,
    approve_gate,
    gate_released,
    open_gate,
)
from server.store.members import Standing, grant_membership
from server.store.runs import start_run

REPO = Path(__file__).resolve().parents[1]
CASE = BoundaryText.of("acme")
APPROVER = BoundaryText.of("ana")
PREVIEW = "a" * 64
FINGERPRINT = "b" * 64


def _run(store: Store) -> str:
    """A run on whose case `APPROVER` holds the standing to release a gate."""
    run_id = start_run(store, case_id=CASE)
    grant_membership(
        store,
        case_id=CASE,
        member_id=APPROVER,
        standing=Standing.APPROVER,
        actor=BoundaryText.of("pm"),
    )
    return run_id


def _gate(run_id: str) -> Gate:
    return Gate(
        run_id=run_id,
        kind=GateKind.SOURCE_SET,
        preview_sha256=PREVIEW,
        input_fingerprint=FINGERPRINT,
    )


def _events(store: Store, kind: EventKind) -> int:
    row = store.execute(
        "SELECT count(*) FROM run_events WHERE kind = %s", (kind.value,)
    ).fetchone()
    assert row is not None
    return int(row[0])


def test_approval_binds_the_exact_reviewed_content(store: Store) -> None:
    """The phase's exit test: a stale approval is refused, not applied.

    A person reads a preview and approves it. In between, the content underneath
    the gate moves and the host re-opens it. The approval still in flight quotes
    the digests of the preview that was actually read, and committing it would
    bind a human decision to content nobody saw.
    """
    run_id = _run(store)
    reviewed = _gate(run_id)
    assert open_gate(store, reviewed) is True

    restated = replace(reviewed, preview_sha256="c" * 64, input_fingerprint="d" * 64)
    assert open_gate(store, restated) is True

    with pytest.raises(Refusal) as caught:
        approve_gate(store, reviewed, approver=APPROVER)
    assert caught.value.code is RefusalCode.APPROVAL_CONTENT_CHANGED
    assert gate_released(store, run_id=run_id, kind=GateKind.SOURCE_SET) is False
    assert _events(store, EventKind.GATE_APPROVED) == 0

    assert approve_gate(store, restated, approver=APPROVER) is True
    assert gate_released(store, run_id=run_id, kind=GateKind.SOURCE_SET) is True


def test_an_identical_preview_over_different_inputs_is_different_content(
    store: Store,
) -> None:
    # Why the fingerprint is carried at all. Two source sets can render the same
    # preview bytes -- a withdrawn document that contributed no visible line, a
    # reordering the renderer normalises away -- and the approval must still be
    # of the inputs, not of the picture of them.
    run_id = _run(store)
    reviewed = _gate(run_id)
    open_gate(store, reviewed)
    open_gate(store, replace(reviewed, input_fingerprint="e" * 64))

    with pytest.raises(Refusal) as caught:
        approve_gate(store, reviewed, approver=APPROVER)
    assert caught.value.code is RefusalCode.APPROVAL_CONTENT_CHANGED


def test_the_release_is_exactly_once_and_a_replay_says_so(store: Store) -> None:
    # The commit gap again: the release commits, the process dies before the
    # caller learns it did, and recovery replays the identical approval.
    run_id = _run(store)
    gate = _gate(run_id)
    open_gate(store, gate)

    assert approve_gate(store, gate, approver=APPROVER) is True
    assert approve_gate(store, gate, approver=APPROVER) is False

    row = store.execute("SELECT count(*) FROM run_gate_approvals").fetchone()
    assert row is not None and row[0] == 1
    assert _events(store, EventKind.GATE_APPROVED) == 1


def test_a_gate_that_was_never_opened_cannot_be_approved(store: Store) -> None:
    # An approval is of something. Nothing to review is not a release, and it is
    # not a replay either -- False would report a decision that never happened.
    run_id = _run(store)
    with pytest.raises(Refusal) as caught:
        approve_gate(store, _gate(run_id), approver=APPROVER)
    assert caught.value.code is RefusalCode.GATE_NOT_OPEN


def test_a_released_gate_is_not_reopened_on_new_content(store: Store) -> None:
    # The engine must not be able to move an interrupt a person already cleared.
    # Re-opening would leave the released content and the asked content
    # disagreeing, with only the approval row saying which was reviewed.
    run_id = _run(store)
    gate = _gate(run_id)
    open_gate(store, gate)
    approve_gate(store, gate, approver=APPROVER)

    with pytest.raises(Refusal) as caught:
        open_gate(store, replace(gate, preview_sha256="f" * 64))
    assert caught.value.code is RefusalCode.GATE_ALREADY_DECIDED
    assert open_gate(store, gate) is False


def test_reopening_a_gate_on_the_same_content_emits_no_second_event(
    store: Store,
) -> None:
    # Recovery replays the gate. A stream that gains an event per replay is a
    # stream that cannot be resumed from, and SSE resume is what reads it.
    run_id = _run(store)
    gate = _gate(run_id)
    assert open_gate(store, gate) is True
    assert open_gate(store, gate) is False
    assert _events(store, EventKind.GATE_OPENED) == 1


def test_two_gate_kinds_on_one_run_are_separate_interrupts(store: Store) -> None:
    # Source-set pinning and research-plan approval are both digest-bound and
    # neither releases the other.
    run_id = _run(store)
    pinning = _gate(run_id)
    plan = replace(pinning, kind=GateKind.RESEARCH_PLAN, preview_sha256="c" * 64)
    open_gate(store, pinning)
    open_gate(store, plan)

    approve_gate(store, pinning, approver=APPROVER)
    assert gate_released(store, run_id=run_id, kind=GateKind.SOURCE_SET) is True
    assert gate_released(store, run_id=run_id, kind=GateKind.RESEARCH_PLAN) is False


def test_the_approver_is_recorded_with_the_release(store: Store) -> None:
    # Who approved is part of what an approval is, and it reaches pinned state,
    # so it crosses the boundary as BoundaryText and never as a bare str.
    run_id = _run(store)
    gate = _gate(run_id)
    open_gate(store, gate)
    approve_gate(store, gate, approver=APPROVER)

    row = store.execute(
        "SELECT approved_by, preview_sha256, input_fingerprint"
        " FROM run_gate_approvals WHERE run_id = %s",
        (run_id,),
    ).fetchone()
    assert row == (APPROVER.value, PREVIEW, FINGERPRINT)


def test_a_digest_that_is_not_a_digest_never_reaches_the_gate(store: Store) -> None:
    run_id = _run(store)
    with pytest.raises(Refusal) as caught:
        open_gate(store, replace(_gate(run_id), preview_sha256="not-a-digest"))
    assert caught.value.code is RefusalCode.DIGEST_INVALID


def test_an_unknown_run_cannot_open_a_gate(store: Store) -> None:
    # The refusal is the host's typed code, never a foreign key's constraint name.
    with pytest.raises(Refusal) as caught:
        open_gate(store, _gate(str(uuid.uuid4())))
    assert caught.value.code is RefusalCode.RUN_NOT_FOUND


def test_the_approval_ledger_has_no_rewrite_path(store: Store) -> None:
    run_id = _run(store)
    gate = _gate(run_id)
    open_gate(store, gate)
    approve_gate(store, gate, approver=APPROVER)

    with pytest.raises(psycopg.errors.RaiseException):
        store.execute("UPDATE run_gate_approvals SET approved_by = 'bo'")
    store.rollback()
    with pytest.raises(psycopg.errors.RaiseException):
        store.execute("DELETE FROM run_gate_approvals")
    store.rollback()


def test_a_gate_cannot_be_truncated_by_either_route(store: Store) -> None:
    # `run_gates` carries no trigger of its own -- it needs an UPDATE path, and
    # a rewrite guard would refuse the re-open the gate exists to allow. What
    # refuses truncation is the approval ledger: the foreign key blocks the
    # plain form, and the cascade drags in a statement trigger that raises.
    with pytest.raises(psycopg.errors.FeatureNotSupported):
        store.execute("TRUNCATE run_gates")
    store.rollback()

    with pytest.raises(psycopg.errors.RaiseException) as caught:
        store.execute("TRUNCATE run_gates CASCADE")
    assert caught.value.diag.message_primary == "APPEND_ONLY_TABLE"
    store.rollback()


def test_the_emitter_refuses_an_unknown_run(store: Store) -> None:
    with pytest.raises(Refusal) as caught:
        with store.transaction():
            emit(store, run_id=str(uuid.uuid4()), kind=EventKind.GATE_OPENED)
    assert caught.value.code is RefusalCode.RUN_NOT_FOUND


def test_lock_run_reports_the_run_it_holds_and_refuses_one_that_left_running(
    store: Store,
) -> None:
    # The one seam every governed write goes through: what it hands back is
    # read under the lock, and a run that has left RUNNING is refused there
    # unless the caller says it will read the state itself.
    run_id = start_run(store, case_id=CASE, ceiling=Decimal("3"))
    with store.transaction():
        held = lock_run(store, run_id=run_id)
    assert held == LockedRun(run_id, CASE.value, "RUNNING", Decimal("3"))

    store.execute("UPDATE runs SET state = 'FAILED' WHERE run_id = %s", (run_id,))
    with pytest.raises(Refusal) as caught, store.transaction():
        lock_run(store, run_id=run_id)
    assert caught.value.code is RefusalCode.RUN_NOT_RUNNING
    # A caller that answers a replay first reads the state itself, then asks
    # the same question through the same one function before writing.
    with store.transaction():
        failed = lock_run(store, run_id=run_id, running=False)
    assert failed.state == "FAILED"
    with pytest.raises(Refusal) as caught:
        require_running(failed)
    assert caught.value.code is RefusalCode.RUN_NOT_RUNNING
    assert require_running(held) is held


def test_lock_run_refuses_an_unknown_run(store: Store) -> None:
    run_id = _run(store)
    lock_run(store, run_id=run_id)  # the run this test opened: no refusal
    with pytest.raises(Refusal) as caught:
        lock_run(store, run_id=str(uuid.uuid4()))
    assert caught.value.code is RefusalCode.RUN_NOT_FOUND


def test_only_the_emitter_inserts_a_run_event() -> None:
    """`SYSTEM_SPEC.md` §10: every run transition through one emitter.

    A second `INSERT INTO run_events` is a second `seq` allocator, and two
    allocators reading the same `max(seq)` is exactly the collision the run row
    lock exists to prevent.

    Coarse on purpose. Matching the whole statement would miss it split across
    two string literals, so what fails a module is naming the table at all while
    carrying an insert of anything. A module that only reads the stream -- which
    is what the SSE tail will be -- still passes.
    """
    writing = sorted(
        str(path.relative_to(REPO))
        for path in (REPO / "server").rglob("*.py")
        if "run_events" in (source := path.read_text(encoding="utf-8"))
        and "INSERT" in source
    )
    assert writing == ["server/store/events.py"]
