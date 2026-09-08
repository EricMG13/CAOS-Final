<!-- CP-2B Schema Reference (T3) | 2026-06-02 -->
`cp2b.cp_model_catalysts` is the ranked, source-grounded workbook projection
of the catalyst register, emitted on every run.

## CP-MODEL projection profile

Stable table ID: `cp2b.cp_model_catalysts`.

Columns: `rank | event_date_or_window | event | credit_relevance | status |
source_id | source_locator | as_of`. Emit one to eight uniquely and
contiguously ranked `READY` rows. The projection is emitted on every run,
preserves CP-2B source lineage and does not replace the seven required
analytical tables.

## Required Tables (7)
| ID | Table | Key Columns |
|----|-------|-------------|
| T5.1 | Event Source Register | Event ID, Source Document, Event Description, Event Category, Date/Range, Evidence Quality, Source Reliability |
| T5.2 | Catalyst Calendar | Date/Window, Event Description, Event Category, Credit Relevance Summary, Source |
| T5.3 | Event Risk Register | Event ID, Description, Probability, Credit Impact Channel(s), Impact Severity, Affected Metrics, Risk Direction, Source |
| T5.4 | Probability/Impact Matrix | Event ID, Description, Probability, Impact, P/I Classification |
| T5.5 | Monitoring Priority Table | Event ID, Description, Priority, Monitoring Frequency, Trigger Condition, Responsible Module |
| T5.6 | Watchlist Handoff Register | Event ID, Description, Priority, Receiving Module, Handoff Content, Timing, Rationale |
| T5.7 | Gaps & Limitations Ledger | Gap Description, Affected Section, Downstream Impact, Severity, Recommended Action |

## QA Checklist
- [ ] All events source-supported  - [ ] Calendar events explicitly dated/scheduled only (no inferred dates; undated events in Gaps Ledger)  - [ ] Probability/impact labels ordinal only  - [ ] Event risk channels mapped  - [ ] Priority rankings assigned  - [ ] Cross-module handoff complete  - [ ] Gaps cumulative  - [ ] Closing statement includes event count and horizon  - [ ] Numeric Confidence Score (0–100) + band computed per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md` and placed in the Audit Summary before the narrative  - [ ] Export contract followed: canonical Markdown valid; the Markdown handoff pass view-appropriate parity (no lettered A–E, JSON blocks, or export manifest)

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
