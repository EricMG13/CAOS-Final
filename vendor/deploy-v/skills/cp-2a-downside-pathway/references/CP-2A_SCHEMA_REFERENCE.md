<!-- CP-2A Schema Reference (T3) | 2026-06-03 -->

## Required Tables (9)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T2B.1 | Source Register | source_document_id, source_document_name, source_quality, period, entity_covered, data_supplied, limitation, downstream_use |
| T2B.2 | Business Model Snapshot | Dimension, Source-Supported Fact, Risk Mechanic, Credit Implication, Source Trace, Limitation |
| T2B.3 | Fragility Map | Fragility Driver, First Break Point, Evidence, Risk Mechanic, Credit Implication, Confidence, Source Trace |
| T2B.4 | Stress Transmission Table | Operating Stress, Cash-Flow Impact, Leverage / Liquidity Result, Credit Consequence, Evidence Status, Source Trace |
| T2B.5 | Downside Pathway Register | Pathway Row ID, Pathway Category, Driver, Causal Vector, PD/LGD/RV/Monitoring Consequence, Source Trace, Confidence, Downstream Module |
| T2B.6 | Downside Sensitivity Matrix | Sensitivity, Input Basis, Formula / Method, Result, Credit Interpretation, Status, Source Trace |
| T2B.7 | Monitoring Sensitivity Flags | Trigger ID, Indicator, Leading / Lagging, Threshold or Qualitative Signal, Linked Pathway Row, Escalation Consequence, Source Trace, Limitation |
| T2B.8 | Cross-Module Handoff Register | Downstream Module, Handoff Item, Why It Matters, Required Consumer Action, Source / Pathway Link, Limitation |
| T2B.9 | Gaps Ledger | Gap ID, Missing Data, Why It Matters, Affected Pathway / Calculation / Trigger, Consequence for Confidence, Required Follow-Up Source |

## Canonical Credit Implication (13 values)
Positive — Deleveraging | Positive — Margin Expansion | Positive — Revenue Growth | Positive — Liquidity Improvement | Positive — Covenant Headroom Expansion | Neutral — Stable | Negative — Leverage Increase | Negative — Margin Compression | Negative — Revenue Decline | Negative — Liquidity Deterioration | Negative — Covenant Erosion | Negative — Refinancing Risk | Insufficient Information

## Evidence Status Values
Source Fact | Calculation | Analyst Inference | Insufficient Information | Directional Only

## Sensitivity Status Values
Calculated | Directional Only | Not Calculable

## Module Confidence
Primary measure: numeric **confidence_score (0–100)** per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md` (computed at output, recomputed/audited by CP-5A). Derived **confidence_band**: High ≥80 | Medium 60–79 | Low 40–59 | Insufficient Information <40 — carried in the canonical Markdown envelope and shown with the score in the Audit Summary.
Row-level "Confidence" (table column on T2B.3 Fragility Map / T2B.5 Downside Pathway Register): High | Medium | Low | Not Assessable — an evidence-quality label on individual rows, not the module-level measure.

## QA Checklist
- [ ] Source register completed with all available sources and limitations
- [ ] Module status stated: Completed / Ready with Limitations / Blocked
- [ ] Blocking gate enforced: both CP-1 and CP-2 unavailable → Blocked
- [ ] Every material conclusion follows [Evidence] → [Risk Mechanic] → [Credit Implication]
- [ ] Required Causal Chain applied: Operating Driver → Break Point → Effect → FCF/Liquidity → Leverage/Covenant/Refi → Consequence
- [ ] First-Break Discipline: no pathway begins with EBITDA decline without identifying operating source
- [ ] Cash-Flow Conversion Discipline: every path translates to cash-flow effects
- [ ] Directional Vector Discipline: explicit arrows, no broad statements without transmission mechanism
- [ ] No False Precision: quantitative sensitivities only where source supports
- [ ] Content distinctions applied: Source Fact | Calculation | Analyst Inference | Monitoring Signal | Credit Implication | Gap
- [ ] All pathway rows have Pathway Row IDs (CP-2A-DP-###)
- [ ] All triggers map to pathway rows
- [ ] All trigger IDs follow format (CP-2A-MON-###)
- [ ] All gaps logged with Gap IDs (CP-2A-GAP-###)
- [ ] Cross-module handoff register covers all 10 downstream consumers
- [ ] Overall View contains no new data — synthesis only
- [ ] Export contract followed per `../../../CANON_SHARED.md § CP_AB_EXPORT_SPEC.md`: canonical Markdown valid; the Markdown handoff pass view-appropriate parity; numeric confidence_score + band in Audit Summary (no lettered appendices A–E, JSON blocks, or export manifest)

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
