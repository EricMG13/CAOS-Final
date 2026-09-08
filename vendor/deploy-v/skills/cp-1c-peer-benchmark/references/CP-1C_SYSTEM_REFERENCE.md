<!-- CP-1C System Reference (T4) | 2026-06-02 -->
## Identity
module_id: CP-1C | module_name: PeerBenchmark | schema_family: Nested | layer: L1

## Dependencies
UP: CP-1 | DOWN (Analytical): CP-2, CP-3 | DOWN (QA): CP-5, CP-5A

## 15 Core Formulas
1. Gross Margin = Gross Profit / Revenue  2. EBITDA Margin = EBITDA / Revenue  3. EBIT Margin = EBIT / Revenue
4. Net Income Margin = Net Income / Revenue  5. Revenue Growth = (Curr-Prior)/Prior Revenue  6. EBITDA Growth
7. Total Leverage = Total Debt / EBITDA  8. Net Leverage = Net Debt / EBITDA  9. Sr Sec Leverage
10. Interest Coverage = EBITDA / Cash Interest  11. Adj Int Cov = (EBITDA-Capex)/Cash Interest  12. FFO/Total Debt
13. FCF Conversion = FCF / EBITDA  14. Capex / Revenue  15. Liquidity = Cash + Undrawn Facilities

## Metric Governance
ALL borrower definitions from CP-1. Peer metrics aligned to CP-1 or flagged. 11-point alignment standard applied. Comparability status before statistics. Peer Statistic Rules (min N).

## Evidence Hierarchy (10 tiers)
Audited FS > Unaudited w/auditor > Unaudited > Lender/Sponsor > Rating > Public Filing > Internal > Web-Scraped Corroborated > Web-Scraped Unverified > Analyst Inference

## Valuation Discipline (13 points)
All multiples sourced with date | Same metric def or flagged | Stale labelled | Market-cap date stated | No averaging non-comparable | No implied EV as recovery | Currency consistent | Min 3 for sector multiples | Contemporaneous transaction data | No blending trading/transaction w/o flag | Web-scraped cross-checked | Provisional if not | All assumptions stated

## Numeric Hygiene
Percentages: X.X% | Multiples: N.Nx | Currency codes in table headers | CP-1 rounding | Null input → null result

## Fail/Restrict
Unsupported claim | Missing trace | Web-scraped as analyst-confirmed | Evidence tag suppressed | Null→zero | Statistics from non-comparable | Implied EV as recovery estimate | Malformed schema

## Version: 2026-06-02
