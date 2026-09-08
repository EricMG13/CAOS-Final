"""Sources and their token index.

A token is one extracted text run with its page and rectangle. Tokens never
leave the host: they exist so a quote can be re-located and one that cannot be
re-located refused (invariant 11).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from server.store import Store


@dataclass(frozen=True, slots=True)
class Token:
    """One extracted text run, with the rectangle it occupies on its page."""

    page: int
    ordinal: int
    text: str
    x0: Decimal
    y0: Decimal
    x1: Decimal
    y1: Decimal


def admit_source(
    store: Store, *, case_id: str, sha256: str, tokens: list[Token]
) -> str:
    """Admit one document and its whole token index, or admit neither."""
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
                " (source_id, page, ordinal, text, x0, y0, x1, y1)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        source_id,
                        token.page,
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
