#!/usr/bin/env python3
"""Parse the tagged Markdown tables that carry data between CP modules.

Canon bans JSON as an analytical artifact (CP_AB_EXPORT_SPEC gate E4: "No
lettered appendices, embedded JSON, export manifest, extraction envelope,
JSONL, database"), so every handoff is Markdown. That is not an obstacle to
scripting it: registers are pipe tables with locked column orders, and the ones
consumed downstream carry an explicit identity comment:

    <!-- table-id: cp1.model_period_register -->
    | period_id | period_type | ... |
    | --- | --- | ... |
    | FY2024 | fiscal_year | ... |

This module is the read side of that contract. It uses only stdlib and the
sibling handoff validator shipped with every consuming skill.

Null discipline matches canon: a missing value is None, never 0 and never "".
Canon is explicit that null is not zero, and the whole point of moving
arithmetic into scripts is lost if the parser quietly coerces an absent figure
into a number that then flows into a ratio.
"""
import math
import re
import sys

sys.dont_write_bytecode = True
from validate_handoff import unfenced_markdown

TABLE_ID_RE = re.compile(r"<!--\s*table-id:\s*([A-Za-z0-9_.]+)\s*-->")
SEPARATOR_RE = re.compile(r"^[\s:\-|]+$")

# Cell spellings that mean "no value". Canon's own vocabulary, casefolded.
NULL_CELLS = {
    "", "-", "\u2014", "\u2013", "n/a", "na", "none", "null", "not applicable",
    "not disclosed", "not assessable", "not calculable", "tbd", "unknown",
    "insufficient information", "[insufficient information]",
    "not calculable from provided materials", "unavailable",
}


def _split_row(line):
    return [c.strip() for c in line.strip().removeprefix("|").removesuffix("|").split("|")]


def is_null(cell):
    return cell is None or str(cell).strip().casefold() in NULL_CELLS


class AmbiguousFigure(ValueError):
    """A figure whose decimal separator cannot be determined from the text."""


