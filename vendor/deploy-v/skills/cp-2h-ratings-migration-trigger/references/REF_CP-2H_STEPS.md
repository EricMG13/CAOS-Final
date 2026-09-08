Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

Original files, in this bundle: REF_CP-2H_A_RatingEvidenceGate.md, REF_CP-2H_B_MethodologyAndMetricBridge.md, REF_CP-2H_C_TriggerHeadroomEngine.md, REF_CP-2H_D_MigrationAndDivergence.md, REF_CP-2H_E_CreditHandoff.md, REF_CP-2H_F_OutputAndQA.md

## REF_CP-2H_A_RatingEvidenceGate.md
# CP-2H A — Rating evidence gate

Capture rating agency, legal issuer, rated instrument, rating type, rating, outlook/watch, recovery rating, effective/action date, publication date, source and exact locator. A rating on a parent, subsidiary or different instrument cannot be silently applied to the target issuer or security.

Prefer current agency actions and criteria. Issuer presentations may report ratings but are secondary evidence and must be labelled. Third-party databases require an observation timestamp and do not override the agency's own action. If current evidence cannot be verified, mark the rating field `[Insufficient Information]` rather than using model memory.

Respect source licensing and quotation limits. Store paraphrased triggers with exact locators; short quotations are used only when necessary to preserve a defined threshold.

## REF_CP-2H_B_MethodologyAndMetricBridge.md
# CP-2H B — Methodology and metric bridge

Identify the criteria actually applicable to the issuer, sector, group structure and instrument. Record publication/effective date and whether a newer criteria version supersedes the cited version. Consider business/industry/country risk, competitive position, cash flow/leverage, liquidity, capital structure, financial policy, governance, comparable-rating modifiers, group support and instrument notching only where the agency methodology applies them.

Bridge each agency metric to CP-1 and CP-2G. Record adjustments for leases, pensions, securitisations, restricted cash, hybrids, capitalised interest, factoring, supplier finance and non-recurring items when supported. If the agency calculation cannot be reproduced, use the disclosed value with a limitation; do not invent adjustments.

## REF_CP-2H_C_TriggerHeadroomEngine.md
# CP-2H C — Trigger headroom engine

For quantitative triggers preserve directionality. A maximum leverage trigger and a minimum coverage trigger require different headroom formulas. Show metric definition, threshold, current/base/downside value, period, units and calculation.

An agency phrase such as "sustained" requires multi-period testing; a point-in-time breach is not automatically a trigger. Where the agency supplies a range rather than a hard threshold, show distance to both bounds. Do not turn general methodology medians into issuer-specific triggers.

Qualitative triggers must identify the cited factor and evidence: financial policy, liquidity, business deterioration, governance, acquisition risk, parent support, regulatory action or refinancing access. Use ordinal direction and state uncertainty; do not manufacture numerical headroom.

## REF_CP-2H_D_MigrationAndDivergence.md
# CP-2H D — Migration and divergence

Map each CP-2G case to the canonical transition classes without converting a threshold result directly into a rating notch. Agency committees consider multiple factors and timing. State the earliest supported review catalyst and whether pressure is temporary, sustained or contingent.

Agency divergence is evidence, not an error. Explain differences through rated entity, instrument, methodology, metric adjustments, sector treatment, country ceiling, recovery/notching, event timing or qualitative modifiers. Never average ratings or choose a preferred agency silently.

If an issuer is unrated, CP-2H may produce a criteria and trigger framework only when explicitly requested. Label it `methodology mapping`, never `shadow rating` or `expected agency rating`.

## REF_CP-2H_E_CreditHandoff.md
# CP-2H E — Credit handoff

The handoff states current sourced rating posture, nearest quantitative and qualitative triggers, base/downside buffer, expected monitoring horizon, potential instrument-level implications and the evidence that would change the view.

CP-2B receives dated rating catalysts. CP-3/CP-3D receive rating and notching context for market pricing. CP-3C receives transition pressure relevant to refinancing. CP-6 receives agency divergence and the strongest challenge to RBOT's base case.

CP-2H does not produce the CP-2G forecast, CP-2 fundamental conclusion, CP-3 security recommendation or an agency rating action.
## REF_CP-2H_F_OutputAndQA.md
# CP-2H F — Output and QA

Required QA tests:

1. Issuer and instrument ratings are not conflated.
2. Every rating/outlook/watch and trigger is agency-attributed, dated and located.
3. Criteria are current and applicable to the target entity/sector/instrument.
4. Agency metrics are bridged to CP-1/CP-2G definitions with adjustments visible.
5. Trigger direction, period and sustainability language are respected.
6. Transition classes are not represented as formal actions or mechanical notches.
7. Agency disagreement remains visible and is not averaged away.
8. No rating, probability or quotation is fabricated.
9. Markdown contract validation and semantic/numerical checks pass.

The Analysis section contains T2R.1–T2R.10. Evidence Trace records action, criteria, metric and forecast lineage. Gaps & Conflicts names stale or unavailable agency evidence. QA Validation reports each test and the final status.
