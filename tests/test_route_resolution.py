"""Route resolution: the phase the predecessor got wrong.

It read `navigation.dependencies` -- 97 untyped pairs meant for display -- so 25
OPTIONAL and 22 ADVISORY edges were enforced as mandatory, the single QA_GATE
did not gate, and RESTRICTED could not occur (`docs/DECISIONS.md` §2). Every
test here runs against the real vendored catalog, because a synthetic profile
would have proved the predecessor correct too.

Readiness is not a parameter: it is read from CP-0's accepted artifact, in the
same attempt ledger `node_states` already walks (`docs/DECISIONS.md` §18).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from server.engine.route import (
    _BLOCKING,
    _SOFT,
    Accepted,
    Edge,
    EdgeType,
    Node,
    NodeState,
    ResolvedRoute,
    State,
    _readiness_of,
    dependency_order,
    frontier,
    node_states,
    resolve_route,
    route_digest,
)
from server.refusals import Refusal, RefusalCode

CATALOG = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "vendor/deploy-v/skills/cp-os-credit-os/references"
        / "CREDIT_OS_V_MODULE_CATALOG_v2.json"
    ).read_text(encoding="utf-8")
)
FULL = "FULL_CREDIT_32"
ASSESSMENT = "FULL_CREDIT_ASSESSMENT"


@pytest.fixture(scope="module")
def route() -> ResolvedRoute:
    return resolve_route(CATALOG, FULL, ASSESSMENT)


def _node(route: ResolvedRoute, module_id: str) -> str:
    return next(n.route_node_id for n in route.nodes if n.module_id == module_id)


def _accept(
    route: ResolvedRoute, *module_ids: str, readiness: str | None = None
) -> dict[str, Accepted]:
    return {
        _node(route, module_id): Accepted(
            artifact_sha256=f"{i:064d}",
            readiness=readiness if module_id == "CP-0" else None,
        )
        for i, module_id in enumerate(module_ids)
    }


def test_the_route_is_the_pathway_the_catalog_declares(route: ResolvedRoute) -> None:
    assert [n.module_id for n in route.nodes][:3] == ["CP-0", "CP-1", "CP-1A"]
    assert len(route.nodes) == 19


def test_dependency_order_puts_every_edge_source_before_its_target(
    route: ResolvedRoute,
) -> None:
    ordered = dependency_order(list(route.nodes), route.edges)
    order = {node.route_node_id: i for i, node in enumerate(ordered)}
    assert all(order[edge.source] < order[edge.target] for edge in route.edges)
    assert ordered == route.nodes, "a resolved route is already in dependency order"


def test_qa_gate_blocks_cp6_until_cp5_accepted(route: ResolvedRoute) -> None:
    # The catalog declares exactly one QA_GATE edge, CP-5 -> CP-6, and the
    # predecessor's untyped read made it not gate at all.
    everything_but = [
        n.module_id for n in route.nodes if n.module_id not in {"CP-5", "CP-6"}
    ]
    accepted = _accept(route, *everything_but, readiness="READY")
    assert node_states(route, accepted)[_node(route, "CP-6")].state is State.BLOCKED

    accepted |= _accept(route, "CP-5")
    assert node_states(route, accepted)[_node(route, "CP-6")].state is State.RUNNABLE


def test_optional_edge_does_not_block(route: ResolvedRoute) -> None:
    # CP-0 accepted, nothing else. Every node whose only unmet incoming edges are
    # OPTIONAL or ADVISORY runs, carrying the limitation.
    states = node_states(route, _accept(route, "CP-0", readiness="BLOCKED"))
    soft_only = [
        target
        for target in {e.target for e in route.edges}
        if all(
            e.type in {"OPTIONAL", "ADVISORY"}
            for e in route.edges
            if e.target == target and e.source != _node(route, "CP-0")
        )
        and any(e.target == target for e in route.edges)
    ]
    assert soft_only, "the catalog has no soft-only target to prove this with"
    assert all(states[target].state is not State.BLOCKED for target in soft_only)


def test_optional_edge_blocks_when_source_ready(route: ResolvedRoute) -> None:
    # The same node, the same accepted set -- only readiness differs.
    ready = node_states(route, _accept(route, "CP-0", readiness="READY"))
    not_ready = node_states(route, _accept(route, "CP-0", readiness="BLOCKED"))
    softened = [
        node_id
        for node_id, state in not_ready.items()
        if state.state is State.RESTRICTED
    ]
    assert softened, "no RESTRICTED node to harden"
    assert all(ready[node_id].state is State.BLOCKED for node_id in softened)


def test_restricted_node_runs_and_carries_limitation(route: ResolvedRoute) -> None:
    # RESTRICTED exists only while readiness has not hardened the soft edges:
    # READY and READY_WITH_LIMITATIONS both turn a missing optional input into a
    # real gap. The predecessor could never reach this state at all.
    accepted = _accept(route, "CP-0", readiness=None)
    states = node_states(route, accepted)
    restricted = [n for n, s in states.items() if s.state is State.RESTRICTED]
    assert restricted, "no RESTRICTED node: soft edges are being enforced"

    runnable_now = frontier(route, accepted)
    for node_id in restricted:
        assert node_id in runnable_now, "a RESTRICTED node runs"
        assert states[node_id].carried, "and names what it is running without"


def test_resolved_route_is_pinned_and_replays_identically() -> None:
    once = resolve_route(CATALOG, FULL, ASSESSMENT)
    twice = resolve_route(CATALOG, FULL, ASSESSMENT)
    assert route_digest(once) == route_digest(twice)
    assert route_digest(once) != route_digest(
        resolve_route(CATALOG, FULL, "PORTFOLIO_DECISION")
    )


def test_resolution_never_reads_navigation_dependencies() -> None:
    # The predecessor's defect, made impossible to repeat by accident: the
    # untyped display list is removed from the catalog and resolution is
    # unchanged, because it was never an input.
    without = json.loads(json.dumps(CATALOG))
    del without["navigation"]["dependencies"]
    assert route_digest(resolve_route(without, FULL, ASSESSMENT)) == route_digest(
        resolve_route(CATALOG, FULL, ASSESSMENT)
    )


def test_readiness_of_reads_cp0s_artifact_and_nothing_else(
    route: ResolvedRoute,
) -> None:
    # DECISIONS.md 18: readiness is not a parameter. It comes from the accepted
    # CP-0 attempt, so recovery recomputes it and has nothing to restore.
    assert _readiness_of(route, {}) is None
    assert _readiness_of(route, _accept(route, "CP-0", readiness="READY")) == "READY"
    # An accepted CP-1 says nothing about readiness.
    assert _readiness_of(route, _accept(route, "CP-1", readiness="READY")) is None


def test_a_resolved_route_is_a_closed_node_list_and_typed_edge_set(
    route: ResolvedRoute,
) -> None:
    assert isinstance(route, ResolvedRoute)
    assert route.nodes and all(isinstance(node, Node) for node in route.nodes)
    known = {node.route_node_id for node in route.nodes}
    assert all({e.source, e.target} <= known for e in route.edges), (
        "an edge may not name a node outside the route"
    )
    assert {e.type for e in route.edges} <= _BLOCKING | _SOFT


def test_node_state_carries_only_the_soft_edges_it_is_missing(
    route: ResolvedRoute,
) -> None:
    states = node_states(route, _accept(route, "CP-0", readiness=None))
    for node_id, state in states.items():
        carried = set(state.carried)
        soft_sources = {
            e.source for e in route.edges if e.target == node_id and e.type in _SOFT
        }
        assert carried <= soft_sources
        assert isinstance(state, NodeState)


def test_every_edge_is_typed(route: ResolvedRoute) -> None:
    # The whole point: the predecessor read untyped pairs. Every Edge carries
    # the type the catalog gave it, and nothing constructs one without.
    assert all(isinstance(e, Edge) and e.type for e in route.edges)


def test_a_plan_cannot_narrow_away_an_input_a_kept_node_requires() -> None:
    # Narrowing filtered the edge set to the surviving modules, so keeping CP-2
    # and dropping CP-1 -- which CP-2 REQUIRES -- silently produced a CP-2 that
    # was RUNNABLE with nothing to read. A REQUIRED edge into a kept node is a
    # constraint on the plan, not a line the plan may delete.
    with pytest.raises(Refusal) as caught:
        resolve_route(CATALOG, FULL, ASSESSMENT, module_order=("CP-0", "CP-2"))
    assert caught.value.code is RefusalCode.ROUTE_NOT_RESOLVABLE

    kept = resolve_route(
        CATALOG, FULL, ASSESSMENT, module_order=("CP-0", "CP-1", "CP-2")
    )
    assert [n.module_id for n in kept.nodes] == ["CP-0", "CP-1", "CP-2"]
    assert {(e.source, e.target) for e in kept.edges if e.type == "REQUIRED"} >= {
        (kept.nodes[1].route_node_id, kept.nodes[2].route_node_id)
    }


def test_a_pathway_the_catalog_does_not_have_is_refused() -> None:
    with pytest.raises(Refusal) as caught:
        resolve_route(CATALOG, FULL, "NO_SUCH_PATHWAY")
    assert caught.value.code is RefusalCode.ROUTE_NOT_RESOLVABLE


def test_cp0s_plan_narrows_the_pathway_and_never_adds_to_it(
    route: ResolvedRoute,
) -> None:
    narrowed = resolve_route(
        CATALOG, FULL, ASSESSMENT, module_order=("CP-0", "CP-1", "CP-5")
    )
    assert [n.module_id for n in narrowed.nodes] == ["CP-0", "CP-1", "CP-5"]
    with pytest.raises(Refusal):
        resolve_route(CATALOG, FULL, ASSESSMENT, module_order=("CP-0", "CP-MEMO"))


def test_a_blocked_node_names_the_edges_it_waits_on(route: ResolvedRoute) -> None:
    # The run view serves the reason beside the state (IA_SPEC 4.5): which
    # upstream, which edge type. A RUNNABLE node waits on nothing.
    cp0, cp1, cp1b, cp1d = (_node(route, m) for m in ("CP-0", "CP-1", "CP-1B", "CP-1D"))
    states = node_states(route, {})
    assert states[cp0].blocked_on == ()
    assert states[cp1b].blocked_on == (
        Edge(cp0, cp1b, EdgeType.REQUIRED),
        Edge(cp1, cp1b, EdgeType.REQUIRED),
    )
    # A soft edge hardened by CP-0's readiness is a reason too, and the node
    # still names it as carried, so a reader can tell the two apart.
    hardened = node_states(route, _accept(route, "CP-0", readiness="READY"))[cp1d]
    soft = node_states(route, _accept(route, "CP-0", readiness="BLOCKED"))[cp1d]
    assert Edge(cp1b, cp1d, EdgeType.OPTIONAL) in hardened.blocked_on
    assert Edge(cp1b, cp1d, EdgeType.OPTIONAL) not in soft.blocked_on
    assert hardened.carried == soft.carried == (cp1b,)
