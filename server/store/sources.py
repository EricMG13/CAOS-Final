"""Sources and their token index.

A token is one extracted text run with its page and rectangle. Tokens never
leave the host: they exist so a quote can be re-located and one that cannot be
re-located refused (invariant 11).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from psycopg import errors

from server.refusals import Refusal, RefusalCode
from server.store import Store


@dataclass(frozen=True, slots=True)
class Block:
    """The unit `read_evidence` returns: one addressable piece of a source."""

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

    A region is a column or a paragraph -- not CONTEXT.md's `block`, which is
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
    "sources_case_id_sha256_key": RefusalCode.SOURCE_ALREADY_ADMITTED,
    "source_tokens_pkey": RefusalCode.SOURCE_TOKEN_INDEX_INVALID,
}


def admit_pack(
    store: Store, *, case_id: str, documents: tuple[SourceDocument, ...]
) -> tuple[str, ...]:
    """Admit every document in a pack, or none of them.

    A pack is admitted or refused whole (SYSTEM_SPEC section 5): a partly
    admitted pack is a case whose evidence nobody chose.
    """
    try:
        return _admit_pack(store, case_id=case_id, documents=documents)
    except errors.IntegrityError as violation:
        code = _code_for(violation)
    # Raised outside the handler on purpose. Inside it, the driver exception is
    # attached as __context__ -- and `raise ... from None` only hides that from
    # a traceback, it does not detach it. The DETAIL line carries key values.
    raise Refusal(code)


def _code_for(violation: errors.IntegrityError) -> RefusalCode:
    """The host's word for a store rule the pack broke. Never the driver's."""
    return _REFUSALS.get(
        violation.diag.constraint_name or "", RefusalCode.SOURCE_NOT_ADMISSIBLE
    )


def pin_source_set(store: Store, *, case_id: str, source_ids: tuple[str, ...]) -> int:
    """Pin an immutable, versioned set of this case's sources; return its version.

    A set is a set: naming a source twice pins it once. Naming none is refused --
    a run pinned to no evidence is a mistake worth making early.
    """
    members = tuple(dict.fromkeys(source_ids))
    if not members:
        raise Refusal(RefusalCode.SOURCE_SET_EMPTY)
    try:
        return _pin(store, case_id=case_id, members=members)
    except errors.IntegrityError as violation:
        code = _code_for(violation)
    raise Refusal(code)


def _pin(store: Store, *, case_id: str, members: tuple[str, ...]) -> int:
    with store.transaction():
        # The case row lock is taken before the current version is read, so two
        # pins cannot allocate the same one.
        store.execute(
            "SELECT case_id FROM cases WHERE case_id = %s FOR UPDATE", (case_id,)
        )
        mine = store.execute(
            "SELECT count(*) FROM sources WHERE case_id = %s AND source_id = ANY(%s)",
            (case_id, list(members)),
        ).fetchone()
        if mine is None or mine[0] != len(members):
            raise Refusal(RefusalCode.SOURCE_NOT_IN_CASE)
        allocated = store.execute(
            "INSERT INTO source_sets (case_id, version)"
            " SELECT %s, coalesce(max(version), 0) + 1 FROM source_sets"
            " WHERE case_id = %s RETURNING version",
            (case_id, case_id),
        ).fetchone()
        if allocated is None:  # pragma: no cover - RETURNING always yields a row
            raise Refusal(RefusalCode.SOURCE_NOT_IN_CASE)
        version = int(allocated[0])
        with store.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO source_set_members (case_id, version, source_id)"
                " VALUES (%s, %s, %s)",
                [(case_id, version, source_id) for source_id in members],
            )
    return version


def _admit_pack(
    store: Store, *, case_id: str, documents: tuple[SourceDocument, ...]
) -> tuple[str, ...]:
    with store.transaction():
        store.execute(
            "INSERT INTO cases (case_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (case_id,),
        )
        return tuple(
            _admit_document(store, case_id=case_id, document=document)
            for document in documents
        )


def _admit_document(store: Store, *, case_id: str, document: SourceDocument) -> str:
    source_id = str(uuid.uuid4())
    store.execute(
        "INSERT INTO sources (source_id, case_id, sha256) VALUES (%s, %s, %s)",
        (source_id, case_id, document.sha256),
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
