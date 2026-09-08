"""The store. Hand-written SQL against PostgreSQL 16; no ORM (DECISIONS.md 12)."""

from __future__ import annotations

from pathlib import Path

from psycopg import Connection
from psycopg.rows import TupleRow

SCHEMA = Path(__file__).with_name("schema.sql")

# One name for "an open connection to the store", so no module has to spell the
# psycopg generic or reach for Any.
type Store = Connection[TupleRow]


def apply_schema(connection: Store) -> None:
    """Create the schema in full. Idempotent, so a restart is not a special case."""
    connection.execute(SCHEMA.read_text(encoding="utf-8"))
