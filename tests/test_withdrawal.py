"""Withdrawal, the second half of invariant 1: checked live at every use.

A pinned source set is immutable, so withdrawing a source cannot edit it.
What withdrawal changes is every use from then on: `read_evidence` refuses the
block as it refuses anything it was not given, `pin_source_set` refuses to pin
it again, and a plan re-derived over a set that names it no longer names it --
so a plan gate a person is mid-way through reviewing is re-opened on the
documents the run will actually read, and their approval of the old list is
refused as the stale content it is.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.engine.plan import Plan, approve_plan, open_plan_gate, plan_gate
from server.engine.route import resolve_route
from server.evidence.citations import anchor_citation
from server.evidence.reads import EvidenceRequest, read_evidence
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.events import EventKind
from server.store.gates import GateKind, approve_gate, gate_released, released_gate
from server.store.members import Standing, grant_membership
from server.store.runs import start_run
from server.store.source_sets import pin_source_set, pinned_evidence
from server.store.sources import (
    Block,
    SourceDocument,
    Token,
    admit_pack,
    withdraw_source,
)

CATALOG = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "vendor/deploy-v/skills/cp-os-credit-os/references"
        / "CREDIT_OS_V_MODULE_CATALOG_v2.json"
    ).read_text(encoding="utf-8")
)
CASE = BoundaryText.of("acme")
RIVAL = BoundaryText.of("rival")
NODE = BoundaryText.of("CP-1")
ANA = BoundaryText.of("ana")
A, B = "a" * 64, "b" * 64
SECRET = "Net leverage was 4.2x and the covenant is 4.50x"


def _document(digest: str, text: str = SECRET) -> SourceDocument:
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
    return SourceDocument(
        sha256=digest, tokens=(token,), blocks=(Block(block_id=0, page=1, text=text),)
    )


def _admit(
    store: Store, *digests: str, case_id: BoundaryText = CASE, text: str = SECRET
) -> tuple[str, ...]:
    documents = tuple(_document(digest, text) for digest in digests)
    return admit_pack(store, case_id=case_id, documents=documents)


def _writer(store: Store, standing: Standing = Standing.WRITER) -> BoundaryText:
    """Ana, with the standing to withdraw: a reader may not, a writer may."""
    grant_membership(store, case_id=CASE, member_id=ANA, standing=standing)
    return ANA


def _withdraw(store: Store, source_id: str, actor: BoundaryText = ANA) -> bool:
    return withdraw_source(store, case_id=CASE, source_id=source_id, actor=actor)


def _request(run_id: str, version: int, digest: str) -> EvidenceRequest:
    return EvidenceRequest(
        case_id=CASE,
        source_set_version=version,
        document_sha256=digest,
        block_id=0,
        run_id=run_id,
        node_id=NODE,
    )


def _plan(version: int) -> Plan:
    return Plan(
        case_id=CASE,
        source_set_version=version,
        route=resolve_route(CATALOG, "FULL_CREDIT_32", "FULL_CREDIT_ASSESSMENT"),
    )


def _approvable_run(store: Store) -> str:
    run_id = start_run(store, case_id=CASE)
    grant_membership(store, case_id=CASE, member_id=ANA, standing=Standing.APPROVER)
    return run_id


def _one(store: Store, query: str, *params: object) -> int:
    row = store.execute(query, params).fetchone()
    assert row is not None
    return int(row[0])


HANDED = "SELECT count(*) FROM delivered_evidence WHERE run_id = %s"
WITHDRAWN = "SELECT count(*) FROM sources WHERE withdrawn_at IS NOT NULL"


def test_a_withdrawn_source_refuses_the_read_and_reopens_the_gate(store: Store) -> None:
    """The phase's exit test, across the three uses withdrawal reaches.

    Two documents are pinned and a plan over both is put in front of Ana. The
    second is withdrawn while she reads. Its block is refused from then on --
    with the code every refused read carries, and no text -- and the plan she
    was shown is stale: re-deriving it re-opens the gate on the one document
    the run will read, her approval of the old list is refused, and the pinned
    set itself is untouched, because it is immutable and was never wrong.
    """
    a, b = _admit(store, A, B)
    version = pin_source_set(store, case_id=CASE, source_ids=(a, b))
    run_id = _approvable_run(store)
    plan = _plan(version)
    reviewed = open_plan_gate(store, run_id=run_id, plan=plan)
    assert read_evidence(store, _request(run_id, version, B)).text == SECRET
    handed = _one(store, HANDED, run_id)

    assert _withdraw(store, b) is True

    with pytest.raises(Refusal) as caught:
        read_evidence(store, _request(run_id, version, B))
    assert caught.value.code is RefusalCode.EVIDENCE_NOT_DELIVERABLE
    rendered = f"{caught.value!r} {caught.value!s} {caught.value.args}"
    assert SECRET not in rendered and "leverage" not in rendered
    assert caught.value.__context__ is None
    assert _one(store, HANDED, run_id) == handed
    assert read_evidence(store, _request(run_id, version, A)).text == SECRET

    restated = open_plan_gate(store, run_id=run_id, plan=plan)
    assert restated == plan_gate(run_id, plan, (A,)), "re-derived without B"
    assert restated != reviewed
    opened = "SELECT count(*) FROM run_events WHERE kind = %s"
    assert _one(store, opened, EventKind.GATE_OPENED.value) == 2

    with pytest.raises(Refusal) as caught:
        approve_gate(store, reviewed, approver=ANA)
    assert caught.value.code is RefusalCode.APPROVAL_CONTENT_CHANGED
    assert gate_released(store, run_id=run_id, kind=GateKind.SOURCE_SET) is False

    approve_plan(store, run_id=run_id, plan=plan, approver=ANA)
    assert gate_released(store, run_id=run_id, kind=GateKind.SOURCE_SET) is True
    pinned = "SELECT count(*) FROM source_set_members WHERE version = %s"
    assert _one(store, pinned, version) == 2, "the pin holds: it was never wrong"


def test_a_withdrawn_source_cannot_be_pinned_again(store: Store) -> None:
    # Pinning is a use. A set naming a withdrawn source is a set the run could
    # never fully read, and that is a mistake worth refusing early rather than
    # one read at a time.
    a, b = _admit(store, A, B)
    _writer(store)
    _withdraw(store, b)
    with pytest.raises(Refusal) as caught:
        pin_source_set(store, case_id=CASE, source_ids=(a, b))
    assert caught.value.code is RefusalCode.SOURCE_WITHDRAWN
    assert pin_source_set(store, case_id=CASE, source_ids=(a,)) == 1


def test_withdrawing_twice_is_the_withdrawal_it_already_has(store: Store) -> None:
    (a,) = _admit(store, A)
    _writer(store)
    assert _withdraw(store, a) is True
    first = store.execute("SELECT withdrawn_at FROM sources").fetchone()
    assert _withdraw(store, a) is False
    assert store.execute("SELECT withdrawn_at FROM sources").fetchone() == first


@pytest.mark.parametrize(
    ("standing", "may"),
    [
        (None, False),
        (Standing.READER, False),
        (Standing.WRITER, True),
        (Standing.APPROVER, True),
        (Standing.ADMIN, True),
    ],
    ids=["absent", "READER", "WRITER", "APPROVER", "ADMIN"],
)
def test_withdrawal_needs_writer_standing_on_the_case(
    store: Store, standing: Standing | None, may: bool
) -> None:
    # Withdrawal is destructive and final, so it is the one governed write here
    # that does not wait for an authority layer: the standing check the gate
    # already has, at the store call, under the same lock discipline.
    (a,) = _admit(store, A)
    if standing is not None:
        _writer(store, standing)
    if may:
        assert _withdraw(store, a) is True
        return
    with pytest.raises(Refusal) as caught:
        _withdraw(store, a)
    assert caught.value.code is RefusalCode.STANDING_INSUFFICIENT
    assert _one(store, WITHDRAWN) == 0, "nothing was withdrawn"


def test_withdrawing_another_case_s_source_is_refused_by_code(store: Store) -> None:
    # A writer on this case naming a source of another case learns only that
    # it is not this case's -- the same answer as for a source that exists
    # nowhere, below.
    _admit(store, A)
    _writer(store)
    (theirs,) = _admit(store, B, case_id=RIVAL)
    with pytest.raises(Refusal) as caught:
        _withdraw(store, theirs)
    assert caught.value.code is RefusalCode.SOURCE_NOT_IN_CASE
    assert _one(store, WITHDRAWN) == 0


@pytest.mark.parametrize(
    "source_id",
    [
        pytest.param(str(uuid.uuid4()), id="unknown"),
        pytest.param("not-a-uuid", id="malformed"),
        pytest.param("urn:uuid:" + str(uuid.uuid4()), id="a-spelling-postgres-refuses"),
    ],
)
def test_withdrawing_an_id_that_names_no_source_is_refused_by_code(
    store: Store, source_id: str
) -> None:
    # One code whether the id names nothing or is no id at all -- and never
    # the driver's complaint about a uuid, in the exception or behind it.
    _admit(store, A)
    _writer(store)
    with pytest.raises(Refusal) as caught:
        _withdraw(store, source_id)
    assert caught.value.code is RefusalCode.SOURCE_NOT_IN_CASE
    assert caught.value.__context__ is None
    assert _one(store, WITHDRAWN) == 0


def test_a_decided_plan_gate_replays_as_decided_after_a_withdrawal(
    store: Store,
) -> None:
    # The approval stands: it bound the list Ana read, which was true when she
    # read it. Recovery replays every gate, so replaying this one after a
    # withdrawal must be the decision it already has -- no re-derivation, no
    # event, the pin it already has -- not a refusal that aborts a healthy run.
    # What withdrawal takes from an approved run is every read of the source.
    a, b = _admit(store, A, B)
    version = pin_source_set(store, case_id=CASE, source_ids=(a, b))
    run_id = _approvable_run(store)
    plan = _plan(version)
    reviewed = open_plan_gate(store, run_id=run_id, plan=plan)
    pinned = approve_plan(store, run_id=run_id, plan=plan, approver=ANA)

    _withdraw(store, b)
    assert released_gate(store, run_id=run_id, kind=GateKind.SOURCE_SET) == reviewed
    assert open_plan_gate(store, run_id=run_id, plan=plan) == reviewed
    assert approve_plan(store, run_id=run_id, plan=plan, approver=ANA) == pinned
    opened = "SELECT count(*) FROM run_events WHERE kind = %s"
    assert _one(store, opened, EventKind.GATE_OPENED.value) == 1
    with pytest.raises(Refusal) as caught:
        read_evidence(store, _request(run_id, version, B))
    assert caught.value.code is RefusalCode.EVIDENCE_NOT_DELIVERABLE


def test_a_plan_over_only_withdrawn_sources_has_nothing_to_approve(
    store: Store,
) -> None:
    (a,) = _admit(store, A)
    version = pin_source_set(store, case_id=CASE, source_ids=(a,))
    run_id = _approvable_run(store)
    _withdraw(store, a)
    with pytest.raises(Refusal) as caught:
        open_plan_gate(store, run_id=run_id, plan=_plan(version))
    assert caught.value.code is RefusalCode.SOURCE_SET_EMPTY


def test_pinned_evidence_lists_only_live_sources(store: Store) -> None:
    # The fifth use, missed by the first draft: what a node is handed. A
    # withdrawn source's blocks in that list are reads the node will make and
    # the host will refuse, one by one -- a failed node instead of a narrower
    # evidence set. Every reader now joins `live_sources`, so a use cannot
    # forget the predicate by being written after the rule.
    a, b = _admit(store, A, B)
    version = pin_source_set(store, case_id=CASE, source_ids=(a, b))
    _writer(store)
    _withdraw(store, b)
    assert pinned_evidence(store, case_id=CASE, source_set_version=version) == ((A, 0),)


def test_only_the_owner_reads_the_sources_table() -> None:
    """One seam owns "sources a run may use": the `live_sources` view.

    The withdrawal predicate was retyped by hand at four reads and forgotten at
    the fifth. A `FROM sources` or `JOIN sources` anywhere but the owner (which
    withdraws) and the pin (which counts the withdrawn to say so) is a read
    that may have forgotten it again. Lexical, and the ledger says so: it
    reads the source for the phrase, in any case, and cannot see a statement
    assembled at runtime.
    """
    repo = Path(__file__).resolve().parents[1]
    table = re.compile(r"\b(?:FROM|JOIN)\s+sources\b", re.IGNORECASE)
    reading = sorted(
        str(path.relative_to(repo))
        for path in (repo / "server").rglob("*.py")
        if table.search(path.read_text(encoding="utf-8"))
    )
    assert reading == ["server/store/source_sets.py", "server/store/sources.py"]


def test_a_citation_does_not_anchor_in_a_withdrawn_source(store: Store) -> None:
    """Anchoring is the fourth use, and the one with a human-timescale window.

    A node reads its evidence, then waits on the provider, then re-locates
    every quote. A withdrawal landing in that wait must not let the quote
    into the artifact. And once the same bytes are re-admitted, the quote is
    re-located in the live source and only there: the withdrawn row shares
    the digest, so the lookup has to say which of the two it means.
    """
    (a,) = _admit(store, A)
    _writer(store)

    def anchored(quote: str) -> bool:
        citation = anchor_citation(
            store, case_id=CASE, document_sha256=A, page=1, matched_text=quote
        )
        return bool(citation.bboxes)

    assert anchored(SECRET)

    _withdraw(store, a)
    with pytest.raises(Refusal) as caught:
        anchored(SECRET)
    assert caught.value.code is RefusalCode.CITATION_NOT_LOCATABLE

    restated = "Net leverage was restated to 4.5x"
    _admit(store, A, text=restated)
    assert anchored(restated)
    with pytest.raises(Refusal) as caught:
        anchored(SECRET)
    assert caught.value.code is RefusalCode.CITATION_NOT_LOCATABLE


def test_a_withdrawn_document_can_be_admitted_again_as_a_new_source(
    store: Store,
) -> None:
    # Withdrawal is final for the source, not for the document. The same bytes
    # come back as a new source with its own id and its own history; while the
    # first is live, admitting them again is refused as it always was.
    (first,) = _admit(store, A)
    _writer(store)
    with pytest.raises(Refusal) as caught:
        _admit(store, A)
    assert caught.value.code is RefusalCode.SOURCE_ALREADY_ADMITTED

    _withdraw(store, first)
    (second,) = _admit(store, A)
    assert second != first
    version = pin_source_set(store, case_id=CASE, source_ids=(second,))
    run_id = start_run(store, case_id=CASE)
    assert read_evidence(store, _request(run_id, version, A)).text == SECRET
    assert _one(store, WITHDRAWN) == 1, "the first stays withdrawn"


def test_a_withdrawal_cannot_be_taken_back_by_a_raw_update(store: Store) -> None:
    # A withdrawn source that a raw UPDATE could reinstate is a source whose
    # refusals nobody can explain afterwards. The store refuses it, not the
    # callers: withdrawal is final, and re-admitting is a new source.
    (a,) = _admit(store, A)
    _writer(store)
    _withdraw(store, a)
    for statement in (
        "UPDATE sources SET withdrawn_at = NULL",
        "UPDATE sources SET withdrawn_at = now() - interval '1 day'",
    ):
        with pytest.raises(psycopg.errors.RaiseException) as caught:
            store.execute(statement)
        assert caught.value.diag.message_primary == "WITHDRAWAL_IS_FINAL"
        store.rollback()
    assert _one(store, WITHDRAWN) == 1


def test_the_read_refusal_for_a_withdrawn_source_is_the_read_refusal(
    store: Store,
) -> None:
    # A module learns it was not given the block, and nothing else: invariant 2
    # wants every refused read to be the same answer. Who withdrew what, and
    # when, is a person's question, answered by the source's own row.
    (a,) = _admit(store, A)
    version = pin_source_set(store, case_id=CASE, source_ids=(a,))
    run_id = start_run(store, case_id=CASE)
    _writer(store)
    _withdraw(store, a)
    withdrawn = _request(run_id, version, A)
    with pytest.raises(Refusal) as first:
        read_evidence(store, withdrawn)
    with pytest.raises(Refusal) as second:
        read_evidence(store, replace(withdrawn, block_id=99))
    assert first.value.code is second.value.code