def _finite_figure(value, where):
    try:
        number = float(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{where}: value must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{where}: value must be a finite number")
    return number


# `1,234.56` (Anglo) and `1.234,56` (continental) are both unambiguous: the
# separator that appears LAST is the decimal one. `5,2` is not -- it is 5.2 in
# continental notation and a malformed thousands group in Anglo notation, and
# the two readings differ by 10x.
_ANGLO_THOUSANDS = re.compile(r"^\d{1,3}(,\d{3})+(\.\d+)?$")
_CONTINENTAL = re.compile(r"^\d{1,3}(\.\d{3})+(,\d+)?$")
_AMBIGUOUS_COMMA = re.compile(r"^\d+,\d{1,2}$")


def parse_figure(cell, where="value"):
    """Parse a figure, or return None for a recognised null.

    Raises AmbiguousFigure rather than guessing when the decimal separator is
    undeterminable. A credit package covering EUR issuers will meet `5,2` meaning
    5.2x; stripping commas as thousands separators turns that into 52.0 -- a 10x
    error, on a leverage multiple, that looks like an ordinary number. Refusing
    is the only safe reading: the caller knows the source's notation and this
    function does not.
    """
    if is_null(cell):
        return None
    if isinstance(cell, bool):
        raise ValueError(f"{where}: boolean is not a figure")
    if isinstance(cell, (int, float)):
        return _finite_figure(cell, where)

    s = str(cell).strip()
    negative = s.startswith("(") and s.endswith(")")
    if negative:
        s = s[1:-1].strip()
    # Strip only KNOWN decorations -- currency symbols, thin/non-breaking
    # spaces, a multiple's trailing x, a trailing percent. Deliberately not
    # "remove every non-digit": that turns prose like "roughly 5" or "5 to 6"
    # into a confident 5.0, which is worse than refusing the cell.
    core = s.replace(" ", " ").replace(" ", " ").replace(" ", "")
    core = re.sub(r"^[€$£¥₹]|[€$£¥₹]$", "", core)
    core = re.sub(r"[xX]$", "", core)
    core = re.sub(r"%$", "", core)
    if not re.fullmatch(r"[-+]?[0-9][0-9.,]*(?:[eE][-+]?[0-9]+)?", core):
        raise ValueError(f"{where}: {cell!r} is not a figure")
    if core.count(",") and core.count("."):
        if core.rfind(",") > core.rfind("."):
            if not _CONTINENTAL.match(core.lstrip("-+")):
                raise AmbiguousFigure(f"{where}: {cell!r} mixes ',' and '.' in an unrecognised pattern")
            core = core.replace(".", "").replace(",", ".")
        else:
            if not _ANGLO_THOUSANDS.fullmatch(core.lstrip("-+")):
                raise AmbiguousFigure(f"{where}: {cell!r} mixes ',' and '.' in an unrecognised pattern")
            core = core.replace(",", "")
    elif "," in core:
        body = core.lstrip("-+")
        if _AMBIGUOUS_COMMA.match(body):
            raise AmbiguousFigure(
                f"{where}: {cell!r} is ambiguous -- ',' before 1-2 digits is a decimal "
                "separator in continental notation (5,2 = 5.2) and a malformed thousands "
                "group in Anglo notation (5,2 -> 52). Supply the figure as a number, or "
                "normalise the notation at the source"
            )
        if _ANGLO_THOUSANDS.match(body):
            core = core.replace(",", "")
        else:
            raise AmbiguousFigure(f"{where}: {cell!r} uses ',' in an unrecognised pattern")

    value = _finite_figure(core, where)
    return -value if negative else value


def to_number(cell):
    """Lenient wrapper: returns None where parse_figure would raise on shape,
    but still refuses to guess an ambiguous decimal separator."""
    try:
        return parse_figure(cell)
    except AmbiguousFigure:
        raise
    except ValueError:
        return None


class Table:
    __slots__ = ("table_id", "columns", "rows")

    def __init__(self, table_id, columns, rows):
        self.table_id = table_id
        self.columns = columns
        self.rows = rows  # list of dict: column -> raw cell string

    def column(self, name):
        return [r.get(name) for r in self.rows]

    def numbers(self, name):
        return [to_number(r.get(name)) for r in self.rows]

    def __len__(self):
        return len(self.rows)

    def __repr__(self):
        return f"<Table {self.table_id} cols={len(self.columns)} rows={len(self.rows)}>"


def parse_tables(text):
    """{table_id: Table} for every `<!-- table-id: -->`-tagged pipe table.

    A tag binds to the next pipe table that follows it. Untagged tables are
    ignored -- they are presentation tables, not the machine interface.
    """
    lines = unfenced_markdown(text).splitlines()
    out = {}
    pending_id = None
    i = 0
    while i < len(lines):
        line = lines[i]
        m = TABLE_ID_RE.fullmatch(line.strip())
        if m:
            if pending_id is not None:
                raise ValueError(f"{pending_id}: table-id has no following table")
            if m.group(1) in out:
                raise ValueError(f"{m.group(1)}: duplicate table-id")
            pending_id = m.group(1)
            i += 1
            continue
        stripped = line.strip()
        if pending_id and stripped.startswith("|") and stripped.count("|") >= 2:
            header = _split_row(stripped)
            if not all(header) or len(header) != len(set(header)):
                raise ValueError(f"{pending_id}: table columns must be nonempty and unique")
            i += 1
            if i >= len(lines) or len(_split_row(lines[i])) != len(header) or not all(
                re.fullmatch(r":?-{3,}:?", cell) for cell in _split_row(lines[i])
            ):
                raise ValueError(f"{pending_id}: missing or malformed table separator")
            i += 1
            rows = []
            while i < len(lines):
                s = lines[i].strip()
                if not s.startswith("|"):
                    break
                cells = _split_row(s)
                if len(cells) != len(header):
                    raise ValueError(f"{pending_id}: table row width differs from its header")
                rows.append(dict(zip(header, cells)))
                i += 1
            out[pending_id] = Table(pending_id, header, rows)
            pending_id = None
            continue
        if stripped and not stripped.startswith("<!--"):
            # Any other content between the tag and its table breaks the bind;
            # better to report the table as absent than to attach the tag to an
            # unrelated table further down.
            pending_id = pending_id if stripped.startswith("|") else None
        i += 1
    if pending_id is not None:
        raise ValueError(f"{pending_id}: table-id has no following table")
    return out


def read_frontmatter(text):
    """The YAML envelope as a flat {key: raw string}. Deliberately not a YAML
    parser: the envelope is flat scalars and simple lists, and taking a
    dependency for that would stop these scripts being drop-in."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out = {}
    for line in text[3:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line or line.startswith((" ", "\t", "-")):
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out
