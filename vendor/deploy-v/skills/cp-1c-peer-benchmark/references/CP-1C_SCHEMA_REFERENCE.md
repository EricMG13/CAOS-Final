<!-- CP-1C Schema Reference (T3) | 2026-06-02 -->
## Required Tables (11)
| ID | Table | Key Columns |
|----|-------|-------------|
| T4.1 | Peer Universe Register | Entity Name, Peer Category Label, Source of Selection, Dimensions Assessed, Strengths, Limitations, Data Availability, Evidence Quality Tier, Usable For, Exclusion Reason |
| T4.2 | Metric Alignment Register | Metric, Borrower Value/Period, Peer Entity/Value/Period, AP1-AP11, Comparability Status, Limitation Notes |
| T4.3 | Operating Benchmark | Entity, Revenue, Revenue Growth, Gross Margin, EBITDA, EBITDA Margin, EBIT Margin, Period, Currency, Calc Status, Comp Status |
| T4.4 | Cash Flow & Cap Intensity | Entity, FCF, FCF Conversion, Capex/Revenue, Capex/EBITDA, WC/Revenue, Period, Currency, Calc Status, Comp Status |
| T4.5 | Credit Metric Benchmark | Entity, Total/Net/Sr Sec Leverage, Int/Adj Int Coverage, FFO/Debt, Liquidity, Period, Currency, Calc/Comp Status |
| T4.6 | Summary Statistics | Metric, Borrower Value, Peer Avg/Median/Min/Max, Q1/Q3, N, Borrower Position |
| T4.7 | Outlier Register | Entity, Metric, Value, Peer Range, Deviation, Direction, 6 Implication Columns, Downstream Handoff |
| T4.8 | Public Trading Comps | Entity, Mkt Cap, Date, EV, EV/Revenue, EV/EBITDA, Period, Metric Def, Comp Status, Source |
| T4.9 | Transaction Comps | Txn Name, Date, Type, Buyer/Seller, TV, TV/Revenue, TV/EBITDA, Period, Metric Def, Comp Status, Source |
| T4.10 | Implied EV | Method, Multiple Source/Value, Borrower Metric/Period, Implied EV/Low/Median/High, Calc Status, Limitations |
| T4.11 | Gaps & Limitations | Gap, Affected Metric/Section, Affected Peer(s), Downstream Impact, Severity, Action |

## Conditional Table (1)
| ID | Table | Key Columns | Required When |
|----|-------|-------------|---------------|
| T4.D1 | Peer Discovery Source Register | Candidate, Query / Source, URL or Source Locator, Retrieval Date, Dimensions Assessed, Promotion Decision, Evidence Tag, Limitation | Auto-discovery or optional web discovery runs |

## QA Checklist
- [ ] CP-1 data foundation confirmed  - [ ] Peer Universe Register complete with provenance tags  - [ ] All 11 alignment points assessed  - [ ] Comparability status before statistics  - [ ] Peer Statistic Rules enforced (N stated)  - [ ] Outliers classified with 6-dim credit translation  - [ ] Valuation multiples sourced with date  - [ ] Implied EV stated as context only  - [ ] Web-discovery runs populate T4.D1 and selected peers carry evidence tags in T4.1  - [ ] No JSON/DOCX/other sidecar created  - [ ] Gaps Ledger cumulative  - [ ] Peer provenance stated in Overall View  - [ ] Confidence Score (0-100) computed per CP_CONFIDENCE_SCORE.md, band derived  - [ ] Canonical Markdown valid; the Markdown handoff pass view-appropriate parity

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
