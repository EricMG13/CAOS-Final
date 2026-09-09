"""The plan gate: the one place a route is pinned, and only once approved.

Invariants 5 and 10 meet here. The route is resolved once and pinned at the
plan gate (10), and what pins it is a person approving the exact content they
were shown (5). Those are one operation rather than two, because a release and
a separate pin can disagree -- approve plan A, pin plan B -- and nothing in the
store would afterwards say which plan was read.

The preview is what a person reads: the case, the pathway, the documents, and
the modules in the order they will run. The fingerprint is what those were
rendered from, and it carries the two things a reader cannot see -- the
source-set version and the route digest. Re-pinning the same documents
allocates a new version whose preview is identical, and approving the old one
must not release the new one.
"""

from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from server.boundary_text import BoundaryText
from server.engine.plan import (
    Plan,
    approve_plan,
    open_plan_gate,
    plan_gate,
    plan_preview,
)
from server.engine.route import resolve_route, route_digest
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.events import EventKind
from server.store.gates import GateKind, gate_released
from server.store.members import Standing, grant_membership
from server.store.routes import pin_route, pinned_route
from server.store.runs import start_run
from server.store.source_sets import pin_source_set
from server.store.sources import Block, SourceDocument, Token, admit_pack

CATALOG = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "vendor/deploy-v/skills/cp-os-credit-os/references"
        / "CREDIT_OS_V_MODULE_CATALOG_v2.json"
    ).read_text(encoding="utf-8")
)
FULL = "FULL_CREDIT_32"
ASSESSMENT = "FULL_CREDIT_ASSESSMENT"
PORTFOLIO = "PORTFOLIO_DECISION"
CASE = BoundaryText.of("acme")
APPROVER = BoundaryText.of("ana")


def _document(digest: str) -> SourceDocument:
    text = "Net leverage was 4.2x"
    return SourceDocument(
        sha256=digest,
        tokens=(
            Token(
                page=1,
                region_id=1,
                line_id=1,
                ordinal=0,
                text=text,
                x0=Decimal(72),
                y0=Decimal(700),
                x1=Decimal(120),
                y1=Decimal(712),
            ),
        ),
        blocks=(Block(block_id=0, page=1, text=text),),
    )


def _evidence(store: Store, *digests: str) -> int:
    admitted = admit_pack(
        store, case_id=CASE, documents=tuple(_document(d) for d in digests)
    )
    return pin_source_set(store, case_id=CASE, source_ids=admitted)


def _run(store: Store) -> str:
    """A run on whose case `APPROVER` holds the standing to release a gate."""
    run_id = start_run(store, case_id=CASE)
    grant_membership(
        store,
        case_id=CASE,
        member_id=APPROVER,
        standing=Standing.APPROVER,
        actor=BoundaryText.of("pm"),
    )
    return run_id


def _plan(version: int, *, selection: str = ASSESSMENT, model: bool = False) -> Plan:
    return Plan(
        case_id=CASE,
        source_set_version=version,
        route=resolve_route(CATALOG, FULL, selection, model_extension=model),
    )


def _events(store: Store, kind: EventKind) -> int:
    row = store.execute(
        "SELECT count(*) FROM run_events WHERE kind = %s", (kind.value,)
    ).fetchone()
    assert row is not None
    return int(row[0])


def test_a_route_is_pinned_only_by_approving_the_plan_that_named_it(
    store: Store,
) -> None:
    version = _evidence(store, "a" * 64)
    run_id = _run(store)
    plan = _plan(version)

    open_plan_gate(store, run_id=run_id, plan=plan)
    assert gate_released(store, run_id=run_id, kind=GateKind.SOURCE_SET) is False
    row = store.execute("SELECT count(*) FROM run_routes").fetchone()
    assert row is not None and row[0] == 0, "nothing is pinned before approval"

    digest = approve_plan(store, run_id=run_id, plan=plan, approver=APPROVER)
    assert digest == route_digest(plan.route)
    assert pinned_route(store, run_id=run_id) == plan.route


def test_approving_a_plan_that_is_not_the_one_on_screen_pins_nothing(
    store: Store,
) -> None:
    # The reason the release and the pin are one call. Two calls could release
    # the reviewed plan and pin a different route, and only the approval row
    # would disagree -- quietly, and after the fact.
    version = _evidence(store, "a" * 64)
    run_id = _run(store)
    reviewed = _plan(version)
    open_plan_gate(store, run_id=run_id, plan=reviewed)

    other = _plan(version, selection=PORTFOLIO)
    with pytest.raises(Refusal) as caught:
        approve_plan(store, run_id=run_id, plan=other, approver=APPROVER)
    assert caught.value.code is RefusalCode.APPROVAL_CONTENT_CHANGED

    assert gate_released(store, run_id=run_id, kind=GateKind.SOURCE_SET) is False
    row = store.execute("SELECT count(*) FROM run_routes").fetchone()
    assert row is not None and row[0] == 0


