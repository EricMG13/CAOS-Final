"""Governed races, proven on two independent PostgreSQL connections.

Concurrency defects are ~2x more frequent in agent-written code
(docs/AI_CODE_QUALITY.md section 1) and a single-connection test cannot see
them: the interleaving that breaks `max(seq) + 1` needs two real sessions.
"""

from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.engine.route import ResolvedRoute, resolve_route, route_digest
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.events import EventKind, emit
from server.store.gates import Gate, GateKind, approve_gate, open_gate
from server.store.members import Standing, grant_membership
from server.store.routes import pin_route
from server.store.runs import TerminalCommit, commit_terminal, start_run

CATALOG = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "vendor/deploy-v/skills/cp-os-credit-os/references"
        / "CREDIT_OS_V_MODULE_CATALOG_v2.json"
    ).read_text(encoding="utf-8")
)
CASE = BoundaryText.of("acme")
NODE = BoundaryText.of("CP-1")
ASSESSMENT = resolve_route(CATALOG, "FULL_CREDIT_32", "FULL_CREDIT_ASSESSMENT")
PORTFOLIO = resolve_route(CATALOG, "FULL_CREDIT_32", "PORTFOLIO_DECISION")


def _connect(url: str, schema: str) -> Store:
    connection = psycopg.connect(url, autocommit=False)
    connection.execute(f'SET search_path TO "{schema}"')
    return connection


def test_two_connections_deliver_one_terminal_event(
    store: Store, store_schema: str, postgres_dsn: str
) -> None:
    run_id = start_run(store, case_id=CASE)
    store.commit()

    def deliver(digest: str) -> bool:
        with _connect(postgres_dsn, store_schema) as connection:
            return commit_terminal(
                connection,
                TerminalCommit(
                    run_id=run_id,
                    node_id=NODE,
                    artifact_sha256=digest,
                    charge=Decimal("0.42"),
                ),
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(deliver, ["a" * 64, "b" * 64]))

    assert sorted(outcomes) == [False, True]
    counts = store.execute(
        "SELECT (SELECT count(*) FROM artifacts),"
        " (SELECT count(*) FROM budget_ledger),"
        " (SELECT count(*) FROM run_events)"
    ).fetchone()
    assert counts == (1, 1, 1)


def test_concurrent_runs_each_start_their_own_sequence(
    store: Store, store_schema: str, postgres_dsn: str
) -> None:
    store.execute("INSERT INTO cases (case_id) VALUES ('acme') ON CONFLICT DO NOTHING")
    store.commit()

    def deliver(_: int) -> str:
        with _connect(postgres_dsn, store_schema) as connection:
            run_id = start_run(connection, case_id=CASE)
            commit_terminal(
                connection,
                TerminalCommit(
                    run_id=run_id,
                    node_id=NODE,
                    artifact_sha256=uuid.uuid4().hex * 2,
                    charge=Decimal("0.01"),
                ),
            )
            return run_id

    with ThreadPoolExecutor(max_workers=4) as pool:
        run_ids = list(pool.map(deliver, range(4)))

    assert len(set(run_ids)) == 4
    seqs = store.execute("SELECT seq FROM run_events").fetchall()
    assert [seq for (seq,) in seqs] == [1, 1, 1, 1]


def test_the_race_suite_refuses_to_pass_without_postgres(postgres_dsn: str) -> None:
    # A race suite that skipped is not a race suite that passed.
    assert postgres_dsn, "the race tests require a real PostgreSQL"
    with pytest.raises(psycopg.errors.UndefinedTable):
        with psycopg.connect(postgres_dsn, autocommit=True) as probe:
            probe.execute("SELECT 1 FROM no_such_table_here")


