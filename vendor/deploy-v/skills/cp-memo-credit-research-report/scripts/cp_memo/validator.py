"""Structural checks for the exact draft and published DOCX."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from docx import Document

from .planner import SECTION_TITLES

MODULE_ID_RE = re.compile(r"\bCP-(?:\d+[A-Z]?|[A-Z][A-Z0-9-]*)\b")


class DocumentValidationError(ValueError):
    pass


def validate_docx(path: Path, *, expected_page_count: int | None = None) -> None:
    if not path.is_file() or path.suffix.lower() != ".docx" or path.stat().st_size == 0:
        raise DocumentValidationError("DOCX artifact is missing or empty")
    doc = Document(path)
    visible = "\n".join(p.text for p in doc.paragraphs)
    visible += "\n" + "\n".join(cell.text for table in doc.tables for row in table.rows for cell in row.cells)
    if "[[PAGE_COUNT]]" in visible:
        raise DocumentValidationError("page-count placeholder remains")
    if expected_page_count is not None and f"Rendered page count: {expected_page_count}." not in visible:
        raise DocumentValidationError("rendered page count does not match the final PDF")
    for title in SECTION_TITLES[1:]:
        if title not in visible:
            raise DocumentValidationError(f"required report section is missing: {title}")
    if "CP-MEMO — CreditResearchReport" not in visible:
        raise DocumentValidationError("report identity is missing")
    for match in MODULE_ID_RE.finditer(visible):
        if re.match(r"\s+—\s+[A-Za-z0-9]", visible[match.end():]) is None:
            raise DocumentValidationError(f"bare module ID in visible report: {match.group(0)}")
    with zipfile.ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml")
        footer_xml = b"".join(archive.read(name) for name in archive.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
    if b"w:tblHeader" not in document_xml:
        raise DocumentValidationError("repeating table header marker is missing")
    if b" PAGE " not in footer_xml or b'w:fldCharType="begin"' not in footer_xml:
        raise DocumentValidationError("PAGE field is missing or malformed")
