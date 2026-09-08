<!-- CP-3 Schema Reference (T3) | 2026-06-03 -->

Loan analysis always resolves and uses the maintained enterprise Sector RV workbook and assumes it is current and relevant. REF_CP-3_Sector_RV.xlsx is an intentionally empty deployment placeholder, not market evidence. Apply the maintained-source protocol in SKILL.md: no freshness/relevance confirmation; preserve stated dates or record `Current — maintained Sector RV source` when no quote date is supplied. This basis satisfies the market-date checks below.

## Sector RV workbook fields

The supplied screenshots illustrate this layout; they are reference examples, not current loan evidence. Read the enterprise workbook itself. The workbook view shows sector tabs such as Software, Media, IT Services and Utilities, with date/title banners and grouped `ISSUERS` / `LOAN DATA` labels above the real header row. The visible view can hide columns and filter rows; retrieve the underlying headers and values before concluding that Borrower Name, Sub-Sector or a loan observation is missing. Find columns by their labels and meaning, allowing spacing variations rather than requiring fixed positions or a specific tab name.

| Workbook fields | Interpretation and handling |
| --- | --- |
| Company; Borrower Name | Company is the display/group name; Borrower Name identifies the borrowing entity. Match the actual facility using identifiers and terms. One borrower can have several loans. |
| Core Business Description; Sub-Sector; Sub-Group; Public/Private | Use the business description and classifications to select peers within a broad sector tab. Treat the description as source context, not a substitute for fundamental underwriting. Public/Private is issuer status; it does not establish loan liquidity. |
| Bloomberg / Bloomberg ID; FIGI | Preserve these as separate exact instrument identifiers. Keep distinct facilities under a repeated company name. Identical repeated observations count once; repeated names alone are not duplicates. |
| Loan Type; Ranking; Ratings | Keep facility codes such as B/B1/B2 separate from rating grades. Ranking describes lien/seniority, not analytical preference. Preserve composite ratings and any supplied agency labels; do not guess an agency or turn withdrawn/not-rated markers into a rating. |
| Size ($Mn); Margin; Maturity | Preserve the size's stated reporting basis and maturity. Resolve loan currency and margin units from workbook conventions or instrument evidence. A dollar reporting-size header does not prove the loan is USD-denominated. |
| Bid; Ask | Keep both sides and their units. Label any calculated midpoint and retain its inputs; it is not an executable bid or ask. A missing side does not erase the usable side. |
| Δ 1D; Δ 1W; Δ 1M; Δ 3M; Δ 6M; Δ 1YR; Δ YTD | Preserve the horizon and workbook-defined change basis. Do not mix price-point changes, percentage returns and spread changes. Zero and negative observations can be valid; red/green shading is presentation, not an RV recommendation. |
| Mid YTM; Mid 3Y DM | Keep yield-to-maturity and the three-year discount-margin horizon distinct. Do not relabel YTM as YTW, DM as contractual margin, or three-year DM as maturity-based DM. Verify anomalous derived values against available terms/inputs before relying on that metric. |
| Blank/error cells; #N/A N/A; Field Not Applicable | Treat missing/error markers only in the affected field; never coerce them to zero. Continue with other usable fields and peers. Missing history, loan-type metadata or one calculated metric does not invalidate the whole row or workbook. |

Read all relevant table regions on a sector sheet, not only the first loan table:

- **Loan rows:** facility-level observations used for instrument identity, terms and comparable loan analysis.
- **Index Statistics:** benchmark rows with index name/ID, Market Value, Avg Price, change horizons, YTM and 3Y DM. Preserve the index identity, rating group and reported units; a broad index is context, not another issuer or a sector-specific loan peer.
- **Sector Ratings Average:** source-reported rating-bucket summaries with `# Issuers`, size, margin, maturity, bid/ask, changes, Mid YTM and Mid 3Y DM. Use comparable rating buckets as a second benchmark, labelling the source aggregation basis. A zero count or dash from an empty/error aggregate means no usable aggregate observation, not zero yield/spread. Preserve the reported count label; do not assume it counts unique borrowers unless the formula/data supports that interpretation.

Keep these three regions separate when selecting peers or calculating summaries. Source averages can use criteria and weighting different from a custom peer set; preserve that distinction and inspect the existing formula when needed rather than silently substituting a different average. Do not ask the user to name a benchmark when suitable index and sector-rating context is already available in the sheet.

Bloomberg `BDP` and related formula cells must be read through their stored/displayed results, without requiring recalculation or a Bloomberg refresh. Keep formula input/scaling provenance when needed to explain a metric, but never treat formula text as its result. A screenshot, hidden column or access-status badge alone does not establish that the enterprise data is inaccessible.

