"""The frontier loop.

    while ready := frontier(route, accepted):
        run each ready node

Recovery is recomputation (`docs/DECISIONS.md` §3). There is no checkpoint to
restore: on restart the loop reads the pinned route, recomputes `node_states`
over the surviving attempt rows, and the frontier tells it exactly what remains.
A node whose artifact is already there is never run again.

Every node reserves before it calls, and the reservation is committed first --
so a crash between the call and the acceptance leaves the exposure recorded
rather than lost (`docs/DECISIONS.md` §21).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from server.boundary_text import BoundaryText
from server.engine.route import Accepted, ResolvedRoute, frontier
from server.store import Store
from server.store.attempts import accept, reserve
from server.store.routes import pinned_route


@dataclass(frozen=True, slots=True)
class NodeOutcome:
    """What one node produced, and what it cost."""

    artifact_sha256: str
    charge: Decimal
    readiness: str | None = None


type Executor = Callable[[str], NodeOutcome]


def accepted_attempts(store: Store, *, run_id: str) -> dict[str, Accepted]:
    """The accepted artifacts, keyed by route node. The whole of execution state."""
    rows = store.execute(
        "SELECT node_id, sha256 FROM artifacts WHERE run_id = %s", (run_id,)
    ).fetchall()
    return {str(node): Accepted(artifact_sha256=str(digest)) for node, digest in rows}


def run_route(store: Store, *, run_id: str, execute: Executor) -> ResolvedRoute:
    """Run the pinned route to a standstill, then return it.

    Nodes run one at a time. `SYSTEM_SPEC.md` §4 gathers them concurrently; that
    waits for a provider call worth overlapping, and for a store that can be
    awaited -- see the known-gaps ledger.
    """
    route = pinned_route(store, run_id=run_id)
    while ready := frontier(route, accepted_attempts(store, run_id=run_id)):
        for route_node_id in ready:
            _run_node(
                store, run_id=run_id, route_node_id=route_node_id, execute=execute
            )
    return route


def _run_node(
    store: Store, *, run_id: str, route_node_id: str, execute: Executor
) -> None:
    outcome = _attempt(
        store, run_id=run_id, route_node_id=route_node_id, execute=execute
    )
    accept(
        store,
        run_id=run_id,
        node_id=BoundaryText.of(route_node_id),
        artifact_sha256=outcome.artifact_sha256,
        charge=outcome.charge,
    )


def _attempt(
    store: Store, *, run_id: str, route_node_id: str, execute: Executor
) -> NodeOutcome:
    """Reserve, commit the reservation, then call. In that order, always."""
    reserve(store, run_id=run_id, route_node_id=route_node_id, amount=_price())
    store.commit()
    return execute(route_node_id)


def _price() -> Decimal:
    # ponytail: one flat price per node until a provider quotes a real one.
    # The ceiling arithmetic is what matters here, not the number.
    return Decimal("1.00")
