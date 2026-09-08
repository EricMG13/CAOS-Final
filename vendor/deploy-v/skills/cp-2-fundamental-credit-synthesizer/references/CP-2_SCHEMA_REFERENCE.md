<!-- CP-2 Schema Reference (T3) | 2026-06-03 -->
`cp2.cp_model_strengths_weaknesses` is the ranked, source-grounded workbook
projection of Step 06, emitted on every run.

## CP-MODEL projection profile

Stable table ID: `cp2.cp_model_strengths_weaknesses`

Columns: `direction | rank | label | mechanism | evidence_ids | status |
source_id | source_locator | as_of`.

Emit one to five independently ranked `STRENGTH` rows and one to five
independently ranked `WEAKNESS` rows. This projection is emitted on every
run and does not replace any of the five required analytical tables.


## Required Tables (5)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T2.1 | Source Register | source_document_id, source_document_name, source_quality, period, entity_covered, data_supplied, limitation, downstream_use |
| T2.7 | Financial Profile Scorecard | Dimension, Assessment, Credit Rationale |
| T2.10 | Materiality Filter | Rank, Driver, Evidence, Risk Mechanic, Credit Implication, Direction, Confidence |
| T2.11 | Issuer Matrix | Business Quality Factor, Assessment, Primary Downside Path, Credit Relevance |
| T2.12 | Monitoring Triggers | Trigger, Threshold / Signal, Why It Matters, Credit Impact, Source / Limitation |

## Canonical Credit Implication (13 values)
Positive — Deleveraging | Positive — Margin Expansion | Positive — Revenue Growth | Positive — Liquidity Improvement | Positive — Covenant Headroom Expansion | Neutral — Stable | Negative — Leverage Increase | Negative — Margin Compression | Negative — Revenue Decline | Negative — Liquidity Deterioration | Negative — Covenant Erosion | Negative — Refinancing Risk | Insufficient Information

## Financial Profile Assessment Values
Strong / Average / Weak / Not Assessable

## Materiality Filter Values
- Direction: Positive / Negative / Mixed
- Confidence: High / Medium / Low / Not Assessable

## QA Checklist
- [ ] Source register completed with all available sources and limitations
- [ ] Module status stated: Full Run / Ready with Limitations / Blocked
- [ ] Every material factual claim traceable to a source
- [ ] Content distinctions applied: Source Fact | Calculation | Analyst Interpretation | Credit Implication | Gap
- [ ] [Evidence] → [Risk Mechanic] → [Credit Implication] chain present for every material conclusion
- [ ] Financial Profile scorecard uses only permitted assessment values
- [ ] Materiality Filter uses only permitted Direction and Confidence values
- [ ] Monitoring triggers use quantitative thresholds only if source-supported
- [ ] All [Insufficient Information] gaps logged
- [ ] Source conflicts logged, not silently reconciled
- [ ] No generic adjectives without issuer-specific evidence
- [ ] No fabricated metrics, ratings, or relative-value labels
- [ ] Overall Credit View contains no new data — synthesis only
- [ ] Numeric Confidence Score (0–100) + band computed per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md` and placed in the Audit Summary before the narrative
- [ ] Export contract followed: canonical Markdown valid; the Markdown handoff pass view-appropriate parity (no lettered A–E, JSON blocks, or export manifest)

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
