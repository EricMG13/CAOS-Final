"""Invariant 11: citations are coordinate-anchored.

A citation is `{document_sha256, page, bboxes, matched_text}`. The host
re-locates the quote in its own token index at the stated page and derives one
rectangle per line the quote covers -- the shape of a PDF highlight's
QuadPoints, and for the same reason: selected text wraps.

The bboxes are derived, never accepted: a module's claim about where its quote
sits is an expectation, and invariant 3 says provider-claimed identity never
survives. A rectangle must never enclose text the quote does not contain, and a
quote must never be assembled across a column gutter -- both were true of the
single-enclosing-rectangle build this replaces (`docs/DECISIONS.md` §15).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from conftest import Counter

from server.boundary_text import BoundaryText
from server.evidence.citations import (
    IO_BUDGET,
    Citation,
    _enclosing_box,
    _line_runs,
    _locate,
    anchor_citation,
)
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.sources import SourceDocument, Token, admit_pack

CASE = BoundaryText.of("acme")
RIVAL = BoundaryText.of("rival")

DIGEST = "a" * 64


def _token(
    place: tuple[int, int, int], text: str, at: tuple[int, int], page: int = 3
) -> Token:
    """`place` is (block, line, ordinal); `at` is the token's top-left corner."""
    block, line, ordinal = place
    x0, y0 = at
    return Token(
        page=page,
        region_id=block,
        line_id=line,
        ordinal=ordinal,
        text=text,
        x0=Decimal(x0),
        y0=Decimal(y0),
        x1=Decimal(x0 + 4 * len(text)),
        y1=Decimal(y0 + 12),
    )


# Page 3, two lines. Page 4 exists so a wrong page has somewhere to hide.
def _tokens() -> list[Token]:
    line_1 = ["Net", "leverage", "was", "4.2x"]
    line_2 = ["at", "the", "year", "end"]
    tokens = []
    x = 72
    for ordinal, word in enumerate(line_1):
        tokens.append(_token((1, 1, ordinal), word, (x, 700)))
        x += 4 * len(word) + 4
    x = 72
    for ordinal, word in enumerate(line_2):
        tokens.append(_token((1, 2, ordinal), word, (x, 686)))
        x += 4 * len(word) + 4
    tokens.append(_token((2, 3, 0), "Covenant", (72, 700), page=4))
    return tokens


def _admit(
    store: Store, case_id: BoundaryText, digest: str, tokens: list[Token]
) -> None:
    admit_pack(
        store,
        case_id=case_id,
        documents=(SourceDocument(sha256=digest, tokens=tuple(tokens), blocks=()),),
    )


@pytest.fixture
def source(store: Store) -> None:
    _admit(store, CASE, DIGEST, _tokens())


def _anchor(store: Store, quote: str, page: int = 3) -> Citation:
    return anchor_citation(
        store, case_id=CASE, document_sha256=DIGEST, page=page, matched_text=quote
    )


def test_uncitable_quote_is_refused_before_artifact(store: Store, source: None) -> None:
    with pytest.raises(Refusal) as caught:
        _anchor(store, "Net leverage was 3.1x")
    assert caught.value.code is RefusalCode.CITATION_NOT_LOCATABLE


def test_a_quote_on_another_page_is_refused(store: Store, source: None) -> None:
    with pytest.raises(Refusal) as caught:
        _anchor(store, "Covenant")
    assert caught.value.code is RefusalCode.CITATION_NOT_LOCATABLE


def test_a_quote_within_one_line_gets_one_tight_rectangle(
    store: Store, source: None
) -> None:
    citation = _anchor(store, "leverage was")
    assert citation.bboxes == ((Decimal(88), Decimal(700), Decimal(136), Decimal(712)),)


def test_a_wrapped_quote_gets_one_rectangle_per_line(
    store: Store, source: None
) -> None:
    # The defect this replaces returned a single box enclosing both lines, and
    # therefore enclosing "Net leverage" and "year end", neither of them quoted.
    citation = _anchor(store, "was 4.2x at the")
    assert len(citation.bboxes) == 2
    first, second = citation.bboxes
    assert first == (Decimal(124), Decimal(700), Decimal(156), Decimal(712))
    assert second == (Decimal(72), Decimal(686), Decimal(96), Decimal(698))
    # Neither rectangle reaches the words that were not quoted.
    assert first[0] > Decimal(88), "must not reach back over 'leverage'"
    assert second[2] < Decimal(104), "must not reach forward over 'year'"


