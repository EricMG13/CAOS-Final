"""The guard that keeps the store suite from passing without a store.

`CAOS_REQUIRE_POSTGRES=1` is what CI sets so a missing DSN is a failure rather
than a silent skip. A broken guard would not show up as a red suite -- it would
show up as a green one that tested nothing, which is the failure
docs/AI_CODE_QUALITY.md section 4 exists to prevent.
"""

from __future__ import annotations

import pytest
from conftest import postgres_dsn_or_none


def test_a_configured_dsn_is_returned() -> None:
    assert postgres_dsn_or_none({"CAOS_TEST_POSTGRES_URL": "postgresql:///caos"}) == (
        "postgresql:///caos"
    )


def test_no_dsn_is_skippable_when_postgres_is_optional() -> None:
    assert postgres_dsn_or_none({}) is None


def test_no_dsn_is_fatal_when_the_suite_may_not_skip() -> None:
    with pytest.raises(pytest.fail.Exception, match="CAOS_REQUIRE_POSTGRES"):
        postgres_dsn_or_none({"CAOS_REQUIRE_POSTGRES": "1"})
