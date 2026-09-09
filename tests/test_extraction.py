"""A real PDF through a real extractor (owed by Phase 2, exited under Phase 6).

Every token carries its page, the region and line the extractor assigned, and
the rectangle it occupies; blocks are packed by the group width in
`SYSTEM_SPEC.md` section 5; and the citations invariant 11 promises anchor in
what came out. Until this file the token index was synthetic
(`tests/test_citation_anchoring.py`).

The fixture is the PDF `_two_columns_pdf` writes -- ASCII, Helvetica, two
pages, rendered by Apple's parser as well as pdfminer's. Page 1 is two
columns of three lines; the left column's last line ends "covenant on net"
and the right column's begins "debt fell to", so a join by y-band alone would
read "net debt" across the gutter. Page 2 is one line whose font carries a
ToUnicode map sending byte 0x80 to U+202E, so a bidirectional override
reaches the extractor as a character of the document.
"""

from __future__ import annotations

import hashlib
import logging
from decimal import Decimal
from typing import NoReturn

import pytest

from server.boundary_text import BoundaryText
from server.evidence import extract
from server.evidence.citations import Citation, anchor_citation
from server.evidence.extract import BLOCK_WIDTH, extract_document, pack_blocks
from server.refusals import Refusal, RefusalCode
from server.store import Store
from server.store.sources import SourceDocument, Token, admit_pack

CASE = BoundaryText.of("acme")
PAGE_WIDTH, PAGE_HEIGHT = Decimal(400), Decimal(300)
HELVETICA = (
    b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
)


def _document(objects: list[bytes]) -> bytes:
    """A PDF from its objects, numbered from 1, with a correct xref table."""
    out = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (number, body)
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return out


def _stream(data: bytes) -> bytes:
    """A stream object; /Length excludes the line end before `endstream`."""
    return b"<< /Length %d >>\nstream\n%s\nendstream" % (len(data), data)


def _to_unicode(mapping: dict[int, int]) -> bytes:
    """A ToUnicode CMap: ASCII as itself, each byte of `mapping` to its code point."""
    chars = b"".join(
        b"<%02X> <%s>\n"
        % (byte, chr(code).encode("utf-16-be", "surrogatepass").hex().upper().encode())
        for byte, code in mapping.items()
    )
    return _stream(
        b"/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n"
        b"1 begincodespacerange\n<00> <FF>\nendcodespacerange\n"
        b"1 beginbfrange\n<20> <7E> <0020>\nendbfrange\n"
        b"%d beginbfchar\n%sendbfchar\nendcmap\n"
        b"CMapName currentdict /CMap defineresource pop\nend\nend\n"
        % (len(mapping), chars)
    )


def _pdf(page_content: bytes, font: bytes = HELVETICA, *more: bytes) -> bytes:
    """One Letter page of `page_content` set as /F1; `more` are objects 6 on."""
    return _document(
        [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
            b" /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            font,
            _stream(page_content),
            *more,
        ]
    )


def _two_columns_pdf() -> bytes:
    """The fixture; `Path("two_columns.pdf").write_bytes(FIXTURE)` to look at it."""
    page_1 = (
        b"BT\n/F1 12 Tf\n40 250 Td (Net leverage was 4.2x at) Tj\n"
        b"0 -14 Td (the year end, within the) Tj\n0 -14 Td (covenant on net) Tj\nET\n"
        b"BT\n/F1 12 Tf\n220 250 Td (Total assets rose to) Tj\n"
        b"0 -14 Td (EUR 120 million, while) Tj\n0 -14 Td (debt fell to EUR 95m.) Tj\nET"
    )
    page_2 = b"BT\n/F2 12 Tf\n40 250 Td (Net debt was \\200EUR 95 million.) Tj\nET"
    page = b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 300]"
    return _document(
        [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
            page + b" /Resources << /Font << /F1 5 0 R >> >> /Contents 7 0 R >>",
            page + b" /Resources << /Font << /F2 6 0 R >> >> /Contents 8 0 R >>",
            HELVETICA,
            HELVETICA[:-3] + b" /ToUnicode 9 0 R >>",
            _stream(page_1),
            _stream(page_2),
            _to_unicode({0x80: 0x202E}),
        ]
    )