If currency, a unit or an anomalous value remains unresolved after checking accessible workbook context and instrument evidence, restrict only the comparison that depends on it and record the gap once. Do not turn that check into a workbook freshness or relevance question.

## Required Tables (7)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T3.1 | Source Register | source_document_id, source_document_name, source_quality, period, entity_covered, data_supplied, limitation, downstream_use |
| T3.3 | Issuer / Security Scorecard | Category, Factor, Weight, Raw Score 1–5, Weighted Score, Confidence, Evidence, Risk Mechanic, Credit Implication |
| T3.4 | Override Log | Override Type, Trigger Evidence, Score Cap / Penalty, Revised Composite Score, Explanation |
| T3.5 | Relative Value Table | Security, Market Level, Market Date, Source, Quote Quality, Comps, Seniority / Security, Compensation vs. Risk, RV Label |
| T3.6 | Fundamental Value Matrix | Security / Issuer, Fundamental View, Relative-Value View, Structural / Recovery View, Final Matrix Bucket, Rationale, Evidence ID |
| T3.7 | Final Ranking | Rank, Issuer, Security / Tranche, Composite Score /100, Normalized /5.0, Credit Tier, Fundamental View, Relative Value View, Final Recommendation, Strongest Attribute, Weakest Attribute, Key Credit Issue, Monitoring Trigger, Evidence ID, Countervailing Evidence |
| T3.9 | Monitoring Triggers | Trigger, Threshold / Signal, Why It Matters, Credit / RV Impact, Evidence ID |

## Standalone Tables
| ID | Name | Columns |
|----|------|---------|
| T3.10 | Gaps Ledger | Gap, Missing Data, Why It Matters, Impact on Output, Required Follow-Up |

## QA Checklist
- [ ] Execution mode determined and required inputs verified per mode
- [ ] Module Status assigned (Full Run / Ready with Limitations / Blocked)
- [ ] Every material factual claim, score, RV conclusion, and recommendation is source-traceable
- [ ] Content distinctions maintained: Sourced Fact | Calculated Metric | Analyst Inference | Insufficient Information | Unsupported Conclusion
- [ ] Scope separation maintained: Fundamental | Structural | Legal/Recovery | Market Compensation | Technicals/Liquidity | Portfolio Constraints | Recommendation
- [ ] Score Direction correct: 1 = Conservative → 5 = Aggressive
- [ ] Every score includes Confidence tag (High / Medium / Low / Not Assessable)
- [ ] No precise composite score assigned if factor evidence materially incomplete — use range, Not Scorable, or Not Assessable
- [ ] Credit Tier correctly mapped from composite score
- [ ] Hard-risk overrides applied only where justified by evidence; not used to force ranking
- [ ] RV label assigned only with current market evidence under CP-3's maintained-source policy; Unclear used when market data absent
- [ ] Market claims identify: pricing date or maintained-source basis, source, instrument, currency, seniority, maturity, metric basis, liquidity/quote-quality limitation
- [ ] Instrument comparisons disclose seniority, maturity, currency, metric basis, and pricing-source limitations
- [ ] Weak credit not classified as Preferred solely due to wide spread
- [ ] Strong credit not classified as Avoid solely due to tight spread (unless clearly inadequate)
- [ ] Security-Selection formulation used for Step 8 conclusions
- [ ] Final Credit/RV View formulation used for Step 11 synthesis
- [ ] Monitoring triggers are specific and observable
- [ ] Gaps Ledger is cumulative across all steps
- [ ] Final view introduces no new data
- [ ] Module completion statement includes Recommendation and RV labels
- [ ] Generic adjectives absent unless issuer-specific evidence and current market data under the maintained-source policy support them
- [ ] No fabrication of spreads, prices, yields, DM, ratings, covenant terms, recovery assumptions, or technicals
- [ ] Python used for all arithmetic (scorecard weighting, composite score, normalization)
- [ ] Structured exports use null (not zero) for unavailable numeric values unless source explicitly states zero
- [ ] Percentages stored as decimals in structured exports
- [ ] CP-1 metric definitions preserved where applicable

<!-- Export rewritten to Markdown handoff+canonical Markdown contract per CP_AB_EXPORT_SPEC.md | 2026-06-26 -->
## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**

## Module Confidence (per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`)
The module's primary output confidence is a numeric **Confidence Score (0–100)**, computed deterministically per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md` and recomputed/audited by CP-5A; the **band** (High ≥80 / Medium 60–79 / Low 40–59 / Insufficient Information <40) is a derived label carried in `confidence_band`. (This is distinct from the per-factor scorecard Confidence tags in T3.3, which remain High / Medium / Low / Not Assessable.)
