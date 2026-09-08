"""One PostgreSQL connection per test, on a schema created for it alone."""

from __future__ import annotations

import os
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass

import pytest
from psycopg import Cursor
from psycopg.abc import Params, Query
from psycopg.rows import TupleRow

from server.store import Store


def postgres_dsn_or_none(environ: Mapping[str, str]) -> str | None:
    """The configured DSN, or None when the suite is allowed to skip.

    Separate from the fixture so the guard itself has a test: a suite that
    passes because it skipped is the failure this exists to prevent, and that
    failure is invisible from the suite's own exit code.
    """
    url = environ.get("CAOS_TEST_POSTGRES_URL")
    if url is None and environ.get("CAOS_REQUIRE_POSTGRES") == "1":
        pytest.fail("CAOS_REQUIRE_POSTGRES=1 but CAOS_TEST_POSTGRES_URL is unset")
    return url


@pytest.fixture
def postgres_dsn() -> str:
    """The store under test. A skipped store suite is not a passed one."""
    url = postgres_dsn_or_none(os.environ)
    if url is None:
        pytest.skip("CAOS_TEST_POSTGRES_URL is unset")
    return url


@pytest.fixture
def store_schema() -> str:
    return f"t{uuid.uuid4().hex}"


@pytest.fixture
def store(postgres_dsn: str, store_schema: str) -> Iterator[Store]:
    """A connection whose search_path is a schema created for this test alone."""
    import psycopg

    from server.store import apply_schema

    with psycopg.connect(postgres_dsn, autocommit=True) as setup:
        setup.execute(f'CREATE SCHEMA "{store_schema}"')
    connection = psycopg.connect(postgres_dsn, autocommit=False)
    connection.execute(f'SET search_path TO "{store_schema}"')
    apply_schema(connection)
    connection.commit()
    try:
        yield connection
    finally:
        connection.close()
        with psycopg.connect(postgres_dsn, autocommit=True) as teardown:
            teardown.execute(f'DROP SCHEMA "{store_schema}" CASCADE')


@dataclass
class Counted:
    """Store round-trips made inside a `count_io` block."""

    statements: int = 0
    rows: int = 0


type Counter = Callable[[Store], AbstractContextManager[Counted]]


@pytest.fixture
def count_io() -> Counter:
    """Count the statements a call makes, and the rows it reads.

    Rows *read*, not written: a delivery record is not a source parse, and the
    defect this measures is a read that parses more than it was asked for.
    """

    @contextmanager
    def counting(store: Store) -> Iterator[Counted]:
        tally = Counted()
        original = store.execute

        def counted(
            query: Query,
            params: Params | None = None,
            *,
            prepare: bool | None = None,
            binary: bool = False,
        ) -> Cursor[TupleRow]:
            tally.statements += 1
            cursor = original(query, params, prepare=prepare, binary=binary)
            if cursor.description is not None:
                tally.rows += max(cursor.rowcount, 0)
            return cursor

        store.execute = counted  # type: ignore[method-assign]
        try:
            yield tally
        finally:
            del store.execute

    return counting
