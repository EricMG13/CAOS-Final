<!-- CP-4A Schema Reference (T3) | 2026-06-03 -->

## Required Output Sections (13)
All 13 sections must be present. If source materials do not support analysis, the section must still appear with [Insufficient Information] and a gap ledger entry.

## Required Tables (10)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T4C.2 | Controlling Capacity Source Map | Authority Rank, Source, Source Type, Version / Date, Status, Controls Legal Formula / Financial Input / Usage, Credit Relevance, Evidence ID |
| T4C.3 | Covenant Definition and Ratio Mechanics Register | Definition / Ratio, Source / Clause, Formula / Definition Summary, Required Inputs, Capacity Effect, Risk Mechanic, Credit Implication, Evidence ID |
| T4C.4 | Headroom Table | Test, Test Type, Threshold, Current Basis, Formula, Headroom, Status, Limitation, Risk Mechanic, Credit Implication, Evidence ID |
| T4C.5 | Capacity Register | Capacity Type, Basket / Test, Formula, Conditions, Current Input, Usage, Estimated Capacity, Remaining Capacity, Status, Severity, Risk Mechanic, Credit Implication, Evidence ID |
| T4C.6 | Debt, Lien, and Priming Capacity Analysis | Route, Supported Legal Capacity, Current Calculation Status, Priming / Dilution Mechanic, PD Effect, LGD / Recovery Effect, RV / Security Selection Effect, Evidence ID |
| T4C.7 | RP, Investment, Asset Transfer, and Leakage Analysis | Leakage Route, Supported Fact, Formula / Basket, Usage / Remaining Capacity, Restricted-Group / Collateral Impact, Severity, Credit Implication, Evidence ID |
| T4C.8 | EBITDA Add-Back and Capacity Inflation Analysis | Add-Back / Definition Feature, Source / Clause, Cap / Condition, Calculation Status, Capacity Inflation Mechanic, PD / LGD / RV Implication, Evidence ID |
| T4C.9 | Leakage and Basket Flags | Flag, Supported Fact, Creditor Risk, Severity, Confidence, Downstream Module, Evidence ID |
| T4C.11 | Capacity Risk Prioritization Matrix | Priority, Capacity Item, Severity, Confidence, Primary Risk Mechanic, PD Effect, LGD / Recovery Effect, Monitoring Action, Evidence ID |
| T4C.12 | Gaps Ledger | Gap, Missing Data, Why It Matters, Impact on Output, Required Follow-Up |

## Narrative Sections (3)
| Step | Section | Format |
|------|---------|--------|
| 1 | Capacity Source Gate | Gate status + input inventory |
| 10 | Nearest Pressure Point | Single pressure point with 6 required fields |
| 13 | Overall Covenant Capacity View | Required formulation + 3–5 supported bullets + completion statement |

## QA Checklist
- [ ] All 13 output sections present and populated (or marked [Insufficient Information] with gap logged)
- [ ] Every capacity calculation includes: formula, numerator, denominator, source inputs, result, period, status, limitation, source trace
- [ ] All severity labels use 5-value framework (Low / Moderate / High / Critical / Insufficient Information)
- [ ] All confidence labels use 5-value framework (High / Moderate / Low / Formula Only / Insufficient)
- [ ] All status labels use 7-value set (Completed / Ready with Limitations / Formula Extracted Only / Provisional / Insufficient Information / Not Applicable / Blocked)
- [ ] Every credit implication uses one of the 8 canonical CP-4A values
- [ ] Content distinctions maintained: Source Fact | Legal Formula | Calculation | Interpretation | Credit Implication | Gap
- [ ] Double-counting discipline applied: no overlapping baskets summed without legal support
- [ ] Null-handling applied: null for unavailable numerics (not zero), [Insufficient Information] in narrative
- [ ] Conflict handling applied: CP-1 vs CP-4 definition conflicts logged, legal definition governs
- [ ] Nearest Pressure Point identifies exactly one item with 6 required fields (or [Insufficient Information])
- [ ] All gaps logged in Gaps Ledger with affected downstream modules
- [ ] Numeric Confidence Score (0–100) computed per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md` and shown with its band in the Audit Summary
- [ ] Canonical Markdown valid; every the Markdown handoff passes view-appropriate parity and uses the matching filename
- [ ] No fabricated capacity, baskets, thresholds, or usage
- [ ] Unsupported superlatives not used without provision-level basis

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
