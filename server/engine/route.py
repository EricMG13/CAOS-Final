"""Route resolution: nodes, typed edges, and the states they imply.

The predecessor read `navigation.dependencies` -- 97 untyped pairs the catalog
keeps for display -- so 25 OPTIONAL and 22 ADVISORY edges were enforced as
mandatory, the single QA_GATE did not gate, and RESTRICTED could not occur
(`docs/DECISIONS.md` §2). Nothing here reads that list. Edges come from
`profile["edges"]`, where every one carries a type.

Resolution is pure: same catalog, same pathway, same route, same digest. The
digest is what gets pinned at the plan gate, and execution reads only the pin
(invariant 10).
"""

from __future__ import annotations

import hashlib
import heapq
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from server.refusals import Refusal, RefusalCode


class State(StrEnum):
    """The bundle's words, unchanged (CONTEXT.md)."""

    COMPLETE = "COMPLETE"
    RUNNABLE = "RUNNABLE"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"


# REQUIRED, CONDITIONAL and QA_GATE block. OPTIONAL and ADVISORY are soft until
# the source's readiness is READY or READY_WITH_LIMITATIONS, at which point a
# missing input is a real gap rather than an absent extra.
_BLOCKING = frozenset({"REQUIRED", "CONDITIONAL", "QA_GATE"})
_SOFT = frozenset({"OPTIONAL", "ADVISORY"})
_HARDENING_READINESS = frozenset({"READY", "READY_WITH_LIMITATIONS"})


@dataclass(frozen=True, slots=True)
class Node:
    route_node_id: str
    module_id: str
    stage: int


@dataclass(frozen=True, slots=True)
class Edge:
    source: str
    target: str
    type: str


@dataclass(frozen=True, slots=True)
class ResolvedRoute:
    """A closed node list and a typed edge set. Nothing else decides the route."""

    profile_id: str
    selection_id: str
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]


@dataclass(frozen=True, slots=True)
class Extension:
    """A node the host appends to a pathway it never edits.

    The mechanism the catalog already uses for CP-DR, which rides
    `profile["research_extension"]` at stage 99. `owners` are the modules whose
    artifacts the appended module reads: every one of them becomes a synthesised
    REQUIRED edge, so a pathway missing any owner cannot carry the extension.
    """

    module_id: str
    route_stage: int
    owners: tuple[str, ...]
    model_module_id: str
    model_stage: int


# CP-CF reads CP-1's actuals, CP-2G's drivers and CP-4's covenant terms
# (SYSTEM_SPEC 6.2). CP-MODEL is `route_eligible` but not `navigable` and
# appears in no pathway, so the host places it too -- nothing else can.
MODEL_EXTENSION = Extension(
    module_id="CP-CF",
    route_stage=100,
    owners=("CP-1", "CP-2G", "CP-4"),
    model_module_id="CP-MODEL",
    model_stage=101,
)


@dataclass(frozen=True, slots=True)
class Accepted:
    """One accepted attempt. CP-0's carries the readiness it established."""

    artifact_sha256: str
    readiness: str | None = None


@dataclass(frozen=True, slots=True)
class NodeState:
    """A node's state, and the soft inputs a RESTRICTED node is running without."""

    state: State
    carried: tuple[str, ...] = ()


def resolve_route(
    catalog: dict[str, Any],
    profile_id: str,
    selection_id: str,
    *,
    module_order: tuple[str, ...] | None = None,
    model_extension: bool = False,
) -> ResolvedRoute:
    """The pathway's nodes and the edges between them. Pure: no I/O, no clock."""
    profiles = catalog.get("profiles", {})
    if profile_id not in profiles:
        raise Refusal(RefusalCode.ROUTE_NOT_RESOLVABLE)
    profile = profiles[profile_id]
    pathway = profile.get("pathways", {}).get(selection_id)
    if pathway is None:
        raise Refusal(RefusalCode.ROUTE_NOT_RESOLVABLE)

    declared = [
        Node(
            route_node_id=str(node["route_node_id"]),
            module_id=str(node["module_id"]),
            stage=int(node["stage"]),
        )
        for node in pathway["nodes"]
    ]
    nodes = _narrowed(declared, module_order, profile["edges"])
    by_module = {node.module_id: node.route_node_id for node in nodes}
    edges = [
        Edge(by_module[edge["source"]], by_module[edge["target"]], str(edge["type"]))
        for edge in profile["edges"]
        if edge["source"] in by_module and edge["target"] in by_module
    ]
    if model_extension:
        nodes, edges = _extend(
            (nodes, edges), MODEL_EXTENSION, (profile_id, selection_id), by_module
        )
    pinned = tuple(edges)
    return ResolvedRoute(
        profile_id, selection_id, dependency_order(nodes, pinned), pinned
    )


def _extend(
    graph: tuple[list[Node], list[Edge]],
    extension: Extension,
    pathway: tuple[str, str],
    by_module: dict[str, str],
) -> tuple[list[Node], list[Edge]]:
    """Append the extension's nodes and its synthesised REQUIRED edges.

    A pathway missing any owner is refused here, during resolution and before
    pinning -- never by dropping the edge or running the module without the
    input it reads.
    """
    nodes, edges = graph
    profile_id, selection_id = pathway
    missing = [owner for owner in extension.owners if owner not in by_module]
    if missing:
        raise Refusal(RefusalCode.ROUTE_EXTENSION_INCOMPLETE)

    appended = [
        Node(
            _route_node_id(profile_id, selection_id, stage, module_id),
            module_id,
            stage,
        )
        for module_id, stage in (
            (extension.module_id, extension.route_stage),
            (extension.model_module_id, extension.model_stage),
        )
    ]
    extended = {node.module_id: node.route_node_id for node in appended}
    synthesised = [
        Edge(by_module[owner], extended[extension.module_id], "REQUIRED")
        for owner in extension.owners
    ]
    synthesised.append(
        Edge(
            extended[extension.module_id],
            extended[extension.model_module_id],
            "REQUIRED",
        )
    )
    return [*nodes, *appended], [*edges, *synthesised]