def test_a_quote_cannot_be_assembled_across_a_column_gutter(store: Store) -> None:
    # Two columns share a y-band and are consecutive lines, so line identity
    # alone would still join them. The extractor gives each column its own
    # region; "net debt" is on no line of this page and must not be citable.
    digest = "c" * 64
    _admit(
        store,
        CASE,
        digest,
        [
            _token((1, 1, 0), "Total", (72, 700), page=1),
            _token((1, 1, 1), "net", (120, 700), page=1),
            _token((2, 2, 0), "debt", (400, 700), page=1),
            _token((2, 2, 1), "rose", (448, 700), page=1),
        ],
    )
    with pytest.raises(Refusal) as caught:
        anchor_citation(
            store,
            case_id=CASE,
            document_sha256=digest,
            page=1,
            matched_text="net debt",
        )
    assert caught.value.code is RefusalCode.CITATION_NOT_LOCATABLE


def test_a_quote_whose_whitespace_differs_still_anchors(
    store: Store, source: None
) -> None:
    assert _anchor(store, "Net   leverage\nwas").bboxes == (
        (Decimal(72), Decimal(700), Decimal(136), Decimal(712)),
    )


def test_a_quote_appearing_twice_on_a_page_is_refused(store: Store) -> None:
    digest = "e" * 64
    _admit(
        store,
        CASE,
        digest,
        [
            _token((1, 1, 0), "total", (72, 700), page=1),
            _token((1, 1, 1), "debt", (120, 700), page=1),
            _token((1, 2, 0), "total", (72, 686), page=1),
            _token((1, 2, 1), "debt", (120, 686), page=1),
        ],
    )
    with pytest.raises(Refusal) as caught:
        anchor_citation(
            store,
            case_id=CASE,
            document_sha256=digest,
            page=1,
            matched_text="total debt",
        )
    assert caught.value.code is RefusalCode.CITATION_AMBIGUOUS


def test_a_quote_anchors_only_within_its_own_case(store: Store) -> None:
    shared = "f" * 64
    _admit(store, CASE, shared, _tokens())
    _admit(store, RIVAL, shared, [_token((1, 1, 0), "Net leverage", (500, 100))])
    citation = anchor_citation(
        store, case_id=CASE, document_sha256=shared, page=3, matched_text="Net"
    )
    assert citation.bboxes[0][0] == Decimal(72)


def test_the_refusal_carries_no_document_text(store: Store, source: None) -> None:
    with pytest.raises(Refusal) as caught:
        _anchor(store, "Net leverage was 9.9x")
    rendered = f"{caught.value!r} {caught.value!s} {caught.value.args}"
    assert "leverage" not in rendered
    assert "9.9x" not in rendered


def test_line_runs_keeps_each_line_separate() -> None:
    runs = _line_runs(_tokens()[:8])
    assert [text for text, _ in runs] == ["Net leverage was 4.2x", "at the year end"]


def test_enclosing_box_is_the_smallest_rectangle_over_the_tokens() -> None:
    covering = _tokens()[1:3]
    assert _enclosing_box(covering) == (
        Decimal(88),
        Decimal(700),
        Decimal(136),
        Decimal(712),
    )


def test_locate_splits_a_wrapped_quote_into_one_run_per_line() -> None:
    covering = _locate(_tokens()[:8], "was 4.2x at the")
    assert [[token.text for token in line] for line in covering] == [
        ["was", "4.2x"],
        ["at", "the"],
    ]


def test_locate_refuses_a_quote_that_would_span_two_blocks() -> None:
    columns = [
        _token((1, 1, 0), "Total", (72, 700), page=1),
        _token((2, 2, 0), "debt", (400, 700), page=1),
    ]
    with pytest.raises(Refusal):
        _locate(columns, "Total debt")


def test_io_budget_anchor_citation(
    store: Store, source: None, count_io: Counter
) -> None:
    # One source lookup and one page fetch, whatever the page holds.
    with count_io(store) as tally:
        _anchor(store, "leverage was")
    assert tally.statements == IO_BUDGET
