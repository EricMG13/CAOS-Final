"""Invariant 10: the resolved route is pinned once, and execution reads the pin.

Resolution is pure, so it can be replayed -- but replay is not the guarantee.
The guarantee is that a run executes the route it was pinned to even if the
catalog changes underneath it, which is what makes a completed run explicable
a year later. The pin, not the catalog, is the authority after the gate.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from server.boundary_text import BoundaryText
from server.engine.route import resolve_route, route_digest
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.routes import pin_route, pinned_route
from server.store.runs import start_run

CATALOG = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "vendor/deploy-v/skills/cp-os-credit-os/references"
        / "CREDIT_OS_V_MODULE_CATALOG_v2.json"
    ).read_text(encoding="utf-8")
)
CASE = BoundaryText.of("acme")
FULL = "FULL_CREDIT_32"
ASSESSMENT = "FULL_CREDIT_ASSESSMENT"


@pytest.fixture
def run_id(store: Store) -> str:
    return start_run(store, case_id=CASE)


def test_a_route_is_pinned_once_and_read_back_identically(
    store: Store, run_id: str
) -> None:
    resolved = resolve_route(CATALOG, FULL, ASSESSMENT)
    digest = pin_route(store, run_id=run_id, resolved=resolved)
    assert digest == route_digest(resolved)

    read_back = pinned_route(store, run_id=run_id)
    assert read_back == resolved
    assert route_digest(read_back) == digest


def test_execution_reads_the_pin_and_not_the_catalog(store: Store, run_id: str) -> None:
    # The catalog is authority until the gate and irrelevant after it. A bundle
    # that changes must not change what an already-pinned run executes.
    pin_route(store, run_id=run_id, resolved=resolve_route(CATALOG, FULL, ASSESSMENT))

    changed = json.loads(json.dumps(CATALOG))
    changed["profiles"][FULL]["pathways"][ASSESSMENT]["nodes"].pop()
    assert route_digest(resolve_route(changed, FULL, ASSESSMENT)) != route_digest(
        resolve_route(CATALOG, FULL, ASSESSMENT)
    )

    assert route_digest(pinned_route(store, run_id=run_id)) == route_digest(
        resolve_route(CATALOG, FULL, ASSESSMENT)
    )


def test_pinning_a_second_route_to_the_same_run_is_refused(
    store: Store, run_id: str
) -> None:
    pin_route(store, run_id=run_id, resolved=resolve_route(CATALOG, FULL, ASSESSMENT))
    with pytest.raises(Refusal) as caught:
        pin_route(
            store,
            run_id=run_id,
            resolved=resolve_route(CATALOG, FULL, "PORTFOLIO_DECISION"),
        )
    assert caught.value.code is RefusalCode.ROUTE_ALREADY_PINNED


def test_pinning_the_same_route_again_is_the_same_pin(
    store: Store, run_id: str
) -> None:
    # Recovery replays the gate. An identical pin is the pin it already has.
    resolved = resolve_route(CATALOG, FULL, ASSESSMENT)
    first = pin_route(store, run_id=run_id, resolved=resolved)
    assert pin_route(store, run_id=run_id, resolved=resolved) == first
    pinned = store.execute(
        "SELECT count(*) FROM run_routes WHERE run_id = %s", (run_id,)
    ).fetchone()
    assert pinned == (1,)


def test_pinning_emits_one_run_event_carrying_the_digest(
    store: Store, run_id: str
) -> None:
    # State and event commit together (SYSTEM_SPEC 2), and a replayed pin adds
    # no second event.
    resolved = resolve_route(CATALOG, FULL, ASSESSMENT)
    digest = pin_route(store, run_id=run_id, resolved=resolved)
    pin_route(store, run_id=run_id, resolved=resolved)

    events = store.execute(
        "SELECT seq, kind, route_digest FROM run_events"
        " WHERE run_id = %s AND kind = 'ROUTE_PINNED'",
        (run_id,),
    ).fetchall()
    assert len(events) == 1
    assert events[0][2] == digest


def test_an_unpinned_run_has_no_route_to_execute(store: Store, run_id: str) -> None:
    with pytest.raises(Refusal) as caught:
        pinned_route(store, run_id=run_id)
    assert caught.value.code is RefusalCode.ROUTE_NOT_PINNED


def test_pinning_a_route_to_an_unknown_run_refuses_by_code(store: Store) -> None:
    # The same leak as the concurrent pin: an unknown run put
    # `run_routes_run_id_fkey` and the run id into the escaping exception.
    # `reserve` already answers RUN_NOT_FOUND here; the gate must too.
    with pytest.raises(Refusal) as caught:
        pin_route(
            store,
            run_id=str(uuid.uuid4()),
            resolved=resolve_route(CATALOG, FULL, ASSESSMENT),
        )
    assert caught.value.code is RefusalCode.RUN_NOT_FOUND
