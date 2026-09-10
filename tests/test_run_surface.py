"""The first HTTP route: a member's view of a run, behind the identity edge.

`docs/SYSTEM_SPEC.md` §8 and §9, `docs/IA_SPEC.md` §4.5, `docs/DECISIONS.md` §50.
"""

from __future__ import annotations

import inspect
import json
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from conftest import Counter, Served, serve
from pydantic import ValidationError
from starlette.routing import Route

from server.api.app import create_app
from server.api.identity import Environment, Identity, environment_from, identify
from server.api.runs import (
    IO_BUDGET,
    EdgeView,
    GateView,
    NodeView,
    RunState,
    RunView,
    run_view,
)
from server.api.wire import RefusalBody, Wire
from server.boundary_text import BoundaryText
from server.engine.route import Accepted, EdgeType, State, node_states, resolve_route
from server.refusals import RefusalCode
from server.store import Store
from server.store.attempts import accept
from server.store.blobs import BlobStore
from server.store.gates import Gate, GateKind, approve_gate, open_gate
from server.store.members import Standing, grant_membership
from server.store.routes import pin_route
from server.store.runs import start_run

CATALOG = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "vendor/deploy-v/skills/cp-os-credit-os/references"
        / "CREDIT_OS_V_MODULE_CATALOG_v2.json"
    ).read_text(encoding="utf-8")
)
CASE = BoundaryText.of("acme")
OTHER_CASE = BoundaryText.of("zenith")
ANA = BoundaryText.of("ana")
PM = BoundaryText.of("pm")
ROUTE = resolve_route(CATALOG, "FULL_CREDIT_32", "FULL_CREDIT_ASSESSMENT")
NOT_FOUND = {"code": "RUN_NOT_FOUND"}


def _grant(
    store: Store,
    standing: Standing,
    member: BoundaryText = ANA,
    case: BoundaryText = CASE,
) -> None:
    grant_membership(store, case_id=case, member_id=member, standing=standing, actor=PM)


def _pinned(store: Store) -> str:
    run_id = start_run(store, case_id=CASE)
    pin_route(store, run_id=run_id, resolved=ROUTE, source_set_version=1)
    return run_id


def _get(
    store: Store,
    blobs: BlobStore,
    run_id: str,
    headers: dict[str, str] | None,
    environment: Environment = Environment.DEVELOPMENT,
) -> Served:
    app = create_app(store, blobs=blobs, environment=environment)
    return serve(app, f"/api/runs/{run_id}", (headers or {}).items())


def _as(member: str) -> dict[str, str]:
    return {"X-Caos-Member": member}


def _wire_models(base: type[Wire]) -> set[type[Wire]]:
    """Every model that extends `Wire`, however deeply."""
    kin = set(base.__subclasses__())
    return kin.union(*(_wire_models(one) for one in kin)) if kin else kin


def _accept_cp0(store: Store, blobs: BlobStore, run_id: str) -> str:
    """CP-0 accepted as READY, so soft edges harden; returns the artifact digest."""
    summary = {"runtime_output": {"readiness_summary": {"overall_readiness": "READY"}}}
    artifact = blobs.put(json.dumps(summary).encode())
    cp0 = next(n.route_node_id for n in ROUTE.nodes if n.module_id == "CP-0")
    node = BoundaryText.of(cp0)
    accept(
        store, run_id=run_id, node_id=node, artifact_sha256=artifact, charge=Decimal(0)
    )
    return artifact


def test_unauthorised_case_is_private_404(store: Store, blobs: BlobStore) -> None:
    """Four strangers, one answer: nothing about the run, not even that it is."""
    run_id = _pinned(store)
    _grant(store, Standing.READER, member=BoundaryText.of("bob"))
    answers = {
        "no standing on the case": _get(store, blobs, run_id, _as("ana")),
        "a run that does not exist": _get(store, blobs, str(uuid.uuid4()), _as("bob")),
        "a run id that is not one": _get(store, blobs, "not-a-run", _as("bob")),
        "no identity at all": _get(store, blobs, run_id, None),
    }
    for who, served in answers.items():
        assert served.status == 404, who
        assert json.loads(served.body) == NOT_FOUND, who
    assert len({served.body for served in answers.values()}) == 1, "one body"


