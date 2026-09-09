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
import uuid
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.engine.loop import (
    Executor,
    NodeOutcome,
    Prepared,
    accepted_attempts,
    run_route,
)
from server.engine.route import Accepted, State, frontier, node_states, resolve_route
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.attempts import accept, reserve, reserved_total
from server.store.blobs import BlobStore
from server.store.routes import pin_route
from server.store.runs import TerminalCommit, commit_terminal, start_run

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
    pin_route(
        store,
        run_id=run_id,
        resolved=resolve_route(CATALOG, FULL, LEDGER),
        source_set_version=1,
    )
    store.commit()
    return run_id


def _executor(
    calls: list[str],
    blobs: BlobStore,
    *,
    die_on: str | None = None,
    charge: Decimal = PRICE,
) -> Executor:
    def execute(route_node_id: str) -> Prepared:
        calls.append(route_node_id)

        def call() -> NodeOutcome:
            if die_on and die_on in route_node_id:
                # The provider completed and billed; the host dies before
                # accepting. Raised from the call, after the reservation.
                raise TimeoutError(route_node_id)
            if route_node_id.endswith("-CP-0"):
                # The loop reads readiness back out of this artifact, so CP-0's
                # has to be a real one.
                return NodeOutcome(
                    artifact_sha256=_cp0_artifact(blobs, "READY"), charge=charge
                )
            digest = f"{abs(hash(route_node_id)):064x}"[:64]
            return NodeOutcome(artifact_sha256=digest, charge=charge)

        return Prepared(ceiling=PRICE, call=call)

    return execute


def test_recovery_is_recomputation(store: Store, pinned: str, blobs: BlobStore) -> None:
    first: list[str] = []
    with pytest.raises(TimeoutError):
        run_route(
            store,
            run_id=pinned,
            blobs=blobs,
            execute=_executor(first, blobs, die_on="CP-8"),
        )

    # Restart. Nothing is restored: node_states is recomputed from the rows.
    second: list[str] = []
    run_route(store, run_id=pinned, blobs=blobs, execute=_executor(second, blobs))

    assert any("CP-0" in c for c in first), "the first pass ran CP-0"
    assert not any("CP-0" in c for c in second), "CP-0 was accepted; do not re-run it"
    assert any("CP-8" in c for c in second)

    tables = store.execute(
        "SELECT count(*) FROM information_schema.tables"
        " WHERE table_schema = current_schema() AND table_name LIKE '%checkpoint%'"
    ).fetchone()
    assert tables == (0,), "there is no checkpointer"


def test_crash_after_remote_completion_keeps_its_reservation(
    store: Store, pinned: str, blobs: BlobStore
) -> None:
    with pytest.raises(TimeoutError):
        run_route(
            store,
            run_id=pinned,
            blobs=blobs,
            execute=_executor([], blobs, die_on="CP-0"),
        )
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
    store: Store, pinned: str, blobs: BlobStore
) -> None:
    with pytest.raises(TimeoutError):
        run_route(
            store,
            run_id=pinned,
            blobs=blobs,
            execute=_executor([], blobs, die_on="CP-0"),
        )
    store.rollback()
    run_route(store, run_id=pinned, blobs=blobs, execute=_executor([], blobs))

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
    store: Store, pinned: str, blobs: BlobStore
) -> None:
    # No checkpoint, no engine state: what a node produced is what the engine
    # knows, and the frontier is recomputed from it every pass.
    route = resolve_route(CATALOG, FULL, LEDGER)
    assert accepted_attempts(store, run_id=pinned, route=route, blobs=blobs) == {}
    run_route(store, run_id=pinned, blobs=blobs, execute=_executor([], blobs))
    accepted = accepted_attempts(store, run_id=pinned, route=route, blobs=blobs)
    assert len(accepted) == 2
    assert all(len(a.artifact_sha256) == 64 for a in accepted.values())


