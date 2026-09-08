"""Profile-scoped routing and exact lineage for Deploy V."""

from __future__ import annotations

from .identity import parse_route_node, require_profile

ACCEPTED = "ACCEPTED"
BLOCKING = frozenset({"REQUIRED", "CONDITIONAL", "QA_GATE"})
SOFT = frozenset({"OPTIONAL", "ADVISORY"})
RUNNABLE = "RUNNABLE"
BLOCKED = "BLOCKED"
COMPLETE = "COMPLETE"
RESTRICTED = "RESTRICTED"


class RouteError(ValueError):
    pass


def dependency_order(edges, preferred):
    """Close mandatory prerequisites, then stably order all selected inputs.

    Optional/advisory inputs constrain order only when selected. Conditional
    prerequisites are enforced by active_incoming when their predicate is true.
    """
    selected = list(dict.fromkeys(preferred))
    for target in selected:
        for edge in edges:
            if edge["target"] == target and edge["type"] in {"REQUIRED", "QA_GATE"}:
                if edge["source"] not in selected:
                    selected.append(edge["source"])
    pending = dict.fromkeys(selected)
    result = []
    while pending:
        ready = next((module for module in pending if not any(
            edge["target"] == module and edge["source"] in pending
            and edge["type"] != "CONDITIONAL" for edge in edges
        )), None)
        if ready is None:
            raise RouteError("dependency cycle among: " + ", ".join(sorted(pending)))
        result.append(ready)
        del pending[ready]
    return result


class Route:
    def __init__(self, catalog: dict, profile_id: str, selection_id: str, module_order=None, research_brief=None) -> None:
        require_profile(profile_id)
        try:
            profile = catalog["profiles"][profile_id]
            pathway = profile["pathways"][selection_id]
        except (KeyError, TypeError) as exc:
            raise RouteError(f"unknown profile/selection: {profile_id}/{selection_id}") from exc
        if pathway.get("profile_id") != profile_id or pathway.get("selection_id") != selection_id:
            raise RouteError("pathway identity does not match its catalog keys")
        self.profile_id = profile_id
        self.selection_id = selection_id
        self.nodes = list(pathway["nodes"])
        self.edges = list(profile["edges"])
        # ponytail: one linked dossier per run; add versioned occurrences only for independent batches.
        self.research_brief = research_brief
        self.research_unresolved = set()
        self.modules = {entry["module_id"]: entry for entry in catalog["modules"]}
        if research_brief and not any(n["module_id"] == "CP-DR" for n in self.nodes):
            extension = profile.get("research_extension", {})
            if extension.get("module_id") != "CP-DR":
                raise RouteError("this profile does not permit linked research")
            self.nodes.append(dict(module_id="CP-DR", module_name="DeepResearch", stage=extension["route_stage"],
                                   route_node_id=f"RN-{profile_id}-{selection_id}-{extension['route_stage']:02d}-CP-DR"))
        self.by_node = {}
        self.by_module = {}
        for index, node in enumerate(self.nodes, start=1):
            route_id = node["route_node_id"]
            parsed = parse_route_node(route_id)
            stage = 99 if research_brief and node["module_id"] == "CP-DR" and node.get("stage") == 99 else index
            if parsed != (profile_id, selection_id, stage, node["module_id"]):
                raise RouteError(f"invalid route occurrence: {route_id}")
            if route_id in self.by_node or node["module_id"] in self.by_module:
                raise RouteError("duplicate route node or module occurrence")
            self.by_node[route_id] = node
            self.by_module[node["module_id"]] = node

        if module_order is not None:
            selected = ["CP-0", *module_order]
            if len(set(selected)) != len(selected):
                raise RouteError("duplicate module in CP-0 plan")
            missing = set(selected) - self.by_module.keys()
            if missing:
                raise RouteError("CP-0 plan contains modules outside the selected pathway: " + ", ".join(sorted(missing)))
            self.nodes = [self.by_module[module] for module in selected]
            self.by_module = {node["module_id"]: node for node in self.nodes}
            self.by_node = {node["route_node_id"]: node for node in self.nodes}
        if research_brief:
            for question in research_brief["questions"]:
                source, target = question["after_module_id"], question["consumer_module_id"]
                terminal_research = target == "NONE" and pathway["terminal_deliverable"] == "CP-DR"
                if (
                    source not in self.by_module
                    or source == "CP-DR"
                    or (not terminal_research and (target not in self.by_module or target in {"CP-0", "CP-DR"}))
                ):
                    raise RouteError("research predecessor and consumer must be distinct selected analytical owners")
                for producer, consumer in ((source, "CP-DR"), ("CP-DR", target)):
                    if consumer != "NONE" and not any(e["source"] == producer and e["target"] == consumer for e in self.edges):
                        self.edges.append(dict(source=producer, target=consumer, type="REQUIRED"))
        ordered = dependency_order(self.edges, list(self.by_module))
        missing = set(ordered) - self.by_module.keys()
        if missing:
            raise RouteError("selected plan omits required prerequisites: " + ", ".join(sorted(missing)))
        # Keep stable occurrence IDs; execution order is dependency order, not ID order.
        self.nodes = [self.by_module[module] for module in ordered]

    def incoming(self, route_node_id: str):
        target = self.by_node[route_node_id]["module_id"]
        for edge in self.edges:
            if edge["target"] == target and (edge["source"] in self.by_module or edge["type"] in BLOCKING):
                yield edge

    def outgoing(self, route_node_id: str):
        source = self.by_node[route_node_id]["module_id"]
        for edge in self.edges:
            if edge["source"] == source and edge["target"] in self.by_module:
                yield edge


