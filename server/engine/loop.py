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

import json
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from server.boundary_text import BoundaryText
from server.engine.route import Accepted, ResolvedRoute, frontier
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.attempts import accept, reserve
from server.store.blobs import BlobStore
from server.store.routes import pinned_route


@dataclass(frozen=True, slots=True)
class NodeOutcome:
    """What one node produced, and what it cost."""

    artifact_sha256: str
    charge: Decimal


type Executor = Callable[[str], NodeOutcome]


# Where CP-0 states what it established, in its own payload schema
# (`CP-0__SourceReadiness__payload.schema.txt`). The enum is copied here because
# that file is not JSON Schema and cannot be validated against; route.py's
# `_HARDENING_READINESS` names the two values that harden soft edges, and
# CONDITIONAL -- which DECISIONS.md §18 did not list -- deliberately does not.
_READINESS_PATH = ("runtime_output", "readiness_summary", "overall_readiness")
_READINESS = frozenset({"READY", "READY_WITH_LIMITATIONS", "CONDITIONAL", "BLOCKED"})


def accepted_attempts(
    store: Store, *, run_id: str, route: ResolvedRoute, blobs: BlobStore
) -> dict[str, Accepted]:
    """The accepted artifacts, keyed by route node. The whole of execution state.

    CP-0's carries the readiness it established, read from the artifact itself
    (`docs/DECISIONS.md` §18). It is kept nowhere else, so a recomputed frontier
    rests on what the run produced and not on what a column claims about it.
    """
    rows = store.execute(
        "SELECT node_id, sha256 FROM artifacts WHERE run_id = %s", (run_id,)
    ).fetchall()
    cp0 = next((n.route_node_id for n in route.nodes if n.module_id == "CP-0"), None)
    return {
        str(node): Accepted(
            artifact_sha256=str(digest),
            readiness=_readiness_in(blobs.get(str(digest))) if node == cp0 else None,
        )
        for node, digest in rows
    }


def _readiness_in(artifact: bytes) -> str:
    """What CP-0 established, or a refusal: an artifact that does not say is not one."""
    try:
        found: object = json.loads(artifact)
    except ValueError:
        found = None
    for key in _READINESS_PATH:
        found = found.get(key) if isinstance(found, dict) else None
    if not isinstance(found, str) or found not in _READINESS:
        raise Refusal(RefusalCode.ENVELOPE_INVALID)
    return found


def run_route(
    store: Store, *, run_id: str, execute: Executor, blobs: BlobStore
) -> ResolvedRoute:
    """Run the pinned route to a standstill, then return it.

    Nodes run one at a time. `SYSTEM_SPEC.md` §4 gathers them concurrently; that
    waits for a provider call worth overlapping, and for a store that can be
    awaited -- see the known-gaps ledger.
    """
    route = pinned_route(store, run_id=run_id)
    while ready := frontier(
        route, accepted_attempts(store, run_id=run_id, route=route, blobs=blobs)
    ):
        for route_node_id in ready:
            _run_node(
                store, run_id=run_id, route_node_id=route_node_id, execute=execute
            )
    return route


def _run_node(
    store: Store, *, run_id: str, route_node_id: str, execute: Executor
) -> None:
    reserved = _price()
    outcome = _attempt(
        store,
        run_id=run_id,
        route_node_id=route_node_id,
        reserved=reserved,
        execute=execute,
    )
    if outcome.charge > reserved:
        # Invariant 8: every ceiling refuses before overspend. The reservation
        # is that ceiling for one call, so a charge above it is an overspend
        # that has already happened. Refusing keeps it out of the ledger, and
        # the attempt row keeps its reserved exposure like any other crash.
        raise Refusal(RefusalCode.CHARGE_EXCEEDS_RESERVATION)
    accept(
        store,
        run_id=run_id,
        node_id=BoundaryText.of(route_node_id),
        artifact_sha256=outcome.artifact_sha256,
        charge=outcome.charge,
    )


def _attempt(
    store: Store,
    *,
    run_id: str,
    route_node_id: str,
    reserved: Decimal,
    execute: Executor,
) -> NodeOutcome:
    """Reserve, commit the reservation, then call. In that order, always."""
    reserve(store, run_id=run_id, route_node_id=route_node_id, amount=reserved)
    store.commit()
    return execute(route_node_id)


def _price() -> Decimal:
    """What one node may cost. Reserved before the call, and its ceiling.

    ponytail: one flat price until a provider quotes a real one. The number is
    not the point -- that the reservation and the charge are the same quantity
    is, so a provider cannot bill past what the budget agreed to.
    """
    return Decimal("1.00")
