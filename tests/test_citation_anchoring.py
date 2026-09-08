"""Invariant 11: citations are coordinate-anchored.

A citation is `{document_sha256, page, bbox, matched_text}`. The host re-locates
the quote in its own token index at the stated page and derives the rectangle.
A quote it cannot re-locate is refused before it reaches the artifact.

The bbox is derived, never accepted: a module's claim about where its quote sits
is an expectation, and invariant 3 says provider-claimed identity never survives.
The predecessor's locators were line ranges over extracted text, so "one click
from its evidence" meant one click to a line range, not to a region on a page.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from server.evidence.citations import (
    Citation,
    anchor_citation,
    enclosing_box,
    page_text,
)
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.sources import Token, admit_source

DIGEST = "a" * 64

# "Net leverage was 4.2x at year end" laid out across one line of page 3, plus a
# second line, so a quote can span tokens and a wrong page has somewhere to hide.
PAGE_3 = [
    ("Net", 72, 700, 96, 712),
    ("leverage", 100, 700, 152, 712),
    ("was", 156, 700, 180, 712),
    ("4.2x", 184, 700, 212, 712),
    ("at", 216, 700, 228, 712),
    ("year", 232, 700, 260, 712),
    ("end", 264, 700, 288, 712),
]
PAGE_4 = [("Covenant", 72, 700, 130, 712), ("headroom", 134, 700, 196, 712)]


def _tokens() -> list[Token]:
    rows = [(3, PAGE_3), (4, PAGE_4)]
    return [
        Token(
            page=page,
            ordinal=ordinal,
            text=text,
            x0=Decimal(x0),
            y0=Decimal(y0),
            x1=Decimal(x1),
            y1=Decimal(y1),
        )
        for page, line in rows
        for ordinal, (text, x0, y0, x1, y1) in enumerate(line)
    ]


@pytest.fixture
def source(store: Store) -> str:
    return admit_source(store, case_id="acme", sha256=DIGEST, tokens=_tokens())


def test_uncitable_quote_is_refused_before_artifact(store: Store, source: str) -> None:
    with pytest.raises(Refusal) as caught:
        anchor_citation(
            store,
            case_id="acme",
            document_sha256=DIGEST,
            page=3,
            matched_text="Net leverage was 3.1x at year end",
        )
    assert caught.value.code is RefusalCode.CITATION_NOT_LOCATABLE


def test_a_quote_on_another_page_is_refused(store: Store, source: str) -> None:
    # The quote exists in the document, but not where the citation says it is.
    with pytest.raises(Refusal) as caught:
        anchor_citation(
            store,
            case_id="acme",
            document_sha256=DIGEST,
            page=3,
            matched_text="Covenant headroom",
        )
    assert caught.value.code is RefusalCode.CITATION_NOT_LOCATABLE


def test_the_derived_rectangle_encloses_exactly_the_quoted_tokens(
    store: Store, source: str
) -> None:
    citation = anchor_citation(
        store,
        case_id="acme",
        document_sha256=DIGEST,
        page=3,
        matched_text="leverage was 4.2x",
    )
    assert citation.bbox == (Decimal(100), Decimal(700), Decimal(212), Decimal(712))
    assert citation.page == 3
    assert citation.document_sha256 == DIGEST


def test_a_quote_whose_whitespace_differs_still_anchors(
    store: Store, source: str
) -> None:
    # Extracted text is one token per word; a module quotes a running sentence.
    citation = anchor_citation(
        store,
        case_id="acme",
        document_sha256=DIGEST,
        page=3,
        matched_text="Net   leverage\nwas",
    )
    assert citation.bbox == (Decimal(72), Decimal(700), Decimal(180), Decimal(712))


def test_the_refusal_carries_no_document_text(store: Store, source: str) -> None:
    quote = "Net leverage was 9.9x at year end"
    with pytest.raises(Refusal) as caught:
        anchor_citation(
            store,
            case_id="acme",
            document_sha256=DIGEST,
            page=3,
            matched_text=quote,
        )
    rendered = f"{caught.value!r} {caught.value!s} {caught.value.args}"
    assert "leverage" not in rendered
    assert "9.9x" not in rendered


def test_a_quote_anchors_only_within_its_own_case(store: Store) -> None:
    # The same document in two cases is ordinary -- a standard credit agreement,
    # a rating methodology. Each case holds its own copy, and a citation must
    # never derive its rectangle from another case's.
    shared = "f" * 64
    admit_source(store, case_id="acme", sha256=shared, tokens=_tokens())
    admit_source(
        store,
        case_id="rival",
        sha256=shared,
        tokens=[
            Token(
                page=3,
                ordinal=0,
                text="Net leverage was 4.2x at year end",
                x0=Decimal(500),
                y0=Decimal(100),
                x1=Decimal(760),
                y1=Decimal(112),
            )
        ],
    )
    citation = anchor_citation(
        store,
        case_id="acme",
        document_sha256=shared,
        page=3,
        matched_text="Net leverage",
    )
    assert citation.bbox == (Decimal(72), Decimal(700), Decimal(152), Decimal(712))


def test_a_quote_appearing_twice_on_a_page_is_refused(store: Store) -> None:
    # "total debt" twice in one table is common. A citation that points at one
    # of two places is not evidence, so the module must quote more context.
    digest = "e" * 64
    row = [("total", 72), ("debt", 110), ("total", 300), ("debt", 340)]
    admit_source(
        store,
        case_id="acme",
        sha256=digest,
        tokens=[
            Token(
                page=1,
                ordinal=ordinal,
                text=text,
                x0=Decimal(x0),
                y0=Decimal(700),
                x1=Decimal(x0 + 30),
                y1=Decimal(712),
            )
            for ordinal, (text, x0) in enumerate(row)
        ],
    )
    with pytest.raises(Refusal) as caught:
        anchor_citation(
            store,
            case_id="acme",
            document_sha256=digest,
            page=1,
            matched_text="total debt",
        )
    assert caught.value.code is RefusalCode.CITATION_AMBIGUOUS


def test_page_text_maps_every_character_back_to_its_token() -> None:
    # The owner map is what turns a matched character span into a rectangle.
    # One separator space is attributed to the token it precedes.
    text, owners = page_text(_tokens()[:3])
    assert text == "Net leverage was"
    assert len(owners) == len(text)
    assert [text[i] for i, o in enumerate(owners) if o == 0] == list("Net")
    assert "".join(text[i] for i, o in enumerate(owners) if o == 1) == " leverage"


def test_enclosing_box_is_the_smallest_rectangle_over_the_tokens() -> None:
    covering = _tokens()[1:4]
    assert enclosing_box(covering) == (
        Decimal(100),
        Decimal(700),
        Decimal(212),
        Decimal(712),
    )


def test_anchor_citation_returns_a_citation(store: Store, source: str) -> None:
    anchored = anchor_citation(
        store, case_id="acme", document_sha256=DIGEST, page=3, matched_text="year end"
    )
    assert isinstance(anchored, Citation)
    assert anchored.matched_text == "year end"