def test_a_charge_above_its_reservation_is_refused(
    store: Store, pinned: str, blobs: BlobStore
) -> None:
    # Invariant 8: every ceiling refuses the next operation before overspend.
    # The reservation is that ceiling for one call, so a charge exceeding it is
    # an overspend that already happened -- the ledger must not record it as if
    # the budget had allowed it.
    def expensive(route_node_id: str) -> Prepared:
        return Prepared(
            ceiling=PRICE,
            call=lambda: NodeOutcome(artifact_sha256="e" * 64, charge=PRICE * 10),
        )

    with pytest.raises(Refusal) as caught:
        run_route(store, run_id=pinned, blobs=blobs, execute=expensive)
    assert caught.value.code is RefusalCode.CHARGE_EXCEEDS_RESERVATION

    store.rollback()
    assert store.execute(
        "SELECT count(*) FROM budget_ledger WHERE run_id = %s", (pinned,)
    ).fetchone() == (0,)
    assert store.execute(
        "SELECT count(*) FROM artifacts WHERE run_id = %s", (pinned,)
    ).fetchone() == (0,)


def test_a_charge_within_its_reservation_is_recorded_as_charged(
    store: Store, pinned: str, blobs: BlobStore
) -> None:
    # The ledger records what it cost, not what was set aside for it.
    cheap = Decimal("0.25")

    run_route(
        store, run_id=pinned, blobs=blobs, execute=_executor([], blobs, charge=cheap)
    )
    charged = store.execute(
        "SELECT sum(amount) FROM budget_ledger WHERE run_id = %s", (pinned,)
    ).fetchone()
    assert charged is not None
    assert charged[0] == cheap * 2


def test_accepting_one_node_twice_records_one_artifact_and_one_charge(
    store: Store, pinned: str
) -> None:
    """Invariant 6: one artifact, one charge, however often a node is accepted.

    The `artifacts` primary key is what refuses the second, and the transaction
    `accept` shares with the ledger insert is what keeps its charge out. Neither
    table carries a rewrite trigger (CLAUDE.md, Phase 1), so this pairing is the
    whole of the guarantee.
    """
    node = BoundaryText.of("CP-0")
    charge = Decimal("1.00")
    accept(store, run_id=pinned, node_id=node, artifact_sha256="a" * 64, charge=charge)
    # No commit here: `accept` opens the outermost transaction, so the first
    # call is already durable. A commit would also mask one that never was.
    with pytest.raises(Refusal):
        accept(
            store, run_id=pinned, node_id=node, artifact_sha256="b" * 64, charge=charge
        )
    store.rollback()
    counted = store.execute(
        "SELECT (SELECT count(*) FROM artifacts WHERE run_id = %s),"
        " (SELECT count(*) FROM budget_ledger WHERE run_id = %s)",
        (pinned, pinned),
    ).fetchone()
    assert counted == (1, 1)


def test_a_terminated_run_refuses_a_reservation(store: Store, pinned: str) -> None:
    """Invariant 8: a terminated run's ceiling is zero, whatever `runs.ceiling` says.

    `reserve` takes the run row lock to make the ceiling real, and the same lock
    makes the state authoritative -- so reading one without the other is a
    choice, not an oversight. A run that has left RUNNING has no next operation
    to fund, and a charge accepted against it is spend nobody can account to a
    live run.
    """
    commit_terminal(
        store,
        TerminalCommit(
            run_id=pinned,
            node_id=BoundaryText.of("CP-0"),
            artifact_sha256="a" * 64,
            charge=PRICE,
        ),
    )
    store.commit()

    with pytest.raises(Refusal) as caught:
        reserve(store, run_id=pinned, route_node_id="CP-8", amount=PRICE)
    assert caught.value.code is RefusalCode.RUN_NOT_RUNNING

    store.rollback()
    store.execute("UPDATE runs SET state = 'FAILED' WHERE run_id = %s", (pinned,))
    with pytest.raises(Refusal) as failed:
        reserve(store, run_id=pinned, route_node_id="CP-8", amount=PRICE)
    assert failed.value.code is RefusalCode.RUN_NOT_RUNNING

    store.rollback()
    assert reserved_total(store, run_id=pinned) == Decimal(0)


