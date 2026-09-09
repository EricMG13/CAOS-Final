"""Extraction: a PDF's bytes to the token index and the blocks a source carries.

The only way document text enters the host. Every token carries its page, the
region and line that pdfminer's layout analysis assigned it, and the rectangle
it occupies in PDF user space: points, origin at the page's lower-left corner,
y increasing upwards, `x0 <= x1` and `y0 <= y1` -- equal for a glyph with no
advance. A region is a column or a paragraph (`docs/DECISIONS.md` section
15). Nothing here decides where one ends: separating two columns that share a
y-band is layout analysis, and a threshold in the host would be a heuristic on
the evidence boundary.

Document text is not `BoundaryText` (`docs/DECISIONS.md` section 16), and it
reaches a prompt, where a character a reviewer cannot see is an instruction
the reviewer did not read. So every control, format and surrogate character
and every Unicode noncharacter is dropped from a token -- a wider set than
`BoundaryText` refuses, since that type guards a name and this text guards a
prompt -- and the document is kept, coordinates and all, which refusing it
would not do for an Arabic or Hebrew filing.

A refusal carries a code and nothing else. pdfminer's exceptions quote the
bytes they choked on, so none is chained; `_index` raises them unwrapped, and
is the way to find out why a filing was refused. A second format arrives as a
second `_index`: `(tokens, pages)` is all `pack_blocks` needs.
"""

from __future__ import annotations

import hashlib
import logging
import math
import unicodedata
from collections.abc import Iterator, Sequence
from decimal import Decimal
from io import BytesIO

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTChar, LTComponent, LTTextBox, LTTextLine

from server.evidence.citations import Rectangle
from server.refusals import Refusal, RefusalCode
from server.store.sources import Block, SourceDocument, Token

# Two jobs, one number (SYSTEM_SPEC section 5): the most characters a block
# carries, and the size of page still packed line by line. Raising it makes
# more, smaller blocks of an ordinary page, not bigger ones. Half a page of
# prose: a judgment, not a measurement (CLAUDE.md's ledger, under its name).
BLOCK_WIDTH = 2000

# Three places of a point, from `repr`, the shortest text that round-trips
# the float -- 0.1 becomes 0.100, not 0.1000000000000000055. `quantize`
# carries 28 digits; past the limit it would refuse instead of the host.
_PLACES = Decimal("0.001")
_COORDINATE_LIMIT = 1e24

# The layout analysis invariant 11 rests on, written out rather than left to
# pdfminer's defaults so a release that moves one cannot move which quotes
# anchor. `all_texts=False` is why a Form XObject's text is not read ("Text
# inside a Form XObject is not extracted" in CLAUDE.md's ledger).
_LAYOUT = LAParams(
    line_overlap=0.5,
    char_margin=2.0,
    line_margin=0.5,
    word_margin=0.1,
    boxes_flow=0.5,
    detect_vertical=False,
    all_texts=False,
)

# pdfminer says what it did not understand -- "unknown operator: 'X'" -- and an
# operator is bytes of the document (SYSTEM_SPEC section 10). Nothing it logs
# reaches a handler: no propagation to the root, and a handler of its own so
# the standard library's last resort does not write to stderr instead.
_PDFMINER = logging.getLogger("pdfminer")
_PDFMINER.propagate = False
_PDFMINER.addHandler(logging.NullHandler())

_DROPPED_CATEGORIES = frozenset({"Cc", "Cf", "Cs"})

# A token before it knows its page, region and line: its text and rectangle.
type _Word = tuple[str, Rectangle]


def extract_document(pdf: bytes) -> SourceDocument:
    """The token index and blocks of a PDF, or a refusal.

    The same bytes give the same text and the same rectangles. The order of
    regions, and so of blocks, is pdfminer's reading order, which breaks a tie
    between equidistant boxes on object addresses ("Region order is
    pdfminer's" in CLAUDE.md's ledger).
    """
    # Malformed input surfaces as `KeyError` deep in pdfminer as often as a
    # typed `PSException`, and refusing only the typed ones would let the rest
    # out carrying the bytes. Memory is the host's failure, and passes through.
    try:
        tokens, pages = _index(pdf)
        failed = False
    except MemoryError:
        raise
    except Exception:  # noqa: BLE001
        failed = True
    # Raised outside the handler so the library's exception, which quotes the
    # bytes it choked on, is not attached as __context__.
    if failed:
        raise Refusal(RefusalCode.SOURCE_NOT_EXTRACTABLE)
    if not tokens:
        raise Refusal(RefusalCode.SOURCE_HAS_NO_TEXT)
    return SourceDocument(
        sha256=hashlib.sha256(pdf).hexdigest(),
        tokens=tuple(tokens),
        blocks=pack_blocks(pages),
    )


def pack_blocks(
    pages: Sequence[Sequence[str]], *, width: int = BLOCK_WIDTH
) -> tuple[Block, ...]:
    """Blocks of every page, numbered through the document (SYSTEM_SPEC 5).

    One block per piece of a line while the page's text fits the width, groups
    of consecutive pieces once it does not. A block never spans two pages, and
    none is empty or blank.
    """
    if width < 1:
        message = f"a block width below one: {width}"
        raise ValueError(message)
    blocks: list[Block] = []
    for page, lines in enumerate(pages, start=1):
        blocks.extend(
            Block(block_id=number, page=page, text=text)
            for number, text in enumerate(_pack_page(lines, width), start=len(blocks))
        )
    return tuple(blocks)


