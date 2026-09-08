"""Terminal delivery is exactly once, across a crash in the commit gap.

Invariant 6 (CLAUDE.md): execution is durable and exactly-once. A crash in the
commit gap yields one artifact, one charge, one terminal event.

The gap is the window between the transaction committing and the caller learning
that it did. The process dies there; recovery replays the identical call. What
makes the replay harmless is the run row lock: the replay reads the state under
`SELECT ... FOR UPDATE`, finds COMPLETE rather than RUNNING, and returns before
any event, artifact or charge is written.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from decimal import Decimal

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.runs import TerminalCommit, commit_terminal, start_run

CASE = BoundaryText.of("acme")
NODE = BoundaryText.of("CP-1")
ARTIFACT = "b" * 64


def _scalar(store: Store, sql: str, *args: object) -> object:
    """One value from one row. A query that returned nothing is a test bug."""
    row = store.execute(sql, args or None).fetchone()
    assert row is not None, sql
    return row[0]


def _counts(store: Store) -> tuple[object, object, object]:
    return (
        _scalar(store, "SELECT count(*) FROM artifacts"),
        _scalar(store, "SELECT count(*) FROM budget_ledger"),
        _scalar(store, "SELECT count(*) FROM run_events WHERE kind = 'RUN_COMPLETED'"),
    )


def _state(store: Store, run_id: str) -> object:
    return _scalar(store, "SELECT state FROM runs WHERE run_id = %s", run_id)


def _terminal(run_id: str) -> TerminalCommit:
    return TerminalCommit(
        run_id=run_id,
        node_id=NODE,
        artifact_sha256=ARTIFACT,
        charge=Decimal("0.42"),
    )


def test_terminal_event_is_exactly_once(store: Store) -> None:
    run_id = start_run(store, case_id=CASE)
    commit = _terminal(run_id)

    assert commit_terminal(store, commit) is True
    # The process dies here, before the caller records that it succeeded.
    # Recovery replays the identical call.
    assert commit_terminal(store, commit) is False

    assert _counts(store) == (1, 1, 1)


def test_a_refused_charge_leaves_the_run_runnable(store: Store) -> None:
    # State and event commit together or not at all. A charge the ledger refuses
    # must take the artifact, the event and the state change down with it.
    run_id = start_run(store, case_id=CASE)
    with pytest.raises(psycopg.errors.CheckViolation):
        commit_terminal(store, replace(_terminal(run_id), charge=Decimal("-1")))
    store.rollback()

    assert _counts(store) == (0, 0, 0)
    assert _state(store, run_id) == "RUNNING"
    assert commit_terminal(store, _terminal(run_id)) is True
    assert _counts(store) == (1, 1, 1)


def test_run_events_has_no_update_path(store: Store) -> None:
    run_id = start_run(store, case_id=CASE)
    commit_terminal(store, _terminal(run_id))
    with pytest.raises(psycopg.errors.RaiseException):
        store.execute("UPDATE run_events SET kind = 'RUN_FAILED'")
    store.rollback()
    with pytest.raises(psycopg.errors.RaiseException):
        store.execute("DELETE FROM run_events")


def test_run_event_seq_is_per_run_and_monotonic(store: Store) -> None:
    first = start_run(store, case_id=CASE)
    second = start_run(store, case_id=CASE)
    commit_terminal(store, _terminal(first))
    commit_terminal(store, replace(_terminal(second), artifact_sha256="c" * 64))

    rows = store.execute(
        "SELECT run_id, seq FROM run_events ORDER BY run_id, seq"
    ).fetchall()
    by_run: dict[str, list[int]] = {}
    for run_id, seq in rows:
        by_run.setdefault(str(run_id), []).append(seq)
    assert all(seqs == list(range(1, len(seqs) + 1)) for seqs in by_run.values())
    assert len(by_run) == 2


def test_an_unknown_run_is_refused_not_reported_as_a_replay(store: Store) -> None:
    # False means "already delivered". A run that never existed must not be able
    # to say that -- a stale or mistyped id would read as success and be dropped.
    with pytest.raises(Refusal) as caught:
        commit_terminal(store, _terminal(str(uuid.uuid4())))
    assert caught.value.code is RefusalCode.RUN_NOT_FOUND


def test_two_runs_with_identical_output_each_record_an_artifact(
    store: Store,
) -> None:
    # A deterministic module run twice produces the same digest. The blob store
    # is what deduplicates bytes; the artifact row is one run's accepted output,
    # so charging a run whose artifact went missing must not be possible.
    first = start_run(store, case_id=CASE)
    second = start_run(store, case_id=CASE)
    commit_terminal(store, _terminal(first))
    commit_terminal(store, _terminal(second))

    recorded = store.execute(
        "SELECT run_id FROM artifacts WHERE sha256 = %s", (ARTIFACT,)
    ).fetchall()
    assert {str(run_id) for (run_id,) in recorded} == {first, second}
    assert _counts(store) == (2, 2, 2)


def test_a_failed_run_is_not_reported_as_a_replay(store: Store) -> None:
    # False means "this delivery already happened". A FAILED run never delivered,
    # so answering False would quietly discard a terminal outcome.
    run_id = start_run(store, case_id=CASE)
    store.execute("UPDATE runs SET state = 'FAILED' WHERE run_id = %s", (run_id,))
    with pytest.raises(Refusal) as caught:
        commit_terminal(store, _terminal(run_id))
    assert caught.value.code is RefusalCode.RUN_NOT_RUNNING
    assert _counts(store) == (0, 0, 0)
