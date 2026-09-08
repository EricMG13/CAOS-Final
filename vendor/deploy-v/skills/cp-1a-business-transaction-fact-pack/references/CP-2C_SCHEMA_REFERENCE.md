<!-- CP-2C Schema Reference (T3) | 2026-06-03 -->

## Required Tables (11)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T2D.1 | Source Register | source_document_id, source_document_name, source_quality, period, entity_covered, data_supplied, limitation, downstream_use |
| T2D.2 | Ownership & Control Register | Item, Source-Supported Fact, Evidence Quality, Source Trace, Credit Mechanic, Credit Implication, Limitation |
| T2D.3 | Governance Register | Governance Topic, Source-Supported Fact, Risk Direction, Risk Mechanic, Credit Implication, Evidence Quality, Source Trace, Limitation |
| T2D.4 | Behavior Flag Register | Flag ID, Behavior Type, Documented Action, Behavior Category, Amount / Funding Source, Legal-Capacity Link, Risk Mechanic, Credit Implication, Evidence Quality, Source Trace, Limitation |
| T2D.5 | Capital Allocation Risk Table | Capital Allocation Item, Source-Supported Fact, Direction, Risk Mechanic, Credit Implication, Evidence Quality, Source Trace, Limitation |
| T2D.6 | Acquisition Appetite Table | Acquisition / Period, Source-Supported Fact, Funding Mix, EBITDA / Pro Forma Basis, Integration Evidence, Leverage / Liquidity Effect, Risk Mechanic, Credit Implication, Source Trace, Limitation |
| T2D.7 | Disclosure Quality Log | Disclosure Item, Available?, Source-Supported Detail, Credit Relevance, Severity, Source Trace, Required Follow-Up |
| T2D.8 | Creditor Alignment & Financial Policy Table | Dimension, Assessment, Evidence, Risk Mechanic, Credit Implication, Score, Evidence Quality, Source Trace, Limitation |
| T2D.9 | Sponsor Risk Assessment Table | Risk-Level Driver, Evidence, Risk Mechanic, Credit Implication, Evidence Quality, Source Trace, Countervailing Evidence, Limitation |
| T2D.10 | Cross-Module Handoff Register | Downstream Module, Handoff Tag, Handoff Item, Why It Matters, Required Consumer Action, Source / Flag Link, Limitation |
| T2D.11 | Gaps Ledger | Gap ID, Missing Data, Why It Matters, Affected Section / Flag / Export Record, Consequence for Confidence, Required Follow-Up Source |

## QA Checklist
- [ ] Module Status assigned (Full Run / Ready with Limitations / Blocked)
- [ ] Every material factual claim is source-traceable
- [ ] Sponsor identity alone is not treated as behavior
- [ ] Sponsor reputation alone is not treated as evidence
- [ ] Missing evidence marked [Insufficient Information] — not converted to adverse conclusion
- [ ] Source conflicts logged (not reconciled silently)
- [ ] Content distinctions maintained: Source Fact | Characterization | Behavior Evidence | Financial Policy | Legal-Capacity Link | Interpretation | Credit Implication | Gap
- [ ] Legal capacity separated from willingness evidence
- [ ] Historical behavior separated from current capacity
- [ ] Support behavior separated from extraction behavior
- [ ] No individual employee evaluation, ranking, or personal-attribute claims
- [ ] Prohibited phrasing absent (management good/bad, aggressive sponsor, creditor-friendly, best-in-class, weak/strong management)
- [ ] All behavior flags use Taxonomy categories (A–E) with evidence support
- [ ] Evidence Quality labels applied per gate (High / Medium / Low / Insufficient)
- [ ] Required Gate Tests passed before Risk Level assignment (Step 9)
- [ ] Composite score requires ≥4 dimensions; else Not Scorable
- [ ] External claims labelled [External]
- [ ] Canonical `## Evidence Trace` and every requested export preserve source_trace, claim_id, evidence_id, lineage_class, deterministic_entity_key
- [ ] null used (not zero) for unavailable numeric values unless source explicitly states zero
- [ ] Handoff tags match predefined set (CP-2C-HANDOFF-CP-*)
- [ ] Gaps Ledger is cumulative across all steps
- [ ] Overall Governance View introduces no new data
- [ ] Module completion statement includes Risk Level

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
