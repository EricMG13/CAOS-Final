<!-- CP-2E Schema Reference (T3) | 2026-06-03 -->

## Required Tables (8)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T2F.1 | Source Register | source_document_id, source_document_name, source_quality, period, entity_covered, data_supplied, limitation, downstream_use |
| T2F.2 | Debt & Rate Exposure Register | Debt Instrument, Amount, Fixed / Floating, Base Rate, Margin / Coupon, Currency, Maturity, Hedge Status, Source Trace, Credit Implication |
| T2F.3 | Hedging Register | Hedge Type, Notional, Instrument Covered, Rate / Strike, Maturity, Coverage Status, Source Trace, Limitation |
| T2F.4 | Unhedged Floating-Rate Exposure | Metric, Amount, Formula / Source, Status, Credit Implication, Source Trace |
| T2F.5 | +100 bps Base-Rate Sensitivity | Sensitivity, Formula, Source Inputs, Estimated Cash Impact, FCF / Liquidity Implication, Status, Source Trace |
| T2F.6 | FX Exposure & Mismatch Register | Exposure Type, Revenue Currency / Region, Cost Currency / Region, Debt / EBITDA / Cash / Covenant Currency, Natural Hedge?, Evidence, Risk Mechanic, Credit Implication, Source Trace, Limitation |
| T2F.7 | Commodity & Inflation Sensitivity | Input / Commodity / Inflation Driver, Cost Exposure, Pass-Through Mechanism, Evidence, Risk Mechanic, Credit Implication, Source Trace, Limitation |
| T2F.8 | Macro Sensitivity Summary | Macro Driver, Evidence, Risk Mechanic, FCF / Liquidity Impact, Refinancing / RV Implication, Monitoring Trigger, Source Trace |

## Standalone Tables
| ID | Name | Columns |
|----|------|---------|
| T2F.9 | Gaps Ledger | Gap, Missing Data, Why It Matters, Impact on Output, Required Follow-Up, Downstream Module Affected |

## QA Checklist
- [ ] Module Status assigned (Full Run / Ready with Limitations / Blocked)
- [ ] Every material factual claim, hedge statement, exposure register, sensitivity input, and macro conclusion is source-traceable
- [ ] Gross floating-rate debt distinguished from hedged and unhedged floating-rate debt
- [ ] Hedge notional distinguished from economically effective cash-flow protection
- [ ] Hedge coverage status assigned using controlled labels (Effective where supported / Partial / Expired / Maturity mismatch / Notional disclosed only / Terms insufficient / Insufficient Information)
- [ ] All debt assumed fixed only where explicitly disclosed; floating-rate classification requires source support
- [ ] Swaps, caps, collars, forwards not assumed effective unless terms disclosed
- [ ] Hedges not assumed to cover full exposure unless disclosed
- [ ] FX exposure not inferred from geography alone — requires currency data support
- [ ] Missing evidence marked [Insufficient Information] — not converted to positive or adverse conclusion
- [ ] Source conflicts logged (not reconciled silently)
- [ ] Content distinctions maintained: Source Fact | Characterization | Calculation | Interpretation | Credit Implication | Gap
- [ ] +100 bps sensitivity uses supported unhedged floating-rate exposure; else [Insufficient Information]
- [ ] Python used for all arithmetic (rate sensitivity, unhedged exposure, FX/commodity sensitivity)
- [ ] Structured exports use null (not zero) for unavailable numeric values unless source explicitly states zero
- [ ] Percentages stored as decimals in structured exports
- [ ] CP-1 metric definitions preserved where applicable
- [ ] Rate Exposure Labels match controlled taxonomy
- [ ] Hedge Labels (Types + Coverage Status) match controlled taxonomy
- [ ] FX Exposure Labels match controlled taxonomy
- [ ] Commodity / Inflation Labels match controlled taxonomy
- [ ] Macro Risk Level assigned with Evidence → Risk Mechanic → Credit Implication support
- [ ] Gaps Ledger is cumulative across all steps
- [ ] Overall Macro / Hedging View introduces no new data
- [ ] Module completion statement includes Macro Risk Level
- [ ] Generic adjectives absent unless issuer-specific evidence supports them

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
