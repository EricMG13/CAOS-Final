Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-2F_StyleAndFormat.md, REF_CP-2F_Workflow.md.

Original files, in this bundle: REF_CP-2F_01_SourceGateESGDisclosureInventory.md, REF_CP-2F_02_EnvironmentalTransitionExposure.md, REF_CP-2F_03_SocialOperationalExposure.md, REF_CP-2F_04_MaterialityClassification.md, REF_CP-2F_05_SustainabilityLinkedDebtMechanics.md, REF_CP-2F_06_RefinancingCostOfCapitalLinkage.md, REF_CP-2F_07_CreditImplicationSynthesis.md, REF_CP-2F_08_GapsLedger.md, REF_CP-2F_09_OverallCreditImplication.md, REF_CP-2F_StyleAndFormat.md, REF_CP-2F_Workflow.md

## REF_CP-2F_01_SourceGateESGDisclosureInventory.md
<!-- REF_CP-2F_01 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-2F" step="01" name="Source Gate and ESG Disclosure Inventory">
<input>Issuer ESG / sustainability reports, annual-report ESG sections, regulatory and transition / emissions disclosures, sustainability-linked debt documents (SLL / SLB term sheets, second-party opinions); CP-1, CP-1A, CP-2 outputs; CP-DR research dossier or user-supplied ESG research criteria (optional).</input>
<gate>Always executes. A valid outcome is **Not Applicable** — no credit-material ESG exposure and no sustainability-linked debt. BLOCKING only where assessment is requested but zero source exists; then Blocked. Never infer materiality from sector reputation.</gate>

## Instructions
1. Inventory ESG / transition disclosures and any sustainability-linked debt terms.
2. Assess reliability: audited / assured vs self-reported / promotional; flag greenwashing or disclosure-quality risk affecting any ESG claim used downstream.
3. Assign Module Status:
   - **Completed:** issuer ESG/transition disclosures and/or sustainability-linked terms available and credit-relevant.
   - **Completed with Limitations:** partial disclosure.
   - **Not Applicable:** no credit-material exposure and no sustainability-linked debt — state with brief basis.
   - **Blocked:** insufficient source to assess. Do not infer from sector reputation.

