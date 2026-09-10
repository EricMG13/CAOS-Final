"""The run's event tail (`docs/SYSTEM_SPEC.md` §9).

Server-sent events over `run_events`, resumable by `Last-Event-ID`. The client
never reads a payload: an event name is what tells it to refetch the run, so a
frame carries its seq, its name and an empty object.

Three things end a tail. A terminal run whose every event has been delivered,
because there will be no more. A member whose standing has gone, because
membership is rechecked before each event and not only at the request. And the
deadline, because a stream held open for hours is an authorisation nobody
revisits -- the client reconnects with `Last-Event-ID` and the edge
reauthenticates it.

One poll is one statement inside its own transaction, and the connection is
left idle before every `await`. That is not tidiness: one synchronous
connection serves every request on the event loop, so a transaction still open
at a yield point would swallow the next request's into a savepoint of this
reader's -- for as long as the tail lives.
"""

from __future__ import annotations

import asyncio
import time
from collections import Counter
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass

import psycopg

from server.api.identity import Identity
from server.api.runs import RunState
from server.digests import checked_uuid
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.events import EventKind

# Store round-trips one poll may cost (test_io_budget_event_tail): the run, the
# member's standing on its case and the events after a seq, in one statement.
IO_BUDGET = 1

# `run_events.seq` is an `integer`, so ten digits covers every id a client can
# legitimately return. The bound is not tidiness: `int()` refuses a string of
# more than 4300 digits outright, and `last_seen` runs before the poll that
# authorises the request, so an unbounded one is a stranger's traceback.
_SEQ_DIGITS = 10

# What one instance holds open at once, and what one member may have of it.
# §11 wants the instance ceiling enforced rather than assumed, and this is the
# first route whose purpose is to hold a request open for minutes: a thousand
# tails put a thousand statements a second on the one connection every other
# request shares, and stall them all (`docs/DECISIONS.md` §51).
MAX_TAILS = 100
MAX_TAILS_PER_MEMBER = 4
_OPEN: Counter[str] = Counter()

# How long the tail waits before looking again. It buys store load against
# how long a member whose standing was revoked keeps reading: membership is
# rechecked at every poll, so this is that ceiling, and one statement a second
# per open stream is what it costs.
POLL_SECONDS = 1.0
# How long a tail lives. `docs/SYSTEM_SPEC.md` §9's five minutes, after which
# the client reconnects with `Last-Event-ID` and the edge reauthenticates it.
TAIL_SECONDS = 300.0

# One statement, because the three questions have one answer: rows mean this is
# a run on a case this member is on, and no rows mean nothing more than that
# (§8). The LEFT JOIN keeps the run's row when it has no event after `after`.
_TAIL = (
    "SELECT r.state, e.seq, e.kind FROM runs r"
    " JOIN case_members m ON m.case_id = r.case_id"
    " LEFT JOIN run_events e ON e.run_id = r.run_id AND e.seq > %s"
    " WHERE r.run_id = %s AND m.member_id = %s"
    " ORDER BY e.seq"
)


@dataclass(frozen=True, slots=True)
class Poll:
    """One look at a run's stream: what is new, and whether there will be more."""

    events: tuple[tuple[int, EventKind], ...]
    terminal: bool


def poll_events(
    store: Store, *, identity: Identity | None, run_id: str, after: int
) -> Poll:
    """The events after `after`, or a refusal that says nothing about the run.

    Decodes `kind` rather than trusting it. `run_events.kind` carries no CHECK
    and the value is framed into the response, where a newline would forge an
    event, so a kind the host did not write raises before it can be framed --
    the host's own failure, like a pin it cannot read back, and not a refusal.
    """
    if identity is None:
        raise Refusal(RefusalCode.STANDING_INSUFFICIENT)
    run_id = checked_uuid(run_id, refusal=RefusalCode.RUN_NOT_FOUND)
    with store.transaction():
        rows = store.execute(
            _TAIL, (after, run_id, identity.member_id.value)
        ).fetchall()
    if not rows:
        raise Refusal(RefusalCode.RUN_NOT_FOUND)
    return Poll(
        events=tuple(
            (int(seq), EventKind(str(kind))) for _, seq, kind in rows if seq is not None
        ),
        terminal=RunState(str(rows[0][0])) is not RunState.RUNNING,
    )


def reserve_tail(identity: Identity) -> None:
    """Take a place at the ceiling, or refuse. Checked after standing is."""
    if sum(_OPEN.values()) >= MAX_TAILS:
        raise Refusal(RefusalCode.STREAM_CEILING_EXCEEDED)
    if _OPEN[identity.member_id.value] >= MAX_TAILS_PER_MEMBER:
        raise Refusal(RefusalCode.STREAM_CEILING_EXCEEDED)
    _OPEN[identity.member_id.value] += 1


def release_tail(identity: Identity) -> None:
    """Give the place back. Releasing what was never reserved is a no-op.

    The reservation is the endpoint's, so a refusal is a status rather than a
    stream that opens and shuts; the release is the tail's, because only it
    knows when the client went away. A caller driving `event_tail` without
    reserving must not push the count below what is really open.
    """
    member = identity.member_id.value
    if _OPEN[member] > 0:
        _OPEN[member] -= 1
    if not _OPEN[member]:
        del _OPEN[member]


async def event_tail(
    store: Store,
    *,
    identity: Identity,
    run_id: str,
    after: int,
    first: Poll,
) -> AsyncIterator[str]:
    """Frame every event as it arrives, and return when the tail is over.

    Returning ends the body cleanly, which a browser answers by reconnecting a
    few seconds later with `Last-Event-ID` -- so ending is a pause, not a
    goodbye. The endpoint says goodbye with `204`, the one status that stops
    `EventSource` asking.
    """
    deadline = time.monotonic() + TAIL_SECONDS
    poll = first
    try:
        while True:
            for seq, kind in poll.events:
                yield f"id: {seq}\nevent: {kind.value}\ndata: {{}}\n\n"
                after = seq
            if poll.terminal or time.monotonic() >= deadline:
                return
            if not poll.events:
                # A comment, which every client ignores. Without it a quiet run
                # sends no byte for five minutes, and a buffering proxy between
                # here and the browser times the stream out first.
                yield ":\n\n"
            await asyncio.sleep(POLL_SECONDS)
            try:
                poll = poll_events(store, identity=identity, run_id=run_id, after=after)
            except (Refusal, ValueError, psycopg.Error):
                # Standing gone, the run with it, a row the host did not write,
                # or the store itself. The status line went out with the first
                # frame, so there is nothing left to say: the tail ends and the
                # client reconnects with `Last-Event-ID`. Ending on the store's
                # own failure matters most -- raising truncates the body, and
                # does it again on every reconnect.
                return
    finally:
        # However this ended, including the client vanishing mid-frame.
        release_tail(identity)


def last_seen(headers: Iterable[tuple[str, str]]) -> int:
    """The seq a reconnecting client already has, from `Last-Event-ID`.

    Anything that is not one resumes from the start. The client is then sent
    events it may already hold, which it cannot misread: the payload is nothing
    and the name only says to refetch.

    ASCII digits and few of them. `str.isdigit` is true of a superscript that
    `int` then refuses, and a header arrives decoded latin-1, so U+00B2 is two
    bytes a client could otherwise crash a request with -- before the poll
    that would have refused it for having no standing.
    """
    for name, value in headers:
        if (
            name.lower() == "last-event-id"
            and len(value) <= _SEQ_DIGITS
            and value.isascii()
            and value.isdigit()
        ):
            return int(value)
    return 0
