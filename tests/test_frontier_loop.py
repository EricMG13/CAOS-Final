"""Phase 4: the frontier loop, and what a crash costs.

Recovery is recomputation (`docs/DECISIONS.md` §3): there is no checkpoint, so
restarting means recomputing `node_states` over the surviving attempt rows.

`run_attempts` is append-only (`SYSTEM_SPEC.md` §2), which decides the shape of
everything here. An attempt row records one try and its reservation and is never
updated; acceptance is a separate row. So an attempt with no artifact is
indeterminate by construction, and `docs/DECISIONS.md` §21's rule -- unknown
usage keeps its reserved exposure -- needs no state machine to enforce.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.engine.loop import (
    Executor,
    NodeOutcome,
    accepted_attempts,
    run_route,
)
from server.engine.route import resolve_route
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.attempts import reserve, reserved_total
from server.store.routes import pin_route
from server.store.runs import start_run

CATALOG = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "vendor/deploy-v/skills/cp-os-credit-os/references"
        / "CREDIT_OS_V_MODULE_CATALOG_v2.json"
    ).read_text(encoding="utf-8")
)
CASE = BoundaryText.of("acme")
# Two nodes, CP-0 -> CP-8: the smallest real pathway in the catalog.
FULL, LEDGER = "FULL_CREDIT_32", "DECISION_LEDGER"
PRICE = Decimal("1.00")


@pytest.fixture
def pinned(store: Store) -> str:
    run_id = start_run(store, case_id=CASE, ceiling=Decimal("100"))
    pin_route(store, run_id=run_id, resolved=resolve_route(CATALOG, FULL, LEDGER))
    store.commit()
    return run_id


def _executor(calls: list[str], *, die_on: str | None = None) -> Executor:
    def execute(route_node_id: str) -> NodeOutcome:
        calls.append(route_node_id)
        if die_on and die_on in route_node_id:
            # The provider completed and billed; the host dies before accepting.
            raise TimeoutError(route_node_id)
        digest = f"{abs(hash(route_node_id)):064x}"[:64]
        return NodeOutcome(artifact_sha256=digest, charge=PRICE)

    return execute


def test_recovery_is_recomputation(store: Store, pinned: str) -> None:
    first: list[str] = []
    with pytest.raises(TimeoutError):
        run_route(store, run_id=pinned, execute=_executor(first, die_on="CP-8"))

    # Restart. Nothing is restored: node_states is recomputed from the rows.
    second: list[str] = []
    run_route(store, run_id=pinned, execute=_executor(second))

    assert any("CP-0" in c for c in first), "the first pass ran CP-0"
    assert not any("CP-0" in c for c in second), "CP-0 was accepted; do not re-run it"
    assert any("CP-8" in c for c in second)

    tables = store.execute(
        "SELECT count(*) FROM information_schema.tables"
        " WHERE table_schema = current_schema() AND table_name LIKE '%checkpoint%'"
    ).fetchone()
    assert tables == (0,), "there is no checkpointer"


def test_crash_after_remote_completion_keeps_its_reservation(
    store: Store, pinned: str
) -> None:
    with pytest.raises(TimeoutError):
        run_route(store, run_id=pinned, execute=_executor([], die_on="CP-0"))
    store.rollback()

    # The attempt row was committed before the call, so it survives the crash.
    attempts = store.execute(
        "SELECT count(*) FROM run_attempts WHERE run_id = %s", (pinned,)
    ).fetchone()
    assert attempts == (1,)
    # And its reservation still counts: releasing it would turn a real charge
    # into free budget, which is the direction that overspends.
    assert reserved_total(store, run_id=pinned) == PRICE
    assert store.execute(
        "SELECT count(*) FROM artifacts WHERE run_id = %s", (pinned,)
    ).fetchone() == (0,)


def test_a_retry_without_provider_idempotency_reserves_again(
    store: Store, pinned: str
) -> None:
    with pytest.raises(TimeoutError):
        run_route(store, run_id=pinned, execute=_executor([], die_on="CP-0"))
    store.rollback()
    run_route(store, run_id=pinned, execute=_executor([]))

    # No provider idempotency is assumed, so the retry is a new operation with
    # its own reservation. Two attempts on CP-0, two reservations.
    cp0 = store.execute(
        "SELECT count(*) FROM run_attempts WHERE run_id = %s"
        " AND route_node_id LIKE '%%CP-0'",
        (pinned,),
    ).fetchone()
    assert cp0 == (2,)
    assert reserved_total(store, run_id=pinned) == PRICE * 3


def test_concurrent_reservations_at_the_ceiling_refuse(
    store: Store, store_schema: str, postgres_dsn: str
) -> None:
    from concurrent.futures import ThreadPoolExecutor

    run_id = start_run(store, case_id=CASE, ceiling=Decimal("1.50"))
    store.commit()

    def take(node: str) -> str:
        with psycopg.connect(postgres_dsn, autocommit=False) as connection:
            connection.execute(f'SET search_path TO "{store_schema}"')
            try:
                reserve(connection, run_id=run_id, route_node_id=node, amount=PRICE)
            except Refusal as refusal:
                return refusal.code.value
            return "reserved"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(take, ["node-a", "node-b"]))

    # A ceiling of 1.50 admits one reservation of 1.00, never two.
    assert outcomes == [RefusalCode.BUDGET_CEILING_EXCEEDED.value, "reserved"]
    assert reserved_total(store, run_id=run_id) == PRICE


def test_accepted_attempts_is_the_whole_of_execution_state(
    store: Store, pinned: str
) -> None:
    # No checkpoint, no engine state: what a node produced is what the engine
    # knows, and the frontier is recomputed from it every pass.
    assert accepted_attempts(store, run_id=pinned) == {}
    run_route(store, run_id=pinned, execute=_executor([]))
    accepted = accepted_attempts(store, run_id=pinned)
    assert len(accepted) == 2
    assert all(len(a.artifact_sha256) == 64 for a in accepted.values())
