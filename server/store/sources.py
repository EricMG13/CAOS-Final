"""Admitting a pack of source documents: their blocks and their token index.

Three things a source carries, easily confused because all three are numbered:

- a **block** is what `read_evidence` returns -- one addressable piece of the
  source, keyed `(source_id, block_id)`;
- a **region** is a column or a paragraph, and a **line** is a line within it.
  Both belong to `source_tokens` and exist only so a quote can be re-located
  and one that cannot be re-located refused (invariant 11).

Blocks and regions are independent: nothing maps one onto the other, and
nothing needs to. Tokens never leave the host.

Pinning a source set lives in `server/store/source_sets.py`: it shares only the
store and `code_for` with this module.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from psycopg import errors

from server.boundary_text import BoundaryText
from server.digests import checked_digest, checked_uuid
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.audit import AuditEvent, AuditKind, record
from server.store.members import Standing, require_standing

# Who may withdraw. A reader is shown the evidence and does not manage it.
_MAY_WITHDRAW = frozenset({Standing.WRITER, Standing.APPROVER, Standing.ADMIN})


@dataclass(frozen=True, slots=True)
class Block:
    """The unit `read_evidence` returns: one addressable piece of a source.

    Unrelated to a token's `region_id`: a block is what a module reads, a region
    is where a quote may wrap. Nothing maps one onto the other.
    """

    block_id: int
    page: int
    text: str


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """One document as it enters a case: its digest, its index, its blocks."""

    sha256: str
    tokens: tuple[Token, ...]
    blocks: tuple[Block, ...]


@dataclass(frozen=True, slots=True)
class Token:
    """One extracted text run, with the rectangle it occupies on its page.

    The rectangle is PDF user space: points from the page's lower-left corner,
    y upwards, so `(x0, y0)` is the bottom-left corner and `(x1, y1)` the top
    right. A region is a column or a paragraph -- not CONTEXT.md's `block`, which is
    the unit `read_evidence` returns. `region_id` and `line_id` come from the
    extractor, not from geometry here:
    separating two columns that share a y-band is layout analysis, and a
    threshold in the anchoring path would be a heuristic on the evidence
    boundary.
    """

    page: int
    region_id: int
    line_id: int
    ordinal: int
    text: str
    x0: Decimal
    y0: Decimal
    x1: Decimal
    y1: Decimal


# The store's uniqueness rules, in the host's own words. A driver exception
# would carry a constraint name, a table and the vendor into whatever logs it.
_REFUSALS = {
    "sources_admitted_once": RefusalCode.SOURCE_ALREADY_ADMITTED,
    "source_tokens_pkey": RefusalCode.SOURCE_TOKEN_INDEX_INVALID,
}


def admit_pack(
    store: Store, *, case_id: BoundaryText, documents: tuple[SourceDocument, ...]
) -> tuple[str, ...]:
    """Admit every document in a pack, or none of them.

    A pack is admitted or refused whole (SYSTEM_SPEC section 5): a partly
    admitted pack is a case whose evidence nobody chose.
    """
    try:
        return _admit_pack(store, case_id=case_id, documents=documents)
    except errors.IntegrityError as violation:
        code = code_for(violation.diag.constraint_name)
    # Raised outside the handler on purpose. Inside it, the driver exception is
    # attached as __context__ -- and `raise ... from None` only hides that from
    # a traceback, it does not detach it. The DETAIL line carries key values.
    raise Refusal(code)


def withdraw_source(
    store: Store, *, case_id: BoundaryText, source_id: str, actor: BoundaryText
) -> bool:
    """Withdraw a source from every use from now on. True now; False if already.

    The row stays, and so does every pin that names it: a pinned set is
    immutable, and an already-executed run was pinned to this source. What
    changes is each use from here -- `read_evidence` refuses the block, a
    citation no longer anchors in it, `pin_source_set` refuses the source, and
    a plan re-derived over a set that names it no longer names it (invariant
    1: checked live at every use).

    Destructive and final, so it carries the standing check a gate's release
    carries: a writer, approver or admin on the case, read under `FOR SHARE`
    inside this transaction so a revocation waits for it. A reader may not.
    A governed write, so the actor is recorded on the case's audit chain in
    the same transaction: the withdrawal commits with its event or not at all.

    `withdrawn_at IS NULL` on the UPDATE is what keeps a second withdrawal from
    reaching the finality trigger; a row it did not match is read again to
    tell "already withdrawn" from "no such source". One refusal for a source
    of another case, of no case, or an id that is no id at all -- the last
    checked before the store sees it, since the driver's complaint would name
    the type.
    """
    source_id = checked_uuid(source_id, refusal=RefusalCode.SOURCE_NOT_IN_CASE)
    params = (case_id.value, source_id)
    with store.transaction():
        require_standing(
            store, case_id=case_id.value, member_id=actor, allowed=_MAY_WITHDRAW
        )
        updated = store.execute(
            "UPDATE sources SET withdrawn_at = now()"
            " WHERE case_id = %s AND source_id = %s AND withdrawn_at IS NULL",
            params,
        )
        if updated.rowcount == 1:
            event = AuditEvent(
                kind=AuditKind.SOURCE_WITHDRAWN,
                actor=actor,
                subject=BoundaryText.of(source_id),
            )
            record(store, case_id=case_id, event=event)
            return True
        found = store.execute(
            "SELECT 1 FROM sources WHERE case_id = %s AND source_id = %s", params
        ).fetchone()
        if found is None:
            raise Refusal(RefusalCode.SOURCE_NOT_IN_CASE)
    return False


def code_for(constraint_name: str | None) -> RefusalCode:
    """The host's word for a store rule that was broken. Never the driver's.

    Takes the name rather than the exception so the mapping can be read and
    tested without constructing a driver error, and so nothing downstream is
    handed something carrying a DETAIL line.
    """
    return _REFUSALS.get(constraint_name or "", RefusalCode.SOURCE_NOT_ADMISSIBLE)


def _admit_pack(
    store: Store, *, case_id: BoundaryText, documents: tuple[SourceDocument, ...]
) -> tuple[str, ...]:
    with store.transaction():
        store.execute(
            "INSERT INTO cases (case_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (case_id.value,),
        )
        return tuple(
            _admit_document(store, case_id=case_id, document=document)
            for document in documents
        )


def _admit_document(
    store: Store, *, case_id: BoundaryText, document: SourceDocument
) -> str:
    source_id = str(uuid.uuid4())
    store.execute(
        "INSERT INTO sources (source_id, case_id, sha256) VALUES (%s, %s, %s)",
        (source_id, case_id.value, checked_digest(document.sha256)),
    )
    tokens = document.tokens
    with store.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO source_tokens"
            " (source_id, page, region_id, line_id, ordinal, text, x0, y0, x1, y1)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    source_id,
                    token.page,
                    token.region_id,
                    token.line_id,
                    token.ordinal,
                    token.text,
                    token.x0,
                    token.y0,
                    token.x1,
                    token.y1,
                )
                for token in tokens
            ],
        )
        cursor.executemany(
            "INSERT INTO source_blocks (source_id, block_id, page, text)"
            " VALUES (%s, %s, %s, %s)",
            [
                (source_id, block.block_id, block.page, block.text)
                for block in document.blocks
            ],
        )
    return source_id