def _route_node_id(
    profile_id: str, selection_id: str, stage: int, module_id: str
) -> str:
    """The catalog's own route-node shape, so an appended node reads like a node."""
    return f"RN-{profile_id}-{selection_id}-{stage:02d}-{module_id}"


def _narrowed(
    declared: list[Node],
    module_order: tuple[str, ...] | None,
    edges: list[dict[str, Any]],
) -> list[Node]:
    """CP-0's plan narrows the pathway; it never adds to it (DECISIONS.md §18).

    Nor does it cut a blocking input out from under a module it keeps (§35):
    the edge set is filtered to the surviving modules afterwards, so a dropped
    REQUIRED source would otherwise leave its target RUNNABLE with nothing to
    read, rather than BLOCKED on what the catalog says it needs.
    """
    if module_order is None:
        return declared
    wanted = set(module_order)
    pathway = {node.module_id for node in declared}
    if not wanted <= pathway:
        raise Refusal(RefusalCode.ROUTE_NOT_RESOLVABLE)
    severed = [
        edge
        for edge in edges
        if edge["type"] in _BLOCKING
        and edge["target"] in wanted
        and edge["source"] in pathway
        and edge["source"] not in wanted
    ]
    if severed:
        raise Refusal(RefusalCode.ROUTE_NOT_RESOLVABLE)
    return [node for node in declared if node.module_id in wanted]


def dependency_order(nodes: list[Node], edges: tuple[Edge, ...]) -> tuple[Node, ...]:
    """Nodes ordered so every edge's source precedes its target.

    Ties break on (stage, route_node_id), so the order is the same on every
    resolution and on every machine -- which is what lets the route digest mean
    anything (invariant 10).
    """
    incoming = {node.route_node_id: 0 for node in nodes}
    outgoing: dict[str, list[str]] = {node.route_node_id: [] for node in nodes}
    for edge in edges:
        incoming[edge.target] += 1
        outgoing[edge.source].append(edge.target)

    by_id = {node.route_node_id: node for node in nodes}
    ready = [
        (n.stage, n.route_node_id) for n in nodes if incoming[n.route_node_id] == 0
    ]
    heapq.heapify(ready)
    ordered: list[Node] = []
    while ready:
        node = by_id[heapq.heappop(ready)[1]]
        ordered.append(node)
        for target in outgoing[node.route_node_id]:
            incoming[target] -= 1
            if incoming[target] == 0:
                heapq.heappush(ready, (by_id[target].stage, target))
    if len(ordered) != len(nodes):
        # A cycle. The catalog is the authority, so this is a bundle defect --
        # but it must never become a silent partial route.
        raise Refusal(RefusalCode.ROUTE_NOT_RESOLVABLE)
    return tuple(ordered)


def _readiness_of(route: ResolvedRoute, accepted: dict[str, Accepted]) -> str | None:
    """The readiness CP-0 established, read from its accepted artifact."""
    for node in route.nodes:
        if node.module_id == "CP-0":
            found = accepted.get(node.route_node_id)
            return found.readiness if found else None
    return None


def node_states(
    route: ResolvedRoute, accepted: dict[str, Accepted]
) -> dict[str, NodeState]:
    """Every node's state, recomputed from the accepted attempts alone."""
    hardened = _readiness_of(route, accepted) in _HARDENING_READINESS
    states: dict[str, NodeState] = {}
    for node in route.nodes:
        if node.route_node_id in accepted:
            states[node.route_node_id] = NodeState(State.COMPLETE)
            continue
        unmet = [
            e
            for e in route.edges
            if e.target == node.route_node_id and e.source not in accepted
        ]
        blocking = [e for e in unmet if e.type in _BLOCKING or hardened]
        carried = tuple(e.source for e in unmet if e.type in _SOFT)
        if blocking:
            states[node.route_node_id] = NodeState(State.BLOCKED, carried)
        elif carried:
            states[node.route_node_id] = NodeState(State.RESTRICTED, carried)
        else:
            states[node.route_node_id] = NodeState(State.RUNNABLE)
    return states


def frontier(route: ResolvedRoute, accepted: dict[str, Accepted]) -> tuple[str, ...]:
    """The nodes that may run now: RUNNABLE plus RESTRICTED, in dependency order."""
    states = node_states(route, accepted)
    return tuple(
        node.route_node_id
        for node in route.nodes
        if states[node.route_node_id].state in {State.RUNNABLE, State.RESTRICTED}
    )


def route_digest(route: ResolvedRoute) -> str:
    """What the plan gate pins. Same route, same digest, on any machine."""
    payload = {
        "profile_id": route.profile_id,
        "selection_id": route.selection_id,
        "nodes": [[n.route_node_id, n.module_id, n.stage] for n in route.nodes],
        "edges": sorted([e.source, e.target, e.type] for e in route.edges),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
