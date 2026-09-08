<!-- CP-3B System Reference (T4) | 2026-06-03 -->

This is an absorbed phase of CP-3. References to CP-3/CP-3A outputs mean the source-grounded results already produced in the current run, or a matching validated handoff when available. No intermediate export, separate invocation or user approval is required. Apply SKILL.md’s maintained Sector RV loan-reference policy here, including its current-source basis and date treatment. Append this phase’s registers to the single CP-3 handoff.

## Identity
module_id: CP-3B | module_name: PortfolioFitPositionSizing | schema_family: Nested | layer: L3

## Dependencies
UP: CP-3 | DOWN (Analytical): CP-6, CP-6A | DOWN (QA): CP-5, CP-5A

## Governance Rules
1. CP-3B does not replace CP-3 security-selection logic — it refines implementation posture after a security-selection conclusion exists.
2. Core Hold requires source-supported evidence for all 7 minimum evidence items; missing any → cannot assign Core unless labelled hypothetical framework-only.
3. Credit attractiveness alone is never sufficient for Core Hold — portfolio capacity, liquidity, concentration, and downside-budget support are required.
4. Yield alone cannot override adverse portfolio mechanics (concentration, liquidity, downside, legal, mandate).
5. Every material sizing conclusion must complete: Evidence → Risk Mechanic → Portfolio / Credit Implication.

## Evidence Hierarchy
Source Fact > Calculation > Analyst Inference > Directional Only > Insufficient Information > Not Assessable

## Sizing Posture Taxonomy (7 values)
Avoid | Watchlist | Starter Position | Core Hold | Hold Existing Only | Reduce / Trim | Requires More Work

## Confidence
Primary measure: numeric **Confidence Score (0–100)** per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md` (recomputed/audited by CP-5A). Derived band (back-compat label): High ≥ 80 | Medium 60–79 | Low 40–59 | Insufficient Information < 40. The per-sizing-conclusion Confidence column carries the derived band label.

## Fit Categories
Mandate fit | RV fit | Liquidity fit | Risk-budget fit | Not fit | Not assessable

## Portfolio Roles
Yield carry | Spread duration | Convexity | Defensive senior secured | Catalyst | RV switch | Recovery-sensitive upside | Watchlist / monitoring only

## Portfolio-Action Labels
Add / Initiate | Hold / Maintain | Trim / Reduce | Avoid | Monitor / Escalate

## Caution Levels (Risk Budget Flags)
High | Medium | Low | Not Assessable

## Downside Status Labels
Calculated | Directional Only | Not Calculable

## Concentration Dimensions (7)
Issuer/group | Sector/subsector | Sponsor/ownership | Rating bucket | Maturity year/wall | Capital-structure layer | Correlated holdings/common factor

## Input Gate
The current run’s CP-3 security-selection results satisfy this input gate. If they do not yet exist, complete that stage first; a separate CP-3 export is not required.

## Fail/Restrict
- **Blocked:** The current run cannot establish a supported security-selection conclusion. Report the affected limitation in the single CP-3 handoff.
- **Restricted (Generic):** Mandate/portfolio data unavailable. Output is generic portfolio-fit logic, not mandate-specific sizing.
- **Core Restricted:** Core Hold cannot be assigned without all 7 minimum evidence items.
- **Sizing Restricted:** No numeric size expressed without user-provided size and available portfolio constraints.
- **Liquidity Restricted:** Exit risk not assessable when liquidity data missing.
- **Scaling Restricted:** No assumption of scaling without price impact unless trading evidence supports it.

## Version: 2026-06-03
