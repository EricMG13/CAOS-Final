<!-- CP-1 System Reference (Tier 4) | 2026-06-02 -->
<system_reference module="CP-1" tier="4">
## Identity
| Field | Value |
|-------|-------|
| module_id | CP-1 |
| module_name | CanonicalDataFoundation |
| owned_object | canonical_financial_data_kpis |
| schema_family | Nested |
| layer | L1 |
| governed_by | CP_GLOBAL_AGENT_INSTRUCTIONS_v3.2.txt |

## Dependencies
UP: CP-0, CP-X | DOWN (Analytical): CP-1B,CP-1C,CP-2,CP-2A,CP-2D,CP-3,CP-3C,CP-4,CP-4A,CP-6,CP-MODEL | DOWN (QA): CP-5,CP-5A

## CP-MODEL interface
Stable tables and controlled identifiers are binding per
`REF_CP-1_13_ModelWorkbookInterface.md`. CP-1 owns every numeric value;
CP-MODEL only maps and calculates. CP-1 also owns the optional
`cp1.operating_kpi_schedule` and, when CP-2G forecasts source segments, the
stable `cp1.cp_model_segment_allocation`. Allocation rows bind source segments
to active `DIVISION_1..3` drivers without changing the separately rendered
segment schedule. CP-MODEL consumes the canonical handoffs to create its
workbook export; it never treats segment order as a forecast mapping.

## 28 Canonical Metrics
| # | Metric | Type | # | Metric | Type |
|---|--------|------|---|--------|------|
| 1 | Revenue | Input | 15 | Net Debt | Calc |
| 2 | Gross Profit | Input | 16 | Liquidity | Calc |
| 3 | Gross Margin | Calc | 17 | Debt/EBITDA | Ratio |
| 4 | EBITDA | Calc | 18 | Net Debt/EBITDA | Ratio |
| 5 | Adj EBITDA | Calc | 19 | FFO/Debt | Ratio |
| 6 | Cash Interest | Input | 20 | FFO Int Cov | Ratio |
| 7 | Cash Tax | Input | 21 | EBITDA Int Cov | Ratio |
| 8 | Other Op Cash | Input | 22 | CFO/Debt | Ratio |
| 9 | Working Capital | Input | 23 | FCF/Debt | Ratio |
| 10 | CFO/OCF | Calc | 24 | DCF/Debt | Ratio |
| 11 | FFO | Calc | 25 | Rev Growth | Calc |
| 12 | FCF | Calc | 26 | EBITDA Margin | Calc |
| 13 | DCF | Calc | 27 | Capex/Rev | Ratio |
| 14 | Debt | Input | 28 | Cash Conversion | Calc |

## Metric Governance
1. Every calc: formula + num + den + period + source trace + normalization notes
2. Downstream inherits CP-1 defs unless explicit override logged
3. CP-prefix only (no M-prefix)

## Evidence Hierarchy
Audited FS > Unaudited w/auditor > Unaudited > Lender/Sponsor > Rating > Internal > External

## Extended Anti-Pattern: Definition Conflict
BAD: "Net Debt/EBITDA was 4.2x based on lender presentation." → LP uses adjusted EBITDA. Canonical = 5.1x. Not disclosed.
GOOD: "Net Debt/EBITDA: 5.1x (reported, Source: AR p.45) vs. 4.2x (adjusted, Source: LP p.12). EUR 25m add-backs. Logged in T4.11."

## Fail/Restrict
Unsupported claim | Missing trace | Undocumented calc | Unresolved conflict | Malformed schema | QA-blocked upstream | Filename-only | Currency switch | Def change w/o log

## Version: 2026-06-02 | conversion + naming (REF_CP-1_NN_Name.md)
</system_reference>
