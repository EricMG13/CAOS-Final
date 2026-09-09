"""Coordinate-anchored citations (invariant 11).

The host re-locates `matched_text` in its own token index at the stated page and
derives one rectangle per line the quote covers -- the shape of a PDF highlight's
QuadPoints, and for the same reason: selected text wraps. A module's claim about
where its quote sits is an expectation, not authority (invariant 3), so
`anchor_citation` takes no rectangle; it returns the ones it derived.

A quote may run within a line and continue onto the next line **of its own
region** -- a column or a paragraph, as the extractor found it. Nothing joins
across regions, so two columns sharing a y-band cannot be assembled into a
phrase the page does not carry. Matching is whitespace-
insensitive in both directions -- the index holds one token per extracted run
while a module quotes a running sentence -- and nothing else is normalised, so a
quote differing by a character is not a match.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import groupby

from server.boundary_text import BoundaryText
from server.digests import checked_digest
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.sources import Token

# One source lookup, one page fetch. Never a whole-source parse: that was the
# predecessor's ~8x I/O defect (docs/AI_CODE_QUALITY.md section 1).
IO_BUDGET = 2

type Rectangle = tuple[Decimal, Decimal, Decimal, Decimal]


@dataclass(frozen=True, slots=True)
class Citation:
    """`{document_sha256, page, bboxes, matched_text}`, the rectangles derived.

    One rectangle per line the quote covers, in reading order.
    """

    document_sha256: str
    page: int
    bboxes: tuple[Rectangle, ...]
    matched_text: str


def _collapse(text: str) -> str:
    return " ".join(text.split())


def _enclosing_box(tokens: list[Token]) -> Rectangle:
    """The smallest rectangle containing every token given."""
    return (
        min(token.x0 for token in tokens),
        min(token.y0 for token in tokens),
        max(token.x1 for token in tokens),
        max(token.y1 for token in tokens),
    )


def _token_runs(members: list[Token], quote: str) -> list[list[Token]]:
    """Every run of whole, consecutive tokens that reads exactly as the quote.

    Whole tokens, never a substring of one: `find` over the joined text would
    match "4.2x" inside "14.2x" and box the whole token, a rectangle enclosing
    a digit the quote does not contain. A quote either is a run of tokens as the
    extractor cut them, or it is not on the page.
    """
    words = [_collapse(token.text) for token in members]
    runs = []
    for start in range(len(words)):
        stop = start + 1
        joined = words[start]
        while len(joined) < len(quote) and stop < len(words):
            joined = f"{joined} {words[stop]}"
            stop += 1
        if joined == quote:
            runs.append(members[start:stop])
    return runs


def _locate(tokens: list[Token], matched_text: str) -> list[list[Token]]:
    """The tokens a quote covers, one list per line, or a refusal.

    A quote absent from every region is not locatable; one present in more than
    one place has as many rectangles as occurrences, so it has none.
    """
    quote = _collapse(matched_text)
    if not quote:
        raise Refusal(RefusalCode.CITATION_NOT_LOCATABLE)

    hits = [
        run
        for _, region in groupby(tokens, key=lambda token: token.region_id)
        for run in _token_runs(list(region), quote)
    ]
    if not hits:
        raise Refusal(RefusalCode.CITATION_NOT_LOCATABLE)
    if len(hits) > 1:
        raise Refusal(RefusalCode.CITATION_AMBIGUOUS)
    by_line = groupby(hits[0], key=lambda token: (token.region_id, token.line_id))
    return [list(line) for _, line in by_line]


def _page_tokens(
    store: Store, *, case_id: BoundaryText, document_sha256: str, page: int
) -> list[Token]:
    # Scoped to the case. The same document in two cases is ordinary, and each
    # case holds its own copy: an unscoped lookup would return an arbitrary one.
    with store.transaction():
        found = store.execute(
            "SELECT source_id FROM sources WHERE case_id = %s AND sha256 = %s",
            (case_id.value, checked_digest(document_sha256)),
        ).fetchone()
        if found is None:
            raise Refusal(RefusalCode.CITATION_NOT_LOCATABLE)
        rows = store.execute(
            "SELECT page, region_id, line_id, ordinal, text, x0, y0, x1, y1"
            " FROM source_tokens WHERE source_id = %s AND page = %s"
            " ORDER BY region_id, line_id, ordinal",
            (found[0], page),
        ).fetchall()
    return [Token(*row) for row in rows]


def anchor_citation(
    store: Store,
    *,
    case_id: BoundaryText,
    document_sha256: str,
    page: int,
    matched_text: str,
) -> Citation:
    """Re-_locate a quote within its case and derive its rectangles, or refuse it."""
    covering = _locate(
        _page_tokens(
            store, case_id=case_id, document_sha256=document_sha256, page=page
        ),
        matched_text,
    )
    return Citation(
        document_sha256=document_sha256,
        page=page,
        bboxes=tuple(_enclosing_box(line) for line in covering),
        matched_text=matched_text,
    )
