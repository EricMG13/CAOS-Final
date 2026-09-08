"""Coordinate-anchored citations (invariant 11).

The host re-locates `matched_text` in its own token index at the stated page and
derives one rectangle per line the quote covers -- the shape of a PDF highlight's
QuadPoints, and for the same reason: selected text wraps. A module's claim about
where its quote sits is an expectation, not authority (invariant 3), so
`anchor_citation` takes no rectangle; it returns the ones it derived.

A quote may run within a line and continue onto the next line **of its own
block**. Nothing joins across blocks, so two columns sharing a y-band cannot be
assembled into a phrase the page does not carry. Matching is whitespace-
insensitive in both directions -- the index holds one token per extracted run
while a module quotes a running sentence -- and nothing else is normalised, so a
quote differing by a character is not a match.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import groupby

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


def line_runs(tokens: list[Token]) -> list[tuple[str, list[Token]]]:
    """Each line as its collapsed text and the tokens that make it up."""
    runs = []
    for _, line in groupby(tokens, key=lambda token: (token.block_id, token.line_id)):
        members = list(line)
        runs.append((" ".join(_collapse(token.text) for token in members), members))
    return runs


def enclosing_box(tokens: list[Token]) -> Rectangle:
    """The smallest rectangle containing every token given."""
    return (
        min(token.x0 for token in tokens),
        min(token.y0 for token in tokens),
        max(token.x1 for token in tokens),
        max(token.y1 for token in tokens),
    )


def _covered(
    runs: list[tuple[str, list[Token]]], start: int, stop: int
) -> list[list[Token]]:
    """The tokens a character span covers, split back into one list per line."""
    covering: list[list[Token]] = []
    at = 0
    for text, members in runs:
        offset = 0
        line: list[Token] = []
        for token in members:
            width = len(_collapse(token.text))
            if at + offset < stop and at + offset + width > start:
                line.append(token)
            offset += width + 1
        if line:
            covering.append(line)
        at += len(text) + 1
    return covering


def locate(tokens: list[Token], matched_text: str) -> list[list[Token]]:
    """The tokens a quote covers, one list per line, or a refusal.

    A quote absent from every block is not locatable; one present in more than
    one place has as many rectangles as occurrences, so it has none.
    """
    quote = _collapse(matched_text)
    if not quote:
        raise Refusal(RefusalCode.CITATION_NOT_LOCATABLE)

    hits: list[list[list[Token]]] = []
    for _, block in groupby(tokens, key=lambda token: token.block_id):
        runs = line_runs(list(block))
        text = " ".join(line for line, _ in runs)
        at = text.find(quote)
        while at >= 0:
            hits.append(_covered(runs, at, at + len(quote)))
            at = text.find(quote, at + 1)

    if not hits:
        raise Refusal(RefusalCode.CITATION_NOT_LOCATABLE)
    if len(hits) > 1:
        raise Refusal(RefusalCode.CITATION_AMBIGUOUS)
    return hits[0]


def _page_tokens(
    store: Store, *, case_id: str, document_sha256: str, page: int
) -> list[Token]:
    # Scoped to the case. The same document in two cases is ordinary, and each
    # case holds its own copy: an unscoped lookup would return an arbitrary one.
    with store.transaction():
        found = store.execute(
            "SELECT source_id FROM sources WHERE case_id = %s AND sha256 = %s",
            (case_id, document_sha256),
        ).fetchone()
        if found is None:
            raise Refusal(RefusalCode.CITATION_NOT_LOCATABLE)
        rows = store.execute(
            "SELECT page, block_id, line_id, ordinal, text, x0, y0, x1, y1"
            " FROM source_tokens WHERE source_id = %s AND page = %s"
            " ORDER BY block_id, line_id, ordinal",
            (found[0], page),
        ).fetchall()
    return [Token(*row) for row in rows]


def anchor_citation(
    store: Store, *, case_id: str, document_sha256: str, page: int, matched_text: str
) -> Citation:
    """Re-locate a quote within its case and derive its rectangles, or refuse it."""
    covering = locate(
        _page_tokens(
            store, case_id=case_id, document_sha256=document_sha256, page=page
        ),
        matched_text,
    )
    return Citation(
        document_sha256=document_sha256,
        page=page,
        bboxes=tuple(enclosing_box(line) for line in covering),
        matched_text=matched_text,
    )