FIXTURE = _two_columns_pdf()


@pytest.fixture(scope="module")
def document() -> SourceDocument:
    return extract_document(FIXTURE)


@pytest.fixture
def admitted(store: Store, document: SourceDocument) -> SourceDocument:
    admit_pack(store, case_id=CASE, documents=(document,))
    return document


def _anchor(store: Store, document: SourceDocument, quote: str, page: int) -> Citation:
    return anchor_citation(
        store,
        case_id=CASE,
        document_sha256=document.sha256,
        page=page,
        matched_text=quote,
    )


def _token(document: SourceDocument, page: int, text: str) -> Token:
    (found,) = [t for t in document.tokens if t.page == page and t.text == text]
    return found


def _packed(lines: list[str], width: int) -> list[str]:
    return [block.text for block in pack_blocks([lines], width=width)]


def test_citations_anchor_in_an_extracted_pdf(
    store: Store, admitted: SourceDocument
) -> None:
    # "was 4.2x at" ends the left column's first line and "the year" begins
    # its second, so the quote wraps within one region.
    citation = _anchor(store, admitted, "was 4.2x at the year", page=1)
    first, second = citation.bboxes
    for x0, y0, x1, y1 in citation.bboxes:
        assert Decimal(0) <= x0 < x1 <= PAGE_WIDTH
        assert Decimal(0) <= y0 < y1 <= PAGE_HEIGHT
    assert first[1] > second[3], "the first line sits above the second"
    assert second[0] == Decimal(40), "the second rectangle starts at the column edge"
    # Neither rectangle encloses a word the quote does not contain.
    assert first[0] > _token(admitted, 1, "leverage").x1
    assert second[2] < _token(admitted, 1, "end,").x0


def test_the_extractor_assigns_each_column_its_own_region(
    document: SourceDocument,
) -> None:
    left, right = _token(document, 1, "net"), _token(document, 1, "debt")
    assert left.y0 == right.y0, "the two words share a y-band"
    assert left.region_id != right.region_id
    regions = {token.region_id for token in document.tokens if token.page == 1}
    assert len(regions) == 2


def test_a_quote_cannot_be_assembled_across_a_gutter_in_an_extracted_pdf(
    store: Store, admitted: SourceDocument
) -> None:
    with pytest.raises(Refusal) as caught:
        _anchor(store, admitted, "net debt", page=1)
    assert caught.value.code is RefusalCode.CITATION_NOT_LOCATABLE


def test_a_quote_anchors_on_its_own_page_only(
    store: Store, admitted: SourceDocument
) -> None:
    with pytest.raises(Refusal) as caught:
        _anchor(store, admitted, "Net debt was", page=1)
    assert caught.value.code is RefusalCode.CITATION_NOT_LOCATABLE
    assert len(_anchor(store, admitted, "Net debt was", page=2).bboxes) == 1


def test_a_bidi_override_in_the_document_is_dropped_not_refused(
    store: Store, admitted: SourceDocument
) -> None:
    # Refusing the document would refuse every Arabic and Hebrew filing; the
    # control is dropped and the coordinates kept (docs/DECISIONS.md 16).
    page_two = [token.text for token in admitted.tokens if token.page == 2]
    assert page_two == ["Net", "debt", "was", "EUR", "95", "million."]
    assert not any("\u202e" in block.text for block in admitted.blocks)
    assert len(_anchor(store, admitted, "EUR 95 million.", page=2).bboxes) == 1


