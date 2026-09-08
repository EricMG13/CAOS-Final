<!-- CP-2C System Reference (T4) | 2026-06-03 -->

## Identity
module_id: CP-2C | module_name: GovernanceSponsorScore | schema_family: Nested | layer: L2

## Dependencies
UP: CP-1A, CP-2 | DOWN (Analytical): CP-6 | DOWN (QA): CP-5, CP-5A  
NOTE: CP-2C-HANDOFF-CP-2 is a supplementary feedback path (not circular). CP-2 may optionally consume CP-2C on re-run.

## Governance Rules
1. Sponsor identity ≠ behavior; sponsor reputation ≠ evidence. Only issuer-specific, source-supported actions qualify.
2. Legal capacity ≠ willingness. Always separate what documents permit from what sponsor has done or stated.
3. Composite governance score requires ≥4 of 9 dimensions evidence-supported; else Not Scorable → Risk Level = Insufficient Information (unless one clearly High-risk documented action).
4. Missing evidence = [Insufficient Information], never an adverse conclusion.
5. Every material conclusion must complete the chain: Evidence → Risk Mechanic → Credit Implication.

## Evidence Hierarchy
1. **High** — Primary source, dated, issuer-specific (OM, credit agreement, indenture, annual report, audited financials, signed amendment, restructuring agreement, filed ownership document)
2. **Medium** — Secondary source or module output citing primary evidence (CP-0, CP-1A, CP-2, CP-3C, CP-4A, internal note with references)
3. **Low** — High-level summary, promotional, stale, incomplete, undated, non-primary (use only with limitation language)
4. **Insufficient** — Unsupported assertion, generic reputation, no source, claim from sponsor identity alone

## Sponsor / Governance Risk Levels
Low | Medium | High | Insufficient Information

## Behavior Taxonomy Categories
A. Supportive / Creditor-Aligned | B. Neutral / Mixed | C. Extraction-Oriented | D. Creditor-Adverse | E. Insufficient Information

## Scoring Dimensions (9)
Leverage tolerance | Shareholder extraction risk | Acquisition appetite | Support behavior | Disclosure transparency | Creditor treatment / amendment behavior | Legal-capacity linkage | Reporting quality | Related-party leakage risk  
Values: 1 (creditor-favorable) | 3 (mixed) | 5 (creditor-adverse) | Not Scorable

## Red-Flag Severity
Critical | Material | Minor

## Risk Direction Labels
Supportive | Neutral | Mixed | Creditor-Adverse | Insufficient Information

## Handoff Tags
CP-2C-HANDOFF-CP-2 | CP-2C-HANDOFF-CP-2A | CP-2C-HANDOFF-CP-2D | CP-2C-HANDOFF-CP-3 | CP-2C-HANDOFF-CP-3C | CP-2C-HANDOFF-CP-4A | CP-2C-HANDOFF-CP-5A | CP-2C-HANDOFF-CP-5 | CP-2C-HANDOFF-CP-6 | CP-2C-HANDOFF-CP-6A

## Fail/Restrict
- **Blocked:** Module Status = Blocked when no ownership / sponsor / shareholder identification is possible from any source.
- **Restricted:** Module Status = Ready with Limitations when partial evidence available but critical governance / sponsor dimensions unsupported.
- **Not Scorable composite:** Fewer than 4 of 9 scoring dimensions evidence-supported → composite Not Scorable, Risk Level defaults to Insufficient Information unless one clearly High-risk documented action.
- **Individual evaluation prohibition:** Any request to evaluate named individuals triggers hard refusal (safety boundary).

## Version: 2026-06-03
