"""The audit chain: every governed write, hash-chained per case.

`docs/SYSTEM_SPEC.md` §2. A governed write commits its state and its audit
event in one transaction, so `record` is called from inside the caller's
transaction, like `emit`. The chain has no external anchor; what it can prove
is internal, and the emitter checks the one link it can before adding
another: the head row must be the digest of the last event as it stands. A
head that was moved, an event rewritten with its triggers disabled and a chain
cut short each refuse the next governed write by code, so nothing is written
over a history that no longer holds.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from server.boundary_text import BoundaryText
from server.refusals import Refusal, RefusalCode
from server.store import Store

# What the first event of a chain links to: a head with nothing under it.
GENESIS = "0" * 64


class AuditKind(StrEnum):
    """The governed writes the chain records, and no others."""

    MEMBERSHIP_GRANTED = "MEMBERSHIP_GRANTED"
    MEMBERSHIP_REVOKED = "MEMBERSHIP_REVOKED"
    SOURCE_WITHDRAWN = "SOURCE_WITHDRAWN"


@dataclass(frozen=True, slots=True, kw_only=True)
class AuditEvent:
    """One governed write as the chain records it: who did what, to what.

    Keyword-only because actor and subject are the same type, and a caller
    that swapped them would record the wrong person with nothing to say so.
    """

    kind: AuditKind
    actor: BoundaryText
    subject: BoundaryText
    detail: BoundaryText | None = None


def record(store: Store, *, case_id: BoundaryText, event: AuditEvent) -> str:
    """Append one event to the case's chain and return its digest, the new head.

    Wants an open transaction: the caller's state change is what this records,
    and the two commit together or not at all. The head row is the lock -- a
    no-op update on conflict is what takes it and hands the row back -- so two
    writes on one case allocate two seqs. Selecting the case rather than
    naming it refuses an unknown one by code, not by the head's foreign key.
    `at` is the clock read under that lock, not `now()`: the transaction's
    start would put a write that waited before the event it waited on.
    """
    head = store.execute(
        "INSERT INTO audit_chain_heads (case_id, seq, head)"
        " SELECT case_id, 0, %s FROM cases WHERE case_id = %s"
        " ON CONFLICT (case_id) DO UPDATE SET head = audit_chain_heads.head"
        " RETURNING seq, head, clock_timestamp()",
        (GENESIS, case_id.value),
    ).fetchone()
    if head is None:
        raise Refusal(RefusalCode.CASE_NOT_FOUND)
    seq, prev, at = int(head[0]), str(head[1]), head[2]
    # Its own statement on purpose: READ COMMITTED takes a snapshot per
    # statement, and this is the one that has to see the event committed by
    # the writer whose lock the statement above just waited on.
    if (seq, prev) != _last_link(store, case_id.value):
        raise Refusal(RefusalCode.AUDIT_CHAIN_BROKEN)
    told = (
        event.kind.value,
        event.actor.value,
        event.subject.value,
        None if event.detail is None else event.detail.value,
    )
    seq += 1
    digest = _digest(case_id.value, seq, prev, told, at)
    # One round trip for the two writes: a data-modifying CTE runs to
    # completion whether or not the statement around it reads from it.
    store.execute(
        "WITH appended AS (INSERT INTO audit_events"
        " (case_id, seq, prev_sha256, sha256, kind, actor, subject, detail, at)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s))"
        " UPDATE audit_chain_heads SET seq = %s, head = %s WHERE case_id = %s",
        (case_id.value, seq, prev, digest, *told, at, seq, digest, case_id.value),
    )
    return digest


def _last_link(store: Store, case_id: str) -> tuple[int, str]:
    """What the head must say: the last event's seq and digest, recomputed now."""
    last = store.execute(
        "SELECT seq, prev_sha256, kind, actor, subject, detail, at"
        " FROM audit_events WHERE case_id = %s ORDER BY seq DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    if last is None:
        return 0, GENESIS
    seq, prev, kind, actor, subject, detail, at = last
    told = (kind, actor, subject, detail)
    return int(seq), _digest(case_id, int(seq), str(prev), told, at)


def _digest(
    case_id: str,
    seq: int,
    prev: str,
    told: tuple[str, str, str, str | None],
    at: datetime,
) -> str:
    """The canonical form: what a verifier with the standard library recomputes.

    Compact JSON over a list, so there is no key order to agree on, and the
    timestamp in UTC to the microsecond, which is the column's own precision.
    """
    stamped = at.astimezone(UTC).isoformat(timespec="microseconds")
    fields = [case_id, seq, prev, *told, stamped]
    canonical = json.dumps(fields, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
