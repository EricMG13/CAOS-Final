<!-- CP-2D System Reference (T4) | 2026-06-03 -->

## Identity
module_id: CP-2D | module_name: LiquidityCashFlowBridge | schema_family: Nested | layer: L2

## Dependencies
UP: CP-1, CP-2 | DOWN (Analytical): CP-3, CP-3C, CP-6 | DOWN (QA): CP-5, CP-5A

## Governance Rules
1. Reported cash ≠ accessible liquidity. Always distinguish cash, restricted cash, committed revolver, and accessible revolver after constraints.
2. Undrawn revolver ≠ accessible revolver. Do not assume availability unless explicitly disclosed with borrowing-base, covenant, and jurisdictional constraints addressed.
3. Months to Empty requires both beginning accessible liquidity and cash-burn basis to be source-supported; otherwise [Insufficient Information].
4. Missing evidence = [Insufficient Information], never a positive or adverse conclusion.
5. Every material conclusion must complete: Evidence → Risk Mechanic → Credit Implication.

## Evidence Standard
- Every material factual claim, calculation input, liquidity-access statement, cash-use estimate, and runway conclusion must be source-traceable.
- Distinguish reported cash from accessible liquidity.
- Distinguish committed available revolver from unavailable, restricted, borrowing-base-limited, covenant-constrained, or undocumented liquidity.

## Liquidity Risk Levels
Adequate | Tight | Weak | Insufficient Information

## Liquidity Data Status Labels
Reported | Calculated | Provisional | Management-guided | Analyst estimate | Insufficient Information | Not Available | Not Comparable | Conflict Logged | Blocked

## Liquidity Component Labels
Cash | Restricted cash | Revolver commitment | Revolver drawn | Undrawn revolver | Accessible revolver availability | Borrowing-base constrained availability | Covenant-constrained availability | Other committed liquidity | Asset-sale proceeds | Sponsor support | Equity cure | Working-capital release

## Cash-Use Category Labels
Cash interest | Cash taxes | Debt amortization | Maturity | Lease payment | Mandatory capex | Growth capex | Restructuring cost | Integration cost | Working-capital outflow | Dividend / distribution | Litigation / settlement | Pension contribution | Other mandatory cash use | Other discretionary cash use

## Monitoring Trigger Types
Cash below threshold | Revolver draw | Revolver availability decline | Working-capital outflow | Cash burn acceleration | Capex inflexibility | Maturity wall | Covenant access constraint | Borrowing-base deterioration | Sponsor support dependence | Asset-sale dependence | Refinancing failure | Reporting gap

## Core Formulas
- Beginning accessible liquidity = Cash + Accessible revolver + Other committed accessible liquidity
- Ending accessible liquidity = Beginning accessible liquidity + operating cash inflow/outflow + WC impact − cash interest − cash taxes − mandatory capex − debt amortization/maturities − other cash uses + committed inflows
- Months to Empty = Beginning accessible liquidity / average monthly cash burn

## Fail/Restrict
- **Blocked:** Module Status = Blocked when no cash position or cash-flow data is identifiable from any source.
- **Restricted:** Module Status = Ready with Limitations when partial evidence available but critical liquidity dimensions (e.g., revolver, debt schedule, WC) unsupported.
- **MTE Not Calculable:** Months to Empty = [Insufficient Information] when either beginning accessible liquidity or cash-burn basis is unsupported.
- **Risk Level Not Assignable:** Liquidity Risk Level = Insufficient Information when evidence does not support a decision-useful classification.

## Version: 2026-06-03
