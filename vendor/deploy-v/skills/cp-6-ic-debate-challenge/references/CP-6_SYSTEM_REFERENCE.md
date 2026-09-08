<!-- CP-6 System Reference (T4) | 2026-06-03 -->

## Identity
module_id: CP-6 | module_name: ICDebateChallenge | schema_family: Nested | layer: L6

## Dependencies
UP: CP-1, CP-1A, CP-1B, CP-1C, CP-2, CP-2A, CP-2B, CP-2C, CP-2D, CP-2E, CP-3, CP-3A, CP-3B, CP-3C, CP-4, CP-4A | DOWN (Analytical): CP-6A | DOWN (QA): CP-5, CP-5A

## Governance Rules
1. CP-6 is an adversarial debate module — output must force a decision-useful action bias, not produce balanced narrative.
2. Three personas (Bull, Bear, Chair) must be maintained throughout; no persona may argue outside its defined scope.
3. Bear must attempt Zero-Bound Chain and Legal-Control Test with evidence; if chain incomplete, Bear case is incomplete.
4. Chair must apply Final Bias Guardrails and Chair Decision Rules — bias selection must be evidence-pattern-consistent.
5. Missing upstream modules trigger specific limitation rules (see Chair Decision Rules) — limitations carried forward, not silently resolved.

## Evidence Hierarchy (5 levels, highest → lowest)
1. Audited financials, executed legal documents, current market levels, current portfolio/mandate data
2. Company-reported financials, management reporting, covenant certificates, lender presentations, offering memoranda
3. Prior module outputs that cite underlying documents
4. Third-party reports, rating-agency reports, covenant-review reports, broker/trading runs
5. Analyst interpretation based on sourced facts

## Evidence Quality Labels (4)
Strong | Moderate | Weak | Insufficient

## IC Action Bias Values (8)
Avoid | Watchlist | Starter Position | Core Hold | Add / Increase | Reduce / Trim | Exit | Requires More Work

## Canonical Credit Implication Values (13)
Positive — Deleveraging | Positive — Margin Expansion | Positive — Revenue Growth | Positive — Liquidity Improvement | Positive — Covenant Headroom Expansion | Neutral — Stable | Negative — Leverage Increase | Negative — Margin Compression | Negative — Revenue Decline | Negative — Liquidity Deterioration | Negative — Covenant Erosion | Negative — Refinancing Risk | Insufficient Information

## Debate Resolution Labels (5)
Bull Sustained | Bear Sustained | Partially Mitigated | Unresolved | Insufficient Information

## Rebuttal Status Values (4)
Fully Rebutted | Partially Rebutted | Failed | Insufficient Information

## Module Status Values (3)
Full Run | Ready with Limitations | Blocked

## Chair Scoring Scale
1 = Bull clearly superior | 2 = Bull somewhat stronger | 3 = Balanced/unresolved | 4 = Bear somewhat stronger | 5 = Bear clearly superior

## Chair Scoring Dimensions (9)
Cash-flow durability | Downside pathway severity | Liquidity runway | Refinancing/maturity risk | Legal/covenant control | Recovery/LGD protection | Sponsor/governance alignment | Relative value compensation | Portfolio fit/sizing

## Debate Winner Values (3)
Bull wins | Bear wins | Neither wins

## Fail/Restrict
- **Blocked:** CP-1 AND CP-2 both unavailable → Module Status = Blocked, STOP.
- **Ready with Limitations (CP-2A missing):** Bear cannot fully map Zero-Bound downside.
- **Ready with Limitations (CP-4 missing):** Lender control, leakage, recovery mechanics cannot be fully tested.
- **Ready with Limitations (CP-3/market data missing):** RV conclusions = [Insufficient Information].
- **Ready with Limitations (CP-2D missing):** Quantified liquidity runway = [Insufficient Information] unless CP-1/CP-1B supports.
- **Ready with Limitations (CP-4A missing):** Basket/covenant-capacity headroom must not be inferred.
- **Bias ceiling (Zero-Bound):** If Bear proves credible Zero-Bound path and Bull cannot quantify liquidity protection → bias ≤ Watchlist.
- **Bias ceiling (legal leakage):** If Bull proves fundamentals but legal leakage unresolved → default bias = Starter Position.
- **Weak evidence:** Both sides weak → Requires More Work.

## Version: 2026-06-03
