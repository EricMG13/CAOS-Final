"""The decision record is checked, not eyeballed.

`docs/DECISIONS.md` is binding and later entries override earlier ones, so the
order and the numbering carry meaning. Every branch appends to its end, which
makes it conflict on every merge of a stack -- and a conflict resolved by hand
is where a lost or duplicated entry hides. These are the properties a bad
resolution breaks.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[1] / "docs"
DECISIONS = DOCS / "DECISIONS.md"
HEADING = re.compile(r"^## (\d{4}-\d{2}-\d{2}) §(\d+) — (.+)$", re.M)


def _sections() -> list[tuple[str, int, str]]:
    return [(d, int(n), t) for d, n, t in HEADING.findall(DECISIONS.read_text("utf-8"))]


def test_the_record_is_numbered_from_one_without_gaps_or_repeats() -> None:
    numbers = [n for _, n, _ in _sections()]
    assert numbers, "no decision entries found: the heading shape must have changed"
    assert numbers == sorted(numbers), f"out of order: {numbers}"
    assert len(numbers) == len(set(numbers)), "a section number appears twice"
    assert numbers == list(range(1, len(numbers) + 1)), f"a gap: {numbers}"


def test_every_entry_has_a_title_on_the_heading_line() -> None:
    # A heading that wraps onto the next line renders as body text, so the entry
    # silently stops being an entry. §16 did exactly this after a merge.
    for date, number, title in _sections():
        assert title.strip(), f"§{number} has no title"
        assert not title.endswith((";", ",")), (
            f"§{number}'s title looks truncated -- a wrapped heading line: {title!r}"
        )
        assert date == "2026-09-08" or date > "2026-09-08"


@pytest.mark.parametrize(
    "document",
    sorted(p.name for p in DOCS.glob("*.md")),
)
def test_no_document_carries_a_conflict_marker(document: str) -> None:
    text = (DOCS / document).read_text("utf-8")
    for marker in ("<<<<<<<", "=======", ">>>>>>>"):
        if marker == "=======":
            continue  # a legitimate Markdown rule; the other two are unambiguous
        assert marker not in text, f"{document} still carries a merge conflict marker"
