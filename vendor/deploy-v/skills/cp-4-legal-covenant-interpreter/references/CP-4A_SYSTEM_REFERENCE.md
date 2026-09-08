<!-- CP-4A System Reference (T4) | 2026-06-03 -->

## Identity
module_id: CP-4A | module_name: CovenantCapacityCalculator | schema_family: Nested | layer: L4

## Dependencies
UP: CP-4, CP-1 | DOWN (Analytical): CP-6, CP-6A | DOWN (QA): CP-5, CP-5A

## Enrichment Consumers (Supplementary — Not Formal Dependencies)
CP-1/CP-1B, CP-2, CP-3, CP-3A, CP-3C may optionally consume CP-4A output on re-run for enrichment.

## Governance Rules
1. Every material capacity/headroom conclusion must complete: Evidence → Risk Mechanic → Credit Implication.
2. Use governing legal definitions for covenant tests — never substitute reported EBITDA for covenant EBITDA without bridge support.
3. Do not infer capacity without source support; do not assume basket capacity is unused without tracker/certificate support.
4. Double-counting discipline: do not add overlapping baskets unless legal document permits independent use.
5. Unavailable values = null in structured exports (not zero); [Insufficient Information] in narrative.

## Evidence Hierarchy
Executed Credit Agreement / Indenture (highest) > Compliance Certificates / Covenant Schedules > CP-1 Financial Foundation > Basket Usage Trackers > CP-4 Legal/Covenant Review Output > Offering Memorandum > Third-Party Reports > Lender Presentations / Term Sheets (lowest)

## Credit Implication Labels (8-value Legal/Covenant subset)
Positive — Covenant Headroom Expansion | Positive — Deleveraging | Neutral — Stable | Negative — Covenant Erosion | Negative — Leverage Increase | Negative — Refinancing Risk | Negative — Liquidity Deterioration | Insufficient Information

## Severity Labels (5)
Low | Moderate | High | Critical | Insufficient Information

## Data-Quality Confidence Labels (5)
High | Moderate | Low | Formula Only | Insufficient

## Capacity Status Labels (7)
Completed | Ready with Limitations | Formula Extracted Only | Provisional | Insufficient Information | Not Applicable | Blocked

## Capacity Type Taxonomy (13)
Maintenance covenant headroom | Incurrence covenant headroom | Debt incurrence capacity | Lien capacity | Restricted payment capacity | Investment capacity | Asset transfer capacity | Unrestricted subsidiary capacity | EBITDA add-back capacity | Builder / available amount capacity | Incremental facility capacity | MFN protection | Guarantor / collateral release capacity

## Formula Labels (10)
Fixed Basket | Grower Basket | Ratio Basket | Builder Basket | Available Amount | General Basket | Reclassification Feature | Free-and-Clear Amount | Incremental Ratio Amount | Prepayment / Reinvestment Capacity

## Content Distinction Labels
Source Fact | Legal Formula | Calculation | Interpretation | Credit Implication | Gap

## Nearest Pressure Point Selection Order
1. Maintenance covenant headroom (near-term breach)
2. Debt/lien capacity (priming/dilution)
3. RP/investment/USub (value leakage)
4. EBITDA add-back (ratio inflation)
5. Amendment/waiver (lender control)

## Downstream Handoff Map
| Destination | What CP-4A Passes |
|-------------|-------------------|
| CP-6 | Bear legal-control attack, nearest pressure point, lender-control weakness |
| CP-6A | Portfolio sizing constraint, legal downside risk, capacity-driven risk-budget |
| CP-3C | Incremental debt, MFN, maturity, refinancing, LME capacity |
| CP-3A | Collateral, guarantor, priority, recovery leakage |
| CP-3 | Debt/lien/leakage capacity for security selection and RV |
| CP-4 | New provision-level findings, discrepancies vs CP-4, source-authority updates |

## Fail/Restrict
- **Blocked:** No executed governing document AND no CP-4 output available. Module produces blocked statement only. Do not fabricate.
- **Restricted (Financial):** CP-1 unavailable → formulas extracted but headroom/capacity not calculable.
- **Restricted (Usage):** Basket usage tracker unavailable → remaining capacity undetermined; estimated capacity only.
- **Restricted (Definitions):** Covenant EBITDA bridge unavailable → ratio capacity unreliable.
- **Restricted (Pressure Point):** Evidence insufficient → nearest pressure point = [Insufficient Information].

## Version: 2026-06-03
