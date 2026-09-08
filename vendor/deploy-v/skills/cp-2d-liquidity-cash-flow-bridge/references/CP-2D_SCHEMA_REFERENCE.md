<!-- CP-2D Schema Reference (T3) | 2026-06-03 -->

## Required Tables (8)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T2E.1 | Source Register | source_document_id, source_document_name, source_quality, period, entity_covered, data_supplied, limitation, downstream_use |
| T2E.2 | Beginning Liquidity Register | Liquidity Component, Source-Supported Amount, Accessibility Status, Source Trace, Limitation / Restriction, Risk Mechanic, Credit Implication |
| T2E.3 | Mandatory Cash Uses Register | Cash Use, Amount, Timing, Mandatory / Discretionary, Source Trace, Risk Mechanic, Credit Implication, Limitation |
| T2E.4 | Working Capital & Capex Pressure | Driver, Evidence, Expected Cash Impact, Risk Mechanic, Credit Implication, Source Trace, Limitation |
| T2E.5 | 12-Month Liquidity Bridge | Bridge Item, Amount, Source / Calculation, Status, Credit Comment, Source Trace |
| T2E.7 | Liquidity Mitigants & Constraints | Mitigant / Constraint, Evidence, Risk Mechanic, Credit Implication, Source Trace, Limitation |
| T2E.9 | Gaps Ledger | Gap, Missing Data, Why It Matters, Impact on Output, Required Follow-Up, Downstream Module Affected |

## Standalone Calculations
| ID | Calculation | Formula |
|----|------------|---------|
| T2E.6 | Months to Empty | Beginning accessible liquidity / average monthly cash burn |

## QA Checklist
- [ ] Module Status assigned (Full Run / Ready with Limitations / Blocked)
- [ ] Every material factual claim, calculation input, and liquidity conclusion is source-traceable
- [ ] Reported cash distinguished from accessible liquidity
- [ ] Committed available revolver distinguished from inaccessible / covenant-constrained capacity
- [ ] Restricted cash excluded from accessible liquidity unless source explicitly confirms availability
- [ ] Undrawn revolver not assumed accessible unless disclosed
- [ ] No cash-use category assumed zero unless explicitly supported
- [ ] Missing evidence marked [Insufficient Information] — not converted to positive or adverse conclusion
- [ ] Source conflicts logged (not reconciled silently)
- [ ] Content distinctions maintained: Source Fact | Characterization | Calculation | Interpretation | Credit Implication | Gap
- [ ] Liquidity Data Status Labels applied to all bridge items (Reported / Calculated / Provisional / Management-guided / Analyst estimate / Insufficient Information / Not Available / Not Comparable / Conflict Logged / Blocked)
- [ ] Liquidity Component labels match controlled taxonomy
- [ ] Cash-Use Category labels match controlled taxonomy
- [ ] Months to Empty calculated only where both inputs supported; else [Insufficient Information]
- [ ] Cash-burn basis period stated with recurring / seasonal / distorted qualifier
- [ ] Volatile cash flows not annualized without limitation statement
- [ ] Python used for all arithmetic (bridge totals, MTE, revolver availability, headroom)
- [ ] Structured exports use null (not zero) for unavailable numeric values unless source explicitly states zero
- [ ] Percentages stored as decimals in structured exports
- [ ] CP-1 metric definitions preserved where applicable
- [ ] Liquidity Risk Level assigned with Evidence → Risk Mechanic → Credit Implication support
- [ ] Gaps Ledger is cumulative across all steps
- [ ] Overall Liquidity View introduces no new data
- [ ] Module completion statement includes Liquidity Risk Level
- [ ] Generic adjectives absent unless issuer-specific evidence supports them

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