def test_a_duplicate_acceptance_refuses_with_a_typed_code(
    store: Store, pinned: str
) -> None:
    """The second acceptance refuses with a code, not with a vendor's constraint.

    `server/refusals.py` exists so that no vendor name, constraint name or key
    value escapes a governed write path. A raw `UniqueViolation` carries all
    three -- `artifacts_pkey` and the offending `(run_id, node_id)` -- straight
    into whatever logs the exception.
    """
    node = BoundaryText.of("CP-0")
    accept(store, run_id=pinned, node_id=node, artifact_sha256="a" * 64, charge=PRICE)

    with pytest.raises(Refusal) as caught:
        accept(
            store, run_id=pinned, node_id=node, artifact_sha256="b" * 64, charge=PRICE
        )
    assert caught.value.code is RefusalCode.NODE_ALREADY_ACCEPTED
    leaked = f"{caught.value!r} {caught.value}"
    assert "artifacts_pkey" not in leaked
    assert pinned not in leaked
    assert "CP-0" not in leaked


def test_accepting_against_an_unknown_run_refuses_by_code(store: Store) -> None:
    # `artifacts_run_id_fkey` and the run id escaped here. `reserve` refuses
    # the same condition by code, and one boundary answers one way.
    with pytest.raises(Refusal) as caught:
        accept(
            store,
            run_id=str(uuid.uuid4()),
            node_id=BoundaryText.of("CP-0"),
            artifact_sha256="a" * 64,
            charge=PRICE,
        )
    assert caught.value.code is RefusalCode.RUN_NOT_FOUND


def _node(route_node_ids: list[str], module_id: str) -> str:
    return next(n for n in route_node_ids if n.endswith(f"-{module_id}"))


def _cp0_artifact(blobs: BlobStore, readiness: str | None) -> str:
    summary = {} if readiness is None else {"overall_readiness": readiness}
    return blobs.put(
        json.dumps({"runtime_output": {"readiness_summary": summary}}).encode()
    )


def test_readiness_is_read_from_the_accepted_cp0_artifact(
    store: Store, blobs: BlobStore
) -> None:
    # `accepted_attempts` built every Accepted without a readiness, so the
    # hardening rule -- soft edges block once CP-0 says READY -- was enforced
    # only in tests that hand-constructed one. DECISIONS.md §18: readiness is
    # derived from the accepted CP-0 artifact, not carried anywhere else.
    route = resolve_route(CATALOG, FULL, "EARNINGS_UPDATE")
    run_id = start_run(store, case_id=CASE, ceiling=Decimal("100"))
    pin_route(store, run_id=run_id, resolved=route, source_set_version=1)
    ids = [n.route_node_id for n in route.nodes]
    cp0, cp5 = _node(ids, "CP-0"), _node(ids, "CP-5")
    accept(
        store,
        run_id=run_id,
        node_id=BoundaryText.of(cp0),
        artifact_sha256=_cp0_artifact(blobs, "READY"),
        charge=PRICE,
    )

    accepted = accepted_attempts(store, run_id=run_id, route=route, blobs=blobs)

    assert accepted[cp0].readiness == "READY"
    # CP-5 has only ADVISORY inputs left. Unhardened it runs RESTRICTED; with
    # CP-0's READY read from the artifact it is BLOCKED on them.
    unread = {cp0: Accepted(accepted[cp0].artifact_sha256)}
    assert node_states(route, unread)[cp5].state is State.RESTRICTED
    assert node_states(route, accepted)[cp5].state is State.BLOCKED
    assert cp5 not in frontier(route, accepted)


def test_a_cp0_artifact_that_states_no_readiness_is_refused(
    store: Store, blobs: BlobStore
) -> None:
    route = resolve_route(CATALOG, FULL, LEDGER)
    run_id = start_run(store, case_id=CASE, ceiling=Decimal("100"))
    pin_route(store, run_id=run_id, resolved=route, source_set_version=1)
    cp0 = _node([n.route_node_id for n in route.nodes], "CP-0")
    accept(
        store,
        run_id=run_id,
        node_id=BoundaryText.of(cp0),
        artifact_sha256=_cp0_artifact(blobs, None),
        charge=PRICE,
    )
    with pytest.raises(Refusal) as caught:
        accepted_attempts(store, run_id=run_id, route=route, blobs=blobs)
    assert caught.value.code is RefusalCode.ENVELOPE_INVALID
