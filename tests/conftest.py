"""One PostgreSQL connection per test, on a schema created for it alone."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest

from server.store import Store


@pytest.fixture
def postgres_dsn() -> str:
    """The store under test. A skipped store suite is not a passed one."""
    url = os.environ.get("CAOS_TEST_POSTGRES_URL")
    if url is None:
        if os.environ.get("CAOS_REQUIRE_POSTGRES") == "1":
            pytest.fail("CAOS_REQUIRE_POSTGRES=1 but CAOS_TEST_POSTGRES_URL is unset")
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
