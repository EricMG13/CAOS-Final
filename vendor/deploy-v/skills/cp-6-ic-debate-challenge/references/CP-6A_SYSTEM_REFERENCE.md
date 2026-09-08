<!-- CP-6A System Reference (T4) | 2026-06-03 -->

## Identity
module_id: CP-6A | module_name: PortfolioDebateChallenge | schema_family: Nested | layer: L6

## Dependencies
UP: CP-0, CP-1, CP-1B, CP-1C, CP-2, CP-2A, CP-2B, CP-2C, CP-2D, CP-2E, CP-3, CP-3A, CP-3B, CP-3C, CP-4, CP-4A, CP-6 | DOWN (Analytical): (terminal L6 module) | DOWN (QA): CP-5, CP-5A

## Governance Rules
1. CP-6A is the terminal portfolio debate module — output must force a definitive sizing and posture decision, not produce balanced narrative.
2. Three personas (RV Trader, Compliance Officer, CIO) must be maintained throughout; no persona may argue outside its defined scope.
3. Final Sizing Posture must use one of 6 permitted Portfolio Posture values with canonical translation to 9-value taxonomy.
4. Exact Portfolio Constraint must identify one binding constraint from the 12-type priority taxonomy; secondary issues go to residual risks in CIO memo.
5. Missing upstream modules trigger specific limitation rules (see CIO Decision Rules) — limitations carried forward, not silently resolved.

## Evidence Hierarchy (7 levels, highest → lowest)
1. Current market data (spreads, yields, prices, DM) from dated, sourced pricing runs or broker sheets
2. CP-3 / CP-3A / CP-3B RV and portfolio-fit outputs citing underlying data
3. CP-2A / CP-2D / CP-2E downside, liquidity, and macro outputs
4. CP-4 / CP-4A legal / covenant outputs
5. CP-6 IC debate output with action bias
6. Portfolio constraints, mandate documents, risk dashboards, exposure reports
7. Analyst interpretation based on sourced facts

## Evidence Quality Labels (4)
Strong | Moderate | Weak | Insufficient

## Portfolio Posture Values (6)
Include | Avoid | Resize-Reduce | Resize-Increase | Maintain-Hold | Requires More Work

## Translation to Canonical 9
Include → Starter Position, Core Hold, Add / Increase | Avoid → Avoid, Exit | Resize-Reduce → Reduce / Trim | Resize-Increase → Add / Increase | Maintain-Hold → Hold Existing Only, Core Hold | Requires More Work → Requires More Work

## Canonical Credit Implication Values (13)
Positive — Deleveraging | Positive — Margin Expansion | Positive — Revenue Growth | Positive — Liquidity Improvement | Positive — Covenant Headroom Expansion | Neutral — Stable | Negative — Leverage Increase | Negative — Margin Compression | Negative — Revenue Decline | Negative — Liquidity Deterioration | Negative — Covenant Erosion | Negative — Refinancing Risk | Insufficient Information

## Allocation Decision Resolution Labels (5)
RV Sustained | Compliance Sustained | Partially Mitigated | Unresolved | Insufficient Information

## Rebuttal Status Values (4)
Fully Rebutted | Partially Rebutted | Failed | Insufficient Information

## Module Status Values (3)
Full Run | Ready with Limitations | Blocked

## CIO Scoring Scale
1 = RV clearly superior | 2 = RV somewhat stronger | 3 = Balanced/unresolved | 4 = Compliance somewhat stronger | 5 = Compliance clearly superior

## CIO Scoring Dimensions (9)
Spread/YTW Benefit | Peer Relative Value | Downside Pathway Severity | Liquidity/Refinancing Risk | Legal/Recovery Protection | CCC-Basket/Downgrade Risk | Concentration/Correlation Risk | Mandate Compliance | Implementation Liquidity

## 9-Item Constraint Taxonomy
Mandate | Concentration | Rating | Geography | Liquidity | Correlation | Downside | Legal / Recovery | Data quality

## Debate Winner Values (3)
RV Trader wins | Compliance Officer wins | Neither wins

## Fail/Restrict
- **Blocked:** CP-3 unavailable → Module Status = Blocked, STOP.
- **Ready with Limitations (CP-3B missing):** Mandate fit and sizing cannot be fully tested.
- **Ready with Limitations (CP-2A missing):** Downside path cannot be fully tested.
- **Ready with Limitations (market pricing missing):** RV conclusions = [Insufficient Information].
- **Ready with Limitations (mandate/constraints missing):** Exact constraint = [Insufficient Information].
- **Ready with Limitations (ratings missing):** CCC-basket/downgrade arguments = [Insufficient Information].
- **Posture ceiling (constraint breach):** Compliance proves binding breach + RV cannot show headroom → cannot Include.
- **Posture ceiling (legal leakage):** RV proves spread + downside + headroom but legal unresolved → Include (Starter Position) with constraint.
- **Weak evidence:** Both sides weak → Requires More Work.

## Version: 2026-06-03
