<!-- CP-6A Schema Reference (T3) | 2026-06-03 -->

## Required Output Sections (11)
All 11 sections must be present using exact required headings.

## Required Tables (4)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T6E.4 | Compliance Cross-Examination | RV Bullet Attacked, Compliance Counter-Evidence, Constraint Vector, Risk Mechanic, Credit Implication, What Would Prove Compliance Wrong |
| T6E.6 | CIO Evidence Weighting | Dimension, Score (1-5), RV Evidence, Compliance Evidence, CIO Assessment |
| T6E.7 | Allocation Decision Matrix | Disputed Risk, RV Position, Compliance Position, Resolution, Evidence Basis, Credit / Portfolio Implication |
| T6E.11 | Gaps Ledger | Gap ID, Gap, Why It Matters, Impact on Debate, Required Follow-Up |

## Structured Sections (7)
| Step | Section | Format |
|------|---------|--------|
| 1 | Portfolio Debate Source Gate | Gate status (Full Run / Ready with Limitations / Blocked) + source register |
| 2 | Pre-Debate Portfolio Thesis Map | Narrative: evidence map + central portfolio controversy |
| 3 | The RV Trader's Pitch | 3 structured bullets: Evidence, Risk Mechanic, Credit Implication, Monitoring Signal |
| 5 | The RV Trader's Defense | Structured rebuttals per attack: rebuttal evidence, mitigation logic, Rebuttal Status + proposed sizing constraint |
| 8 | Final Sizing Posture | Required formulation: "Final Sizing Posture: [Posture]. The decision is driven by [evidence], because [mechanic], which implies [implication]." + canonical translation |
| 9 | Exact Portfolio Constraint | Structured: constraint category, evidence, risk mechanic, credit/portfolio implication, evidence needed |
| 10 | CIO Final Memo | Narrative: Decision, winner, RV/Compliance evidence, legal/recovery, liquidity/refi, RV/portfolio, sizing constraint, follow-up |

## QA Checklist
- [ ] All 11 output sections present using exact required headings
- [ ] Exactly 3 RV bullets in Step 3 (Bullet 1 = spread/YTW/DM, Bullet 2 = instrument mispricing, Bullet 3 = portfolio implementation)
- [ ] Compliance attacks exactly the 3 RV bullets (no more, no fewer)
- [ ] RV defense responds to each Compliance attack (no new arguments)
- [ ] All 9 CIO scoring dimensions addressed (scored or [Insufficient Information])
- [ ] CIO scoring uses 1-5 scale only; no average unless all dimensions scored
- [ ] All resolution labels from permitted set (RV Sustained / Compliance Sustained / Partially Mitigated / Unresolved / Insufficient Information)
- [ ] Final Sizing Posture from permitted 6-value set only
- [ ] Posture uses required formulation exactly
- [ ] Posture consistent with Posture Guardrails
- [ ] CIO Decision Rules applied (blocking rules for missing modules)
- [ ] Exact Portfolio Constraint = exactly ONE binding constraint (from 12-type taxonomy) or [Insufficient Information]
- [ ] Constraint not derived from generic credit risk unless mapped to explicit limit/bucket
- [ ] All Credit Implications from 13-value Canonical set
- [ ] All Evidence Quality from 4-value label set (Strong / Moderate / Weak / Insufficient)
- [ ] CIO Final Memo covers all 9 required elements
- [ ] Gaps Ledger has sequential IDs (CP-6A-GAP-NNN)
- [ ] Numeric Confidence Score (0–100) + derived band present in Audit Summary, before the narrative (per CP_CONFIDENCE_SCORE.md)
- [ ] Canonical Markdown valid; every the Markdown handoff passes view-appropriate parity (per CP_AB_EXPORT_SPEC.md)
- [ ] No balanced narrative — output forces a sizing decision
- [ ] Canonical translation included with Final Sizing Posture

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
