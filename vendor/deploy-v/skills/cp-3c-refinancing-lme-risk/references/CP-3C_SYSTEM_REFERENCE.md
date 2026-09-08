<!-- CP-3C System Reference (T4) | 2026-06-03 -->

## Identity
module_id: CP-3C | module_name: RefinancingLMERisk | schema_family: Nested | layer: L3

## Dependencies
UP: CP-1, CP-1A, CP-2A, CP-2D | DOWN (Analytical): CP-4, CP-6 | DOWN (QA): CP-5, CP-5A

## Governance Rules
1. Do not infer LME intent from maturity pressure alone — pressure, legal capacity, and incentive/willingness must all be present for High vulnerability.
2. Legal capacity must be source-supported (governing executed documents outrank drafts/summaries) — do not infer from market convention.
3. Every material conclusion must complete: Evidence → Risk Mechanic → Credit Implication.
4. Use directional probability labels only — never fabricate numerical probabilities.
5. If CP-4A unavailable, do not infer exact legal capacity; if CP-2C unavailable, do not infer sponsor willingness from identity alone.

## Evidence Hierarchy
Governing Executed Legal Document > Draft / Term Sheet / Posting Memorandum > Lender Presentation > Third-Party Covenant Review > Market Convention / Analyst Inference > Insufficient Information

## Prime / LME Vulnerability Score Labels
Low | Medium | High | Insufficient Information

## Dimension Scoring Labels
Low | Medium | High | Insufficient Information

## Probability Direction Labels
Low | Medium | High | Increasing | Stable | Decreasing | Insufficient Information

## Evidence Confidence Labels
High | Medium | Low | Formula Only | Insufficient Information

## Refinancing / LME Path Types (7 canonical)
Consensual Refinancing | Amend-and-Extend | Exchange Offer | Distressed Exchange | Uptier | Drop-Down | Priming Debt

## Refinancing / LME Path Types (12 detailed)
Consensual refinancing | Amend & Extend | Open-market repurchase | Exchange offer | Distressed exchange | Uptier | Drop-down | J.Crew-style transfer | Serta-style non-pro-rata exchange | Priming debt | Asset sale / partial paydown | Sponsor equity injection

## Legal-Capacity Indicators (14)
Incremental debt capacity | Lien capacity | Unrestricted subsidiary capacity | Investment capacity | RP/junior debt payment capacity | Collateral release | Guarantor release | Amendment thresholds | Sacred rights | Open-market purchase provisions | MFN protection | Intercreditor terms | Class voting | Pro rata sharing provisions

## Refinancing Pressure Indicators (10)
Near-term maturity relative to liquidity | Distressed trading | Negative FCF/cash burn | High cash interest burden | Covenant headroom compression | Ratings downgrade/negative outlook | Revolver draw | Sponsor support | Asset sale proceeds | Improving EBITDA/deleveraging

## Downstream Handoffs
CP-1/CP-1B: maturity/cash-interest data needs | CP-2: fundamental outlook constraints | CP-2A: downside mechanics | CP-2C: sponsor evidence | CP-2D: liquidity runway | CP-3: RV impact | CP-3A: exposed creditor class | CP-3B: sizing constraints | CP-4/CP-4A: legal capacity gaps | CP-6/CP-6A: debate evidence

## Output (per CP_AB_EXPORT_SPEC.md)
Author and validate canonical Markdown first as `[IssuerID]_CP-3C_[YYYYMMDD].md`, using exact front-matter `issuer_id` and `analysis_date` without hyphens (authoritative handoff saved to OneDrive, with a YAML envelope containing `confidence_score` + `confidence_band` and canonical H2 headings `## Audit Summary` / `## Analysis` / `## Evidence Trace` / `## Source Registry` / `## Gaps & Conflicts` / `## QA Validation`). Do not create alternate analytical exports. A failed optional view does not invalidate valid Markdown or a successful sibling export. No separate renderer/parser agent or database; no JSON blocks, export manifest, or extraction envelope.

## Module Confidence
Primary measure is the numeric **confidence_score (0–100)** computed per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md` (and recomputed/audited by CP-5A), with the **band** (High ≥80 / Medium 60–79 / Low 40–59 / Insufficient Information <40) as a derived label carried in the `confidence_band` envelope field. The per-row Evidence Confidence Labels remain part of the analysis method (table evidence quality), feeding the score's E (evidence-quality) input.

## Fail/Restrict
- **Blocked:** No maturity/debt-schedule data available. Module produces blocked statement only.
- **Restricted (Legal):** CP-4A unavailable → legal capacity flagged [Insufficient Information], exact basket availability not inferred.
- **Restricted (Sponsor):** CP-2C unavailable → sponsor willingness flagged [Insufficient Information], not inferred from identity.
- **Restricted (Market):** Market data missing → market access/RV conclusions marked [Market Data Not Provided] or [Insufficient Information].
- **Score Restricted:** Path not labelled High unless pressure, feasibility, and incentive ALL supported.
- **Probability Restricted:** No fabricated numerical probabilities — directional labels only.

## Version: 2026-06-03
