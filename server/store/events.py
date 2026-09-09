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

from enum import StrEnum

from server.refusals import Refusal, RefusalCode
from server.store import Store


class EventKind(StrEnum):
    """The closed set of transitions a run's stream carries."""

    ROUTE_PINNED = "ROUTE_PINNED"
    GATE_OPENED = "GATE_OPENED"
    GATE_APPROVED = "GATE_APPROVED"
    RUN_COMPLETED = "RUN_COMPLETED"


def lock_run(store: Store, *, run_id: str) -> None:
    """Take the run row lock, the serialisation point for everything about a run.

    Wants an open transaction, and that is the whole point: the lock is released
    when the transaction ends, so a caller that takes it outside one holds
    nothing. An unknown run is refused here rather than by a foreign key, so no
    constraint name reaches a caller.
    """
    locked = store.execute(
        "SELECT 1 FROM runs WHERE run_id = %s FOR UPDATE", (run_id,)
    ).fetchone()
    if locked is None:
        raise Refusal(RefusalCode.RUN_NOT_FOUND)


def emit(
    store: Store, *, run_id: str, kind: EventKind, route_digest: str | None = None
) -> int:
    """Append one event to a run's stream and return the seq it was given.

    Called from inside the transaction that commits the transition it records,
    so that state and event commit together or not at all.
    """
    lock_run(store, run_id=run_id)
    allocated = store.execute(
        "INSERT INTO run_events (run_id, seq, kind, route_digest)"
        " SELECT %s, coalesce(max(seq), 0) + 1, %s, %s"
        " FROM run_events WHERE run_id = %s RETURNING seq",
        (run_id, kind.value, route_digest, run_id),
    ).fetchone()
    if allocated is None:  # pragma: no cover - RETURNING always yields a row
        raise Refusal(RefusalCode.RUN_NOT_FOUND)
    return int(allocated[0])
