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


def reserve(store: Store, *, run_id: str, route_node_id: str, amount: Decimal) -> str:
    """Reserve budget for one try and return its attempt id.

    The run row lock makes the ceiling real: two callers cannot both read the
    same remaining budget and both fit inside it.
    """
    attempt_id = str(uuid.uuid4())
    with store.transaction():
        run = store.execute(
            "SELECT ceiling FROM runs WHERE run_id = %s FOR UPDATE", (run_id,)
        ).fetchone()
        if run is None:
            raise Refusal(RefusalCode.RUN_NOT_FOUND)
        taken = store.execute(
            "SELECT coalesce(sum(reserved), 0) FROM run_attempts WHERE run_id = %s",
            (run_id,),
        ).fetchone()
        if taken is None or Decimal(taken[0]) + amount > Decimal(run[0]):
            raise Refusal(RefusalCode.BUDGET_CEILING_EXCEEDED)
        store.execute(
            "INSERT INTO run_attempts (attempt_id, run_id, route_node_id, reserved)"
            " VALUES (%s, %s, %s, %s)",
            (attempt_id, run_id, route_node_id, amount),
        )
    return attempt_id


def reserved_total(store: Store, *, run_id: str) -> Decimal:
    """Everything reserved for this run, indeterminate attempts included."""
    found = store.execute(
        "SELECT coalesce(sum(reserved), 0) FROM run_attempts WHERE run_id = %s",
        (run_id,),
    ).fetchone()
    return Decimal(found[0]) if found else Decimal(0)


def accept(
    store: Store,
    *,
    run_id: str,
    node_id: BoundaryText,
    artifact_sha256: str,
    charge: Decimal,
) -> None:
    """Record the artifact and its charge. This is what makes an attempt accepted."""
    with store.transaction():
        store.execute(
            "INSERT INTO artifacts (run_id, node_id, sha256) VALUES (%s, %s, %s)",
            (run_id, node_id.value, checked_digest(artifact_sha256)),
        )
        store.execute(
            "INSERT INTO budget_ledger (run_id, node_id, amount) VALUES (%s, %s, %s)",
            (run_id, node_id.value, charge),
        )
