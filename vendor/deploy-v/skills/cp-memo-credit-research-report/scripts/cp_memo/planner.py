"""Deterministically arrange upstream-authored excerpts into a reader report."""

from __future__ import annotations

import re
from datetime import date

from .domain import (
    ELIGIBLE,
    LIMITATIONS_ONLY,
    InventoryResult,
    ReportBlock,
    ReportSection,
    ReportSpec,
    SourceNote,
)
from .markdown import limitation_passages, reader_passages

SECTION_TITLES = (
    "Cover and publication status",
    "Executive credit snapshot",
    "Business and transaction profile",
    "Financial performance and forward trajectory",
    "Capital structure, liquidity, and refinancing",
    "Downside, recovery, covenant, and structural protection",
    "Market pricing, relative value, security preference, and portfolio posture",
    "Catalysts, monitoring triggers, and thesis breakers",
    "Evidence quality, unresolved conflicts, limitations, and QA status",
    "Module provenance index",
)

MODULE_SECTION = {
    "CP-1A": SECTION_TITLES[2],
    "CP-1": SECTION_TITLES[3],
    "CP-1B": SECTION_TITLES[3],
    "CP-1C": SECTION_TITLES[3],
    "CP-1D": SECTION_TITLES[3],
    "CP-2": SECTION_TITLES[3],
    "CP-2E": SECTION_TITLES[3],
    "CP-2D": SECTION_TITLES[3],
    "CP-2G": SECTION_TITLES[3],
    "CP-2H": SECTION_TITLES[3],
    "CP-L10": SECTION_TITLES[3],
    "CP-2A": SECTION_TITLES[5],
    "CP-4": SECTION_TITLES[5],
    "CP-3C": SECTION_TITLES[5],
    "CP-3D": SECTION_TITLES[4],
    "CP-4C": SECTION_TITLES[5],
    "CP-3": SECTION_TITLES[6],
    "CP-6": SECTION_TITLES[6],
    "CP-8": SECTION_TITLES[7],
    "CP-DR": SECTION_TITLES[7],
}
DECISION_OWNERS = frozenset({"CP-3", "CP-6"})
MODULE_REFERENCE_RE = re.compile(
    r"(?P<module_id>\bCP-(?:\d+[A-Z]?|[A-Z][A-Z0-9-]*)\b)"
    r"(?:[ \t]+—[ \t]+[A-Za-z][A-Za-z0-9_-]*)?"
)


def _present_passage(text: str, artifact, display_by_id: dict[str, str]) -> str:
    text = MODULE_REFERENCE_RE.sub(
        lambda match: display_by_id.get(match.group("module_id"), match.group(0)),
        text,
    )
    qualifications: set[str] = set()
    body = text
    while True:
        prefix, separator, remainder = body.partition(" — ")
        prefix_parts = [part.strip() for part in prefix.split(";")]
        if not separator or not prefix_parts or any(part not in {"Restricted", "SCREENING_ONLY"} for part in prefix_parts):
            break
        qualifications.update(prefix_parts)
        body = remainder
    if artifact.qa_status == "Restricted" and not text.startswith("Restricted —"):
        qualifications.add("Restricted")
    if artifact.module_id and artifact.module_id.startswith("CP-L"):
        qualifications.add("SCREENING_ONLY")
    ordered = [item for item in ("Restricted", "SCREENING_ONLY") if item in qualifications]
    return f"{'; '.join(ordered)} — {body}" if ordered else text


def _publication_status(inventory: InventoryResult) -> str:
    owners = {item.module_id for item in inventory.artifacts if item.disposition == ELIGIBLE}
    if not owners.intersection(DECISION_OWNERS):
        return "Research synthesis — no investment recommendation"
    return "Editorial consolidation of upstream research — no CP-MEMO recommendation"


def plan_report(inventory: InventoryResult, publication_date: str | None = None, confidentiality_label: str = "Confidential") -> ReportSpec:
    if inventory.status != "READY" or inventory.anchor is None:
        raise ValueError("inventory must be READY before report planning")
    publication_date = publication_date or date.today().isoformat()
    section_blocks: dict[str, list[ReportBlock]] = {title: [] for title in SECTION_TITLES}
    notes: list[SourceNote] = []
    display_by_id = {
        item.module_id: item.display
        for item in inventory.artifacts
        if item.module_id and item.display
    }

    for artifact in inventory.artifacts:
        if artifact.disposition not in {ELIGIBLE, LIMITATIONS_ONLY} or not artifact.display:
            continue
        passages = (
            limitation_passages(artifact.text)
            if artifact.disposition == LIMITATIONS_ONLY
            else reader_passages(artifact.text)
        )
        destination = (
            SECTION_TITLES[8]
            if artifact.disposition == LIMITATIONS_ONLY
            else MODULE_SECTION.get(artifact.module_id or "", SECTION_TITLES[7])
        )
        for passage in passages:
            note_number = len(notes) + 1
            notes.append(SourceNote(note_number, artifact.display, artifact.name, artifact.sha256, passage.locator))
            section_blocks[destination].append(
                ReportBlock("bullet", _present_passage(passage.text, artifact, display_by_id), note_number)
            )

    executive_sources = [
        item for item in inventory.artifacts
        if item.disposition == ELIGIBLE and item.module_id in {"CP-6", "CP-3", "CP-2", "CP-L10"}
    ]
    for artifact in executive_sources:
        passages = reader_passages(artifact.text, limit=2)
        for passage in passages:
            note_number = len(notes) + 1
            notes.append(SourceNote(note_number, artifact.display or "", artifact.name, artifact.sha256, passage.locator))
            section_blocks[SECTION_TITLES[1]].append(
                ReportBlock("bullet", _present_passage(passage.text, artifact, display_by_id), note_number)
            )

    if not section_blocks[SECTION_TITLES[1]]:
        section_blocks[SECTION_TITLES[1]].append(
            ReportBlock("paragraph", "Research synthesis — no investment recommendation")
        )

    cp5_present = any(item.module_id == "CP-5" and item.disposition == LIMITATIONS_ONLY for item in inventory.artifacts)
    if not cp5_present:
        section_blocks[SECTION_TITLES[8]].insert(
            0,
            ReportBlock(
                "warning",
                "CP-5 — EvidenceTraceValidator / CP-5A — ResearchIntegrityQA clearance was not available at publication time.",
            ),
        )

    coverage_rows = [("Module", "Status", "Contribution", "Artifact")]
    for item in inventory.artifacts:
        label = item.display or "Unregistered or unidentified module"
        coverage_rows.append((label, item.qa_status or "—", item.disposition, item.name))
    section_blocks[SECTION_TITLES[9]].append(ReportBlock("table", "Module provenance index", rows=tuple(coverage_rows)))

    sections = tuple(
        ReportSection(title, tuple(section_blocks[title]))
        for title in SECTION_TITLES[1:]
    )
    return ReportSpec(
        anchor=inventory.anchor,
        publication_date=publication_date,
        publication_status=_publication_status(inventory),
        confidentiality_label=confidentiality_label,
        sections=sections,
        source_notes=tuple(notes),
        artifacts=inventory.artifacts,
    )
