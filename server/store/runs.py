"""Run state and its events, committed together or not at all.

Invariant 6: execution is durable and exactly-once. The mechanism is the run row
lock. A run leaves RUNNING exactly once, so the artifact, the charge and the
terminal event happen once -- including when a crash in the commit gap makes
recovery replay the identical call.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from server.boundary_text import BoundaryText
from server.digests import checked_digest
from server.refusals import Refusal, RefusalCode
from server.store import Store


@dataclass(frozen=True, slots=True)
class TerminalCommit:
    """Everything one terminal delivery writes. Money is Decimal, never float."""

    run_id: str
    node_id: BoundaryText
    artifact_sha256: str
    charge: Decimal


def start_run(
    connection: Store, *, case_id: BoundaryText, ceiling: Decimal = Decimal(0)
) -> str:
    """Open a run in RUNNING and return its id."""
    run_id = str(uuid.uuid4())
    with connection.transaction():
        connection.execute(
            "INSERT INTO cases (case_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (case_id.value,),
        )
        connection.execute(
            "INSERT INTO runs (run_id, case_id, state, ceiling)"
            " VALUES (%s, %s, 'RUNNING', %s)",
            (run_id, case_id.value, ceiling),
        )
    return run_id


def commit_terminal(connection: Store, commit: TerminalCommit) -> bool:
    """Deliver a run's terminal outcome. True on the delivery, False on a replay.

    The run row lock is taken before anything is read or written, so exactly one
    caller can see RUNNING: a replay finds COMPLETE and writes no artifact, no
    charge and no event. The lock is also what makes `max(seq) + 1` safe, since
    two callers cannot read the same sequence.

    False means "this delivery already happened", so only a COMPLETE run may
    answer it. A run that does not exist, and one that failed, are refused --
    either would otherwise discard a terminal outcome by looking like a replay.
    """
    with connection.transaction():
        # Held for the rest of the transaction, so this state is authoritative:
        # a concurrent deliverer has already committed COMPLETE by the time the
        # lock is granted, and this read sees that version, not a stale one.
        locked = connection.execute(
            "SELECT state FROM runs WHERE run_id = %s FOR UPDATE", (commit.run_id,)
        ).fetchone()
        if locked is None:
            raise Refusal(RefusalCode.RUN_NOT_FOUND)
        state = locked[0]
        if state == "COMPLETE":
            return False
        if state != "RUNNING":
            raise Refusal(RefusalCode.RUN_NOT_RUNNING)

        connection.execute(
            "UPDATE runs SET state = 'COMPLETE' WHERE run_id = %s", (commit.run_id,)
        )
        connection.execute(
            "INSERT INTO artifacts (run_id, node_id, sha256) VALUES (%s, %s, %s)",
            (
                commit.run_id,
                commit.node_id.value,
                checked_digest(commit.artifact_sha256),
            ),
        )
        connection.execute(
            "INSERT INTO budget_ledger (run_id, node_id, amount) VALUES (%s, %s, %s)",
            (commit.run_id, commit.node_id.value, commit.charge),
        )
        connection.execute(
            "INSERT INTO run_events (run_id, seq, kind)"
            " SELECT %s, coalesce(max(seq), 0) + 1, 'RUN_COMPLETED'"
            " FROM run_events WHERE run_id = %s",
            (commit.run_id, commit.run_id),
        )
    return True
