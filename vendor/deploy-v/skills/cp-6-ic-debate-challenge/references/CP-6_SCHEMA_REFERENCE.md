<!-- CP-6 Schema Reference (T3) | 2026-06-03 -->

## Required Output Sections (11)
All 11 sections must be present using exact required headings.

## Required Tables (4)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T6A.4 | Bear Cross-Examination | Bull Claim Attacked, Bear Counter-Evidence, Fragility Vector, Legal / Covenant Exploit, Risk Mechanic, Credit Implication, What Would Prove Bear Wrong |
| T6A.6 | Chair Evidence Weighting | Dimension, Score (1-5), Bull Evidence, Bear Evidence, Chair Assessment |
| T6A.7 | Debate Resolution Matrix | Disputed Risk, Bull Position, Bear Position, Resolution, Evidence Basis, Credit Implication |
| T6A.11 | Gaps Ledger | Gap ID, Gap, Why It Matters, Impact on Debate, Required Follow-Up |

## Structured Sections (7)
| Step | Section | Format |
|------|---------|--------|
| 1 | IC Debate Source Gate | Gate status (Full Run / Ready with Limitations / Blocked) + source register |
| 2 | Pre-Debate Thesis Map | Narrative: 10-dimension evidence map + central investment controversy |
| 3 | Bull Analyst Opening Statement | 3 structured claims: Evidence, Risk Mechanic, Credit Implication, Monitoring Signal |
| 5 | Bull Analyst Defense | Structured rebuttals per attack: rebuttal evidence, mitigation logic, Rebuttal Status |
| 8 | Action Bias Determination | Required formulation: "Final Action Bias: [Bias]. The decision is driven by [evidence], because [mechanic], which implies [implication]. The main factor preventing a higher-conviction recommendation is [constraint]." |
| 9 | Single Greatest Uncertainty | Structured: uncertainty, why it matters, evidence needed, positive/negative resolution impact |
| 10 | IC Chair Final Memo | Narrative: Decision, winner, Bull/Bear evidence, legal/recovery, liquidity/refi, RV/portfolio, follow-up |

## QA Checklist
- [ ] All 11 output sections present using exact required headings
- [ ] Exactly 3 Bull claims in Step 3 (Claim 1 = cash-flow/revenue, Claim 2 = structural/liquidity/recovery/covenant, Claim 3 = catalyst/RV/refi/portfolio)
- [ ] Bear attacks exactly the 3 Bull claims (no more, no fewer)
- [ ] Bull defense responds to each Bear attack (no new claims)
- [ ] All 9 Chair scoring dimensions addressed (scored or [Insufficient Information])
- [ ] Chair scoring uses 1-5 scale only; no average unless all dimensions scored
- [ ] All resolution labels from permitted set (Bull Sustained / Bear Sustained / Partially Mitigated / Unresolved / Insufficient Information)
- [ ] Final Action Bias from permitted 8-value set only
- [ ] Action Bias uses required formulation exactly
- [ ] Action Bias consistent with Final Bias Guardrails
- [ ] Chair Decision Rules applied (blocking rules for missing modules)
- [ ] Zero-Bound Chain attempted by Bear (complete or state missing link)
- [ ] Legal-Control Test attempted by Bear (evidence-based or [Insufficient Information])
- [ ] Single Greatest Uncertainty = exactly ONE uncertainty (not a list)
- [ ] All Credit Implications from 13-value Canonical set
- [ ] All Evidence Quality from 4-value label set (Strong / Moderate / Weak / Insufficient)
- [ ] IC Chair Final Memo covers all 8 required elements
- [ ] Gaps Ledger has sequential IDs (CP-6-GAP-NNN)
- [ ] Canonical Markdown valid; every the Markdown handoff passes view-appropriate parity
- [ ] Audit Summary + numeric Confidence Score (0–100) + band precede the analysis narrative; single Audit Appendix holds all audit items
- [ ] canonical Markdown front-matter carries confidence_score + confidence_band (per CP_CONFIDENCE_SCORE.md) and canonical H2 headings
- [ ] No balanced narrative — output forces a decision

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
