"""A member's view of a run (`docs/IA_SPEC.md` §4.5): every node's state with
its reason -- which upstream, which edge type -- recomputed from the accepted
attempts as the loop recomputes it, and the gates the run is parked on."""

from __future__ import annotations

from enum import StrEnum

from server.api.identity import Identity
from server.api.wire import Wire
from server.digests import checked_uuid
from server.engine.loop import accepted_attempts
from server.engine.route import (
    EdgeType,
    ResolvedRoute,
    State,
    node_states,
    route_digest,
)
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.blobs import BlobStore
from server.store.gates import GateKind
from server.store.routes import pinned_route

# Store round-trips one view may cost (test_io_budget_run_view): the run this
# member may see, the pin, the artifacts, the gates. States are computed.
IO_BUDGET = 4


class RunState(StrEnum):
    """The `runs.state` CHECK, spelled for the wire."""

    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class EdgeView(Wire):
    """One reason a node waits: the upstream module and the edge's type."""

    upstream: str
    type: EdgeType


class NodeView(Wire):
    route_node_id: str
    module_id: str
    stage: int
    state: State
    blocked_on: list[EdgeView]
    carried: list[str]
    artifact_sha256: str | None


class GateView(Wire):
    """An interrupt the run is parked on, and who released it if anyone has."""

    kind: GateKind
    approved_by: str | None


class RunView(Wire):
    run_id: str
    case_id: str
    state: RunState
    route_digest: str | None
    nodes: list[NodeView]
    gates: list[GateView]


def run_view(
    store: Store, *, blobs: BlobStore, identity: Identity | None, run_id: str
) -> RunView:
    """The run as this member may see it, or a refusal that says nothing.

    One statement asks whether this is a run on a case this person is on, and
    answers with one row or none, so an outsider cannot tell an unknown run
    from one they hold no standing on (§8). A malformed id is refused before
    the store sees it, by the same code.
    """
    if identity is None:
        raise Refusal(RefusalCode.STANDING_INSUFFICIENT)
    run_id = checked_uuid(run_id, refusal=RefusalCode.RUN_NOT_FOUND)
    with store.transaction():
        found = store.execute(
            "SELECT r.case_id, r.state FROM runs r"
            " JOIN case_members m ON m.case_id = r.case_id"
            " WHERE r.run_id = %s AND m.member_id = %s",
            (run_id, identity.member_id.value),
        ).fetchone()
        if found is None:
            raise Refusal(RefusalCode.RUN_NOT_FOUND)
        case_id, state = found
        route = _pinned(store, run_id)
        nodes = _nodes(store, run_id=run_id, route=route, blobs=blobs) if route else []
        gates = _gates(store, run_id)
    return RunView(
        run_id=run_id,
        case_id=str(case_id),
        state=RunState(str(state)),
        route_digest=route_digest(route) if route else None,
        nodes=nodes,
        gates=gates,
    )


def _pinned(store: Store, run_id: str) -> ResolvedRoute | None:
    """The pinned route, or None for a run that has not reached the gate."""
    try:
        return pinned_route(store, run_id=run_id)
    except Refusal as refused:
        if refused.code is not RefusalCode.ROUTE_NOT_PINNED:
            raise
    # ponytail: a pin the store wrote and cannot read back also reads as no pin;
    # give pinned_route a second code when anything but the store can write one.
    return None


def _nodes(
    store: Store, *, run_id: str, route: ResolvedRoute, blobs: BlobStore
) -> list[NodeView]:
    accepted = accepted_attempts(store, run_id=run_id, route=route, blobs=blobs)
    states = node_states(route, accepted)
    module_of = {node.route_node_id: node.module_id for node in route.nodes}
    views: list[NodeView] = []
    for node in route.nodes:
        state, artifact = states[node.route_node_id], accepted.get(node.route_node_id)
        views.append(
            NodeView(
                route_node_id=node.route_node_id,
                module_id=node.module_id,
                stage=node.stage,
                state=state.state,
                blocked_on=[
                    EdgeView(upstream=module_of[e.source], type=EdgeType(e.type))
                    for e in state.blocked_on
                ],
                carried=[module_of[c] for c in state.carried],
                artifact_sha256=artifact.artifact_sha256 if artifact else None,
            )
        )
    return views


def _gates(store: Store, run_id: str) -> list[GateView]:
    opened = store.execute(
        "SELECT g.kind, a.approved_by FROM run_gates g"
        " LEFT JOIN run_gate_approvals a ON a.run_id = g.run_id AND a.kind = g.kind"
        " WHERE g.run_id = %s ORDER BY g.kind",
        (run_id,),
    ).fetchall()
    return [
        GateView(kind=GateKind(str(kind)), approved_by=None if by is None else str(by))
        for kind, by in opened
    ]
