"""Governed races, proven on two independent PostgreSQL connections.

Concurrency defects are ~2x more frequent in agent-written code
(docs/AI_CODE_QUALITY.md section 1) and a single-connection test cannot see
them: the interleaving that breaks `max(seq) + 1` needs two real sessions.
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.store import Store
from server.store.runs import TerminalCommit, commit_terminal, start_run

CASE = BoundaryText.of("acme")
NODE = BoundaryText.of("CP-1")


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