def test_two_source_set_versions_over_the_same_documents_are_different_inputs(
    store: Store,
) -> None:
    """Why the fingerprint is carried beside the preview, on real inputs.

    Re-pinning the same documents allocates a new version. A person is shown
    the same document list either way -- the version is bookkeeping, not
    something a reader can see -- so the preview digests are identical and only
    the fingerprint separates them. Approving the earlier version must not
    release a run pinned to the later one.
    """
    admitted = admit_pack(store, case_id=CASE, documents=(_document("a" * 64),))
    first = pin_source_set(store, case_id=CASE, source_ids=admitted)
    second = pin_source_set(store, case_id=CASE, source_ids=admitted)
    assert (first, second) == (1, 2)

    run_id = _run(store)
    earlier, later = _plan(first), _plan(second)
    reviewed = plan_gate(run_id, earlier, ("a" * 64,))
    restated = plan_gate(run_id, later, ("a" * 64,))

    assert reviewed.preview_sha256 == restated.preview_sha256, "same bytes on screen"
    assert reviewed.input_fingerprint != restated.input_fingerprint

    open_plan_gate(store, run_id=run_id, plan=later)
    with pytest.raises(Refusal) as caught:
        approve_plan(store, run_id=run_id, plan=earlier, approver=APPROVER)
    assert caught.value.code is RefusalCode.APPROVAL_CONTENT_CHANGED


def test_the_preview_names_every_document_and_every_module(store: Store) -> None:
    # It is what a person reads, so it has to say what they are approving. A
    # preview that omitted a module would be an approval of a route nobody saw.
    version = _evidence(store, "a" * 64, "b" * 64)
    plan = _plan(version)
    preview = plan_preview(plan, ("a" * 64, "b" * 64))

    assert "a" * 64 in preview and "b" * 64 in preview
    for node in plan.route.nodes:
        assert node.module_id in preview
    assert CASE.value in preview and ASSESSMENT in preview


def test_the_preview_does_not_depend_on_the_order_it_was_handed(store: Store) -> None:
    """The digests are over content, so the order the store returned cannot show.

    `_members` runs a join with no `ORDER BY`, which is deliberate and only safe
    while nothing downstream is order-sensitive. Calling the same function twice
    with the same tuple would prove none of that -- it would pass on a preview
    that simply echoed whatever order it was given. Handing it the two orders is
    what fails if either `sorted` call goes away.
    """
    plan = _plan(1)
    forwards, backwards = ("a" * 64, "b" * 64), ("b" * 64, "a" * 64)
    assert plan_preview(plan, forwards) == plan_preview(plan, backwards)
    assert plan_gate("r", plan, forwards) == plan_gate("r", plan, backwards)

    # And the edges, which arrive in whatever order the catalog listed them.
    version = _evidence(store, "a" * 64)
    real = _plan(version)
    shuffled = replace(real, route=replace(real.route, edges=real.route.edges[::-1]))
    assert plan_preview(real, ("a" * 64,)) == plan_preview(shuffled, ("a" * 64,))


def test_the_model_extension_is_part_of_what_is_approved(store: Store) -> None:
    # Nothing selected the model extension before this; the plan does, and the
    # gate binds the choice. Approving a plan without the model effect must not
    # release a run that would build one.
    version = _evidence(store, "a" * 64)
    plain, extended = _plan(version), _plan(version, model=True)
    assert {n.module_id for n in extended.route.nodes} > {
        n.module_id for n in plain.route.nodes
    }

    gate = plan_gate("r", plain, ("a" * 64,))
    assert gate != plan_gate("r", extended, ("a" * 64,))
    assert "CP-CF" in plan_preview(extended, ("a" * 64,))
    assert "CP-CF" not in plan_preview(plain, ("a" * 64,))


def test_a_plan_over_a_source_set_that_was_never_pinned_is_refused(
    store: Store,
) -> None:
    # A version with no members and a version that does not exist are the same
    # thing to a plan: there is no evidence to run against.
    _evidence(store, "a" * 64)
    run_id = _run(store)
    with pytest.raises(Refusal) as caught:
        open_plan_gate(store, run_id=run_id, plan=_plan(99))
    assert caught.value.code is RefusalCode.SOURCE_SET_EMPTY


