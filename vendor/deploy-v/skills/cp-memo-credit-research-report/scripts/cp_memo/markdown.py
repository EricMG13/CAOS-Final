"""Small conservative Markdown reader for accepted handoffs."""

from __future__ import annotations

import re
from dataclasses import dataclass

from validate_handoff import unfenced_markdown

H2_RE = re.compile(r"^ {0,3}##(?!#)[ \t]+(.+?)[ \t]*$")
H3_RE = re.compile(r"^ {0,3}###(?!#)[ \t]+(.+?)[ \t]*$")


@dataclass(frozen=True)
class Passage:
    locator: str
    text: str


def section(text: str, title: str) -> str:
    lines = unfenced_markdown(text).splitlines()
    start = None
    for index, line in enumerate(lines):
        match = H2_RE.match(line)
        if match and match.group(1).strip() == title:
            start = index + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start, len(lines)):
        line = lines[index]
        if H2_RE.match(line):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def _clean_inline(value: str) -> str:
    value = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", value)
    value = value.replace("**", "").replace("__", "").replace("`", "")
    return re.sub(r"\s+", " ", value).strip()


def reader_passages(text: str, *, limit: int = 6) -> tuple[Passage, ...]:
    """Return conclusion-first prose/bullets from Analysis, without appendix data."""
    body = section(text, "Analysis")
    if not body:
        return ()
    passages: list[Passage] = []
    current_heading = "Analysis"
    paragraph: list[str] = []

    def flush() -> None:
        nonlocal paragraph
        if not paragraph or len(passages) >= limit:
            paragraph = []
            return
        cleaned = _clean_inline(" ".join(paragraph))
        paragraph = []
        if cleaned and not cleaned.startswith("|") and cleaned != "---":
            passages.append(Passage(current_heading, cleaned))

    in_table = False
    for line in body.splitlines():
        h3 = H3_RE.match(line)
        if h3:
            flush()
            heading = h3.group(1).strip()
            if heading.casefold().startswith("analytical appendix"):
                break
            current_heading = heading
            continue
        stripped = line.strip()
        if stripped.startswith("|"):
            flush()
            in_table = True
            continue
        if in_table and not stripped.startswith("|"):
            in_table = False
        if in_table:
            continue
        if not stripped:
            flush()
            continue
        if stripped.startswith(("- ", "* ", "+ ")):
            flush()
            cleaned = _clean_inline(stripped[2:])
            if cleaned and len(passages) < limit:
                passages.append(Passage(current_heading, cleaned))
            continue
        if not stripped.startswith(("#", "<", ">")):
            paragraph.append(stripped)
    flush()
    return tuple(passages[:limit])


def limitation_passages(text: str, *, limit: int = 4) -> tuple[Passage, ...]:
    body = section(text, "Gaps & Conflicts")
    if not body:
        return ()
    result: list[Passage] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "+ ")):
            cleaned = _clean_inline(stripped[2:])
            if cleaned:
                result.append(Passage("Gaps & Conflicts", cleaned))
        if len(result) >= limit:
            break
    return tuple(result)
