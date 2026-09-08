<!-- CP-5 Schema Reference (T3) | 2026-06-03 -->

## Required Output Sections (9)
All 9 sections must be present using exact required headings.

## Required Tables (8)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T5B.1 | Source Register | Source Document ID, Source Document Name, Source Quality, Period, Entity Covered, Data Supplied, Limitation, Downstream Use |
| T5B.2 | Top 5 Material Credit Drivers | Rank, Credit Driver, Originating Module, Source-Supported Basis, Why Material, Committee Relevance, Source Trace, Limitation |
| T5B.3 | Traceability Map | Credit Driver / Conclusion, Originating Module, Source Evidence, Citation Present?, Source Quality, Classification, Claim Status, Confidence Level, Traceability Status |
| T5B.4 | Source Lineage Register | Statement, Source Path, Source File, Source Document ID, Page / Section, Module Section, Type, Source Quality, Notes |
| T5B.5 | Calculation and Assumption Register | Item, Where Used, Source Inputs / Assumption, Formula or Logic, Status, Claim Status, Confidence Level, Credit Relevance, Source Trace |
| T5B.6 | Missing Citation and Weak-Lineage Flags | Severity, Conclusion, Issue, Classification, Why It Matters, Required Remediation, Affected Output / Export Record |
| T5B.7 | Auditability Assessment | Auditability Dimension, Assessment, Evidence, Risk Mechanic, Credit Implication, Remediation Needed |
| T5B.8 | Gaps Ledger | Gap ID, Gap, Missing Evidence / Citation, Why It Matters, Impact on Output, Consequence for Confidence, Required Follow-Up Source |

## Narrative Sections (1)
| Step | Section | Format |
|------|---------|--------|
| 9 | Overall Traceability View | Required formulation: "Overall, evidence traceability is [Assessment]. Of the Top 5 material credit drivers, [N] are directly sourced, [N] are calculated, [N] are assumption-based, [N] are analyst inferences, and [N] are weak-lineage/untraced/conflicting/insufficient-information items. The most important provenance gap is [gap], which matters because [risk mechanic] and implies [committee-readiness impact]." |

## QA Checklist
- [ ] All 9 output sections present using exact required headings
- [ ] All lineage classifications use ONLY the 8 canonical values (Directly Sourced / Calculated / Assumption-Based / Analyst Inference / Weak Lineage / Untraced / Conflicting / Insufficient Information)
- [ ] All severity values use ONLY: Critical / Material / Minor
- [ ] Traceability scope declared (Top 5 or Full) in Step 1
- [ ] Module Status assigned (Full Run / Ready with Limitations / Blocked)
- [ ] Orphan Claim protocol applied: any Untraced/Weak Lineage/Insufficient Information conclusion in committee-facing output without mitigation flag triggers VE-015
- [ ] Every material claim traced to source or explicitly flagged
- [ ] No silent citation repair — missing citations flagged, not fabricated
- [ ] No alteration of substantive upstream conclusions
- [ ] Auditability Assessment covers all 5 dimensions (source coverage, citation completeness, calculation traceability, assumption transparency, Markdown/export artifact integrity)
- [ ] Gaps Ledger has sequential IDs (CP-5-GAP-NNN)
- [ ] Overall Traceability View uses required formulation
- [ ] Overall assessment aligned with Auditability Assessment (T5B.7)
- [ ] Numeric Confidence Score (0–100) + band emitted per CP_CONFIDENCE_SCORE.md (band is the derived label)
- [ ] Canonical Markdown authored and valid; every the Markdown handoff verified and reported independently
- [ ] Exact source filenames quoted where available (NATIVE CITATIONS)

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