def test_concurrent_first_pins_refuse_with_a_typed_code(
    store: Store, store_schema: str, postgres_dsn: str
) -> None:
    """`pin_route`'s `FOR UPDATE` locks nothing when there is no row to lock.

    Four callers all find no pin, all insert, and three collide on
    `run_routes_pkey` -- a vendor constraint name escaping a governed write
    path. Pinning the *same* route is meant to be the pin it already has, since
    recovery replays the gate, so the concurrent replay must return the digest.
    """
    run_id = start_run(store, case_id=CASE)
    store.commit()

    def pin(_: int) -> str:
        with _connect(postgres_dsn, store_schema) as connection:
            return pin_route(
                connection, run_id=run_id, resolved=ASSESSMENT, source_set_version=1
            )

    with ThreadPoolExecutor(max_workers=4) as pool:
        digests = list(pool.map(pin, range(4)))

    assert set(digests) == {route_digest(ASSESSMENT)}
    counted = store.execute(
        "SELECT (SELECT count(*) FROM run_routes WHERE run_id = %s),"
        " (SELECT count(*) FROM run_events WHERE run_id = %s)",
        (run_id, run_id),
    ).fetchone()
    assert counted == (1, 1), "one pin, one ROUTE_PINNED event"


def test_a_concurrent_pin_of_a_different_route_refuses_by_code(
    store: Store, store_schema: str, postgres_dsn: str
) -> None:
    # The loser is refused because the route differs, not because an index said
    # so: invariant 10 is what is being enforced, and the code has to say it.
    run_id = start_run(store, case_id=CASE)
    store.commit()

    def pin(resolved: ResolvedRoute) -> str:
        with _connect(postgres_dsn, store_schema) as connection:
            try:
                pin_route(
                    connection, run_id=run_id, resolved=resolved, source_set_version=1
                )
            except Refusal as refusal:
                return refusal.code.value
            return "pinned"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(pin, [ASSESSMENT, PORTFOLIO]))

    assert outcomes == [RefusalCode.ROUTE_ALREADY_PINNED.value, "pinned"]


def test_two_connections_release_one_gate_once(
    store: Store, store_schema: str, postgres_dsn: str
) -> None:
    # Invariant 5: a single-actor release is a store CAS transaction. Two people
    # reading the same preview and pressing approve together must produce one
    # approval and one event, and the loser must learn it was a replay rather
    # than see a primary key.
    run_id = start_run(store, case_id=CASE)
    for approver in ("ana", "bo"):
        grant_membership(
            store,
            case_id=CASE,
            member_id=BoundaryText.of(approver),
            standing=Standing.APPROVER,
        )
    gate = Gate(run_id, GateKind.SOURCE_SET, "a" * 64, "b" * 64)
    open_gate(store, gate)
    store.commit()

    def release(approver: str) -> bool:
        with _connect(postgres_dsn, store_schema) as connection:
            return approve_gate(connection, gate, approver=BoundaryText.of(approver))

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(release, ["ana", "bo"]))

    assert outcomes == [False, True]
    counted = store.execute(
        "SELECT (SELECT count(*) FROM run_gate_approvals),"
        " (SELECT count(*) FROM run_events WHERE kind = 'GATE_APPROVED')"
    ).fetchone()
    assert counted == (1, 1), "one release, one GATE_APPROVED event"


def test_concurrent_emitters_allocate_distinct_sequences(
    store: Store, store_schema: str, postgres_dsn: str
) -> None:
    """`max(seq) + 1` is safe only while one allocator reads it at a time.

    Two guards used to supply that by accident: `commit_terminal` holds the run
    row lock for its own reasons, and `pin_route` is serialised by
    `run_routes_pkey`. Any third path had neither, and two concurrent inserts of
    the same kind collided on `run_events_pkey` -- a vendor constraint name
    escaping a governed write. Gate events are that third path, so the emitter
    takes the lock itself and this is what says so.
    """
    run_id = start_run(store, case_id=CASE)
    store.commit()

    def append(_: int) -> int:
        with _connect(postgres_dsn, store_schema) as connection:
            with connection.transaction():
                return emit(connection, run_id=run_id, kind=EventKind.GATE_OPENED)

    with ThreadPoolExecutor(max_workers=6) as pool:
        seqs = sorted(pool.map(append, range(6)))

    assert seqs == [1, 2, 3, 4, 5, 6]