def test_production_never_trusts_role_header(store: Store, blobs: BlobStore) -> None:
    run_id = _pinned(store)
    _grant(store, Standing.READER)
    production = Environment.PRODUCTION

    forged = _get(store, blobs, run_id, _as("ana"), production)
    assert forged.status == 404, "the development header is not read in production"
    asserted = _get(store, blobs, run_id, {"X-Forwarded-User": "ana"}, production)
    assert asserted.status == 200, "what the OIDC edge asserted is"
    both = {"X-Caos-Member": "ana", "X-Forwarded-User": "bob"}
    assert _get(store, blobs, run_id, both, production).status == 404, "never escalates"

    development = _get(store, blobs, run_id, {"X-Forwarded-User": "ana"})
    assert development.status == 404, "and development trusts only its own header"
    assert _get(store, blobs, run_id, _as("ana")).status == 200
    # A proxy that appends its assertion behind a client's copy leaves two
    # values, the client's first. Two values are no identity.
    app = create_app(store, blobs=blobs, environment=production)
    twice = [("X-Forwarded-User", "ana"), ("X-Forwarded-User", "mallory")]
    assert serve(app, f"/api/runs/{run_id}", twice).status == 404


def test_identity_is_the_edge_s_word_in_production_and_the_header_s_in_dev() -> None:
    headers = {
        "x-caos-member": "ana",
        "x-caos-groups": "caos-admin",
        "x-forwarded-user": "bob",
        "x-forwarded-groups": "analysts,approvers",
    }
    pairs = list(headers.items())
    assert identify(pairs, environment=Environment.PRODUCTION) == Identity(
        BoundaryText.of("bob"), frozenset({"analysts", "approvers"})
    )
    assert identify(pairs, environment=Environment.DEVELOPMENT) == Identity(
        BoundaryText.of("ana"), frozenset({"caos-admin"})
    )
    assert identify([], environment=Environment.PRODUCTION) is None

    # h11 hands header bytes over and the framework decodes them latin-1, so a
    # name reaches `identify` as mojibake and must be read back as UTF-8 -- or
    # a member the store granted is a stranger for as long as they are called
    # that. A refused name is then no identity rather than an error.
    def sent(name: str) -> list[tuple[str, str]]:
        return [("X-Forwarded-User", name.encode("utf-8").decode("latin-1"))]

    assert identify(sent("josé"), environment=Environment.PRODUCTION) == Identity(
        BoundaryText.of("josé"), frozenset()
    )
    assert identify(sent("a\u202eb"), environment=Environment.PRODUCTION) is None


def test_an_unset_environment_is_production() -> None:
    assert environment_from({}) is Environment.PRODUCTION
    assert environment_from({"CAOS_ENV": "development"}) is Environment.DEVELOPMENT
    with pytest.raises(ValueError, match="staging"):
        environment_from({"CAOS_ENV": "staging"})


@pytest.mark.parametrize(
    ("actor", "status"),
    [
        ("anonymous", 404),
        ("stranger", 404),
        (Standing.READER, 200),
        (Standing.WRITER, 200),
        (Standing.APPROVER, 200),
        (Standing.ADMIN, 200),
    ],
)
def test_the_actor_matrix_for_the_run_view(
    store: Store, blobs: BlobStore, actor: Standing | str, status: int
) -> None:
    run_id = _pinned(store)
    start_run(store, case_id=OTHER_CASE)
    if actor == "stranger":
        _grant(store, Standing.ADMIN, case=OTHER_CASE)
    elif isinstance(actor, Standing):
        _grant(store, actor)
    headers = None if actor == "anonymous" else _as("ana")
    assert _get(store, blobs, run_id, headers).status == status


