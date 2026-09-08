#!/usr/bin/env python3
"""Validate a CP Agents canonical Markdown handoff without modifying it.

This validator implements the current contract in CP_AB_EXPORT_SPEC.md.  It is
intentionally independent of the legacy JSON envelope schemas and uses only the
Python standard library so it can run beside either deployment structure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Sequence


EXIT_VALID = 0
EXIT_MALFORMED = 2
EXIT_BLOCKED = 3
EXIT_IDENTITY_MISMATCH = 4

REQUIRED_FIELDS = (
    "module_id",
    "module_name",
    "run_id",
    "reporting_period",
    "analysis_date",
    "confidence_score",
    "confidence_band",
    "qa_status",
    "committee_status",
    "limitation_flags",
    "validation_warnings",
    "upstream_artifacts_used",
    "downstream_consumers",
)

ISSUER_FIELDS = ("issuer_name", "issuer_id")
CP_DR_FIELDS = (
    "scope_type",
    "scope_key",
    "subject_name",
    "research_question",
    "source_mode",
    "approved_plan_hash",
    "coverage_score",
    "research_status",
    "research_stop_reason",
)

CANONICAL_HEADINGS = (
    "Audit Summary",
    "Analysis",
    "Evidence Trace",
    "Source Registry",
    "Gaps & Conflicts",
    "QA Validation",
)

CONFIDENCE_BANDS = {
    "High",
    "Medium",
    "Low",
    "Insufficient Information",
}
QA_STATUSES = {"Passed", "Restricted", "Blocked"}
COMMITTEE_STATUSES = {
    "Committee Ready",
    "Draft Only",
    "Requires More Work",
    "Insufficient Information",
    "Restricted",
    "Blocked",
}

MODULE_ID_RE = re.compile(r"^CP-(?:\d+[A-Z]?|[A-Z][A-Z0-9-]*)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SUBJECT_KEY_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$")
PLAN_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]*(.*))?$")
BLOCK_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]*(.*))?$")
H2_RE = re.compile(r"^ {0,3}##(?!#)[ \t]+(.+?)[ \t]*$")
H3_RE = re.compile(r"^ {0,3}###(?!#)[ \t]+(.+?)[ \t]*$")
H4_RE = re.compile(r"^ {0,3}####(?!#)[ \t]+(.+?)[ \t]*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
TABLE_SEPARATOR_CELL_RE = re.compile(r"^:?-{3,}:?$")
CONCLUSION_TITLE_RE = re.compile(
    r"\b(?:view|read-through|recommendation|decision|answer|conclusion|implication|thesis|summary|outlook)\b",
    re.IGNORECASE,
)
LITE_SCREENING_H3_BY_MODULE = {
    "CP-L10": "Financial change screen",
    "CP-L20": "Credit screen",
    "CP-L23": "Liquidity and forward-risk screen",
    "CP-L30": "Security opportunity screen",
    "CP-L40": "Creditor-document screen",
}

ANALYTICAL_APPENDIX_TITLE = "analytical appendix — complete canonical registers"
RAW_APPENDIX_COLUMNS = frozenset({"source_locator", "conflict_refs", "limitation_refs"})
MAX_READER_TABLE_COLUMNS = 6
MAX_READER_TABLE_ROWS = 8


@dataclass(frozen=True)
class ValidationResult:
    """Result returned by :func:`validate_text`."""

    errors: tuple[str, ...]
    identity_mismatches: tuple[str, ...]
    fields: dict[str, Any] | None
    presentation_warnings: tuple[str, ...] = ()

    @property
    def exit_code(self) -> int:
        if self.errors:
            return EXIT_MALFORMED
        if self.identity_mismatches:
            return EXIT_IDENTITY_MISMATCH
        if self.fields is not None and self.fields.get("qa_status") == "Blocked":
            return EXIT_BLOCKED
        return EXIT_VALID


class FrontmatterError(ValueError):
    """Raised when the restricted YAML frontmatter cannot be parsed."""


def _split_flow(value: str, separator: str = ",") -> list[str]:
    """Split a flow collection while respecting quotes and nested brackets."""

    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    escaped = False

    index = 0
    while index < len(value):
        char = value[index]
        if quote is not None:
            if quote == '"' and escaped:
                escaped = False
            elif quote == '"' and char == "\\":
                escaped = True
            elif char == quote:
                if quote == "'" and index + 1 < len(value) and value[index + 1] == "'":
                    index += 2
                    continue
                quote = None
            index += 1
            continue

        if char in {"'", '"'}:
            quote = char
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
            if depth < 0:
                raise FrontmatterError("unbalanced flow collection")
        elif char == separator and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
        index += 1

    if quote is not None or depth != 0:
        raise FrontmatterError("unterminated quote or flow collection")
    parts.append(value[start:].strip())
    return parts


def _split_mapping_entry(value: str) -> tuple[str, str]:
    """Split a ``key: value`` entry at its first top-level colon."""

    depth = 0
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(value):
        char = value[index]
        if quote is not None:
            if quote == '"' and escaped:
                escaped = False
            elif quote == '"' and char == "\\":
                escaped = True
            elif char == quote:
                if quote == "'" and index + 1 < len(value) and value[index + 1] == "'":
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        elif char == ":" and depth == 0:
            key = value[:index].strip()
            remainder = value[index + 1 :].strip()
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", key):
                raise FrontmatterError(f"invalid mapping key {key!r}")
            if not remainder:
                raise FrontmatterError(f"mapping key {key!r} has no value")
            return key, remainder
        index += 1
    raise FrontmatterError(f"mapping entry has no colon: {value!r}")


def _parse_scalar_or_flow(value: str) -> Any:
    value = value.strip()
    if not value:
        raise FrontmatterError("empty value")

    if value.startswith("["):
        if not value.endswith("]"):
            raise FrontmatterError("unterminated flow sequence")
        inner = value[1:-1].strip()
        if not inner:
            return []
        items = _split_flow(inner)
        if any(not item for item in items):
            raise FrontmatterError("empty item in flow sequence")
        return [_parse_scalar_or_flow(item) for item in items]

    if value.startswith("{"):
        if not value.endswith("}"):
            raise FrontmatterError("unterminated flow mapping")
        inner = value[1:-1].strip()
        if not inner:
            return {}
        result: dict[str, Any] = {}
        for entry in _split_flow(inner):
            key, raw = _split_mapping_entry(entry)
            if key in result:
                raise FrontmatterError(f"duplicate mapping key {key!r}")
            result[key] = _parse_scalar_or_flow(raw)
        return result

    if value.startswith('"'):
        if not value.endswith('"'):
            raise FrontmatterError("unterminated double-quoted scalar")
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise FrontmatterError(f"invalid double-quoted scalar: {exc.msg}") from exc
        if not isinstance(parsed, str):
            raise FrontmatterError("quoted scalar must be a string")
        return parsed

    if value.startswith("'"):
        if not value.endswith("'"):
            raise FrontmatterError("unterminated single-quoted scalar")
        return value[1:-1].replace("''", "'")

    if value in {"null", "Null", "NULL", "~"}:
        return None
    if re.fullmatch(r"[-+]?(?:0|[1-9]\d*)", value):
        return int(value)
    return value


def _parse_block_sequence(lines: list[tuple[int, str, int]], field: str) -> list[Any]:
    """Parse the small block-sequence subset needed by the handoff contract."""

    meaningful = [(indent, content, number) for indent, content, number in lines if content]
    if not meaningful:
        raise FrontmatterError(f"field {field!r} has no value")
    base_indent = meaningful[0][0]
    if base_indent <= 0:
        raise FrontmatterError(f"field {field!r} block value must be indented")

    result: list[Any] = []
    current_mapping: dict[str, Any] | None = None
    for indent, content, line_number in meaningful:
        if indent == base_indent and content.startswith("-"):
            if content != "-" and not content.startswith("- "):
                raise FrontmatterError(f"line {line_number}: malformed sequence marker")
            raw_item = content[1:].strip()
            if not raw_item:
                raise FrontmatterError(f"line {line_number}: empty sequence item")

            current_mapping = None
            if raw_item.startswith("{"):
                item = _parse_scalar_or_flow(raw_item)
            elif re.match(r"^[A-Za-z_][A-Za-z0-9_-]*:", raw_item):
                key, raw = _split_mapping_entry(raw_item)
                item = {key: _parse_scalar_or_flow(raw)}
                current_mapping = item
            else:
                item = _parse_scalar_or_flow(raw_item)
            result.append(item)
            continue

        if indent > base_indent and current_mapping is not None:
            match = BLOCK_KEY_RE.fullmatch(content)
            if not match or not match.group(2):
                raise FrontmatterError(f"line {line_number}: malformed mapping continuation")
            key, raw = match.group(1), match.group(2)
            if key in current_mapping:
                raise FrontmatterError(f"line {line_number}: duplicate mapping key {key!r}")
            current_mapping[key] = _parse_scalar_or_flow(raw)
            continue

        raise FrontmatterError(
            f"line {line_number}: block sequence entries must use one indentation level"
        )
    return result


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise FrontmatterError("document must begin with a '---' frontmatter boundary")

    try:
        closing_index = lines[1:].index("---") + 1
    except ValueError as exc:
        raise FrontmatterError("frontmatter is missing its closing '---' boundary") from exc

    raw_lines = lines[1:closing_index]
    fields: dict[str, Any] = {}
    index = 0
    while index < len(raw_lines):
        raw_line = raw_lines[index]
        line_number = index + 2
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            index += 1
            continue
        if raw_line[0].isspace():
            raise FrontmatterError(f"line {line_number}: unexpected indentation")

        match = TOP_LEVEL_KEY_RE.fullmatch(raw_line)
        if not match:
            raise FrontmatterError(f"line {line_number}: malformed top-level field")
        key, raw_value = match.group(1), match.group(2) or ""
        if key in fields:
            raise FrontmatterError(f"line {line_number}: duplicate field {key!r}")

        if raw_value:
            fields[key] = _parse_scalar_or_flow(raw_value)
            index += 1
            continue

        block: list[tuple[int, str, int]] = []
        index += 1
        while index < len(raw_lines):
            candidate = raw_lines[index]
            if candidate and not candidate[0].isspace() and candidate.strip():
                break
            stripped = candidate.lstrip(" \t")
            indent = len(candidate) - len(stripped)
            if stripped.startswith("#"):
                stripped = ""
            block.append((indent, stripped, index + 2))
            index += 1
        fields[key] = _parse_block_sequence(block, key)

    body = "\n".join(lines[closing_index + 1 :])
    return fields, body


def _unfenced_lines(body: str) -> list[tuple[int, str]]:
    """Return one-based body lines outside fenced code blocks."""

    lines: list[tuple[int, str]] = []
    fence_char: str | None = None
    fence_length = 0

    for line_number, line in enumerate(body.splitlines(), start=1):
        if fence_char is not None:
            stripped = line.lstrip(" ")
            indentation = len(line) - len(stripped)
            if indentation <= 3 and re.fullmatch(
                re.escape(fence_char) + "{" + str(fence_length) + ",}[ \t]*", stripped
            ):
                fence_char = None
                fence_length = 0
            continue

        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            fence_char = marker[0]
            fence_length = len(marker)
            continue

        lines.append((line_number, line))

    return lines


def parse_restricted_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse the canonical restricted-YAML envelope for downstream validators.

    Keeping one parser avoids semantic validators silently accepting a valid
    envelope form (for example block lists or a UTF-8 BOM) that the common
    handoff validator understands differently.
    """

    return _parse_frontmatter(text)


