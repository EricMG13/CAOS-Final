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


def admit_source(
    store: Store, *, case_id: str, sha256: str, tokens: list[Token]
) -> str:
    """Admit one document and its whole token index, or admit neither."""
    try:
        return _admit(store, case_id=case_id, sha256=sha256, tokens=tokens)
    except errors.UniqueViolation as violation:
        code = _REFUSALS.get(
            violation.diag.constraint_name or "",
            RefusalCode.SOURCE_TOKEN_INDEX_INVALID,
        )
    # Raised outside the handler on purpose. Inside it, the driver exception is
    # attached as __context__ -- and `raise ... from None` only hides that from
    # a traceback, it does not detach it. The DETAIL line carries key values.
    raise Refusal(code)


def _admit(store: Store, *, case_id: str, sha256: str, tokens: list[Token]) -> str:
    source_id = str(uuid.uuid4())
    with store.transaction():
        store.execute(
            "INSERT INTO cases (case_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (case_id,),
        )
        store.execute(
            "INSERT INTO sources (source_id, case_id, sha256) VALUES (%s, %s, %s)",
            (source_id, case_id, sha256),
        )
        with store.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO source_tokens"
                " (source_id, page, region_id, line_id, ordinal, text,"
                " x0, y0, x1, y1)"
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
    return source_id
