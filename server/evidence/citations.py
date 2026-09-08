"""Coordinate-anchored citations (invariant 11).

The host re-locates `matched_text` in its own token index at the stated page and
derives the rectangle. A module's claim about where its quote sits is an
expectation, not authority (invariant 3), so `anchor_citation` takes no bbox --
it returns the one it derived, and refuses a quote it cannot re-locate.

Matching is whitespace-insensitive in both directions: the index holds one token
per extracted run, while a module quotes a running sentence. Nothing else about
the text is normalised, so a quote that differs by a character is not a match.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.sources import Token

# One source lookup, one page fetch. Never a whole-source parse: that was the
# predecessor's ~8x I/O defect (docs/AI_CODE_QUALITY.md section 1).
IO_BUDGET = 2


@dataclass(frozen=True, slots=True)
class Citation:
    """`{document_sha256, page, bbox, matched_text}` -- the bbox host-derived."""

    document_sha256: str
    page: int
    bbox: tuple[Decimal, Decimal, Decimal, Decimal]
    matched_text: str


def _collapse(text: str) -> str:
    return " ".join(text.split())


def page_text(tokens: list[Token]) -> tuple[str, list[int]]:
    """The page as one string, and the token each character came from.

    Tokens are joined by a single space so a quote that runs across several of
    them matches; the map is what turns a character span back into a rectangle.
    """
    parts: list[str] = []
    owners: list[int] = []
    for index, token in enumerate(tokens):
        if parts:
            parts.append(" ")
            owners.append(index)
        collapsed = _collapse(token.text)
        parts.append(collapsed)
        owners.extend([index] * len(collapsed))
    return "".join(parts), owners


def enclosing_box(tokens: list[Token]) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """The smallest rectangle containing every token given."""
    return (
        min(token.x0 for token in tokens),
        min(token.y0 for token in tokens),
        max(token.x1 for token in tokens),
        max(token.y1 for token in tokens),
    )


def locate(tokens: list[Token], matched_text: str) -> list[Token]:
    """The tokens a quote covers, or a refusal if the page does not carry it once.

    A quote appearing twice on a page has two rectangles, so it has none: a
    citation that points at one of two places is not evidence. The module is
    expected to quote enough context to be unambiguous.
    """
    quote = _collapse(matched_text)
    if not quote:
        raise Refusal(RefusalCode.CITATION_NOT_LOCATABLE)
    text, owners = page_text(tokens)
    start = text.find(quote)
    if start < 0:
        raise Refusal(RefusalCode.CITATION_NOT_LOCATABLE)
    if text.find(quote, start + 1) >= 0:
        raise Refusal(RefusalCode.CITATION_AMBIGUOUS)
    return tokens[owners[start] : owners[start + len(quote) - 1] + 1]


def _page_tokens(
    store: Store, *, case_id: str, document_sha256: str, page: int
) -> list[Token]:
    # Scoped to the case. The same document in two cases is ordinary, and each
    # case holds its own copy: an unscoped lookup would return an arbitrary one.
    found = store.execute(
        "SELECT source_id FROM sources WHERE case_id = %s AND sha256 = %s",
        (case_id, document_sha256),
    ).fetchone()
    if found is None:
        raise Refusal(RefusalCode.CITATION_NOT_LOCATABLE)
    rows = store.execute(
        "SELECT page, ordinal, text, x0, y0, x1, y1 FROM source_tokens"
        " WHERE source_id = %s AND page = %s ORDER BY ordinal",
        (found[0], page),
    ).fetchall()
    return [Token(*row) for row in rows]


def anchor_citation(
    store: Store, *, case_id: str, document_sha256: str, page: int, matched_text: str
) -> Citation:
    """Re-locate a quote within its case and derive its rectangle, or refuse it."""
    covered = locate(
        _page_tokens(
            store, case_id=case_id, document_sha256=document_sha256, page=page
        ),
        matched_text,
    )
    return Citation(
        document_sha256=document_sha256,
        page=page,
        bbox=enclosing_box(covered),
        matched_text=matched_text,
    )