def unfenced_markdown(text: str) -> str:
    """Blank fenced code while preserving line and paragraph boundaries."""

    visible = dict(_unfenced_lines(text))
    return "\n".join(visible.get(number, "") for number in range(1, len(text.splitlines()) + 1))


def _heading_text(match: re.Match[str]) -> str:
    return re.sub(r"[ \t]+#+[ \t]*$", "", match.group(1)).strip()


def _canonical_h2s(body: str) -> list[str]:
    headings: list[str] = []

    for _, line in _unfenced_lines(body):
        heading_match = H2_RE.fullmatch(line)
        if heading_match:
            headings.append(_heading_text(heading_match))
    return headings


@dataclass(frozen=True)
class _MarkdownTable:
    start_index: int
    line_number: int
    headers: tuple[str, ...]
    body_rows: int


def _analysis_lines(body: str) -> list[tuple[int, str]]:
    """Return unfenced lines inside the canonical Analysis H2 section."""

    result: list[tuple[int, str]] = []
    in_analysis = False
    for line_number, line in _unfenced_lines(body):
        heading_match = H2_RE.fullmatch(line)
        if heading_match:
            heading = _heading_text(heading_match)
            if in_analysis:
                break
            in_analysis = heading == "Analysis"
            continue
        if in_analysis:
            result.append((line_number, line))
    return result


