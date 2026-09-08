<!-- CP-3B Schema Reference (T3) | 2026-06-03 -->

This is an absorbed phase of CP-3. References to CP-3/CP-3A outputs mean the source-grounded results already produced in the current run, or a matching validated handoff when available. No intermediate export, separate invocation or user approval is required. Apply SKILL.md’s maintained Sector RV loan-reference policy here, including its current-source basis and date treatment. Append this phase’s registers to the single CP-3 handoff.

## Required Tables (8)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T3C.1 | Portfolio Input Gate | Input, Available / Missing, Source, Limitation, Portfolio Impact |
| T3C.2 | Portfolio Fit Register | Name / Instrument, Fit Category, Evidence, Risk Mechanic, Why It Fits / Does Not Fit, Constraints / Notes, Source Trace |
| T3C.3 | Position Sizing Posture Table | Name / Instrument, Sizing Posture, Evidence, Reason, Key Risk, Implementation Note, Confidence, Source Trace |
| T3C.4 | Risk Budget Flags | Flag, Evidence, Risk Mechanic, Why It Matters, Caution Level, Portfolio Impact, Source Trace |
| T3C.5 | Concentration and Correlation Register | Exposure Dimension, Current Exposure, Proposed / Pro Forma Exposure, Limit / Capacity, Evidence Status, Risk Mechanic, Portfolio Implication, Source Trace |
| T3C.6 | Liquidity and Implementation Assessment | Liquidity / Implementation Factor, Evidence, Risk Mechanic, Implementation Consequence, Constraint / Action, Source Trace |
| T3C.7 | Downside Budget and Recovery Sensitivity | Downside Scenario / Driver, Input Basis, Formula / Method, Result / Directional View, Portfolio Loss / Risk-Budget Implication, Status, Source Trace |
| T3C.8 | Monitoring Triggers | Trigger ID, Indicator, Leading / Lagging, Threshold or Qualitative Signal, Linked Risk Flag, Portfolio Action, Source Trace, Limitation |

## Standalone Tables
| ID | Name | Columns |
|----|------|---------|
| T3C.9 | Gaps Ledger | Gap ID, Missing Data, Why It Matters, Affected Sizing / Risk Budget / Trigger, Consequence for Confidence, Required Follow-Up Source |

## QA Checklist
- [ ] Current-run CP-3 security-selection results available; no separate CP-3 file required
- [ ] Module Status assigned (Completed / Completed with Limitations / Blocked)
- [ ] Output mode determined (Mandate-Specific / Generic Portfolio-Fit Logic)
- [ ] Every material factual claim, position number, mandate limit, security datapoint, market datapoint, legal/structural conclusion, liquidity assertion, and sizing conclusion is source-traceable
- [ ] Content distinctions maintained: Source Fact | Calculation | Analyst Inference | Portfolio Implication | Gap
- [ ] Sizing Posture assigned from canonical 7-value taxonomy (Avoid / Watchlist / Starter Position / Core Hold / Hold Existing Only / Reduce / Trim / Requires More Work)
- [ ] Minimum Evidence for Core verified — all 7 items present, or Core labelled as hypothetical framework-only
- [ ] Starter Conditions verified where Starter assigned
- [ ] Credit attractiveness alone does not justify Core Hold — portfolio capacity, liquidity, concentration, and downside-budget support required
- [ ] Numeric size expressed only if user provided one and portfolio constraints available
- [ ] Module Confidence Score (0–100) computed per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`, with derived band (High ≥ 80 / Medium 60–79 / Low 40–59 / Insufficient Information < 40); per-sizing-conclusion Confidence column carries the derived band label
- [ ] Fit Category assigned per issuer/security (Mandate fit / RV fit / Liquidity fit / Risk-budget fit / Not fit / Not assessable)
- [ ] Concentration assessed across 7 dimensions where data available
- [ ] Null used for unavailable numeric values — no unexplained blanks
- [ ] Liquidity/exit risk flagged where missing
- [ ] Scaling assumption not made without trading evidence
- [ ] Downside budget connected to portfolio loss at proposed size
- [ ] Monitoring triggers are specific, observable, and linked to portfolio actions
- [ ] Trigger IDs use CP-3B-MON-NNN format; Gap IDs use CP-3B-GAP-NNN format
- [ ] Gaps Ledger is cumulative across all steps
- [ ] Overall view introduces no new data
- [ ] Module completion statement includes Sizing Posture; canonical Markdown is valid, and every the Markdown handoff result is reported independently per `../../../CANON_SHARED.md § CP_AB_EXPORT_SPEC.md`
- [ ] No generic buy/sell language — controlled sizing/action labels only
- [ ] No promotional language, equity-upside framing, or unsupported sizing conviction
- [ ] Limitations stated next to affected conclusion, not hidden in footnotes
- [ ] Canonical Markdown and every requested export use null / [Insufficient Information] (not zero) for unavailable numeric values unless the source explicitly states zero

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