def test_invisible_characters_are_dropped_from_document_text() -> None:
    # What a reader cannot see -- the tag block that spells an instruction to
    # a model, a joiner, the byte-order mark, the soft hyphen, NUL, a lone
    # surrogate, the noncharacters -- is dropped; what is visible stays. One
    # per word: two zero-width glyphs in a row are a line break to pdfminer.
    invisible = {
        0x80: 0xE0041,
        0x81: 0x200D,
        0x82: 0xFEFF,
        0x83: 0x00AD,
        0x84: 0x0000,
        0x85: 0xD800,
        0x86: 0xFFFE,
        0x87: 0xFDD0,
    }
    words = [b"net", b"debt", b"was", b"EUR", b"95", b"million", b"in", b"2025"]
    text = b" ".join(
        b"%s\\%o" % (word, byte) for word, byte in zip(words, invisible, strict=True)
    )
    font = HELVETICA[:-3] + b" /ToUnicode 6 0 R >>"
    document = extract_document(
        _pdf(
            b"BT /F1 12 Tf 72 700 Td (" + text + b") Tj ET",
            font,
            _to_unicode(invisible),
        )
    )
    assert [token.text for token in document.tokens] == [w.decode() for w in words]
    assert [block.text for block in document.blocks] == [
        "net debt was EUR 95 million in 2025"
    ]


def test_a_dropped_glyph_does_not_widen_the_box() -> None:
    # A font of its own name, so pdfminer takes its widths from the file and
    # not from Helvetica's metrics: E and U 600 wide, byte 0x80 -- mapped to a
    # bidirectional override -- 500 wide. The override goes, and its advance
    # with it: a rectangle never encloses text the token does not contain.
    widths = b" ".join([b"600"] * 59 + [b"500"])
    font = (
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Fixture /FirstChar 69"
        b" /LastChar 128 /Widths [" + widths + b"] /ToUnicode 6 0 R >>"
    )
    content = b"BT /F1 10 Tf 72 700 Td (EU\\200) Tj ET"
    document = extract_document(_pdf(content, font, _to_unicode({0x80: 0x202E})))
    (token,) = document.tokens
    assert token.text == "EU"
    assert (token.x0, token.x1) == (Decimal(72), Decimal(84))


def test_the_lines_of_a_region_are_numbered_in_reading_order(
    document: SourceDocument,
) -> None:
    region = _token(document, 1, "Net").region_id
    lines = sorted(
        {
            (token.line_id, token.y0)
            for token in document.tokens
            if token.page == 1 and token.region_id == region
        }
    )
    assert [line for line, _ in lines] == [0, 1, 2]
    assert [y for _, y in lines] == sorted((y for _, y in lines), reverse=True)


def test_extraction_is_deterministic(document: SourceDocument) -> None:
    assert extract_document(FIXTURE) == document


def test_the_digest_is_of_the_bytes_given(document: SourceDocument) -> None:
    assert document.sha256 == hashlib.sha256(FIXTURE).hexdigest()


def test_bytes_that_are_not_a_pdf_are_refused_without_the_bytes() -> None:
    with pytest.raises(Refusal) as caught:
        extract_document(b"%PDF-1.4 covenant breach on page 9")
    assert caught.value.code is RefusalCode.SOURCE_NOT_EXTRACTABLE
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "covenant" not in f"{caught.value!r} {caught.value!s} {caught.value.args}"