def _table_cells(line: str) -> tuple[str, ...]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|") and not stripped.endswith(r"\|"):
        stripped = stripped[:-1]
    if "|" not in stripped:
        return ()
    return tuple(cell.strip().replace(r"\|", "|") for cell in re.split(r"(?<!\\)\|", stripped))


def _is_table_separator(line: str) -> bool:
    cells = _table_cells(line)
    return bool(cells) and all(TABLE_SEPARATOR_CELL_RE.fullmatch(cell) for cell in cells)


def _markdown_tables(lines: list[tuple[int, str]]) -> tuple[_MarkdownTable, ...]:
    tables: list[_MarkdownTable] = []
    index = 0
    while index + 1 < len(lines):
        line_number, header_line = lines[index]
        headers = _table_cells(header_line)
        if not headers or not _is_table_separator(lines[index + 1][1]):
            index += 1
            continue

        end_index = index + 2
        while end_index < len(lines) and _table_cells(lines[end_index][1]):
            end_index += 1
        tables.append(_MarkdownTable(index, line_number, headers, end_index - index - 2))
        index = end_index
    return tuple(tables)


def _is_comment_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("<!--") and stripped.endswith("-->")


def _previous_content_line(
    lines: list[tuple[int, str]], start_index: int
) -> tuple[int, str] | None:
    for index in range(start_index - 1, -1, -1):
        line_number, line = lines[index]
        if line.strip() and not _is_comment_line(line):
            return line_number, line
    return None


