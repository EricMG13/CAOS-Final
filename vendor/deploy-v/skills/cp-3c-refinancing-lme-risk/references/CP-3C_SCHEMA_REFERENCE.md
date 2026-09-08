<!-- CP-3C Schema Reference (T3) | 2026-06-03 -->

## Required Tables (10)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T3D.1 | Source Register | source_document_id, source_document_name, source_quality, period / date, entity_covered, data_supplied, limitation, downstream_use |
| T3D.2 | Maturity Wall Register | Instrument, Amount, Currency, Maturity Date, Years to Maturity, Seniority / Lien, Coupon / Margin, Fixed / Floating, Call Date, Refinancing Pressure, Credit Implication, Source Trace |
| T3D.3 | Liquidity / Market Access Table | Factor, Evidence, Current Level / Status, Direction, Risk Mechanic, Credit Implication, Confidence, Source Trace |
| T3D.4 | Legal Capacity Register | Legal-Capacity Indicator, Available / Not Available / Unclear, Evidence, Risk Mechanic, LME Paths Enabled, Confidence, Source Trace |
| T3D.5 | Sponsor Willingness Table | Factor, Evidence, Assessment, Risk Mechanic, Credit Implication, Source Trace |
| T3D.6 | Refinancing Path Table | Path Type, Feasibility, Likelihood Direction, Evidence Supporting, Evidence Against, Legal Capacity Required, Creditor Impact, Source Trace |
| T3D.7 | Vulnerability Score Table | Dimension, Score, Evidence, Risk Mechanic, Credit Implication, Source Trace |
| T3D.8 | Creditor Class Exposure Table | Creditor Class, Exposure: Base Case, Exposure: Stress Case, Exposure: LME Case, Recovery Implication, Priming / Subordination Risk, Source Trace |
| T3D.9 | Monitoring Triggers | Trigger, Indicator, Threshold / Qualitative Signal, Leading / Lagging, Why It Matters, Linked Path(s), Source Trace |
| T3D.10 | Scenario Map | Scenario, Key Assumptions, Refinancing Path, Timeline, Creditor Impact, Recovery Implication, Probability Direction, Confidence, Source Trace |

## Standalone Tables
| ID | Name | Columns |
|----|------|---------|
| T3D.11 | Gaps Ledger | Gap, Missing Data, Why It Matters, Impact on Output, Required Follow-Up |

## QA Checklist
- [ ] Minimum maturity/debt-schedule data available — if missing, module is Blocked
- [ ] Module Status assigned (Full Run / Ready with Limitations / Blocked)
- [ ] Every material maturity, amount, price, yield, spread, liquidity, FCF, debt capacity, covenant capacity, sponsor behavior, and legal-flexibility claim is source-supported
- [ ] Content distinctions maintained: Maturity Fact | Liquidity/FCF Fact | Market Signal | Legal-Capacity Evidence | Sponsor-Behavior Evidence | Analyst Interpretation | Creditor-Class Impact | Gap
- [ ] Governing executed legal documents outrank drafts, summaries, term sheets, posting memoranda, lender presentations
- [ ] LME intent not inferred from maturity pressure alone
- [ ] Legal capacity not inferred from market convention — source-supported provisions only
- [ ] Path not labelled High unless pressure, feasibility, and incentive ALL supported
- [ ] No fabricated numerical probabilities — directional labels only
- [ ] If CP-4A unavailable, exact capacity not inferred
- [ ] If CP-2C unavailable, sponsor willingness not inferred from identity alone
- [ ] If market data missing, market access/RV conclusions marked [Market Data Not Provided] or [Insufficient Information]
- [ ] Prime/LME Vulnerability Score assigned (Low / Medium / High / Insufficient Information) with dimension breakdown
- [ ] Score Selection Rules applied correctly (High requires all three: pressure + capacity + incentive)
- [ ] All 14 Legal-Capacity Indicators assessed where evidence available
- [ ] All applicable paths from 12-path taxonomy assessed for feasibility
- [ ] Creditor class exposure mapped under Base, Stress, and LME scenarios
- [ ] 3 scenarios constructed (Base, Stress, LME Case)
- [ ] Monitoring triggers are specific, observable, and linked to refinancing/LME paths
- [ ] Draft, unsigned, stale, incomplete, or conflicting documents flagged with reduced confidence
- [ ] Gaps Ledger is cumulative across all steps
- [ ] Overall view introduces no new data
- [ ] Module completion statement includes Vulnerability Score and Most Likely Path
- [ ] Evidence Confidence Labels used consistently (High / Medium / Low / Formula Only / Insufficient Information)
- [ ] Probability Direction Labels used consistently (Low / Medium / High / Increasing / Stable / Decreasing / Insufficient Information)
- [ ] Structured exports use null (not zero) for unavailable numeric values unless source explicitly states zero

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
