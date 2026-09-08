<!-- CP-8 Schema Reference (T3) | PROPOSED | 2026-06-22 -->

## Required Output Sections (9)
All 9 sections must be present. Where the observation window is open or a record is missing, the section still appears with [Insufficient Information] and a gap ledger entry.

## Required Tables (8)
| ID | Table Name | Key Columns |
|----|-----------|-------------|
| T7.1 | Decision Record | Action Bias, Posture, Instrument, Size, Decision Date, Decision-Maker Role, Module Status |
| T7.2 | Thesis / Expectation Register | Thesis, Greatest Uncertainty, Flagged Catalysts/Downside Paths, Expected Spread/Return, Expected Rating Path, Expected Hold, Exit Triggers, Evidence ID |
| T7.3 | Realized Outcome Log | Metric, Realized Value, As-of Date, Source, Interim/Final, Evidence ID |
| T7.4 | Variance Table | Metric, Expected, Realized, Variance (direction + magnitude), Confidence, Evidence ID |
| T7.5 | Attribution Table | Variance, Attribution Label, Process Sound? (Y/N), Originating Module (if gap), Basis, Evidence ID |
| T7.6 | Calibration Register (advisory) | Pattern, Target Module, Specific Prior, Supporting Decisions, Advisory Recommendation |
| T7.7 | Track-Record Dashboard | Hit rate, realized-vs-expected by cut (pathway/sector/sponsor), attribution distribution, lessons register |
| T7.8 | Gaps Ledger | Gap, Missing Item, Why It Matters, Impact on Output, Required Follow-Up |

## Required Final Narrative

Section 9, Post-Mortem Synthesis, states outcome versus the contemporaneously recorded thesis, canonical attribution, process quality separately from outcome, timing/sizing/exit discipline, any pattern-eligible evidence-grounded lesson, and the most material unresolved gap. It must not reconstruct the original thesis, form a new credit view, or assign individual blame.

## QA Checklist
- [ ] All 9 output sections present and populated (or [Insufficient Information] with gap logged)
- [ ] Every realized outcome is sourced and dated; none fabricated or estimated
- [ ] Every attribution drawn only from the 6 canonical labels
- [ ] Process quality explicitly separated from outcome in each attribution
- [ ] Flagged-vs-unflagged risk distinguished using T7.2's recorded downside paths
- [ ] Calibration entries gated to ≥3 comparable decisions and marked advisory/non-binding
- [ ] No credit view formed, revised, or overridden
- [ ] No individual named or graded
- [ ] Open observation windows flagged for revisit
- [ ] Step 9 gives a narrative post-mortem conclusion without hindsight reconstruction or a new credit view
- [ ] Source gate status documented (Completed / Completed with Limitations / Blocked)
- [ ] Canonical Markdown valid; every the Markdown handoff passes view-appropriate parity; numeric Confidence Score (0–100) + band present in the Audit Summary/envelope and every generated view

## Confidence
Primary measure is the numeric **Confidence Score (0–100)** computed per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`; the band (High / Medium / Low / Insufficient Information) is the derived label carried in the canonical `confidence_band` envelope field.

## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**