def accepted_digest_for(state: dict, route_node_id: str) -> str | None:
    for attempt in state.get("attempts", ()):
        if attempt.get("route_node_id") == route_node_id and attempt.get("status") == ACCEPTED:
            return attempt.get("artifact_sha256")
    return None


def active_incoming(route: Route, route_node_id: str, predicates: dict[str, bool] | None = None):
    predicates = predicates or {}
    for edge in route.incoming(route_node_id):
        if edge["type"] == "CONDITIONAL" and not predicates.get(edge.get("predicate"), False):
            continue
        yield edge


def expected_upstream_digests(
    route: Route,
    route_node_id: str,
    accepted: dict[str, str],
    *,
    predicates: dict[str, bool] | None = None,
    readiness: dict[str, str] | None = None,
) -> dict[str, str]:
    """Return every accepted active direct input and refuse missing blockers."""
    expected: dict[str, str] = {}
    for edge in active_incoming(route, route_node_id, predicates):
        if edge["source"] == "CP-DR" and route.by_node[route_node_id]["module_id"] in route.research_unresolved:
            raise RouteError(f"{route_node_id} has unresolved research questions")
        source = route.by_module.get(edge["source"])
        if source is None:
            raise RouteError(f"{route_node_id} omits blocking upstream {edge['source']}")
        source_node = source["route_node_id"]
        source_digest = accepted.get(source_node)
        if source_digest is None:
            if edge["type"] in BLOCKING or (readiness or {}).get(edge["source"]) in {"READY", "READY_WITH_LIMITATIONS"}:
                raise RouteError(
                    f"{route_node_id} is missing blocking upstream {source_node}"
                )
            continue
        expected[source_node] = source_digest
    return dict(sorted(expected.items()))


def node_states(route: Route, state: dict, *, predicates: dict[str, bool] | None = None) -> dict:
    accepted = {
        node["route_node_id"]: accepted_digest_for(state, node["route_node_id"])
        for node in route.nodes
    }
    result = {}
    for node in route.nodes:
        route_id = node["route_node_id"]
        if accepted[route_id]:
            result[route_id] = {"status": COMPLETE, "reasons": []}
            continue
        blockers, limitations = [], []
        for edge in active_incoming(route, route_id, predicates):
            if edge["source"] == "CP-DR" and node["module_id"] in route.research_unresolved:
                blockers.append("Unresolved research questions")
                continue
            source = route.by_module.get(edge["source"])
            source_id = source["route_node_id"] if source else None
            if accepted.get(source_id):
                continue
            label = route.modules.get(edge["source"], {}).get("display", edge["source"])
            (blockers if edge["type"] in BLOCKING or state.get("source_readiness", {}).get(edge["source"]) in {"READY", "READY_WITH_LIMITATIONS"} else limitations).append(label)
        status = BLOCKED if blockers else RESTRICTED if limitations else RUNNABLE
        result[route_id] = {"status": status, "reasons": blockers or limitations}
    return result


def frontier(route: Route, state: dict, **kwargs) -> list[str]:
    states = node_states(route, state, **kwargs)
    return [
        node["route_node_id"]
        for node in route.nodes
        if states[node["route_node_id"]]["status"] in {RUNNABLE, RESTRICTED}
    ]