def test_running_out_of_memory_is_not_the_documents_fault(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Every other failure while pdfminer parses is refused against the
    # document. Exhausting the host is the host's, and an analyst told the
    # filing does not parse would act on the wrong thing.
    def exhausted(*args: object, **kwargs: object) -> NoReturn:
        raise MemoryError

    monkeypatch.setattr(extract, "extract_pages", exhausted)
    with pytest.raises(MemoryError):
        extract_document(FIXTURE)


def test_a_pdf_with_no_text_is_refused() -> None:
    with pytest.raises(Refusal) as caught:
        extract_document(_pdf(b"0 0 m 100 100 l S"))
    assert caught.value.code is RefusalCode.SOURCE_HAS_NO_TEXT


def test_a_non_finite_coordinate_is_refused() -> None:
    # A content stream can carry a 400-digit number, which pdfminer reads as
    # float("inf"); as a horizontal scaling it makes every advance infinite.
    # Invariant 7: non-finite values are refused before use -- by the host,
    # not by what `Decimal.quantize` happens to do with an infinity or a
    # 300-digit magnitude, and not for NaN, which it quantizes without
    # complaint and Postgres stores.
    huge = b"1" + b"0" * 400 + b".0"
    with pytest.raises(Refusal) as caught:
        extract_document(_pdf(b"BT /F1 12 Tf " + huge + b" Tz 72 700 Td (Total) Tj ET"))
    assert caught.value.code is RefusalCode.SOURCE_NOT_EXTRACTABLE
    for value in (float("nan"), float("inf"), float("-inf"), 1e300, -1e300):
        with pytest.raises(Refusal):
            extract._decimal(value)


def test_blocks_are_one_per_line_while_the_page_is_small(
    document: SourceDocument,
) -> None:
    assert [block.block_id for block in document.blocks] == list(range(7))
    assert [block.page for block in document.blocks] == [1] * 6 + [2]
    assert [block.text for block in document.blocks] == [
        "Net leverage was 4.2x at",
        "the year end, within the",
        "covenant on net",
        "Total assets rose to",
        "EUR 120 million, while",
        "debt fell to EUR 95m.",
        "Net debt was EUR 95 million.",
    ]


def test_pack_blocks_groups_lines_once_the_page_exceeds_the_width() -> None:
    assert _packed(["aaaa", "bbbb"], width=9) == ["aaaa", "bbbb"]
    assert _packed(["aaaa", "bbbb", "cccc"], width=9) == ["aaaa\nbbbb", "cccc"]
    # A line wider than the group is split at the width, at a space when one
    # is there, rather than becoming a block of its own.
    assert _packed(["one two three"], width=7) == ["one two", "three"]
    assert _packed(["abcdefghij"], width=4) == ["abcd", "efgh", "ij"]
    assert all(len(text) <= 9 for text in _packed(["x" * 50] * 5, width=9))


def test_the_width_is_also_the_size_of_a_page_packed_line_by_line() -> None:
    # Forty lines of eighty characters. Raising the width past the page's
    # text makes forty blocks of it where there were two: the number does two
    # jobs, and a maintainer after bigger blocks gets smaller ones.
    page = ["x" * 80] * 40
    assert len(pack_blocks([page], width=2000)) == 2
    assert len(pack_blocks([page], width=4000)) == 40


def test_pack_blocks_never_joins_two_pages() -> None:
    blocks = pack_blocks([["a", "b"], [], ["c"]], width=BLOCK_WIDTH)
    assert [(block.block_id, block.page, block.text) for block in blocks] == [
        (0, 1, "a"),
        (1, 1, "b"),
        (2, 3, "c"),
    ]


def test_pack_blocks_emits_no_empty_or_blank_block() -> None:
    # A line's trailing spaces after its last cut left an empty remainder,
    # which became a block with nothing in it; a leading space left a piece
    # of one space.
    assert _packed(["abc   "], width=3) == ["abc"]
    assert _packed(["  abcdef"], width=3) == ["abc", "def"]
    assert _packed(["", "   "], width=5) == []


def test_pack_blocks_refuses_a_width_below_one() -> None:
    # `_split` cannot make progress at width 0 and looped forever.
    with pytest.raises(ValueError, match="width"):
        pack_blocks([["a"]], width=0)


def test_nothing_pdfminer_logs_reaches_a_handler(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # pdfminer logs the operators it does not know, and an operator is bytes of
    # the document (SYSTEM_SPEC section 10). Unguarded, this page produces 234
    # DEBUG records, four of them quoting the stream. The host itself logs
    # nothing yet; this proves the library's records stop before the root.
    content = b"BT /F1 12 Tf 72 700 Td (Total debt) Tj COVENANT ET"
    with caplog.at_level(logging.DEBUG):
        extract_document(_pdf(content))
    assert caplog.records == []