def _table_has_prose_takeaway(
    lines: list[tuple[int, str]], table: _MarkdownTable
) -> bool:
    previous = _previous_content_line(lines, table.start_index)
    if previous is None:
        return False
    return H3_RE.fullmatch(previous[1]) is None and H4_RE.fullmatch(previous[1]) is None


def _is_detailed_table(table: _MarkdownTable) -> bool:
    return (
        len(table.headers) > MAX_READER_TABLE_COLUMNS
        or table.body_rows > MAX_READER_TABLE_ROWS
        or any(header.casefold() in RAW_APPENDIX_COLUMNS for header in table.headers)
    )


def _approved_lite_screen_heading(
    fields: dict[str, Any], first_h3: re.Match[str]
) -> bool:
    """Whether this exact V-native screen title replaces the generic P2 heuristic."""

    module_id = fields.get("module_id")
    return (
        isinstance(module_id, str)
        and LITE_SCREENING_H3_BY_MODULE.get(module_id) == _heading_text(first_h3)
    )


def _presentation_warnings(body: str, fields: dict[str, Any]) -> tuple[str, ...]:
    """Return non-blocking credit-research presentation warnings."""

    lines = _analysis_lines(body)
    if not lines:
        return ()

    warnings: list[str] = []
    first_line = next(
        (line for _, line in lines if line.strip() and not _is_comment_line(line)),
        None,
    )
    if first_line is not None:
        first_h3 = H3_RE.fullmatch(first_line)
        if first_h3 is None:
            warnings.append(
                "P1: Analysis must begin with a conclusion-first H3 before prose or tables"
            )
        elif (
            CONCLUSION_TITLE_RE.search(_heading_text(first_h3)) is None
            and not _approved_lite_screen_heading(fields, first_h3)
        ):
            warnings.append(
                "P2: first Analysis H3 should signal the conclusion "
                "(for example Credit view, Analytical read-through, Recommendation, "
                "Executive answer, or Decision)"
            )

    appendix_index: int | None = None
    for index, (_, line) in enumerate(lines):
        h3_match = H3_RE.fullmatch(line)
        if h3_match and _heading_text(h3_match).casefold() == ANALYTICAL_APPENDIX_TITLE:
            appendix_index = index
            break

    tables = _markdown_tables(lines)
    reader_tables = tuple(
        table for table in tables if appendix_index is None or table.start_index < appendix_index
    )
    lite_screen = fields.get("module_id") in LITE_SCREENING_H3_BY_MODULE
    if reader_tables:
        if not lite_screen:
            wide_tables = [
                f"{table.line_number} ({len(table.headers)} columns)"
                for table in reader_tables
                if len(table.headers) > MAX_READER_TABLE_COLUMNS
            ]
            if wide_tables:
                warnings.append(
                    f"P3: reader-facing tables may have at most {MAX_READER_TABLE_COLUMNS} "
                    "columns; Analysis body line(s): "
                    + ", ".join(wide_tables)
                )
            long_tables = [
                f"{table.line_number} ({table.body_rows} body rows)"
                for table in reader_tables
                if table.body_rows > MAX_READER_TABLE_ROWS
            ]
            if long_tables:
                warnings.append(
                    f"P4: reader-facing tables may have at most {MAX_READER_TABLE_ROWS} "
                    "body rows; Analysis body line(s): "
                    + ", ".join(long_tables)
                )

        raw_columns = sorted(
            {
                header.casefold()
                for table in reader_tables
                for header in table.headers
                if header.casefold() in RAW_APPENDIX_COLUMNS
            }
        )
        if raw_columns:
            warnings.append(
                "P5: raw appendix columns appear in the reader-facing section: "
                + ", ".join(raw_columns)
            )

        missing_takeaways = [
            str(table.line_number)
            for table in reader_tables
            if not _table_has_prose_takeaway(lines, table)
        ]
        if missing_takeaways:
            warnings.append(
                "P6: reader-facing tables need a prose takeaway immediately before them; "
                "Analysis body line(s): "
                + ", ".join(missing_takeaways)
            )

    if not lite_screen and appendix_index is None and any(_is_detailed_table(table) for table in tables):
        warnings.append(
            "P7: detailed tables require "
            "'### Analytical appendix — complete canonical registers'"
        )

    return tuple(warnings)