def _pack_page(lines: Sequence[str], width: int) -> list[str]:
    """One page's block texts.

    "Fits the width" counts the pieces' characters alone, without the newlines
    a group would put between them; changing that changes every block id.
    """
    pieces = [piece for line in lines for piece in _split(line, width)]
    if sum(map(len, pieces)) <= width:
        return pieces
    texts: list[str] = []
    for piece in pieces:
        if texts and len(texts[-1]) + 1 + len(piece) <= width:
            texts[-1] += "\n" + piece
        else:
            texts.append(piece)
    return texts


def _split(line: str, width: int) -> list[str]:
    """The line in pieces of at most `width` characters, none blank.

    A cut falls at the last space up to and including index `width` -- never
    at index 0, which would make an empty piece and no progress -- and at the
    width when there is none. The spaces at either end of the line, and those
    a cut leaves at the front of the remainder, are dropped.
    """
    line = line.strip(" ")
    pieces: list[str] = []
    while len(line) > width:
        space = line.rfind(" ", 1, width + 1)
        cut = space if space >= 0 else width
        pieces.append(line[:cut])
        line = line[cut:].lstrip(" ")
    return [*pieces, line] if line else pieces


def _index(pdf: bytes) -> tuple[list[Token], list[list[str]]]:
    """Every token of every page, and each page's lines as text for the blocks.

    Lines are flattened region by region, so a grouped block can carry the
    last line of one column and the first of the next: nothing maps a block
    onto a region (`server/store/sources.py`).
    """
    tokens: list[Token] = []
    pages: list[list[str]] = []
    layouts = extract_pages(BytesIO(pdf), laparams=_LAYOUT)
    for page, layout in enumerate(layouts, start=1):
        lines: list[str] = []
        regions = (item for item in layout if isinstance(item, LTTextBox))
        for region_id, region in enumerate(regions):
            for line_id, words in enumerate(_lines(region)):
                for ordinal, (text, (x0, y0, x1, y1)) in enumerate(words):
                    token = Token(
                        page=page,
                        region_id=region_id,
                        line_id=line_id,
                        ordinal=ordinal,
                        text=text,
                        x0=x0,
                        y0=y0,
                        x1=x1,
                        y1=y1,
                    )
                    tokens.append(token)
                lines.append(" ".join(text for text, _ in words))
        pages.append(lines)
    return tokens, pages


def _lines(region: LTTextBox) -> Iterator[list[_Word]]:
    """The region's lines that still carry a word, in the extractor's order."""
    for line in region:
        if isinstance(line, LTTextLine) and (words := _words(line)):
            yield words


def _words(line: LTTextLine) -> list[_Word]:
    """The line cut at whitespace, each word with the box its characters cover.

    pdfminer marks the gaps it inferred with `LTAnno`, which is whitespace by
    construction; a space glyph is an `LTChar` whose text is a space. A word is
    always being gathered: whitespace closes it once it holds a glyph, and the
    empty one left at the end is nothing `_word` returns.
    """
    chars_by_word: list[list[LTChar]] = [[]]
    for item in line:
        if isinstance(item, LTChar) and not item.get_text().isspace():
            chars_by_word[-1].append(item)
        elif chars_by_word[-1]:
            chars_by_word.append([])
    return [word for word in map(_word, chars_by_word) if word]


def _word(chars: list[LTChar]) -> _Word | None:
    """The glyphs' text, and the box of those that keep any once cleaned."""
    texts = [_clean(char.get_text()) for char in chars]
    kept = [char for char, text in zip(chars, texts, strict=True) if text]
    return ("".join(texts), _box(kept)) if kept else None


def _clean(text: str) -> str:
    return "".join(character for character in text if not _dropped(character))


def _dropped(character: str) -> bool:
    """A control, format or surrogate character, or a Unicode noncharacter.

    Cf holds the bidirectional controls `BoundaryText` refuses, the joiners,
    soft hyphen and byte-order mark it admits, and the tag block U+E0000 to
    U+E007F, which spells an instruction no reviewer sees. Marks, private-use
    glyphs and look-alike letters are visible, and stay.
    """
    code = ord(character)
    return (
        unicodedata.category(character) in _DROPPED_CATEGORIES
        or 0xFDD0 <= code <= 0xFDEF
        or (code & 0xFFFE) == 0xFFFE
    )


def _box(items: Sequence[LTComponent]) -> Rectangle:
    return (
        _decimal(min(item.x0 for item in items)),
        _decimal(min(item.y0 for item in items)),
        _decimal(max(item.x1 for item in items)),
        _decimal(max(item.y1 for item in items)),
    )


def _decimal(value: float) -> Decimal:
    # Refused by the host, not by what `quantize` happens to do with an
    # infinity or a 300-digit number -- and it does nothing with NaN, which
    # Postgres would store.
    if not math.isfinite(value) or abs(value) >= _COORDINATE_LIMIT:
        raise Refusal(RefusalCode.SOURCE_NOT_EXTRACTABLE)
    return Decimal(repr(value)).quantize(_PLACES)