def test_the_run_view_serves_node_states_with_their_reasons(
    store: Store, blobs: BlobStore
) -> None:
    run_id = _pinned(store)
    _grant(store, Standing.APPROVER)
    by_module = {n.module_id: n.route_node_id for n in ROUTE.nodes}
    artifact = _accept_cp0(store, blobs, run_id)
    gate = Gate(run_id, GateKind.SOURCE_SET, "a" * 64, "b" * 64)
    open_gate(store, gate)

    served = _get(store, blobs, run_id, _as("ana"))
    assert served.status == 200
    view = RunView.model_validate_json(served.body)
    assert (view.run_id, view.case_id, view.state) == (run_id, "acme", RunState.RUNNING)
    assert view.gates == [GateView(kind=GateKind.SOURCE_SET, approved_by=None)]

    nodes = {node.module_id: node for node in view.nodes}
    assert [n.route_node_id for n in view.nodes] == [
        n.route_node_id for n in ROUTE.nodes
    ]
    expected = node_states(ROUTE, {by_module["CP-0"]: Accepted(artifact, "READY")})
    assert {n.route_node_id: n.state for n in view.nodes} == {
        node_id: state.state for node_id, state in expected.items()
    }
    assert nodes["CP-0"].artifact_sha256 == artifact
    cp1 = nodes["CP-1"]
    assert (cp1.state, cp1.blocked_on, cp1.carried, cp1.artifact_sha256) == (
        State.RUNNABLE,
        [],
        [],
        None,
    )
    # Which upstream and which edge type -- including the OPTIONAL edge CP-0's
    # readiness hardened, which is why CP-1D is BLOCKED and not RESTRICTED.
    assert nodes["CP-1D"].state is State.BLOCKED
    assert nodes["CP-1D"].blocked_on == [
        EdgeView(upstream="CP-1", type=EdgeType.REQUIRED),
        EdgeView(upstream="CP-1B", type=EdgeType.OPTIONAL),
    ]
    assert nodes["CP-1D"].carried == ["CP-1B"]
    # The one QA_GATE reads as a gate: the edge type is on the wire.
    assert EdgeView(upstream="CP-5", type=EdgeType.QA_GATE) in nodes["CP-6"].blocked_on

    approve_gate(store, gate, approver=ANA)
    decided = RunView.model_validate_json(_get(store, blobs, run_id, _as("ana")).body)
    assert decided.gates == [GateView(kind=GateKind.SOURCE_SET, approved_by="ana")]


def test_a_run_before_its_gate_has_no_route(store: Store, blobs: BlobStore) -> None:
    run_id = start_run(store, case_id=CASE)
    _grant(store, Standing.READER)
    view = RunView.model_validate_json(_get(store, blobs, run_id, _as("ana")).body)
    assert (view.route_digest, view.nodes, view.gates) == (None, [], [])


def test_io_budget_run_view(store: Store, blobs: BlobStore, count_io: Counter) -> None:
    run_id = _pinned(store)
    _grant(store, Standing.READER)
    open_gate(store, Gate(run_id, GateKind.SOURCE_SET, "a" * 64, "b" * 64))
    _accept_cp0(store, blobs, run_id)
    identity = identify(_as("ana").items(), environment=Environment.DEVELOPMENT)

    with count_io(store) as tally:
        run_view(store, blobs=blobs, identity=identity, run_id=run_id)

    assert tally.statements == IO_BUDGET
    assert tally.rows <= 4, "a nineteen-node route is one row"


def test_every_route_serves_a_named_model_with_a_pinned_key_set(
    store: Store, blobs: BlobStore
) -> None:
    app = create_app(store, blobs=blobs, environment=Environment.DEVELOPMENT)
    served = {r.path: r for r in app.routes if isinstance(r, Route)}
    # SSE is `docs/SYSTEM_SPEC.md` §9's one carve-out from a named model, and
    # it is named here rather than left to what a route happens to return.
    tail = "/api/runs/{run_id}/events"
    assert set(served) == {"/api/runs/{run_id}", tail}
    for path, route in served.items():
        # The one connection is safe only while no request leaves the loop
        # for a threadpool: dropping `async` would put two on one of it.
        assert inspect.iscoroutinefunction(route.endpoint), path
        model = getattr(route, "response_model", None)
        if path == tail:
            assert model is None, "the carve-out serves no model, and no other"
            continue
        assert isinstance(model, type) and issubclass(model, Wire), path

    assert Wire.model_config["extra"] == "forbid"
    pinned: dict[type[Wire], str] = {
        RunView: "run_id case_id state route_digest nodes gates",
        NodeView: "route_node_id module_id stage state blocked_on carried"
        " artifact_sha256",
        EdgeView: "upstream type",
        GateView: "kind approved_by",
        RefusalBody: "code",
    }
    for model, keys in pinned.items():
        assert set(model.model_fields) == set(keys.split()), model.__name__
    # Every model, not only every route's: one nested inside a served model
    # would otherwise ship with no pinned key set and this test still green.
    assert _wire_models(Wire) == set(pinned)
    with pytest.raises(ValidationError):
        RefusalBody.model_validate({"code": RefusalCode.RUN_NOT_FOUND, "detail": "x"})
