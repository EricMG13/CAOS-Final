<!-- CP-2F System Reference (T4) | PROPOSED | 2026-06-22 -->

## Identity
module_id: CP-2F | module_name: ESGSustainabilityCreditRisk | schema_family: Nested | layer: L2

## Dependencies
UP: CP-1, CP-1A, CP-2 | DOWN (Analytical): CP-6 | DOWN (QA): CP-5, CP-5A
NOTE: Governance/sponsor conduct is owned by CP-2C; CP-2F references CP-2C and does not duplicate it.

## Governance Rules
1. No ESG values judgement, ethics score, or non-credit ESG rating — credit transmission only.
2. Materiality-gated: default every factor to Immaterial to Credit unless issuer-specific transmission to cash flow / asset value / spread is shown.
3. Every material conclusion must complete: Evidence → Risk Mechanic → Credit Implication.
4. No fabrication of emissions data, transition costs, KPI/SPT terms, ratchet sizes, or regulations.
5. No materiality inference from sector reputation alone.
6. A green/sustainability label is not creditor protection unless the document grants enforceable protection.

## Owned Object
esg_credit_risk (environmental/social/transition exposure + sustainability-linked-debt mechanics)

## Materiality Classes (5)
Material — Quantified | Material — Directional | Watch | Immaterial to Credit | Insufficient Information

## Content Distinction Labels
ESG Source Fact | Sustainability-Linked Documentary Term | Materiality Judgement | Analyst Interpretation | Credit Implication | Immaterial-to-Credit Flag | Gap

## Sustainability-Linked Debt Fields
KPI | SPT + Test Date | Ratchet (direction, bps) | Step-up/down Symmetry | Miss Consequence | Reporting/Verification | Credit-Meaningful vs Cosmetic | Expected Spread Effect

## Gate Status Labels
Completed | Completed with Limitations | Not Applicable | Blocked

## Upstream Dependency Map
| Module | What CP-2F Needs | Impact if Missing |
|--------|-----------------|-------------------|
| CP-1 | Financials, asset base, maturity profile | Transition-cost and refinancing linkage limited |
| CP-1A | Business description, sector, operating model | Sector transition context limited |
| CP-2 | Fundamental synthesis | Credit-implication integration limited |

## Fail/Restrict
- **Not Applicable:** No credit-material ESG/transition exposure and no sustainability-linked debt — stated explicitly with brief basis (a valid, common outcome).
- **Blocked:** Assessment requested but zero source exists. Do not infer from sector reputation.
- **Restricted (Disclosure):** Partial disclosure → factors limited to [Directional] or [Watch].
- **Restricted (SLL):** Sustainability-linked terms missing → ratchet mechanics [Insufficient Information].

## Version: 2026-06-22 (proposed)
