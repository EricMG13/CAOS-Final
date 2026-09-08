<!-- CP-PARSE Schema Reference | v2.0 | 2026-08-04 -->
<schema_reference module="CP-PARSE" tier="3">
# CP-PARSE data-preparation schema

Phase identity: `document_parse_manifest`, within owner `module_id=CP-0`, `module_name=SourceReadiness`.

## Core objects

| ID | Object | Purpose |
|---|---|---|
| P1 | Pipeline | run identity, objective and preparation status |
| P2 | Workspace Record | immutable source roots, managed workspace and original hashes |
| P3 | Input Sources | original identity, authority, entity, period and version links |
| P4 | Triage Register | scores, frozen decisions, rationale, overrides and profiles |
| P5 | Parse Jobs | methods, status, fidelity, coverage and limitations |
| P6 | Prepared Artifacts | artifact paths/hashes, locators and original lineage |
| P7 | Representation Catalog | one active content representation per retained logical source |
| P8 | Package Record | batches, members, indexes, checksums and safe-path validation |

## Representation invariants

- `PASS_THROUGH` selects the immutable original as `ACTIVE_CONTENT`.
- `COMPLETE` or `DEGRADED` parsing selects the prepared representation as `ACTIVE_CONTENT`; the original remains authority and verification provenance.
- `BLOCKED` has no active content and no silent fallback.
- `SKIP_DUPLICATE` names a valid selected source; `SKIP_LOW_VALUE` remains inventory only.
- Each retained logical source has exactly one active representation.

## Analysis sections

Preparation summary; pack inventory and version map; triage rationale; extraction/fidelity assessment; representation catalog; package status; limitations; CP-0 handoff.

## QA and export

The preparation registers belong inside `[IssuerID]_CP-0_[YYYYMMDD].md`, the only module handoff. Supporting prepared Markdown and ZIP batches remain evidence artifacts. Preserve the canonical YAML and six H2 sections defined by `CP_AB_EXPORT_SPEC.md`; fail closed on fidelity, representation, checksum, package or Markdown validation failure.
</schema_reference>
