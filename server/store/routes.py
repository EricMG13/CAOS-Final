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
from server.store.events import EventKind, emit


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


def pin_route(
    store: Store, *, run_id: str, resolved: ResolvedRoute, source_set_version: int
) -> str:
    """Pin the plan at the gate -- route and evidence version -- and return the digest.

    Pinning the same plan again is the pin it already has -- recovery replays
    the gate, and that must not be an error. Pinning a *different* route, or the
    same route over a different source-set version, is refused: either would
    mean a run executing something other than what was approved.

    The insert is what serialises this, not a prior `SELECT ... FOR UPDATE`:
    there is no row to lock before the first pin, so two concurrent gate
    replays both found nothing and one collided on `run_routes_pkey` -- a
    vendor constraint name escaping a governed write path, and an identical
    replay turned into an error. `ON CONFLICT DO NOTHING` blocks on the
    conflicting insert instead, so a skipped row means the pin is durably
    there. Selecting the run rather than naming it does the same for the
    foreign key: an unknown run writes nothing instead of raising
    `run_routes_run_id_fkey`. The re-read then says which of the three
    answers a skipped write earned, and only a refused write pays for it.
    """
    if source_set_version <= 0:
        # Refused here rather than by the column's CHECK, which would escape
        # naming the table and the constraint.
        raise Refusal(RefusalCode.SOURCE_SET_EMPTY)
    digest = route_digest(resolved)
    with store.transaction():
        pinned = store.execute(
            "INSERT INTO run_routes"
            " (run_id, route_digest, profile_id, selection_id, resolved,"
            "  source_set_version)"
            " SELECT %s, %s, %s, %s, %s, %s FROM runs WHERE run_id = %s"
            " ON CONFLICT (run_id) DO NOTHING",
            (
                run_id,
                digest,
                resolved.profile_id,
                resolved.selection_id,
                Jsonb(_payload(resolved)),
                source_set_version,
                run_id,
            ),
        )
        if pinned.rowcount == 0:
            existing = store.execute(
                "SELECT route_digest, source_set_version FROM run_routes"
                " WHERE run_id = %s",
                (run_id,),
            ).fetchone()
            if existing is None:
                raise Refusal(RefusalCode.RUN_NOT_FOUND)
            if (str(existing[0]), int(existing[1])) != (digest, source_set_version):
                raise Refusal(RefusalCode.ROUTE_ALREADY_PINNED)
            return digest
        # State and its event in one transaction (SYSTEM_SPEC 2).
        emit(store, run_id=run_id, kind=EventKind.ROUTE_PINNED, route_digest=digest)
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


def pinned_source_set_version(store: Store, *, run_id: str) -> int:
    """The evidence version this run executes over. Refuses an unpinned run."""
    found = store.execute(
        "SELECT source_set_version FROM run_routes WHERE run_id = %s", (run_id,)
    ).fetchone()
    if found is None:
        raise Refusal(RefusalCode.ROUTE_NOT_PINNED)
    return int(found[0])
