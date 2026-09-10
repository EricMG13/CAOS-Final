"""The run's event tail (`docs/SYSTEM_SPEC.md` §9).

Progress reaches the browser as SSE over `run_events`, resumable by
`Last-Event-ID`. Membership is rechecked before each event, the stream closes
once a terminal run is fully delivered, and a tail that never ends closes at
its deadline so the edge can reauthenticate. The client never reads a payload:
an event name is what triggers a refetch.

The store is one synchronous connection on the event loop, so the property
underneath all of it is that no transaction is ever open across an `await`.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from decimal import Decimal

import psycopg
import pytest
from conftest import Counter, serve
from psycopg.pq import TransactionStatus

from server.api import events
from server.api.app import create_app
from server.api.events import (
    IO_BUDGET,
    MAX_TAILS,
    MAX_TAILS_PER_MEMBER,
    Poll,
    event_tail,
    last_seen,
    poll_events,
    release_tail,
    reserve_tail,
)
from server.api.identity import Environment, Identity, identify
from server.api.runs import RunState, RunView, run_view
from server.boundary_text import BoundaryText
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.blobs import BlobStore
from server.store.events import EventKind, emit
from server.store.members import Standing, grant_membership, revoke_membership
from server.store.runs import TerminalCommit, commit_terminal, start_run

CASE = BoundaryText.of("acme")
ANA = BoundaryText.of("ana")
PM = BoundaryText.of("pm")
NODE = BoundaryText.of("RN-FULL_CREDIT_32-DECISION_LEDGER-01-CP-0")


def _run(store: Store, standing: Standing | None = Standing.READER) -> str:
    run_id = start_run(store, case_id=CASE)
    if standing is not None:
        grant_membership(
            store, case_id=CASE, member_id=ANA, standing=standing, actor=PM
        )
    store.commit()
    return run_id


def _member() -> Identity:
    who = identify([("X-Caos-Member", "ana")], environment=Environment.DEVELOPMENT)
    assert who is not None
    return who


def _tail(store: Store, run_id: str, *, after: int = 0) -> AsyncIterator[str]:
    identity = _member()
    first = poll_events(store, identity=identity, run_id=run_id, after=after)
    return event_tail(store, identity=identity, run_id=run_id, after=after, first=first)


def _finish(store: Store, run_id: str) -> None:
    commit_terminal(
        store,
        TerminalCommit(
            run_id=run_id, node_id=NODE, artifact_sha256="a" * 64, charge=Decimal(0)
        ),
    )
    store.commit()


def _names(frames: list[str]) -> list[str]:
    return [
        line[7:]
        for frame in frames
        for line in frame.splitlines()
        if line[:7] == "event: "
    ]


def test_sse_closes_after_terminal_delivery(store: Store, blobs: BlobStore) -> None:
    """The phase's exit test, over the route rather than the generator.

    `serve` returns only once the app has finished the response, so a body
    holding both frames is the stream having closed itself."""
    run_id = _run(store)
    emit(store, run_id=run_id, kind=EventKind.ROUTE_PINNED)
    store.commit()
    _finish(store, run_id)
    app = create_app(store, blobs=blobs, environment=Environment.DEVELOPMENT)

    answer = serve(app, f"/api/runs/{run_id}/events", [("X-Caos-Member", "ana")])

    assert answer.status == 200
    # SSE is `docs/SYSTEM_SPEC.md` §9's one carve-out from a named model.
    assert answer.headers["content-type"].startswith("text/event-stream")
    # A proxy that buffers a stream defeats it; one that caches it hands a
    # member's events to whoever asks next.
    assert answer.headers["x-accel-buffering"] == "no"
    assert answer.headers["cache-control"] == "no-store"
    assert answer.headers["vary"] == "X-Forwarded-User, X-Caos-Member"
    assert answer.body == (
        b"id: 1\nevent: ROUTE_PINNED\ndata: {}\n\n"
        b"id: 2\nevent: RUN_COMPLETED\ndata: {}\n\n"
    ), "both frames, in order, and nothing after the terminal one"


def test_the_tail_resumes_from_the_last_event_it_sent(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(events, "POLL_SECONDS", 0)
    run_id = _run(store)
    emit(store, run_id=run_id, kind=EventKind.GATE_OPENED)
    store.commit()
    _finish(store, run_id)

    async def scenario() -> list[str]:
        return [frame async for frame in _tail(store, run_id, after=1)]

    assert _names(asyncio.run(scenario())) == [EventKind.RUN_COMPLETED]
    assert last_seen([("Last-Event-ID", "7")]) == 7
    # A header that is not a seq resumes from the start: the client is sent
    # events it may already have, which it cannot misread, because the payload
    # is nothing and the name only says to refetch.
    assert last_seen([("Last-Event-ID", "not-a-seq")]) == 0
    assert last_seen([("Last-Event-ID", "-3")]) == 0
    assert last_seen([]) == 0
    # `str.isdigit` is true for a superscript that `int` then refuses, and a
    # header arrives decoded latin-1, which carries U+00B2 off the wire: a
    # client could otherwise crash its own request with two bytes.
    assert last_seen([("Last-Event-ID", "\u00b2")]) == 0
    # `int()` refuses a string of more than 4300 digits, and `last_seen` runs
    # before the poll that would refuse the caller for having no standing.
    assert last_seen([("Last-Event-ID", "9" * 4301)]) == 0


def test_a_member_whose_standing_is_revoked_stops_receiving_events(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Membership is rechecked before each event, not only at the request."""
    monkeypatch.setattr(events, "POLL_SECONDS", 0)
    run_id = _run(store)
    emit(store, run_id=run_id, kind=EventKind.ROUTE_PINNED)
    store.commit()

    async def scenario() -> str:
        tail = _tail(store, run_id)
        first = await anext(tail)
        revoke_membership(store, case_id=CASE, member_id=ANA, actor=PM)
        store.commit()
        with pytest.raises(StopAsyncIteration):
            await anext(tail)
        return first

    assert _names([asyncio.run(scenario())]) == [EventKind.ROUTE_PINNED]


