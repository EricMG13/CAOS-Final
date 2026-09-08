"""CP-CF rides a host-declared extension, and waits for every owner it reads.

`SYSTEM_SPEC.md` §6.2: CP-CF is appended by a host-declared model extension
mirroring `profile["research_extension"]`, with synthesised REQUIRED edges from
CP-1, CP-2G and CP-4 -- every artifact owner it reads, including the covenant
terms. CP-2G completing alone does not release it. No pathway node list is
edited (`docs/DECISIONS.md` §6), and the extension is part of the resolved route
that gets pinned, so replay is unaffected.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from server.engine.route import (
    MODEL_EXTENSION,
    Accepted,
    Extension,
    ResolvedRoute,
    State,
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
# CP-1 and CP-4, but no CP-2G.
NO_DRIVERS = "COVENANT_REFINANCING"


def _extended() -> ResolvedRoute:
    return resolve_route(CATALOG, FULL, ASSESSMENT, model_extension=True)


def _node(route: ResolvedRoute, module_id: str) -> str:
    return next(n.route_node_id for n in route.nodes if n.module_id == module_id)


def _accept(route: ResolvedRoute, *module_ids: str) -> dict[str, Accepted]:
    return {
        _node(route, m): Accepted(artifact_sha256=f"{i:064d}", readiness="READY")
        for i, m in enumerate(("CP-0", *module_ids))
    }


def test_the_extension_appends_cp_cf_and_cp_model_without_editing_the_pathway() -> None:
    plain = resolve_route(CATALOG, FULL, ASSESSMENT)
    extended = _extended()
    assert [n.module_id for n in plain.nodes] == [
        n.module_id for n in extended.nodes if n.module_id not in {"CP-CF", "CP-MODEL"}
    ]
    added = [n for n in extended.nodes if n.module_id in {"CP-CF", "CP-MODEL"}]
    assert [n.module_id for n in added] == ["CP-CF", "CP-MODEL"]
    assert [n.stage for n in added] == [
        MODEL_EXTENSION.route_stage,
        MODEL_EXTENSION.model_stage,
    ]


def test_cp_cf_waits_for_all_required_owners() -> None:
    route = _extended()
    cp_cf = _node(route, "CP-CF")

    # CP-2G alone must not release it: the covenant terms and the actuals are
    # owners too, and a forecast built without them is built on nothing.
    assert node_states(route, _accept(route, "CP-2G"))[cp_cf].state is State.BLOCKED
    assert (
        node_states(route, _accept(route, "CP-1", "CP-2G"))[cp_cf].state
        is State.BLOCKED
    )
    assert (
        node_states(route, _accept(route, "CP-2G", "CP-4"))[cp_cf].state
        is State.BLOCKED
    )
    assert (
        node_states(route, _accept(route, "CP-1", "CP-2G", "CP-4"))[cp_cf].state
        is State.RUNNABLE
    )


def test_cp_model_waits_for_cp_cf() -> None:
    route = _extended()
    ready = _accept(route, "CP-1", "CP-2G", "CP-4")
    assert node_states(route, ready)[_node(route, "CP-MODEL")].state is State.BLOCKED
    with_cf = ready | _accept(route, "CP-1", "CP-2G", "CP-4", "CP-CF")
    assert node_states(route, with_cf)[_node(route, "CP-MODEL")].state is State.RUNNABLE


def test_model_extension_refuses_missing_owner() -> None:
    # An extended route missing a required owner is refused during resolution,
    # before pinning -- never by dropping the edge or running without the input.
    with pytest.raises(Refusal) as caught:
        resolve_route(CATALOG, FULL, NO_DRIVERS, model_extension=True)
    assert caught.value.code is RefusalCode.ROUTE_EXTENSION_INCOMPLETE

    # The same pathway resolves fine without the extension.
    assert resolve_route(CATALOG, FULL, NO_DRIVERS).nodes


def test_the_extension_changes_the_pinned_digest() -> None:
    assert route_digest(_extended()) != route_digest(
        resolve_route(CATALOG, FULL, ASSESSMENT)
    )


def test_the_extension_declares_every_owner_cp_cf_reads() -> None:
    # SYSTEM_SPEC 6.2, as the adversarial review corrected it: CP-2G completing
    # alone does not release CP-CF, because it also reads CP-1's actuals and
    # CP-4's covenant terms. The declaration is the contract.
    assert isinstance(MODEL_EXTENSION, Extension)
    assert MODEL_EXTENSION.owners == ("CP-1", "CP-2G", "CP-4")
    assert MODEL_EXTENSION.module_id == "CP-CF"
    assert MODEL_EXTENSION.model_module_id == "CP-MODEL"
    assert MODEL_EXTENSION.route_stage < MODEL_EXTENSION.model_stage


def test_every_synthesised_edge_is_required() -> None:
    route = _extended()
    appended = {_node(route, "CP-CF"), _node(route, "CP-MODEL")}
    synthesised = [e for e in route.edges if e.target in appended]
    assert len(synthesised) == len(MODEL_EXTENSION.owners) + 1
    assert {e.type for e in synthesised} == {"REQUIRED"}