## Output
T2G.1: ESG disclosure inventory + reliability assessment + Module Status: Completed / Completed with Limitations / Not Applicable / Blocked
<!-- Upstream re-anchor (common_rules #10): re-import and verify the specific upstream outputs consumed (CP-1, CP-1A, CP-2); restate exact run_id/period. If a required upstream value is absent or mismatched, mark [Insufficient Information] and gate the dependent step — do not infer it. -->
</step_reference>
## REF_CP-2F_02_EnvironmentalTransitionExposure.md
<!-- REF_CP-2F_02 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-2F" step="02" name="Environmental and Transition Exposure">
<input>T2G.1; emissions data, asset-base description, sector transition context, applicable regulation.</input>
<gate>Step 1 complete and not Blocked.</gate>

## Instructions
1. Identify environmental / transition exposures that have a **credit transmission path**: emissions / carbon cost, physical climate risk to operating assets, remediation / decommissioning liabilities, stranded-asset exposure, and regulatory transition (carbon pricing, bans, mandates).
2. Source and date each exposure. State the transmission mechanic (revenue, margin, capex, asset value, refinancing) — an exposure without a mechanic is not yet credit-relevant.
3. No values or ethics judgement — credit transmission only.

## Output
T2G.2: Transition Risk Register — `Exposure`|`Source/Date`|`Transmission Mechanic`|`Affected Driver`|`Evidence ID`
</step_reference>
## REF_CP-2F_03_SocialOperationalExposure.md
<!-- REF_CP-2F_03 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-2F" step="03" name="Social and Operational Exposure">
<input>T2G.1; labor, safety, product-liability, and license-to-operate disclosures and events.</input>
<gate>Step 1 complete.</gate>

## Instructions
1. Identify social / operational exposures with a cash-flow or event-risk impact: labor disputes, safety / regulatory penalties, product liability, license-to-operate / permit risk.
2. Source and date each; state the transmission mechanic.
3. Reference CP-2C for governance and sponsor-conduct matters — do **not** duplicate governance analysis here.

## Output
T2G.3: Social Event-Risk Register — `Exposure`|`Source/Date`|`Transmission Mechanic`|`Event-Risk vs Ongoing`|`Evidence ID`
</step_reference>
## REF_CP-2F_04_MaterialityClassification.md
<!-- REF_CP-2F_04 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-2F" step="04" name="Materiality Classification">
<input>T2G.2 (transition) and T2G.3 (social) registers.</input>
<gate>Steps 2–3 complete.</gate>

## Instructions
1. Classify every factor for credit materiality before any implication: Material — Quantified | Material — Directional | Watch | Immaterial to Credit | Insufficient Information.
2. Require issuer-specific transmission. **Default to Immaterial to Credit** unless transmission to cash flow / asset value / spread is shown — resist ESG narrative for its own sake.
3. For Watch items, name the catalyst that would make the factor material.
4. Do not infer materiality from sector reputation alone.

## Output
T2G.4: Materiality Table — `Factor`|`Materiality Class`|`Transmission Basis`|`Catalyst (if Watch)`|`Evidence ID`
</step_reference>
## REF_CP-2F_05_SustainabilityLinkedDebtMechanics.md
<!-- REF_CP-2F_05 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-2F" step="05" name="Sustainability-Linked Debt Mechanics">
<input>T2G.1; sustainability-linked loan / bond terms, KPI and SPT definitions, ratchet schedule, second-party opinion / verification.</input>
<gate>Step 1 complete. Not Applicable if the issuer has no sustainability-linked debt — state and skip.</gate>

## Instructions
1. For each sustainability-linked instrument capture: KPI definition and ambition, SPT thresholds and test dates, ratchet direction and size (bps), step-up / step-down symmetry, consequence of a miss, and reporting / verification (second-party opinion, assurance).
2. Judge whether the ratchet is **credit-meaningful or cosmetic** (size vs spread, symmetry, ambition of the SPT).
3. Translate to the expected spread effect and any covenant-headroom or reporting / monitoring implication.
4. Do not fabricate KPI, SPT, or ratchet terms — mark [Insufficient Information] where the document is silent.

## Output
T2G.5: KPI / SPT / Ratchet Table — `Instrument`|`KPI`|`SPT + Test Date`|`Ratchet (direction, bps)`|`Symmetry`|`Credit-Meaningful?`|`Expected Spread Effect`|`Evidence ID`
</step_reference>
## REF_CP-2F_06_RefinancingCostOfCapitalLinkage.md
<!-- REF_CP-2F_06 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-2F" step="06" name="Refinancing and Cost-of-Capital Linkage">
<input>T2G.4 (materiality) and T2G.5 (sustainability-linked mechanics); CP-3 market context where available.</input>
<gate>Steps 4–5 complete.</gate>

## Instructions
1. Assess ESG-driven effects on refinancing access and cost of capital: investor-mandate exclusions, green / sustainability premium (greenium), and sector capital-availability shifts.
2. Ground each effect in a source; mark Directional where the magnitude cannot be quantified from sources.
3. Tie effects to the issuer's actual maturity profile / refinancing needs — a cost-of-capital effect with no near-term funding need is lower priority; say so.

## Output
T2G.6: Demand / Access Implications — `Effect`|`Direction`|`Quantified vs Directional`|`Linked Maturity / Funding Need`|`Evidence ID`
</step_reference>
## REF_CP-2F_07_CreditImplicationSynthesis.md
<!-- REF_CP-2F_07 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-2F" step="07" name="Credit Implication Synthesis">
<input>T2G.4 (materiality), T2G.5 (sustainability-linked mechanics), T2G.6 (refinancing / cost-of-capital).</input>
<gate>Step 6 complete.</gate>

## Instructions
1. Synthesize the material ESG factors into credit implications using Evidence → Risk Mechanic → Credit Implication: PD, LGD, liquidity, FCF durability, refinancing capacity, relative value, security selection, monitoring posture.
2. Lead with Material — Quantified factors; state Immaterial-to-Credit explicitly so the committee sees what was assessed and dismissed.
3. Identify the single most material ESG / transition credit driver for the Step 9 CP-6 handoff.
4. State module confidence as the numeric `confidence_score` (0–100) with its derived band, computed per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`, and name its drivers (evidence quality, coverage, source gate, any QA penalties).

## Output
T2G.7: ESG Credit Implication Table — `Material Factor`|`Risk Mechanic`|`Credit Implication`|`Confidence`|`Evidence ID`. This register supports but does not replace Step 9's narrative conclusion.
</step_reference>
## REF_CP-2F_08_GapsLedger.md
<!-- REF_CP-2F_08 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-2F" step="08" name="Gaps Ledger">
<input>All prior step outputs (T2G.1–T2G.7); cumulative gaps identified throughout the workflow.</input>
<gate>Always executes.</gate>

## Instructions
1. Compile all gaps from Steps 1–7 into one consolidated ledger.
2. For each gap record: Gap, Missing Item (emissions disclosure, transition exposure, KPI / SPT terms, ratchet size, verification), Why It Matters, Impact on Output, Required Follow-Up.
3. Flag where missing disclosure prevented a materiality classification (factor left Insufficient Information).
4. Every section marked [Insufficient Information] in Steps 1–7 must have a corresponding gap entry.

## Output
T2G.8: Gaps Ledger — `Gap`|`Missing Item`|`Why It Matters`|`Impact on Output`|`Required Follow-Up`
</step_reference>
## REF_CP-2F_09_OverallCreditImplication.md
<!-- REF_CP-2F_09 (T2) | 2026-08-02 -->
<step_reference module="CP-2F" step="09" name="Overall Credit Implication">
<input>T2G.1-T2G.8</input>
<gate>Steps 1-8 complete, including the cumulative gaps ledger.</gate>

## Instructions
1. State the highest-priority ESG or transition factor and the affected credit metric or decision dimension.
2. Explain the supported Evidence → Risk Mechanic → Credit Implication path, including direction and quantification where the evidence permits it.
3. Distinguish operating, liquidity/refinancing, PD and LGD channels; do not imply a channel that the evidence does not support.
4. State the decisive uncertainty or limitation and the dated monitoring condition that would strengthen, weaken or invalidate the conclusion.
5. End with one CP-6 debate handoff: the single most material supported ESG/transition driver. Synthesis only — no new fact, estimate, score or source may be introduced.

## Output
Narrative `### Credit implication` final view in `## Analysis` of the canonical Markdown handoff. Render this conclusion before reader tables while retaining T2G.1-T2G.8 losslessly below the analytical appendix heading.
</step_reference>
## REF_CP-2F_StyleAndFormat.md
<!-- REF_CP-2F_StyleAndFormat.md — created 2026-07-11 as SEC8 compression relocation target for CP-2F_ACTIVE_PROMPT.md -->

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Institutional, creditor-first, materiality-gated, evidence-led. Default to "immaterial to credit" unless transmission is shown — resist ESG narrative for its own sake. Prefer materiality tables and SLL term tables over prose. Use creditor language: transition cost, stranded asset, remediation liability, margin ratchet, SPT, step-up, refinancing access, recovery. Target 1–3 pages, shorter where ESG is immaterial.
## REF_CP-2F_Workflow.md
<!-- REF_CP-2F_Workflow.md — created 2026-07-11 as SEC8 compression relocation target for CP-2F_ACTIVE_PROMPT.md -->

## Workflow — 9 Steps (relocated from ACTIVE_PROMPT 2026-07-11; final synthesis added 2026-08-02)
| Step | Name | REF File | Output |
|------|------|----------|--------|
| 1 | Source Gate & ESG Disclosure Inventory | REF_CP-2F_01 | T2G.1 Source Register + Module Status |
| 2 | Environmental & Transition Exposure | REF_CP-2F_02 | T2G.2 Transition Risk Register |
| 3 | Social / Operational Exposure | REF_CP-2F_03 | T2G.3 Social Event-Risk Register |
| 4 | Materiality Classification | REF_CP-2F_04 | T2G.4 Materiality Table |
| 5 | Sustainability-Linked Debt Mechanics | REF_CP-2F_05 | T2G.5 KPI/SPT/Ratchet Table |
| 6 | Refinancing & Cost-of-Capital Linkage | REF_CP-2F_06 | T2G.6 Demand / Access Implications |
| 7 | Credit Implication Synthesis | REF_CP-2F_07 | T2G.7 ESG Credit Implication Table |
| 8 | Gaps Ledger | REF_CP-2F_08 | T2G.8 Gaps Ledger |
| 9 | Overall Credit Implication | REF_CP-2F_09 | Narrative final view in canonical Markdown Analysis |
