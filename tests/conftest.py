"""One PostgreSQL connection per test, on a schema created for it alone."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator, Mapping

import pytest

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
