"""A governed write commits its audit event or nothing.

`docs/SYSTEM_SPEC.md` §2: `audit_events` is hash-chained per case with an
`audit_chain_heads` lock row, append-only, every string on it `BoundaryText`.
The chain has no external anchor, so what it can prove is internal: each event
is the digest of its own row and the one before it, and the head row names the
last. A rewrite is a link that no longer holds -- and the emitter checks that
link before it chains another event onto it, so a rewritten chain refuses the
governed write rather than growing over the rewrite.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal

import psycopg
import pytest

from server.boundary_text import BoundaryText
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.audit import GENESIS, AuditEvent, AuditKind, record
from server.store.members import Standing, grant_membership, revoke_membership
from server.store.runs import start_run
from server.store.sources import (
    Block,
    SourceDocument,
    Token,
    admit_pack,
    withdraw_source,
)

CASE = BoundaryText.of("acme")
RIVAL = BoundaryText.of("rival")
ANA = BoundaryText.of("ana")
PM = BoundaryText.of("pm")
A, B = "a" * 64, "b" * 64

EVENTS = (
    "SELECT seq, prev_sha256, sha256, kind, actor, subject, detail, at"
    " FROM audit_events WHERE case_id = %s ORDER BY seq"
)
HEAD = "SELECT seq, head FROM audit_chain_heads WHERE case_id = %s"
WITHDRAWN = "SELECT count(*) FROM sources WHERE withdrawn_at IS NOT NULL"


def _document(digest: str) -> SourceDocument:
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
    return SourceDocument(sha256=digest, tokens=(token,), blocks=(block,))


def _admit(store: Store, *digests: str) -> tuple[str, ...]:
    documents = tuple(_document(digest) for digest in digests)
    return admit_pack(store, case_id=CASE, documents=documents)


def _grant(
    store: Store,
    standing: Standing = Standing.WRITER,
    case_id: BoundaryText = CASE,
) -> bool:
    return grant_membership(
        store, case_id=case_id, member_id=ANA, standing=standing, actor=PM
    )


def _withdraw(store: Store, source_id: str, actor: BoundaryText = ANA) -> bool:
    return withdraw_source(store, case_id=CASE, source_id=source_id, actor=actor)


def _events(store: Store, case_id: BoundaryText = CASE) -> list[tuple[object, ...]]:
    return store.execute(EVENTS, (case_id.value,)).fetchall()


def _head(store: Store, case_id: BoundaryText = CASE) -> tuple[object, ...] | None:
    return store.execute(HEAD, (case_id.value,)).fetchone()


def _withdrawn(store: Store) -> object:
    row = store.execute(WITHDRAWN).fetchone()
    assert row is not None
    return row[0]


def _recomputed(case_id: str, row: tuple[object, ...]) -> str:
    """The digest as a verifier holding only the standard library recomputes it."""
    seq, prev, _, kind, actor, subject, detail, at = row
    assert hasattr(at, "astimezone")
    stamped = at.astimezone(UTC).isoformat(timespec="microseconds")
    fields = [case_id, seq, prev, kind, actor, subject, detail, stamped]
    canonical = json.dumps(fields, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def test_a_governed_write_commits_its_audit_event_or_nothing(store: Store) -> None:
    """The phase's exit test, in both directions of "or nothing".

    Ana withdraws a source: the row is withdrawn and the chain grows by one
    event naming her, in one transaction. A replay and a refused attempt write
    no event. Then the chain's head is moved under her -- the rewrite the chain
    exists to detect -- and her next withdrawal is refused by code with the
    source still live: the event could not be written, so neither was the
    state it records.
    """
    a, b = _admit(store, A, B)
    _grant(store)
    granted = _events(store)
    assert len(granted) == 1, "the grant is a governed write too"

    assert _withdraw(store, a) is True
    *_, withdrawn = _events(store)
    seq, prev, digest, kind, actor, subject, detail, _ = withdrawn
    assert (seq, kind, actor, subject) == (2, "SOURCE_WITHDRAWN", "ana", a)
    assert detail is None
    assert prev == granted[0][2], "chained onto the event before it"
    assert _head(store) == (2, digest)

    assert _withdraw(store, a) is False
    with pytest.raises(Refusal) as caught:
        _withdraw(store, b, BoundaryText.of("cy"))
    assert caught.value.code is RefusalCode.STANDING_INSUFFICIENT
    assert len(_events(store)) == 2, "a replay and a refusal record nothing"

    store.execute("UPDATE audit_chain_heads SET head = %s", ("f" * 64,))
    with pytest.raises(Refusal) as caught:
        _withdraw(store, b)
    assert caught.value.code is RefusalCode.AUDIT_CHAIN_BROKEN
    assert _withdrawn(store) == 1, "no event, so no withdrawal"
    assert len(_events(store)) == 2


def test_a_membership_change_is_a_governed_write(store: Store) -> None:
    # `case_members` holds current membership only; its history is here, with
    # the actor each grant and revocation was made by and the standing each
    # moved. A grant of the standing already held, a revocation that removed
    # nothing and a grant on a case that is not there record nothing.
    start_run(store, case_id=CASE)
    assert _grant(store, Standing.READER) is True
    assert _grant(store, Standing.ADMIN) is True
    assert _grant(store, Standing.ADMIN) is False, "a retried grant is not a change"
    assert revoke_membership(store, case_id=CASE, member_id=ANA, actor=PM) is True
    assert revoke_membership(store, case_id=CASE, member_id=ANA, actor=PM) is False
    with pytest.raises(Refusal) as caught:
        _grant(store, case_id=RIVAL)
    assert caught.value.code is RefusalCode.CASE_NOT_FOUND

    told = [
        (seq, kind, actor, subject, detail)
        for seq, _, _, kind, actor, subject, detail, _ in _events(store)
    ]
    assert told == [
        (1, "MEMBERSHIP_GRANTED", "pm", "ana", "READER"),
        (2, "MEMBERSHIP_GRANTED", "pm", "ana", "ADMIN"),
        (3, "MEMBERSHIP_REVOKED", "pm", "ana", "ADMIN"),
    ]
    assert _head(store, RIVAL) is None, "no case, no chain"


def test_every_event_is_the_digest_of_its_row_and_the_one_before(store: Store) -> None:
    """What a retained package can check with the standard library alone.

    Recomputed here from the rows and not through the emitter: the canonical
    form is `[case, seq, prev, kind, actor, subject, detail, at]` as compact
    JSON with `at` in UTC to the microsecond, and this is the second place
    that spells it out, on purpose.
    """
    a, b = _admit(store, A, B)
    _grant(store)
    _withdraw(store, a)
    _withdraw(store, b)
    rows = _events(store)
    assert [row[0] for row in rows] == [1, 2, 3]
    prev = GENESIS
    for row in rows:
        assert row[1] == prev
        assert row[2] == _recomputed(CASE.value, row)
        prev = str(row[2])
    assert _head(store) == (3, prev)


def test_a_chain_is_per_case_and_names_only_a_case_that_exists(store: Store) -> None:
    # The emitter, used directly: seq is per case, the head row is minted on
    # the first event, and a case that does not exist is refused by code --
    # never by the head table's foreign key. Both of this case's events are
    # written in one transaction, so `at` is the clock and not `now()`, which
    # would stamp them identically and stamp a write that waited on the lock
    # before the event it waited on.
    for case_id in (CASE, RIVAL):
        start_run(store, case_id=case_id)

    def _record(case_id: BoundaryText) -> str:
        event = AuditEvent(kind=AuditKind.MEMBERSHIP_GRANTED, actor=PM, subject=ANA)
        return record(store, case_id=case_id, event=event)

    _record(CASE)
    second = _record(RIVAL)
    third = _record(CASE)
    first_at, third_at = (row[7] for row in _events(store))
    assert isinstance(first_at, datetime) and isinstance(third_at, datetime)
    assert first_at < third_at, "`at` increases with seq"
    assert [row[0] for row in _events(store)] == [1, 2]
    assert _head(store) == (2, third)
    assert _head(store, RIVAL) == (1, second)
    with pytest.raises(Refusal) as caught:
        _record(BoundaryText.of("nowhere"))
    assert caught.value.code is RefusalCode.CASE_NOT_FOUND


@pytest.mark.parametrize(
    "rewrite",
    [
        pytest.param(
            "UPDATE audit_chain_heads SET head = repeat('f', 64)", id="head-moved"
        ),
        pytest.param(
            "UPDATE audit_chain_heads SET seq = 0, head = repeat('0', 64)",
            id="head-wound-back",
        ),
        pytest.param(
            "ALTER TABLE audit_events DISABLE TRIGGER ALL;"
            " UPDATE audit_events SET actor = 'bo'",
            id="event-rewritten",
        ),
        pytest.param(
            "ALTER TABLE audit_events DISABLE TRIGGER ALL; DELETE FROM audit_events",
            id="event-removed",
        ),
    ],
)
def test_a_rewritten_chain_refuses_the_next_governed_write(
    store: Store, rewrite: str
) -> None:
    # No external anchor (SYSTEM_SPEC 2), so the one link the emitter can
    # check is the last: the head must be the digest of the last row as it
    # stands now. Each of these is a rewrite the triggers refuse and the table
    # owner can make anyway; each is caught before another event is chained
    # onto it, and the write it would have recorded is refused with it.
    (a,) = _admit(store, A)
    _grant(store)
    store.execute(rewrite)
    with pytest.raises(Refusal) as caught:
        _withdraw(store, a)
    assert caught.value.code is RefusalCode.AUDIT_CHAIN_BROKEN
    assert _withdrawn(store) == 0


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE audit_events SET actor = 'bo'",
        "DELETE FROM audit_events",
        "DELETE FROM audit_chain_heads",
    ],
)
def test_the_chain_and_its_head_refuse_a_rewrite_at_the_store(
    store: Store, statement: str
) -> None:
    # Proven on populated rows, which the ledger says the other append-only
    # tables still lack. The head row keeps its UPDATE path -- the head moves
    # with every event -- and loses its DELETE: a chain whose head is gone
    # would be re-minted at genesis over its own history.
    start_run(store, case_id=CASE)
    _grant(store)
    with pytest.raises(psycopg.errors.RaiseException) as caught:
        store.execute(statement)
    assert caught.value.diag.message_primary == "APPEND_ONLY_TABLE"
    store.rollback()


def test_the_digest_does_not_depend_on_the_session_time_zone(
    store: Store, store_schema: str, postgres_dsn: str
) -> None:
    # `at` is inside the digest, and the driver hands it back in whatever zone
    # the session is set to. A link written under one zone has to recompute
    # under another, or the chain breaks the first time two processes differ.
    start_run(store, case_id=CASE)
    store.commit()
    _grant(store)
    store.commit()
    with psycopg.connect(postgres_dsn, autocommit=False) as other:
        other.execute(f'SET search_path TO "{store_schema}"')
        other.execute("SET TIME ZONE 'Asia/Kathmandu'")
        grant_membership(
            other, case_id=CASE, member_id=ANA, standing=Standing.ADMIN, actor=PM
        )
    _grant(store, Standing.READER)
    rows = _events(store)
    assert [row[0] for row in rows] == [1, 2, 3]
    assert all(row[2] == _recomputed(CASE.value, row) for row in rows)