def _expected_band(score: int) -> str:
    if score >= 80:
        return "High"
    if score >= 60:
        return "Medium"
    if score >= 40:
        return "Low"
    return "Insufficient Information"


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def canonical_markdown_filename(fields: dict[str, Any]) -> str:
    """Return the exact canonical Markdown filename for validated fields."""

    module_id = fields.get("module_id")
    analysis_date = fields.get("analysis_date")
    if not (
        _is_nonempty_string(module_id)
        and MODULE_ID_RE.fullmatch(module_id)
        and _is_nonempty_string(analysis_date)
        and DATE_RE.fullmatch(analysis_date)
    ):
        raise ValueError("cannot derive canonical filename from invalid identity fields")

    key_field = "scope_key" if module_id == "CP-DR" else "issuer_id"
    subject_key = fields.get(key_field)
    if subject_key is None or isinstance(subject_key, (bool, list, dict)):
        raise ValueError("cannot derive canonical filename from invalid identity fields")

    subject_key = str(subject_key)
    if not SUBJECT_KEY_RE.fullmatch(subject_key):
        raise ValueError("cannot derive canonical filename from invalid identity fields")

    compact_date = analysis_date.replace("-", "")
    return f"{subject_key}_{module_id}_{compact_date}.md"


def _validate_string_list(field: str, value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return
    for index, item in enumerate(value):
        if not _is_nonempty_string(item):
            errors.append(f"{field}[{index}] must be a non-empty string")


def _validate_fields(fields: dict[str, Any], body: str) -> list[str]:
    errors: list[str] = []
    module_id = fields.get("module_id")
    profile_fields = CP_DR_FIELDS if module_id == "CP-DR" else ISSUER_FIELDS
    required = (*REQUIRED_FIELDS, *profile_fields)
    missing = [field for field in required if field not in fields]
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
    for field in required:
        if field in fields and fields[field] is None:
            errors.append(f"{field} must not be null")
    enum_fields = ["confidence_band", "qa_status", "committee_status"]
    if module_id == "CP-DR":
        enum_fields.extend(("scope_type", "source_mode", "research_status", "research_stop_reason"))
    for field in enum_fields:
        if field in fields and not isinstance(fields[field], str):
            errors.append(f"{field} must be a string")
    if errors:
        return errors

    string_fields = ["module_id", "module_name", "run_id", "reporting_period"]
    if module_id == "CP-DR":
        string_fields.extend(("scope_key", "subject_name", "research_question", "approved_plan_hash"))
    else:
        string_fields.append("issuer_name")
    for field in string_fields:
        if field in fields and not _is_nonempty_string(fields[field]):
            errors.append(f"{field} must be a non-empty string")

    if "issuer_id" in fields and (
        isinstance(fields["issuer_id"], (bool, list, dict)) or fields["issuer_id"] is None
    ):
        errors.append("issuer_id must be a non-empty scalar")
    elif "issuer_id" in fields and not str(fields["issuer_id"]).strip():
        errors.append("issuer_id must be a non-empty scalar")

    if _is_nonempty_string(module_id) and not MODULE_ID_RE.fullmatch(module_id):
        errors.append("module_id must match a canonical CP-* identifier")

    key_field = "scope_key" if module_id == "CP-DR" else "issuer_id"
    subject_key = fields.get(key_field)
    if (
        subject_key is not None
        and not isinstance(subject_key, (bool, list, dict))
        and str(subject_key).strip()
        and not SUBJECT_KEY_RE.fullmatch(str(subject_key))
    ):
        errors.append(
            f"{key_field} must use only ASCII letters, digits, periods, and hyphens; "
            "it cannot contain whitespace or start or end with punctuation"
        )

    if module_id == "CP-DR":
        if fields.get("scope_type") not in {"issuer", "sector"}:
            errors.append("scope_type must be issuer or sector")
        if fields.get("source_mode") not in {"supplied_only", "web_only", "hybrid"}:
            errors.append("source_mode is not a CP-DR enum value")
        plan_hash = fields.get("approved_plan_hash")
        if plan_hash is not None and (
            not isinstance(plan_hash, str) or not PLAN_HASH_RE.fullmatch(plan_hash)
        ):
            errors.append("approved_plan_hash must be sha256: followed by 64 lowercase hex characters")
        coverage = fields.get("coverage_score")
        if coverage is not None and (isinstance(coverage, bool) or not isinstance(coverage, int)):
            errors.append("coverage_score must be an integer")
        elif isinstance(coverage, int) and not 0 <= coverage <= 100:
            errors.append("coverage_score must be between 0 and 100")
        research_status = fields.get("research_status")
        if research_status not in {"Complete", "Complete with Gaps", "Blocked"}:
            errors.append("research_status is not a CP-DR enum value")
        stop_reason = fields.get("research_stop_reason")
        if stop_reason not in {
            "coverage_satisfied", "budget_exhausted", "sources_exhausted", "blocked", "user_stopped"
        }:
            errors.append("research_stop_reason is not a CP-DR enum value")
        if research_status == "Blocked" and stop_reason != "blocked":
            errors.append("research_status Blocked requires research_stop_reason blocked")
        if stop_reason == "blocked" and research_status != "Blocked":
            errors.append("research_stop_reason blocked requires research_status Blocked")
        if research_status == "Blocked" and fields.get("qa_status") != "Blocked":
            errors.append("research_status Blocked requires qa_status Blocked")

    analysis_date = fields.get("analysis_date")
    if analysis_date is not None:
        if not _is_nonempty_string(analysis_date) or not DATE_RE.fullmatch(analysis_date):
            errors.append("analysis_date must use YYYY-MM-DD")
        else:
            try:
                date.fromisoformat(analysis_date)
            except ValueError:
                errors.append("analysis_date is not a valid calendar date")

    score = fields.get("confidence_score")
    if score is not None and (isinstance(score, bool) or not isinstance(score, int)):
        errors.append("confidence_score must be an integer")
    elif isinstance(score, int) and not 0 <= score <= 100:
        errors.append("confidence_score must be between 0 and 100")

    band = fields.get("confidence_band")
    if band is not None and band not in CONFIDENCE_BANDS:
        errors.append("confidence_band is not a canonical enum value")
    if isinstance(score, int) and 0 <= score <= 100 and band in CONFIDENCE_BANDS:
        expected_band = _expected_band(score)
        if band != expected_band:
            errors.append(
                f"confidence_band {band!r} is inconsistent with score {score}; "
                f"expected {expected_band!r}"
            )

    qa_status = fields.get("qa_status")
    if qa_status is not None and qa_status not in QA_STATUSES:
        errors.append("qa_status is not a canonical enum value")
    if isinstance(score, int) and 0 <= score <= 100:
        if qa_status == "Blocked" and score > 39:
            errors.append("qa_status Blocked caps confidence_score at 39")
        elif qa_status == "Restricted" and score > 59:
            errors.append("qa_status Restricted caps confidence_score at 59")

    committee_status = fields.get("committee_status")
    if committee_status is not None and committee_status not in COMMITTEE_STATUSES:
        errors.append("committee_status is not a canonical enum value")

    for field in ("limitation_flags", "validation_warnings", "downstream_consumers"):
        if field in fields:
            _validate_string_list(field, fields[field], errors)

    downstream = fields.get("downstream_consumers")
    if isinstance(downstream, list):
        for index, consumer in enumerate(downstream):
            if _is_nonempty_string(consumer) and not MODULE_ID_RE.fullmatch(consumer):
                errors.append(f"downstream_consumers[{index}] is not a canonical CP-* identifier")

    upstream = fields.get("upstream_artifacts_used")
    if upstream is not None and not isinstance(upstream, list):
        errors.append("upstream_artifacts_used must be a list")
    elif isinstance(upstream, list):
        for index, artifact in enumerate(upstream):
            if not isinstance(artifact, dict):
                errors.append(f"upstream_artifacts_used[{index}] must be a mapping")
                continue
            for key in ("module_id", "run_id", "period"):
                if key not in artifact or not _is_nonempty_string(artifact[key]):
                    errors.append(
                        f"upstream_artifacts_used[{index}].{key} must be a non-empty string"
                    )
            upstream_module = artifact.get("module_id")
            if _is_nonempty_string(upstream_module) and not MODULE_ID_RE.fullmatch(upstream_module):
                errors.append(
                    f"upstream_artifacts_used[{index}].module_id is not a canonical CP-* identifier"
                )

    headings = _canonical_h2s(body)
    if headings != list(CANONICAL_HEADINGS):
        errors.append(
            "H2 headings must be exactly once and in canonical order: "
            + " -> ".join(CANONICAL_HEADINGS)
            + f"; found: {headings!r}"
        )
    return errors


def validate_text(
    text: str,
    *,
    filename: str | Path | None = None,
    expected_module: str | None = None,
    expected_run_id: str | None = None,
    expected_period: str | None = None,
) -> ValidationResult:
    """Validate handoff text, its optional filename, and expected identity values."""

    try:
        fields, body = _parse_frontmatter(text)
    except FrontmatterError as exc:
        return ValidationResult((str(exc),), (), None)

    errors = _validate_fields(fields, body)
    presentation_warnings = _presentation_warnings(body, fields) if not errors else ()
    if errors:
        return ValidationResult(tuple(errors), (), fields, presentation_warnings)

    if filename is not None:
        observed_filename = Path(filename).name
        expected_filename = canonical_markdown_filename(fields)
        if observed_filename != expected_filename:
            error = (
                "canonical Markdown filename mismatch: "
                f"expected {expected_filename!r}, found {observed_filename!r}"
            )
            return ValidationResult((error,), (), fields, presentation_warnings)

    expected_values = (
        ("module_id", expected_module),
        ("run_id", expected_run_id),
        ("reporting_period", expected_period),
    )
    mismatches = tuple(
        f"{field} mismatch: expected {expected!r}, found {fields.get(field)!r}"
        for field, expected in expected_values
        if expected is not None and fields.get(field) != expected
    )
    return ValidationResult((), mismatches, fields, presentation_warnings)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a CP_AB_EXPORT_SPEC canonical Markdown handoff without repairing it."
    )
    parser.add_argument("handoff", help="Markdown handoff to validate, or - to read from stdin")
    parser.add_argument("--expected-module", help="required module_id value")
    parser.add_argument("--expected-run-id", help="required run_id value")
    parser.add_argument("--expected-period", help="required reporting_period value")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.handoff == "-":
        # Stdin mode: the code interpreter has the completed artifact
        # already in context and no durable filesystem -- there is nothing
        # to open a path for. No real filename exists to identity-check
        # against, so that check is skipped (filename=None), same as any
        # other caller that passes filename=None.
        try:
            text = sys.stdin.read()
        except UnicodeError as exc:
            print(f"MALFORMED <stdin>: cannot read UTF-8 handoff: {exc}", file=sys.stderr)
            return EXIT_MALFORMED
        display = "<stdin>"
        filename_for_check = None
    else:
        handoff_path = Path(args.handoff)
        if handoff_path.suffix.lower() != ".md":
            print(f"MALFORMED {handoff_path}: handoff filename must end in .md", file=sys.stderr)
            return EXIT_MALFORMED
        try:
            text = handoff_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            print(f"MALFORMED {handoff_path}: cannot read UTF-8 handoff: {exc}", file=sys.stderr)
            return EXIT_MALFORMED
        display = str(handoff_path)
        filename_for_check = handoff_path.name

    result = validate_text(
        text,
        filename=filename_for_check,
        expected_module=args.expected_module,
        expected_run_id=args.expected_run_id,
        expected_period=args.expected_period,
    )
    if result.errors:
        print(f"MALFORMED {display}", file=sys.stderr)
        for error in result.errors:
            print(f"- {error}", file=sys.stderr)
    elif result.identity_mismatches:
        print(f"IDENTITY_MISMATCH {display}", file=sys.stderr)
        for mismatch in result.identity_mismatches:
            print(f"- {mismatch}", file=sys.stderr)
    elif result.exit_code == EXIT_BLOCKED:
        print(f"BLOCKED {display}: structurally valid; qa_status is Blocked")
    else:
        print(f"VALID {display}")
    if not result.errors and not result.identity_mismatches and result.presentation_warnings:
        print(f"PRESENTATION_WARNINGS {display}", file=sys.stderr)
        for warning in result.presentation_warnings:
            print(f"- {warning}", file=sys.stderr)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
