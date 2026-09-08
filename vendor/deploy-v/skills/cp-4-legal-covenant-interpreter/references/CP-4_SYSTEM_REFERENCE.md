<!-- CP-4 System Reference (T4) | 2026-06-03 -->

## Identity
module_id: CP-4 | module_name: LegalCovenantInterpreter | schema_family: Nested | layer: L4

## Dependencies
UP: CP-1, CP-1A, CP-3C | DOWN (Analytical): CP-4A, CP-6 | DOWN (QA): CP-5, CP-5A

## Governance Rules
1. Every material legal/covenant conclusion must complete: Evidence → Risk Mechanic → Credit Implication.
2. Source authority hierarchy is absolute: executed legal documents (Rank 1) outrank all other sources; conflicts resolved by rank.
3. Do not fabricate covenant terms, baskets, thresholds, or legal conclusions — if evidence unavailable, mark [Insufficient Information].
4. Covenant aggressiveness score is not a simple average — weight toward highest creditor-adverse severity; requires ≥3 scorable areas.
5. Do not provide legal advice. Do not assign a formal credit rating.

## Evidence Hierarchy
Executed Credit Agreement / Indenture (Rank 1) > Executed Intercreditor Agreement (Rank 2) > Compliance Certificates / Covenant Schedules (Rank 3) > Offering Memorandum (Rank 4) > Third-Party Covenant-Review Report (Rank 5) > Lender Presentation / Term Sheet / Posting Memorandum (Rank 6)

## Credit Implication Labels (8-value Legal/Covenant subset)
Positive — Covenant Headroom Expansion | Positive — Deleveraging | Neutral — Stable | Negative — Covenant Erosion | Negative — Leverage Increase | Negative — Refinancing Risk | Negative — Liquidity Deterioration | Insufficient Information

## Covenant Aggressiveness Score Labels
1 (Lender-Friendly) | 2 (Disciplined) | 3 (Market-Standard) | 4 (Aggressive) | 5 (Highly Creditor-Adverse)

## Scoring Confidence Labels
Completed | Provisional | Not Scorable

## Evidence Confidence Labels
High | Medium | Low | Provisional | Not Scorable

## Content Distinction Labels
Documentary Fact | Analyst Interpretation | Market Comparison | PD Effect | LGD / Recovery Effect | Monitoring Implication

## Gate Status Labels
Completed | Completed with Limitations | Blocked

## Aggressiveness Scoring Areas (7)
Maintenance covenant architecture | Debt / lien incurrence capacity | RP / investment / leakage capacity | EBITDA definitions and add-back flexibility | Collateral / guarantor protection | Amendment / control mechanics | Overall

## Standard Finding Format Fields
Provision | Source | Summary | Risk Mechanic | PD Effect | LGD / Recovery Effect | Monitoring Implication | Credit Implication | Confidence | Evidence ID

## Upstream Dependency Map
| Module | What CP-4 Needs | Impact if Missing |
|--------|----------------|-------------------|
| CP-1 | Financial definitions, EBITDA, debt, cash, ratios | Headroom and capacity calculations limited |
| CP-1A | Transaction summary, facility structure, maturity profile | Transaction context limited |
| CP-3C | Refinancing pressure, maturity wall, LME path assessment | LME legal-capacity overlay incomplete |

## Fail/Restrict
- **Blocked:** No executed credit agreement or indenture available. Module produces blocked statement only. Do not fabricate.
- **Restricted (Financial):** CP-1 unavailable → formulas extracted but headroom/capacity not calculable.
- **Restricted (LME):** CP-3C unavailable → LME legal-capacity overlay incomplete.
- **Restricted (Market Norm):** No comparative source → market-norm commentary skipped (Step 10 conditional).
- **Restricted (Score):** Fewer than 3 areas scorable → overall aggressiveness = [Not Scorable] or [Provisional].

## Version: 2026-06-03
