"""The attempt ledger: one row per try, reserved before the provider is called.

`docs/DECISIONS.md` §21. The row is committed *before* the call, so it is the
durable identity of that call: a crash in the gap leaves the reservation behind
rather than losing it. `run_attempts` is append-only, so there is no state to
transition -- acceptance is the artifact row, and an attempt without one is
indeterminate by construction.

Unknown usage keeps its reserved exposure. Releasing it would let a crash turn a
real charge into free budget, which is the direction that overspends.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from server.boundary_text import BoundaryText
from server.digests import checked_digest
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.events import lock_run


def reserve(
    store: Store, *, run_id: str, route_node_id: BoundaryText, amount: Decimal
) -> str:
    """Reserve budget for one try and return its attempt id.

    The run row lock makes the ceiling real: two callers cannot both read the
    same remaining budget and both fit inside it. It makes the *state* real for
    the same reason -- a run that has left RUNNING has no next operation to
    fund, and `lock_run` refuses it before the ceiling is read. Refusing here
    is what keeps a charge from being accepted against a run nothing can
    account it to.
    """
    attempt_id = str(uuid.uuid4())
    with store.transaction():
        run = lock_run(store, run_id=run_id)
        [(taken,)] = store.execute(
            "SELECT coalesce(sum(reserved), 0) FROM run_attempts WHERE run_id = %s",
            (run_id,),
        )
        if Decimal(taken) + amount > run.ceiling:
            raise Refusal(RefusalCode.BUDGET_CEILING_EXCEEDED)
        store.execute(
            "INSERT INTO run_attempts (attempt_id, run_id, route_node_id, reserved)"
            " VALUES (%s, %s, %s, %s)",
            (attempt_id, run_id, route_node_id.value, amount),
        )
    return attempt_id


def reserved_total(store: Store, *, run_id: str) -> Decimal:
    """Everything reserved for this run, indeterminate attempts included."""
    [(found,)] = store.execute(
        "SELECT coalesce(sum(reserved), 0) FROM run_attempts WHERE run_id = %s",
        (run_id,),
    )
    return Decimal(found)


def accept(
    store: Store,
    *,
    run_id: str,
    node_id: BoundaryText,
    artifact_sha256: str,
    charge: Decimal,
) -> None:
    """Record the artifact and its charge. This is what makes an attempt accepted.

    Under the run row lock, so a run that has left RUNNING accepts nothing more
    (invariants 6 and 8): a provider call that outlives the run's terminal
    event has no run left to charge. The `artifacts` primary key is what makes
    this exactly-once: one accepted output per node per run, and the charge
    shares its transaction, so a second acceptance takes neither. The refusal
    is *read* rather than raised -- `ON CONFLICT DO NOTHING` skips instead of
    colliding, which would otherwise escape carrying `artifacts_pkey` and the
    offending key, exactly the leak `server/refusals.py` exists to stop.
    """
    with store.transaction():
        lock_run(store, run_id=run_id)
        accepted = store.execute(
            "INSERT INTO artifacts (run_id, node_id, sha256) VALUES (%s, %s, %s)"
            " ON CONFLICT (run_id, node_id) DO NOTHING",
            (run_id, node_id.value, checked_digest(artifact_sha256)),
        )
        if accepted.rowcount == 0:
            raise Refusal(RefusalCode.NODE_ALREADY_ACCEPTED)
        store.execute(
            "INSERT INTO budget_ledger (run_id, node_id, amount) VALUES (%s, %s, %s)",
            (run_id, node_id.value, charge),
        )