def test_replaying_the_plan_gate_opens_no_second_interrupt(store: Store) -> None:
    # Recovery replays the gate. `pin_route` was written for exactly this and
    # the gate has to match it, or a restart asks a person to approve twice.
    version = _evidence(store, "a" * 64)
    run_id = _run(store)
    plan = _plan(version)

    assert open_plan_gate(store, run_id=run_id, plan=plan) == plan_gate(
        run_id, plan, ("a" * 64,)
    )
    open_plan_gate(store, run_id=run_id, plan=plan)
    assert _events(store, EventKind.GATE_OPENED) == 1


def test_approving_the_same_plan_twice_is_the_pin_it_already_has(
    store: Store,
) -> None:
    # The commit gap: the transaction commits, the process dies before the
    # caller learns it did, and recovery replays the identical approval.
    version = _evidence(store, "a" * 64)
    run_id = _run(store)
    plan = _plan(version)
    open_plan_gate(store, run_id=run_id, plan=plan)

    first = approve_plan(store, run_id=run_id, plan=plan, approver=APPROVER)
    assert approve_plan(store, run_id=run_id, plan=plan, approver=APPROVER) == first

    counted = store.execute(
        "SELECT (SELECT count(*) FROM run_routes),"
        " (SELECT count(*) FROM run_gate_approvals)"
    ).fetchone()
    assert counted == (1, 1), "one pin, one release"
    # Named rather than counted: three transitions happened once each, and the
    # replay added none. A count alone would pass if the replay emitted a
    # second GATE_APPROVED and the first ROUTE_PINNED had never been written.
    kinds = store.execute("SELECT kind FROM run_events ORDER BY seq").fetchall()
    assert [kind for (kind,) in kinds] == [
        EventKind.GATE_OPENED,
        EventKind.GATE_APPROVED,
        EventKind.ROUTE_PINNED,
    ]


def test_a_pinned_plan_replays_as_pinned_after_the_run_ends(store: Store) -> None:
    # Recovery replays the approval on runs in every state, and the run may
    # have ended between the commit and the replay. The gate already answers a
    # replay before the run's state; the pin has to as well, or a replay that
    # changes nothing refuses RUN_NOT_RUNNING -- the first draft of the run
    # lock did exactly that, and the adversarial pass reproduced it live.
    version = _evidence(store, "a" * 64)
    run_id = _run(store)
    plan = _plan(version)
    open_plan_gate(store, run_id=run_id, plan=plan)
    pinned = approve_plan(store, run_id=run_id, plan=plan, approver=APPROVER)

    store.execute("UPDATE runs SET state = 'COMPLETE' WHERE run_id = %s", (run_id,))
    assert approve_plan(store, run_id=run_id, plan=plan, approver=APPROVER) == pinned
    assert open_plan_gate(store, run_id=run_id, plan=plan) == plan_gate(
        run_id, plan, ("a" * 64,)
    )


def test_a_plan_cannot_be_approved_before_it_is_opened(store: Store) -> None:
    version = _evidence(store, "a" * 64)
    run_id = _run(store)
    with pytest.raises(Refusal) as caught:
        approve_plan(store, run_id=run_id, plan=_plan(version), approver=APPROVER)
    assert caught.value.code is RefusalCode.GATE_NOT_OPEN
    row = store.execute("SELECT count(*) FROM run_routes").fetchone()
    assert row is not None and row[0] == 0


def test_a_pin_that_fails_takes_the_release_down_with_it(store: Store) -> None:
    """What proves the release and the pin really share one transaction.

    The release is written first and the pin happens after it, so the ordering
    is what makes this checkable: make the *pin* fail. A release surviving one
    would record that a person approved a plan the run never took, which is the
    disagreement `approve_plan` exists to make impossible.

    An earlier version of this test moved the source-set version instead. That
    is refused while reading the members, before the transaction is even
    opened, so it proved the refusal and nothing about the rollback.
    """
    version = _evidence(store, "a" * 64)
    run_id = _run(store)
    pin_route(
        store,
        run_id=run_id,
        resolved=resolve_route(CATALOG, FULL, PORTFOLIO),
        source_set_version=version,
    )

    plan = _plan(version)
    open_plan_gate(store, run_id=run_id, plan=plan)
    with pytest.raises(Refusal) as caught:
        approve_plan(store, run_id=run_id, plan=plan, approver=APPROVER)
    assert caught.value.code is RefusalCode.ROUTE_ALREADY_PINNED

    assert gate_released(store, run_id=run_id, kind=GateKind.SOURCE_SET) is False
    assert _events(store, EventKind.GATE_APPROVED) == 0
