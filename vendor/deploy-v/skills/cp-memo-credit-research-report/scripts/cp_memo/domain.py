"""Typed, non-analytical records used by CP-MEMO."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ELIGIBLE = "ELIGIBLE"
LIMITATIONS_ONLY = "LIMITATIONS_ONLY"
EXCLUDED = "EXCLUDED"


@dataclass(frozen=True)
class Candidate:
    name: str
    text: str
    sha256: str
    fields: dict[str, Any] | None
    validation_exit_code: int
    validation_errors: tuple[str, ...] = ()
    identity_mismatches: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArtifactRecord:
    name: str
    sha256: str
    module_id: str | None
    module_name: str | None
    display: str | None
    run_id: str | None
    issuer_id: str | None
    issuer_name: str | None
    reporting_period: str | None
    analysis_date: str | None
    profile_id: str | None
    selection_id: str | None
    route_node_id: str | None
    qa_status: str | None
    confidence_score: int | None
    confidence_band: str | None
    disposition: str
    reason: str
    text: str = field(repr=False, default="")

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("text", None)
        return data


@dataclass(frozen=True)
class RunAnchor:
    issuer_id: str
    issuer_name: str
    run_id: str
    profile_id: str
    selection_id: str
    reporting_period: str
    analysis_date: str
    authority_digest: str


@dataclass(frozen=True)
class InventoryResult:
    status: str
    anchor: RunAnchor | None
    artifacts: tuple[ArtifactRecord, ...]
    candidate_run_ids: tuple[str, ...] = ()
    message: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "anchor": asdict(self.anchor) if self.anchor else None,
            "artifacts": [item.public_dict() for item in self.artifacts],
            "candidate_run_ids": list(self.candidate_run_ids),
            "message": self.message,
        }


@dataclass(frozen=True)
class SourceNote:
    number: int
    display: str
    artifact_name: str
    sha256: str
    locator: str


@dataclass(frozen=True)
class ReportBlock:
    kind: str
    text: str
    source_note: int | None = None
    rows: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class ReportSection:
    title: str
    blocks: tuple[ReportBlock, ...]


@dataclass(frozen=True)
class ReportSpec:
    anchor: RunAnchor
    publication_date: str
    publication_status: str
    confidentiality_label: str
    sections: tuple[ReportSection, ...]
    source_notes: tuple[SourceNote, ...]
    artifacts: tuple[ArtifactRecord, ...]
    page_target: str = "10–15 pages (soft target)"


@dataclass(frozen=True)
class BuildResult:
    status: str
    session_path: str | None = None
    output_path: str | None = None
    page_count: int | None = None
    sha256: str | None = None
    message: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
