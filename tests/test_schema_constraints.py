"""What the schema refuses on its own, with no application code in the way.

A governed table that only its callers guard is a table one raw statement
rewrites. The triggers and CHECKs are asserted here against the store itself.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.store import Store
from server.store.runs import TerminalCommit, commit_terminal, start_run

CASE = BoundaryText.of("acme")
NODE = BoundaryText.of("CP-1")


def _one_event(store: Store) -> None:
    run_id = start_run(store, case_id=CASE)
    commit_terminal(
        store,
        TerminalCommit(
            run_id=run_id,
            node_id=NODE,
            artifact_sha256="b" * 64,
            charge=Decimal("0.42"),
        ),
    )


def test_run_events_refuses_an_update(store: Store) -> None:
    _one_event(store)
    with pytest.raises(psycopg.errors.RaiseException) as caught:
        store.execute("UPDATE run_events SET kind = 'FORGED'")
    assert caught.value.diag.message_primary == "APPEND_ONLY_TABLE"
    store.rollback()


def test_run_events_refuses_a_delete(store: Store) -> None:
    _one_event(store)
    with pytest.raises(psycopg.errors.RaiseException) as caught:
        store.execute("DELETE FROM run_events")
    assert caught.value.diag.message_primary == "APPEND_ONLY_TABLE"
    store.rollback()


@pytest.mark.parametrize(
    "table", ["run_events", "source_set_members", "delivered_evidence"]
)
def test_an_append_only_table_refuses_a_truncate(store: Store, table: str) -> None:
    """Refuse truncation for every directly guarded append-only table."""
    # A row-level trigger never sees TRUNCATE: it empties the table without
    # producing a row to fire on. Statement-level is the only guard that catches
    # it, and TRUNCATE is the one statement that erases a whole ledger at once.
    # Nothing references these three, so each table's own trigger is what refuses.
    with pytest.raises(psycopg.errors.RaiseException) as caught:
        store.execute(f"TRUNCATE {table}")
    assert caught.value.diag.message_primary == "APPEND_ONLY_TABLE"
    store.rollback()


def test_source_sets_cannot_be_truncated_by_either_route(store: Store) -> None:
    # Stated separately because the two routes are refused by different guards:
    # a plain TRUNCATE by the members foreign key, a cascading one by the
    # trigger the cascade drags in. `source_sets_no_truncate` is redundant
    # today and is what refuses if either of those ever goes away.
    with pytest.raises(psycopg.errors.FeatureNotSupported):
        store.execute("TRUNCATE source_sets")
    store.rollback()

    with pytest.raises(psycopg.errors.RaiseException) as caught:
        store.execute("TRUNCATE source_sets CASCADE")
    assert caught.value.diag.message_primary == "APPEND_ONLY_TABLE"
    store.rollback()


@pytest.mark.parametrize(
    "digest",
    [
        pytest.param("abc", id="too-short"),
        pytest.param("A" * 64, id="uppercase"),
        pytest.param("g" * 64, id="not-hex"),
        pytest.param("a" * 63 + " ", id="space-padded"),
    ],
)
def test_a_source_digest_that_is_not_64_lowercase_hex_is_refused(
    store: Store, digest: str
) -> None:
    # char(64) pads a short value with spaces and stores it: the identity the
    # host owns (invariant 3) would then be whatever the caller passed.
    store.execute("INSERT INTO cases (case_id) VALUES ('acme')")
    with pytest.raises(psycopg.errors.CheckViolation):
        store.execute(
            "INSERT INTO sources (source_id, case_id, sha256) VALUES (%s, 'acme', %s)",
            (str(uuid.uuid4()), digest),
        )
    store.rollback()


def test_every_table_that_refuses_a_rewrite_also_refuses_a_truncate(
    store: Store,
) -> None:
    """Require every rewrite-guarded table to also refuse truncation."""
    # The guards were enumerated by table name in schema.sql and one table was
    # missed. This derives the list instead: a table wired to `refuse_rewrite`
    # has a ledger to protect, and needs both guards to protect it -- a row
    # trigger for the statements that produce rows, a statement trigger for
    # TRUNCATE, which produces none and erases the whole table at once. Asserted
    # in both directions, so neither guard alone reads as covered.
    #
    # `tgtype` is a bitmask: DELETE is 8, UPDATE is 16, TRUNCATE is 32.
    guarded = store.execute(
        "SELECT c.relname,"
        "       bool_or(t.tgtype & 24 <> 0),"
        "       bool_or(t.tgtype & 32 <> 0)"
        " FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid"
        " WHERE NOT t.tgisinternal"
        " AND c.relnamespace = current_schema()::regnamespace"
        " AND t.tgfoid = 'refuse_rewrite'::regproc"
        " GROUP BY c.relname"
    ).fetchall()
    # A query that matched nothing would pass the assertions below without
    # having read a single trigger. Four tables carry `refuse_rewrite` today.
    assert len(guarded) >= 4
    assert [table for table, rewrite, _ in guarded if not rewrite] == []
    assert [table for table, _, truncate in guarded if not truncate] == []
