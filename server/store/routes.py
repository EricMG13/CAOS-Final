"""Pinning the resolved route, and reading it back.

Invariant 10: the route is resolved once, at the plan gate, and execution reads
only the pin. Resolution being pure makes replay possible; the pin is what makes
it binding. A bundle that changes after the gate must not change what an
already-running run executes, or a completed run stops being explicable.
"""

from __future__ import annotations

import json

from psycopg.types.json import Jsonb

from server.engine.route import Edge, Node, ResolvedRoute, route_digest
from server.refusals import Refusal, RefusalCode
from server.store import Store


def _payload(resolved: ResolvedRoute) -> dict[str, object]:
    return {
        "profile_id": resolved.profile_id,
        "selection_id": resolved.selection_id,
        "nodes": [[n.route_node_id, n.module_id, n.stage] for n in resolved.nodes],
        "edges": [[e.source, e.target, e.type] for e in resolved.edges],
    }


def _rows(payload: object, key: str) -> list[list[object]]:
    """A stored triple list, checked. A pinned row is data like any other."""
    if not isinstance(payload, dict):
        raise Refusal(RefusalCode.ROUTE_NOT_PINNED)
    rows = payload.get(key)
    if not isinstance(rows, list) or not all(
        isinstance(row, list) and len(row) == 3 for row in rows
    ):
        raise Refusal(RefusalCode.ROUTE_NOT_PINNED)
    return rows


def _text(payload: object, key: str) -> str:
    if not isinstance(payload, dict) or not isinstance(payload.get(key), str):
        raise Refusal(RefusalCode.ROUTE_NOT_PINNED)
    return str(payload[key])


def _route(payload: object) -> ResolvedRoute:
    nodes = tuple(
        Node(str(row[0]), str(row[1]), int(str(row[2])))
        for row in _rows(payload, "nodes")
    )
    edges = tuple(
        Edge(str(row[0]), str(row[1]), str(row[2])) for row in _rows(payload, "edges")
    )
    return ResolvedRoute(
        _text(payload, "profile_id"), _text(payload, "selection_id"), nodes, edges
    )


def pin_route(store: Store, *, run_id: str, resolved: ResolvedRoute) -> str:
    """Pin the route at the gate and return its digest.

    Pinning the same route again is the pin it already has -- recovery replays
    the gate, and that must not be an error. Pinning a *different* route is
    refused: it would mean a run executing something other than what was
    approved.
    """
    digest = route_digest(resolved)
    with store.transaction():
        existing = store.execute(
            "SELECT route_digest FROM run_routes WHERE run_id = %s FOR UPDATE",
            (run_id,),
        ).fetchone()
        if existing is not None:
            if existing[0] != digest:
                raise Refusal(RefusalCode.ROUTE_ALREADY_PINNED)
            return digest
        store.execute(
            "INSERT INTO run_routes"
            " (run_id, route_digest, profile_id, selection_id, resolved)"
            " VALUES (%s, %s, %s, %s, %s)",
            (
                run_id,
                digest,
                resolved.profile_id,
                resolved.selection_id,
                Jsonb(_payload(resolved)),
            ),
        )
        # State and its event in one transaction (SYSTEM_SPEC 2).
        store.execute(
            "INSERT INTO run_events (run_id, seq, kind, route_digest)"
            " SELECT %s, coalesce(max(seq), 0) + 1, 'ROUTE_PINNED', %s"
            " FROM run_events WHERE run_id = %s",
            (run_id, digest, run_id),
        )
    return digest


def pinned_route(store: Store, *, run_id: str) -> ResolvedRoute:
    """The route this run executes. Refuses a run that never reached the gate."""
    found = store.execute(
        "SELECT resolved FROM run_routes WHERE run_id = %s", (run_id,)
    ).fetchone()
    if found is None:
        raise Refusal(RefusalCode.ROUTE_NOT_PINNED)
    stored = found[0]
    return _route(stored if isinstance(stored, dict) else json.loads(str(stored)))
