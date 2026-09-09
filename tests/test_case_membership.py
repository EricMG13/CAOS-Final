"""Authority is checked where the commit is (`docs/SYSTEM_SPEC.md` §8).

A gate's release is a human decision, and the store call that commits it is
where standing has to hold -- not at the request that asked for it. Between the
two, a membership can be revoked; an approval that then commits was made by
someone who no longer had the standing to make it. `case_members` is read
inside the releasing transaction, under the run row lock, and the row is held
`FOR SHARE` so a revocation in flight waits for the release to finish rather
than slipping between its read and its commit.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.engine.plan import Plan, approve_plan, open_plan_gate
from server.engine.route import resolve_route
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.events import EventKind, lock_run
from server.store.gates import Gate, GateKind, approve_gate, gate_released, open_gate
from server.store.members import (
    Standing,
    grant_membership,
    require_standing,
    revoke_membership,
)
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
CASE = BoundaryText.of("acme")
ANA = BoundaryText.of("ana")
PM = BoundaryText.of("pm")
GATE = (GateKind.SOURCE_SET, "a" * 64, "b" * 64)


def _gate(run_id: str) -> Gate:
    return Gate(run_id, *GATE)


def _grant(store: Store, standing: Standing, member: BoundaryText = ANA) -> None:
    grant_membership(store, case_id=CASE, member_id=member, standing=standing, actor=PM)


def _revoke(store: Store) -> bool:
    return revoke_membership(store, case_id=CASE, member_id=ANA, actor=PM)


def _opened(store: Store, standing: Standing | None = Standing.APPROVER) -> Gate:
    run_id = start_run(store, case_id=CASE)
    if standing is not None:
        _grant(store, standing)
    gate = _gate(run_id)
    open_gate(store, gate)
    return gate


def _plan(store: Store) -> Plan:
    text = "Net leverage was 4.2x"
    token = Token(
        page=1,
        region_id=1,
        line_id=1,
        ordinal=0,
        text=text,
        x0=Decimal(72),
        y0=Decimal(700),
        x1=Decimal(120),
        y1=Decimal(712),
    )
    block = Block(block_id=0, page=1, text=text)
    document = SourceDocument(sha256="a" * 64, tokens=(token,), blocks=(block,))
    admitted = admit_pack(store, case_id=CASE, documents=(document,))
    version = pin_source_set(store, case_id=CASE, source_ids=admitted)
    route = resolve_route(CATALOG, "FULL_CREDIT_32", "FULL_CREDIT_ASSESSMENT")
    return Plan(case_id=CASE, source_set_version=version, route=route)


def _counts(store: Store) -> tuple[int, int, int]:
    row = store.execute(
        "SELECT (SELECT count(*) FROM run_gate_approvals),"
        " (SELECT count(*) FROM run_routes),"
        " (SELECT count(*) FROM run_events WHERE kind = %s)",
        (EventKind.GATE_APPROVED.value,),
    ).fetchone()
    assert row is not None
    return int(row[0]), int(row[1]), int(row[2])


def test_membership_revocation_refuses_commit(store: Store) -> None:
    """The phase's exit test, on the full path a person's approval takes.

    Ana has approver standing when the plan is put in front of her. It is
    revoked before she approves. The approval reaches the store carrying the
    exact content she reviewed -- invariant 5 is satisfied -- and it must still
    write nothing: no release, no pin, no event.
    """
    plan = _plan(store)
    run_id = start_run(store, case_id=CASE)
    _grant(store, Standing.APPROVER)
    open_plan_gate(store, run_id=run_id, plan=plan)

    assert _revoke(store) is True
    with pytest.raises(Refusal) as caught:
        approve_plan(store, run_id=run_id, plan=plan, approver=ANA)
    assert caught.value.code is RefusalCode.STANDING_INSUFFICIENT
    assert _counts(store) == (0, 0, 0), "no release, no pin, no event"

    _grant(store, Standing.APPROVER)
    approve_plan(store, run_id=run_id, plan=plan, approver=ANA)
    assert _counts(store) == (1, 1, 1), "one release, one pin, one event"


@pytest.mark.parametrize(
    ("standing", "releases"),
    [
        (None, False),
        (Standing.READER, False),
        (Standing.WRITER, False),
        (Standing.APPROVER, True),
        (Standing.ADMIN, True),
    ],
    ids=["absent", "READER", "WRITER", "APPROVER", "ADMIN"],
)
def test_only_approver_or_admin_standing_releases_a_gate(
    store: Store, standing: Standing | None, releases: bool
) -> None:
    # One code for absent standing and for insufficient standing. An outsider
    # told "you are only a reader" has learned they are a member of something;
    # the two are the same private refusal at the store as at the edge (§8).
    gate = _opened(store, standing)
    if releases:
        assert approve_gate(store, gate, approver=ANA) is True
        return
    with pytest.raises(Refusal) as caught:
        approve_gate(store, gate, approver=ANA)
    assert caught.value.code is RefusalCode.STANDING_INSUFFICIENT
    assert gate_released(store, run_id=gate.run_id, kind=gate.kind) is False


def test_a_replayed_release_stands_after_the_approver_is_revoked(store: Store) -> None:
    # The decision was made by someone who had the standing to make it. What
    # revocation takes away is the next decision, not the one already committed
    # -- and recovery replaying the identical call must be told it stands (False)
    # rather than be refused for a release that is durably there.
    gate = _opened(store)
    assert approve_gate(store, gate, approver=ANA) is True
    _revoke(store)
    assert approve_gate(store, gate, approver=ANA) is False


def test_standing_is_checked_before_the_content(store: Store) -> None:
    # Whether the plan moved, and whether it was already decided, are things
    # only a member may learn. The one answer that precedes standing is the
    # exact replay, which reports a decision the caller already holds.
    gate = _opened(store, Standing.READER)
    moved = Gate(gate.run_id, gate.kind, "c" * 64, "d" * 64)
    with pytest.raises(Refusal) as caught:
        approve_gate(store, moved, approver=ANA)
    assert caught.value.code is RefusalCode.STANDING_INSUFFICIENT

    _grant(store, Standing.APPROVER, BoundaryText.of("bo"))
    approve_gate(store, gate, approver=BoundaryText.of("bo"))
    with pytest.raises(Refusal) as caught:
        approve_gate(store, moved, approver=ANA)
    assert caught.value.code is RefusalCode.STANDING_INSUFFICIENT, (
        "decided, and private"
    )
    assert approve_gate(store, gate, approver=ANA) is False, "the exact replay"


def _demote(store: Store) -> None:
    _grant(store, Standing.READER)


@pytest.mark.parametrize(
    ("change", "after"),
    [(_revoke, None), (_demote, ("READER",))],
    ids=["revoke", "demote"],
)
def test_a_revocation_waits_for_a_release_in_flight(
    store: Store,
    store_schema: str,
    postgres_dsn: str,
    change: Callable[[Store], None],
    after: tuple[str] | None,
) -> None:
    """The check is not only inside the transaction; it is serialised with revocation.

    Read the standing, then let a revocation commit, then commit the release:
    that ordering satisfies "checked inside the transaction" and still commits
    an approval by someone who has just lost the standing to make it. `FOR
    SHARE` on the membership row is what refuses the interleaving -- a DELETE
    and a change of standing both wait for the releasing transaction to end
    (`FOR KEY SHARE` would let the second through). Proven with a lock timeout
    on the revoking connection, so a wait is visible as a refusal rather than
    as a hang.
    """
    run_id = start_run(store, case_id=CASE)
    _grant(store, Standing.APPROVER)
    store.commit()

    with store.transaction():
        lock_run(store, run_id=run_id)
        require_standing(
            store,
            case_id=CASE.value,
            member_id=ANA,
            allowed=frozenset({Standing.APPROVER}),
        )
        with psycopg.connect(postgres_dsn, autocommit=False) as other:
            other.execute(f'SET search_path TO "{store_schema}"')
            other.execute("SET lock_timeout TO '200ms'")
            with pytest.raises(psycopg.errors.LockNotAvailable):
                change(other)

    with psycopg.connect(postgres_dsn, autocommit=False) as other:
        other.execute(f'SET search_path TO "{store_schema}"')
        change(other)
        row = other.execute(
            "SELECT standing FROM case_members WHERE member_id = %s", (ANA.value,)
        ).fetchone()
    assert row == after, "the change landed once the release ended"


def test_reopening_an_undecided_gate_replays_whatever_the_run_state(
    store: Store,
) -> None:
    # Recovery replays every gate, and a run that has since failed still holds
    # the ask it was parked on. An identical ask is the ask it already has --
    # False, and no second event -- before the run's state is even consulted.
    gate = _opened(store)
    store.execute("UPDATE runs SET state = 'FAILED' WHERE run_id = %s", (gate.run_id,))
    assert open_gate(store, gate) is False
    row = store.execute(
        "SELECT count(*) FROM run_events WHERE kind = %s",
        (EventKind.GATE_OPENED.value,),
    ).fetchone()
    assert row == (1,)


@pytest.mark.parametrize("state", ["COMPLETE", "FAILED"])
def test_a_gate_is_not_opened_on_a_run_that_has_left_running(
    store: Store, state: str
) -> None:
    # `reserve` already refuses a run that left RUNNING; a gate must too, or a
    # person is asked to approve a plan for a run that will never read it.
    run_id = start_run(store, case_id=CASE)
    store.execute("UPDATE runs SET state = %s WHERE run_id = %s", (state, run_id))
    with pytest.raises(Refusal) as caught:
        open_gate(store, _gate(run_id))
    assert caught.value.code is RefusalCode.RUN_NOT_RUNNING


@pytest.mark.parametrize("state", ["COMPLETE", "FAILED"])
def test_a_gate_is_not_released_on_a_run_that_has_left_running(
    store: Store, state: str
) -> None:
    gate = _opened(store)
    store.execute("UPDATE runs SET state = %s WHERE run_id = %s", (state, gate.run_id))
    with pytest.raises(Refusal) as caught:
        approve_gate(store, gate, approver=ANA)
    assert caught.value.code is RefusalCode.RUN_NOT_RUNNING
    assert gate_released(store, run_id=gate.run_id, kind=gate.kind) is False


def test_a_decided_gate_replays_as_decided_whatever_the_run_state(store: Store) -> None:
    # Recovery replays gates on runs in every state. A release that stands is
    # reported as standing; only a *new* decision needs a RUNNING run.
    gate = _opened(store)
    approve_gate(store, gate, approver=ANA)
    store.execute(
        "UPDATE runs SET state = 'COMPLETE' WHERE run_id = %s", (gate.run_id,)
    )
    assert open_gate(store, gate) is False
    assert approve_gate(store, gate, approver=ANA) is False


def test_granting_again_moves_the_standing(store: Store) -> None:
    gate = _opened(store, Standing.APPROVER)
    _grant(store, Standing.READER)
    with pytest.raises(Refusal) as caught:
        approve_gate(store, gate, approver=ANA)
    assert caught.value.code is RefusalCode.STANDING_INSUFFICIENT
    row = store.execute("SELECT count(*) FROM case_members").fetchone()
    assert row == (1,), "one member, one row: a re-grant moves it, never doubles it"


def test_a_grant_on_a_case_that_does_not_exist_is_refused_by_code(store: Store) -> None:
    # The store's typed code, never `case_members_case_id_fkey`. Membership is
    # not what mints a case (the ledger already has two things that do).
    with pytest.raises(Refusal) as caught:
        _grant(store, Standing.READER)
    assert caught.value.code is RefusalCode.CASE_NOT_FOUND


def test_revoking_a_member_who_is_not_one_removes_nothing(store: Store) -> None:
    start_run(store, case_id=CASE)
    assert _revoke(store) is False


def test_standing_is_one_of_the_four_the_spec_names(store: Store) -> None:
    # `SYSTEM_SPEC.md` §8: READER, WRITER, APPROVER, ADMIN. The store refuses a
    # fifth on its own, so no caller can invent one the check would not read.
    start_run(store, case_id=CASE)
    assert [s.value for s in Standing] == ["READER", "WRITER", "APPROVER", "ADMIN"]
    with pytest.raises(psycopg.errors.CheckViolation):
        store.execute(
            "INSERT INTO case_members (case_id, member_id, standing)"
            " VALUES (%s, 'ana', 'OWNER')",
            (CASE.value,),
        )
    store.rollback()
