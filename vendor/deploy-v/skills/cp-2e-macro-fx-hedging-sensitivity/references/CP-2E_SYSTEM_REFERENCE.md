<!-- CP-2E System Reference (T4) | 2026-06-03 -->

## Identity
module_id: CP-2E | module_name: MacroFXHedgingSensitivity | schema_family: Nested | layer: L2

## Dependencies
UP: CP-2 | DOWN (Analytical): CP-6 | DOWN (QA): CP-5, CP-5A

## Governance Rules
1. Gross floating-rate debt ≠ hedged floating-rate debt ≠ unhedged floating-rate debt. Always distinguish all three.
2. Hedge notional ≠ effective cash-flow protection. Do not treat notional as effective unless instrument, covered exposure, rate/strike, maturity, and coverage period are sufficiently disclosed.
3. FX exposure requires currency data — do not infer from geography alone.
4. Missing evidence = [Insufficient Information], never a positive or adverse conclusion.
5. Every material conclusion must complete: Evidence → Risk Mechanic → Credit Implication.

## Evidence Standard
- Every material factual claim, hedge statement, exposure register, sensitivity input, and macro conclusion must be source-traceable.
- Distinguish gross floating-rate debt, hedged floating-rate debt, and unhedged floating-rate debt.
- Distinguish hedge notional from economically effective cash-flow protection.

## Macro Risk Levels
Low | Moderate | High | Insufficient Information

## Rate Exposure Labels
Fixed-rate debt | Floating-rate debt | Base-rate exposure | Gross floating-rate debt | Hedged floating-rate debt | Unhedged floating-rate debt | Cash-interest sensitivity | Interest-rate floor | Margin | Coupon | Reference rate | Hedge cliff

## Hedge Type Labels
Interest-rate swap | Interest-rate cap | Collar | Fixed-rate debt | FX forward | FX option | Natural hedge | Commodity hedge | Fuel hedge | Energy hedge | Inflation-linked pass-through

## Hedge Coverage Status Labels
Effective where supported | Partial | Expired | Maturity mismatch | Notional disclosed only | Terms insufficient | Insufficient Information

## FX Exposure Labels
Revenue currency | Cost currency | EBITDA currency | Debt currency | Cash currency | Covenant currency | Translation exposure | Transaction exposure | Natural hedge | Covenant currency mismatch | Cash repatriation constraint

## Commodity / Inflation Labels
Raw-material exposure | Energy exposure | Freight exposure | Labour / wage inflation | Rent inflation | Procurement exposure | Pass-through mechanism | Indexation | Surcharge | Lagged recovery | Margin squeeze | Demand elasticity

## Core Formulas
- Gross floating-rate debt = debt instruments explicitly disclosed as floating rate
- Hedged floating-rate debt = floating-rate debt covered by disclosed hedge with sufficient terms
- Unhedged floating-rate debt = Gross floating-rate debt − Hedged floating-rate debt
- Unhedged debt percentage = Unhedged floating-rate debt / Total debt
- +100 bps cash-interest impact = Unhedged floating-rate debt × 1.00%

## Fail/Restrict
- **Blocked:** Module Status = Blocked when no debt schedule or fixed/floating split is identifiable from any source.
- **Restricted:** Module Status = Ready with Limitations when partial evidence available but critical dimensions (e.g., hedge terms, FX currency data, commodity costs) unsupported.
- **Sensitivity Not Calculable:** +100 bps sensitivity = [Insufficient Information] when unhedged floating-rate exposure is unsupported.
- **Risk Level Not Assignable:** Macro Risk Level = Insufficient Information when evidence does not support a decision-useful classification.

## Version: 2026-06-03
