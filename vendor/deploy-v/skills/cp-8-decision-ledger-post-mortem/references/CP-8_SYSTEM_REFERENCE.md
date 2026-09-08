<!-- CP-8 System Reference (T4) | PROPOSED | 2026-06-22 -->

## Identity
module_id: CP-8 | module_name: DecisionLedgerPostMortem | schema_family: Nested | layer: L8

## Dependencies
UP: CP-6, CP-6A | DOWN (Analytical, advisory): CP-1C, CP-2, CP-3A | DOWN (QA): CP-5, CP-5A
NOTE: L8 is terminal (post-decision). Calibration edges to CP-1C/CP-2/CP-3A are advisory and out-of-band — they inform priors, they do not re-trigger analytical execution, so no cycle is created.

## Governance Rules
1. Record and attribute — do not form, revise, or override a credit view.
2. Every realized outcome is sourced and dated; no fabricated prices, rating actions, or recovery figures.
3. Separate process quality from outcome: a flagged downside that materialized is sound process, not a miss.
4. No individual blame — attribute to the decision and reasoning, record the decision-maker role only.
5. Calibration is pattern-gated (≥3 comparable decisions) and advisory; a single outcome never binds a model change.
6. No thesis reconstruction after the fact — missing decision record/thesis = [Insufficient Information].

## Owned Object
decision_ledger (decision record + thesis/expectation + realized outcome + attribution + advisory calibration)

## Attribution Taxonomy (6)
Thesis Confirmed | Flagged Risk Materialized | Unflagged Risk Materialized | Right for Wrong Reason | Premature / Mistimed | Insufficient Information

## Outcome Metrics
Realized spread Δ vs expected | Rating migration vs expected | Default / restructuring incidence | Realized recovery vs CP-3A estimate | Holding period vs plan | Exit-trigger discipline

## Content Distinction Labels
Decision Fact | Original Thesis (as recorded) | Realized Outcome (sourced) | Attribution Judgement | Process-vs-Outcome Separation | Calibration Signal | Gap

## Calibration Discipline
Pattern = same directional miss across ≥3 comparable decisions. Each entry names target module + specific prior + supporting decisions + advisory recommendation. Marked non-binding. Single-decision misses recorded, not calibrated.

## Gate Status Labels
Completed | Completed with Limitations | Blocked

## Upstream Dependency Map
| Module | What CP-8 Needs | Impact if Missing |
|--------|-----------------|-------------------|
| CP-6 | IC Action Bias, final memo, single greatest uncertainty | No decision/thesis to attribute → Blocked |
| CP-6A | Portfolio Posture, sizing | Portfolio-level attribution limited |
| Independent realized-event sources | Dated rating, price, default, restructuring and recovery evidence; each item must be re-verified | Outcome tracking may remain limited while the observation window is open |

## Fail/Restrict
- **Blocked:** No dated decision record available to attribute. Do not reconstruct a thesis after the fact.
- **Restricted (Window Open):** Decision recorded but outcomes not yet observable → interim tracking only, attribution deferred.
- **Restricted (Calibration):** Fewer than 3 comparable decisions → record only, no calibration recommendation.
- **Individual-evaluation prohibition:** Any request to grade named individuals is declined (governance boundary).

## Version: 2026-06-22 (proposed)