def test_an_unauthorised_tail_is_the_same_private_404(
    store: Store, blobs: BlobStore
) -> None:
    """No stream opens for a stranger, and nothing distinguishes the four."""
    run_id = _run(store, standing=None)
    app = create_app(store, blobs=blobs, environment=Environment.DEVELOPMENT)
    asked = [
        f"/api/runs/{run_id}/events",
        f"/api/runs/{uuid.uuid4()}/events",
        "/api/runs/not-a-run/events",
    ]
    answers = [serve(app, path, [("X-Caos-Member", "ana")]) for path in asked]
    answers.append(serve(app, f"/api/runs/{run_id}/events"))
    for answer in answers:
        assert answer.status == 404
        assert answer.body == b'{"code":"RUN_NOT_FOUND"}'


def test_the_tail_never_holds_a_transaction_across_an_await(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A tail parked at its sleep with a transaction open would make the next
    request's `store.transaction()` a savepoint inside this reader's, for up to
    five minutes. The sample is taken inside the sleep: at the yields it would
    only ever see the endpoint's own poll."""
    sampled: list[TransactionStatus] = []
    slept = asyncio.sleep

    async def probe(seconds: float) -> None:
        sampled.append(store.info.transaction_status)
        await slept(0)

    monkeypatch.setattr(asyncio, "sleep", probe)
    run_id = _run(store)
    emit(store, run_id=run_id, kind=EventKind.ROUTE_PINNED)
    store.commit()

    async def scenario() -> list[str]:
        frames = []
        async for frame in _tail(store, run_id):
            frames.append(frame)
            # Ending the run is what lets the second poll be the last.
            if len(frames) == 1:
                _finish(store, run_id)
        return frames

    assert len(asyncio.run(scenario())) == 2, "the loop ran a second poll"
    assert sampled == [TransactionStatus.IDLE], "parked, holding nothing"


def test_the_tail_closes_at_its_deadline(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run that never ends is a tail that does, so the edge can reauthenticate."""
    monkeypatch.setattr(events, "POLL_SECONDS", 0)
    monkeypatch.setattr(events, "TAIL_SECONDS", 0)
    run_id = _run(store)
    emit(store, run_id=run_id, kind=EventKind.ROUTE_PINNED)
    store.commit()

    async def scenario() -> list[str]:
        return [frame async for frame in _tail(store, run_id)]

    # The run is still RUNNING: only the deadline can end this.
    assert _names(asyncio.run(scenario())) == [EventKind.ROUTE_PINNED]


def test_io_budget_event_tail(
    store: Store, count_io: Counter, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One statement per poll: the run, the member's standing and the events."""
    monkeypatch.setattr(events, "POLL_SECONDS", 0)
    run_id = _run(store)
    for kind in (EventKind.ROUTE_PINNED, EventKind.GATE_OPENED):
        emit(store, run_id=run_id, kind=kind)
    store.commit()

    with count_io(store) as tally:
        poll_events(store, identity=_member(), run_id=run_id, after=0)

    assert tally.statements == IO_BUDGET
    assert tally.rows == 2, "the run's two events, and no row per poll besides"


def test_a_run_with_no_events_yet_is_a_tail_that_stays_open(store: Store) -> None:
    run_id = _run(store)
    poll = poll_events(store, identity=_member(), run_id=run_id, after=0)
    assert poll == Poll(events=(), terminal=False)
    # §9's five minutes, and the second that bounds a revoked reader, pinned
    # here because this is the test that patches neither.
    assert (events.TAIL_SECONDS, events.POLL_SECONDS) == (300.0, 1.0)


def test_an_event_kind_the_host_did_not_write_is_refused(store: Store) -> None:
    """The kind is framed into the response, and `run_events.kind` has no CHECK.

    A raw insert is the only way in, and a newline in one would forge an event
    on the wire, so the tail decodes the closed set rather than trusting it.
    """
    run_id = _run(store)
    store.execute(
        "INSERT INTO run_events (run_id, seq, kind) VALUES (%s, 1, %s)",
        (run_id, "GATE_OPENED\nevent: RUN_COMPLETED"),
    )
    store.commit()
    with pytest.raises(ValueError):
        poll_events(store, identity=_member(), run_id=run_id, after=0)


def test_a_client_that_has_seen_everything_is_told_to_stop(
    store: Store, blobs: BlobStore
) -> None:
    """A stream that merely ends is one `EventSource` reconnects to forever."""
    run_id = _run(store)
    emit(store, run_id=run_id, kind=EventKind.ROUTE_PINNED)
    store.commit()
    _finish(store, run_id)
    app = create_app(store, blobs=blobs, environment=Environment.DEVELOPMENT)
    asking = [("X-Caos-Member", "ana"), ("Last-Event-ID", "2")]

    answer = serve(app, f"/api/runs/{run_id}/events", asking)

    assert (answer.status, answer.body) == (204, b"")
    assert "content-type" not in answer.headers


def test_a_member_cannot_spend_the_instance_s_streams(
    store: Store, blobs: BlobStore
) -> None:
    """A tail is a request that lasts minutes, so it is counted.

    One member holding a thousand open put a thousand statements a second on
    the connection every other request shares and stalled them all
    (`docs/DECISIONS.md` §51). The ceiling is what `SYSTEM_SPEC.md` §11 means
    by enforced rather than assumed.
    """
    run_id = _run(store)
    emit(store, run_id=run_id, kind=EventKind.ROUTE_PINNED)
    store.commit()
    ana, other = _member(), Identity(BoundaryText.of("bo"), frozenset())
    for _ in range(MAX_TAILS_PER_MEMBER):
        reserve_tail(ana)
    with pytest.raises(Refusal) as caught:
        reserve_tail(ana)
    assert caught.value.code is RefusalCode.STREAM_CEILING_EXCEEDED
    assert MAX_TAILS > MAX_TAILS_PER_MEMBER, "one member does not own them all"
    reserve_tail(other)  # another member is unaffected by what this one holds
    release_tail(other)

    app = create_app(store, blobs=blobs, environment=Environment.DEVELOPMENT)
    answer = serve(app, f"/api/runs/{run_id}/events", [("X-Caos-Member", "ana")])
    assert answer.status == 429
    assert answer.body == b'{"code":"STREAM_CEILING_EXCEEDED"}'

    for _ in range(MAX_TAILS_PER_MEMBER):
        release_tail(ana)
    # Releasing what was never reserved cannot push the count below what is
    # really open, or the ceiling stops meaning anything.
    release_tail(ana)
    reserve_tail(ana)
    release_tail(ana)


def test_a_quiet_run_still_sends_something(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Five minutes of silence is a stream a buffering proxy times out."""
    monkeypatch.setattr(events, "POLL_SECONDS", 0)
    run_id = _run(store)
    store.commit()

    async def scenario() -> list[str]:
        frames = []
        async for frame in _tail(store, run_id):
            frames.append(frame)
            if len(frames) == 1:
                _finish(store, run_id)
        return frames

    frames = asyncio.run(scenario())
    assert frames[0] == ":\n\n", "a comment, which every client ignores"
    assert _names(frames) == [EventKind.RUN_COMPLETED]


def test_a_store_failure_mid_stream_ends_the_tail_rather_than_breaking_it(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Raising truncates the body, and does it again on every reconnect."""
    monkeypatch.setattr(events, "POLL_SECONDS", 0)
    run_id = _run(store)
    emit(store, run_id=run_id, kind=EventKind.ROUTE_PINNED)
    store.commit()

    async def scenario() -> list[str]:
        frames = []
        async for frame in _tail(store, run_id):
            frames.append(frame)
            store.execute(
                "INSERT INTO run_events (run_id, seq, kind) VALUES (%s, 2, %s)",
                (run_id, "NOT-A-KIND"),
            )
            store.commit()
        return frames

    assert _names(asyncio.run(scenario())) == [EventKind.ROUTE_PINNED]


def test_two_tails_and_a_view_share_the_one_connection(
    store: Store, blobs: BlobStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One connection, several readers, which the whole design rests on.

    Both tails park at a `yield` holding nothing, so a run view issued between
    their polls opens its own transaction rather than a savepoint of somebody
    else's -- and each tail still sees every event."""
    monkeypatch.setattr(events, "POLL_SECONDS", 0)
    run_id = _run(store)
    emit(store, run_id=run_id, kind=EventKind.ROUTE_PINNED)
    store.commit()

    async def scenario() -> tuple[list[str], RunView, list[str]]:
        left, right = _tail(store, run_id), _tail(store, run_id)
        opening = [await anext(left), await anext(right)]
        seen = run_view(store, blobs=blobs, identity=_member(), run_id=run_id)
        _finish(store, run_id)
        rest = [f async for f in left] + [f async for f in right]
        return opening, seen, rest

    opening, seen, rest = asyncio.run(scenario())
    assert _names(opening) == [EventKind.ROUTE_PINNED] * 2
    assert (seen.run_id, seen.state) == (run_id, RunState.RUNNING)
    assert _names(rest) == [EventKind.RUN_COMPLETED] * 2


def test_a_poll_leaves_the_connection_as_it_found_it(
    store: Store, postgres_dsn: str, store_schema: str
) -> None:
    """Idle stays idle, and a caller's transaction is still theirs to commit."""
    run_id = _run(store)
    emit(store, run_id=run_id, kind=EventKind.ROUTE_PINNED)
    store.commit()
    with psycopg.connect(postgres_dsn, autocommit=False) as second:
        second.execute(f'SET search_path TO "{store_schema}"')
        second.commit()
        who = _member()
        poll = poll_events(second, identity=who, run_id=run_id, after=0)
        assert [kind for _, kind in poll.events] == [EventKind.ROUTE_PINNED]
        after_poll = second.info.transaction_status
        assert after_poll == TransactionStatus.IDLE
        with second.transaction(force_rollback=True):
            second.execute("INSERT INTO cases (case_id) VALUES (%s)", ("zenith",))
            poll_events(second, identity=who, run_id=run_id, after=0)
            inside = second.info.transaction_status
            assert inside == TransactionStatus.INTRANS
        left = second.execute(
            "SELECT count(*) FROM cases WHERE case_id = %s", ("zenith",)
        ).fetchone()
        assert left == (0,), "the poll committed nothing of the caller's"


def test_an_unknown_run_refuses_before_any_stream_opens(store: Store) -> None:
    with pytest.raises(Refusal) as caught:
        poll_events(store, identity=_member(), run_id=str(uuid.uuid4()), after=0)
    assert caught.value.code is RefusalCode.RUN_NOT_FOUND
