"""Every run event, allocated through one emitter under the run row lock.

`run_events.seq` is per-run monotonic and allocated as `max(seq) + 1`, which is
safe only while no two allocators can read the same maximum. Two paths used to
get that by accident rather than by design: `commit_terminal` holds the run row
`FOR UPDATE` for its own reasons, and `pin_route` is serialised against itself
by `run_routes_pkey`. Two concurrent inserts from any third path read the same
maximum and collided on `run_events_pkey` -- a vendor constraint name escaping a
governed write, and the first gate event would have been that third path.

So the lock is taken here. The guarantee belongs to the emitter rather than to
whatever the caller happened to be holding, which is also what
`docs/SYSTEM_SPEC.md` §10 asks for: run and node transitions, all of them
through one emitter.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from server.refusals import Refusal, RefusalCode
from server.store import Store


class EventKind(StrEnum):
    """The closed set of transitions a run's stream carries."""

    ROUTE_PINNED = "ROUTE_PINNED"
    GATE_OPENED = "GATE_OPENED"
    GATE_APPROVED = "GATE_APPROVED"
    RUN_COMPLETED = "RUN_COMPLETED"


@dataclass(frozen=True, slots=True)
class LockedRun:
    """A run row held `FOR UPDATE` until the transaction ends.

    Read under the lock, so every field is authoritative for the rest of the
    transaction: a caller deciding on them is deciding on what the run is, not
    on what it was a moment ago.
    """

    run_id: str
    case_id: str
    state: str
    ceiling: Decimal


def lock_run(store: Store, *, run_id: str, running: bool = True) -> LockedRun:
    """Take the run row lock, the one seam every governed write goes through.

    Wants an open transaction, and that is the whole point: the lock is released
    when the transaction ends, so a caller that takes it outside one holds
    nothing. An unknown run is refused here rather than by a foreign key, so no
    constraint name reaches a caller.

    A run that has left RUNNING is refused too, by default: it has no next
    operation to fund, accept, pin or emit for, and four writes that each
    re-derived that were joined by two that forgot it. A caller that must
    answer a replay first -- a terminal delivery, a gate's release, a pin, each
    of which recovery may replay after the run has ended -- passes
    `running=False`, reads what stands, and calls `require_running` before
    writing anything new. `emit` passes it too: a terminal event is emitted
    after the run has left RUNNING, in the same transaction.
    """
    locked = store.execute(
        "SELECT case_id, state, ceiling FROM runs WHERE run_id = %s FOR UPDATE",
        (run_id,),
    ).fetchone()
    if locked is None:
        raise Refusal(RefusalCode.RUN_NOT_FOUND)
    run = LockedRun(run_id, str(locked[0]), str(locked[1]), Decimal(locked[2]))
    return require_running(run) if running else run


def require_running(run: LockedRun) -> LockedRun:
    """Refuse a run that has left RUNNING: it has no next operation to take."""
    if run.state != "RUNNING":
        raise Refusal(RefusalCode.RUN_NOT_RUNNING)
    return run


def emit(
    store: Store, *, run_id: str, kind: EventKind, route_digest: str | None = None
) -> int:
    """Append one event to a run's stream and return the seq it was given.

    Called from inside the transaction that commits the transition it records,
    so that state and event commit together or not at all. The lock is taken
    without the state check: a terminal event is emitted after the run has
    left RUNNING, in the same transaction.
    """
    lock_run(store, run_id=run_id, running=False)
    allocated = store.execute(
        "INSERT INTO run_events (run_id, seq, kind, route_digest)"
        " SELECT %s, coalesce(max(seq), 0) + 1, %s, %s"
        " FROM run_events WHERE run_id = %s RETURNING seq",
        (run_id, kind.value, route_digest, run_id),
    ).fetchone()
    if allocated is None:  # pragma: no cover - RETURNING always yields a row
        raise Refusal(RefusalCode.RUN_NOT_FOUND)
    return int(allocated[0])
