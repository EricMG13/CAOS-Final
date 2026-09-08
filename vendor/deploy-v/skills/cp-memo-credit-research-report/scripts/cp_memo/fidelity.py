"""Conservative source-mapping checks for editorial report statements."""

from __future__ import annotations

import re

from .domain import ReportSpec

NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])(?:[$€£¥]?\(?-?\d[\d,.]*(?:%|x|bps|bp)?\)?)(?![A-Za-z0-9])", re.IGNORECASE)
MODULE_ID_RE = re.compile(r"\bCP-(?:\d+[A-Z]?|[A-Z][A-Z0-9-]*)\b")


class FidelityError(ValueError):
    pass


def _numbers(text: str) -> set[str]:
    return {match.group(0) for match in NUMBER_RE.finditer(text)}


def validate_fidelity(spec: ReportSpec) -> None:
    note_by_number = {note.number: note for note in spec.source_notes}
    artifact_by_name = {item.name: item for item in spec.artifacts}
    for section in spec.sections:
        for block in section.blocks:
            if block.kind == "table":
                texts = [cell for row in block.rows for cell in row]
            else:
                texts = [block.text]
            for text in texts:
                for module_id in MODULE_ID_RE.findall(text):
                    if not re.search(rf"\b{re.escape(module_id)}\s+—\s+[A-Za-z0-9]", text):
                        raise FidelityError(f"bare or unverified module reference: {module_id}")
            if block.source_note is None:
                continue
            note = note_by_number.get(block.source_note)
            if note is None:
                raise FidelityError("report block references an unknown source note")
            artifact = artifact_by_name.get(note.artifact_name)
            if artifact is None:
                raise FidelityError("source note references an unknown artifact")
            unsupported = _numbers(block.text) - _numbers(artifact.text)
            if unsupported:
                raise FidelityError(f"unsupported numeric tokens in statement: {sorted(unsupported)}")
