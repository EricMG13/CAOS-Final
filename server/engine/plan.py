"""The plan gate: the one place a route is pinned, and only once approved.

Invariants 5 and 10 meet here. Invariant 10 says the route is resolved once and
digested at the plan gate, and execution reads only the pin. Invariant 5 says a
human gate binds the exact reviewed content. Together they say what this module
does: the route that gets pinned is the route a person read and approved.

Release and pin are one call rather than two. Two calls can disagree -- release
the reviewed plan, pin a different route -- and afterwards nothing in the store
says which plan was read. `approve_plan` opens the transaction that both commit
in, so a refusal takes the pin, the release and the event down together.

Two digests, and each covers what the other cannot. `preview_sha256` is over
the text a person reads: the case, the pathway, the documents, the modules in
the order they will run. `input_fingerprint` is over what that text was
rendered from, and it carries the two things a reader cannot see -- the
source-set version and the route digest. Re-pinning the same documents
allocates a new version whose preview is byte-identical, and approving the
earlier one must not release a run bound to the later one.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from server.boundary_text import BoundaryText
from server.engine.route import ResolvedRoute, route_digest
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.gates import Gate, GateKind, approve_gate, open_gate, released_gate
from server.store.routes import pin_route


@dataclass(frozen=True, slots=True)
class Plan:
    """What a run is asked to approve before it executes anything.

    The evidence it will read and the route it will take. Nothing else is
    decided at the gate, and nothing decided here moves afterwards.
    """

    case_id: BoundaryText
    source_set_version: int
    route: ResolvedRoute


def plan_preview(plan: Plan, members: tuple[str, ...]) -> str:
    """The text a person reads before approving. Deterministic on every machine.

    Module ids rather than route node ids, because this is read by a person and
    a route node id is an internal spelling. The route's exact identity is not
    lost by that -- `plan_gate` puts `route_digest` in the fingerprint, which is
    what the pin is checked against.
    """
    edges = sorted((edge.type, edge.source, edge.target) for edge in plan.route.edges)
    by_node = {node.route_node_id: node.module_id for node in plan.route.nodes}
    return "\n".join(
        [
            f"case {plan.case_id.value}",
            f"profile {plan.route.profile_id}",
            f"pathway {plan.route.selection_id}",
            "evidence",
            *(f"  {digest}" for digest in sorted(members)),
            "route",
            *(f"  {node.stage:03d} {node.module_id}" for node in plan.route.nodes),
            "edges",
            *(f"  {kind} {by_node[a]} -> {by_node[b]}" for kind, a, b in edges),
            "",
        ]
    )


def plan_gate(run_id: str, plan: Plan, members: tuple[str, ...]) -> Gate:
    """The interrupt this plan asks for. Pure: same plan, same gate, anywhere."""
    preview = plan_preview(plan, members).encode("utf-8")
    inputs = json.dumps(
        {
            "case_id": plan.case_id.value,
            "source_set_version": plan.source_set_version,
            "members": sorted(members),
            "route_digest": route_digest(plan.route),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return Gate(
        run_id=run_id,
        kind=GateKind.SOURCE_SET,
        preview_sha256=hashlib.sha256(preview).hexdigest(),
        input_fingerprint=hashlib.sha256(inputs).hexdigest(),
    )


def open_plan_gate(store: Store, *, run_id: str, plan: Plan) -> Gate:
    """Park the run on its plan, and return the gate a person is asked to clear.

    Replaying it is ordinary -- recovery re-runs the gate -- and `open_gate`
    emits nothing when the content has not moved, so a restart does not ask for
    a second approval of the same plan. A decided plan replays as decided:
    the release stands whatever the member list reads now, and a run whose set
    has since lost a source finds that out at the read, not here.
    """
    gate = _current_gate(store, run_id=run_id, plan=plan)
    open_gate(store, gate)
    return gate


def approve_plan(
    store: Store, *, run_id: str, plan: Plan, approver: BoundaryText
) -> str:
    """Release this plan's gate and pin the route it named. Returns the digest.

    One transaction, opened here. `approve_gate` and `pin_route` each open their
    own, which nest as savepoints inside this one, so either both commit or
    neither does -- and the route is pinned only against content this approver
    was shown. A plan that is not the one on screen is refused by the gate's
    own compare-and-set before anything is pinned.

    Idempotent for the same reason both halves are: a replayed release writes
    nothing and a replayed pin is the pin it already has -- including after a
    withdrawal has moved what the member list would say today.
    """
    gate = _current_gate(store, run_id=run_id, plan=plan)
    with store.transaction():
        approve_gate(store, gate, approver=approver)
        return pin_route(store, run_id=run_id, resolved=plan.route)


def _current_gate(store: Store, *, run_id: str, plan: Plan) -> Gate:
    """The decision if there is one, else the ask this plan makes today."""
    released = released_gate(store, run_id=run_id, kind=GateKind.SOURCE_SET)
    return released or plan_gate(run_id, plan, _members(store, plan))


def _members(store: Store, plan: Plan) -> tuple[str, ...]:
    """The digests of the sources this plan is pinned to, in no order.

    No `ORDER BY` on purpose, and no order to rely on: both `plan_preview` and
    `plan_gate` sort what they are given, because a digest that depends on the
    order a join happened to return rows in is a digest that differs between
    two machines reading the same set.

    A version with no members and a version that was never pinned are the same
    answer to a plan: there is no evidence to run against, so nothing to
    approve. So is a version whose every member has been withdrawn: the
    preview is what a run will read, and a withdrawn source is not that, so it
    is left out here -- which is what moves a gate a person is mid-way through
    reviewing onto the documents that remain (invariant 1, checked at this use).
    """
    rows = store.execute(
        "SELECT s.sha256 FROM source_set_members m"
        " JOIN sources s ON s.source_id = m.source_id"
        " WHERE m.case_id = %s AND m.version = %s AND s.withdrawn_at IS NULL",
        (plan.case_id.value, plan.source_set_version),
    ).fetchall()
    if not rows:
        raise Refusal(RefusalCode.SOURCE_SET_EMPTY)
    return tuple(str(digest) for (digest,) in rows)
