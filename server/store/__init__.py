"""The store. Hand-written SQL against PostgreSQL 16; no ORM (DECISIONS.md 12)."""

from __future__ import annotations

import uuid
from pathlib import Path

from psycopg import Connection
from psycopg.rows import TupleRow

SCHEMA = Path(__file__).with_name("schema.sql")

# One name for "an open connection to the store", so no module has to spell the
# psycopg generic or reach for Any.
type Store = Connection[TupleRow]


class SchemaDrifted(RuntimeError):
    """The store holds a shape `schema.sql` no longer declares.

    Schema text, not document text: naming what differs is what makes the
    refusal actionable, and there is nothing here that a document wrote.
    """

    def __init__(self, missing: list[str], undeclared: list[str]) -> None:
        super().__init__(
            "the store does not match schema.sql, and there are no migrations "
            f"to reconcile it. missing from the store: {missing}. "
            f"not declared by the file: {undeclared}"
        )


# Everything a schema holds that `schema.sql` can declare, one line each.
# The outer replace strips the owning schema's name -- `pg_get_triggerdef` and
# `indexdef` qualify their table, `pg_get_constraintdef` does not -- so two
# schemas declaring the same thing describe it identically.
_DESCRIBE = """
SELECT replace(line, quote_ident(%(schema)s) || '.', '') FROM (
    SELECT 'column ' || c.relname || '.' || a.attname
           || ' ' || format_type(a.atttypid, a.atttypmod)
           || CASE WHEN a.attnotnull THEN ' NOT NULL' ELSE '' END
           || coalesce(' IDENTITY ' || nullif(a.attidentity, '')::text, '')
           || coalesce(' DEFAULT ' || pg_get_expr(d.adbin, d.adrelid), '')
      FROM pg_attribute a
      JOIN pg_class c ON c.oid = a.attrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
      LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
     WHERE n.nspname = %(schema)s AND c.relkind IN ('r', 'p')
       AND a.attnum > 0 AND NOT a.attisdropped
    UNION ALL
    SELECT 'constraint ' || c.relname || '.' || con.conname
           || ' ' || pg_get_constraintdef(con.oid)
      FROM pg_constraint con
      JOIN pg_class c ON c.oid = con.conrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = %(schema)s
    UNION ALL
    SELECT 'index ' || indexdef FROM pg_indexes WHERE schemaname = %(schema)s
    UNION ALL
    SELECT 'trigger ' || pg_get_triggerdef(t.oid)
      FROM pg_trigger t
      JOIN pg_class c ON c.oid = t.tgrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = %(schema)s AND NOT t.tgisinternal
) AS described(line)
"""


def _describe(connection: Store, schema: str) -> set[str]:
    return {row[0] for row in connection.execute(_DESCRIBE, {"schema": schema})}


def _declared(connection: Store, statements: str) -> set[str]:
    """What `schema.sql` declares, read back from an empty schema it was applied to.

    Postgres parses the file; nothing here does. `search_path` is moved to reach
    that schema and put back before it is dropped, so no caller sees it moved.
    """
    [(search_path,)] = connection.execute("SELECT current_setting('search_path')")
    schema = f"caos_declared_{uuid.uuid4().hex}"
    connection.execute(f'CREATE SCHEMA "{schema}"')
    connection.execute("SELECT set_config('search_path', %s, false)", (schema,))
    connection.execute(statements)
    declared = _describe(connection, schema)
    connection.execute("SELECT set_config('search_path', %s, false)", (search_path,))
    connection.execute(f'DROP SCHEMA "{schema}" CASCADE')
    return declared


def apply_schema(connection: Store) -> None:
    """Create the schema in full and refuse a store that does not match the file.

    Idempotent, so a restart is not a special case -- but idempotent is exactly
    what makes the file's second claim untrue. `CREATE TABLE IF NOT EXISTS` is a
    no-op on a table that already exists, *including* one whose columns the file
    has since changed: no error, no warning, and the old shape survives. Adding
    a table works; widening one does not. So the file is applied a second time
    into an empty schema -- Postgres reads it, nothing here parses SQL -- and
    what it declares is compared against what the store actually has.

    Wants a connection in a transaction, and that is load-bearing rather than
    tidy: the file is applied before the comparison can be made, so the caller's
    rollback is what un-applies it. In autocommit the refusal would arrive after
    the store had already been changed, which is the opposite of SYSTEM_SPEC 11.

    The comparison reads the whole schema `search_path` resolves to, so an
    object in it that `schema.sql` did not declare reads as drift.
    """
    # Read before the apply: afterwards every schema is populated, by this.
    [(schema, populated)] = connection.execute(
        "SELECT current_schema(),"
        " EXISTS (SELECT FROM pg_class"
        "          WHERE relnamespace = current_schema()::regnamespace)"
    )
    statements = SCHEMA.read_text(encoding="utf-8")
    connection.execute(statements)
    if not populated:
        # Nothing was here to drift from: what the schema holds is what was
        # just applied. A first boot skips the comparison; every restart after
        # it pays for one, which is the only time it can fail.
        return

    live = _describe(connection, schema)
    declared = _declared(connection, statements)
    if live != declared:
        raise SchemaDrifted(sorted(declared - live), sorted(live - declared))
