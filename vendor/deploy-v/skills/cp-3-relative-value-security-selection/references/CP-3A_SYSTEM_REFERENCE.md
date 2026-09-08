<!-- CP-3A System Reference (T4) | 2026-06-03 -->

This is an absorbed phase of CP-3. References to CP-3/CP-3A outputs mean the source-grounded results already produced in the current run, or a matching validated handoff when available. No intermediate export, separate invocation or user approval is required. Apply SKILL.md’s maintained Sector RV loan-reference policy here, including its current-source basis and date treatment. Append this phase’s registers to the single CP-3 handoff.

## Identity
module_id: CP-3A | module_name: RecoveryInstrumentPreference | schema_family: Nested | layer: L3

## Dependencies
UP: CP-3 | DOWN (Analytical): CP-6 | DOWN (QA): CP-5, CP-5A

## Governance Rules
1. CP-3A is not standalone fundamental underwriting — it relies on CP-3 (which inherits CP-1/CP-2) and converts capital-structure, legal, recovery, and market evidence into instrument-level preference conclusions.
2. Instruments must be ordered by structural priority, not maturity.
3. Yield alone cannot override weak recovery, legal position, maturity concentration, liquidity, or LME exposure.
4. Preference requires supported structural position + adequate compensation + manageable maturity/liquidity + no overriding legal/recovery weakness.
5. Every material conclusion must complete: Evidence → Risk Mechanic → Credit Implication.

## Evidence Hierarchy
Sourced Fact > Calculated Metric > Analyst Inference > Insufficient Information > Unsupported Conclusion

## Input Gates (Blocking)
Gate 1: CP-3 RV analysis available | Gate 2: Capital structure includes seniority/subordination
Failure blocks only the affected preference assessment (UPSTREAM_DEPENDENCY_MISSING); preserve supported RV results and continue independent work in the same CP-3 handoff.

## Instrument Type Taxonomy
Revolving credit facility | First-lien term loan | First-lien secured notes | Second-lien loan/notes | Senior unsecured notes | Subordinated notes | HoldCo debt | Non-guarantor/local debt | Leasing/factoring/ABL

## Recovery Sensitivity Labels
Low sensitivity | Moderate sensitivity | High sensitivity | Binary / highly uncertain | Insufficient Information

## Preference Labels
Preferred | Secondary | Avoid | Requires More Work

## Evidence Confidence Labels
High | Medium | Low | Structural Only | Market Only | Insufficient Information

## Compensation Adequacy Labels
Attractive | Adequate | Inadequate | Unclear | Insufficient Information

## Key Risk Mechanics
Maturity concentration | Weak collateral | Guarantor leakage | Priming debt | Drop-down risk | Uptier risk | Unsecured subordination | Illiquidity | Rich pricing | Low price / wide spread not supported by recovery

## Downstream Handoffs
CP-3: instrument preference | CP-3B: portfolio implementation constraints | CP-3C: maturity and LME exposure | CP-4/CP-4A: legal/structural gaps | CP-6/CP-6A: security-selection debate evidence

## Fail/Restrict
- **Preference assessment blocked:** When usable CP-3 RV results or seniority/subordination detail are unavailable, record UPSTREAM_DEPENDENCY_MISSING and withhold dependent preference conclusions. Preserve supported RV results and continue independent work; this phase does not discard or halt the whole CP-3 handoff.
- **Restricted:** Module Status = Ready with Limitations when partial evidence available (e.g., no CP-4/CP-4A → legal/recovery views flagged, no market data → compensation = Unclear).
- **Preference Restricted:** Do not force preference where pricing, ranking, collateral, guarantor, recovery, or legal data is insufficient — use Requires More Work.
- **Recovery Restricted:** Do not infer recovery values unless supported by provided evidence — use Insufficient Information.

## Version: 2026-06-03
