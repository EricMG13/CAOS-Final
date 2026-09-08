"""Import paths, and one PostgreSQL connection per test on a private schema."""

from __future__ import annotations

import os
import sys
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

from server.store import Store

REPO = Path(__file__).resolve().parents[1]
# The gate scripts are executables, not a package; import them by path.
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))


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
