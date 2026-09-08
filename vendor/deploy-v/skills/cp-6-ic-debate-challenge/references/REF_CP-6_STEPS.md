Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-6_ExampleOutputPattern.md, REF_CP-6_Export.md, REF_CP-6_ScoringAndBias.md, REF_CP-6_Workflow.md.

Original files, in this bundle: REF_CP-6_01_ICDebateSourceGate.md, REF_CP-6_02_PreDebateThesisMap.md, REF_CP-6_03_BullAnalystOpeningStatement.md, REF_CP-6_04_BearAnalystCrossExamination.md, REF_CP-6_05_BullAnalystDefense.md, REF_CP-6_06_ICChairEvidenceWeighting.md, REF_CP-6_07_DebateResolutionMatrix.md, REF_CP-6_08_ActionBiasDetermination.md, REF_CP-6_09_SingleGreatestUncertainty.md, REF_CP-6_10_ICChairFinalMemo.md, REF_CP-6_11_GapsLedger.md, REF_CP-6_ExampleOutputPattern.md, REF_CP-6_Export.md, REF_CP-6_ScoringAndBias.md, REF_CP-6_Workflow.md

## REF_CP-6_01_ICDebateSourceGate.md
<!-- REF_CP-6_01 (T2) | 2026-06-03 -->
<step_reference module="CP-6" step="01" name="IC Debate Source Gate">
<input>CP-0 registry, all upstream module canonical `.md` handoffs (YAML front-matter envelope + canonical H2 headings, attached as grounding), source files, market data, portfolio/mandate inputs.</input>
<gate>Always executes. This IS the gate check. BLOCKING: If CP-1 AND CP-2 are both unavailable → Module Status = Blocked, STOP (Bull opening cannot be evidence-led).</gate>

## Instructions
1. Confirm availability of all upstream module canonical `.md` handoffs, source materials, market data, and portfolio/mandate inputs.
2. Determine gate status:
   - **Full Run:** CP-1, CP-2, CP-2A, CP-4, and market data available.
   - **Ready with Limitations:** CP-1 and CP-2 available but CP-2A, CP-4, CP-3, CP-2D, CP-3C, CP-3A, or CP-4A missing. Carry each limitation forward.
   - **Blocked:** CP-1 AND CP-2 unavailable → STOP.
3. Apply limitation rules:
   - CP-2A missing → Bear cannot fully map Zero-Bound downside.
   - CP-4 missing → lender control, leakage, recovery mechanics cannot be fully tested.
   - CP-3/market data missing → RV conclusions = [Insufficient Information].
   - CP-2D missing → quantified liquidity runway = [Insufficient Information] unless directly supported by CP-1/CP-1B.
   - CP-4A missing → basket/covenant-capacity headroom must not be inferred.
   - CP-3C missing → refinancing/LME path must not be claimed.
   - CP-3A missing → instrument preference/recovery conclusion must not be claimed.
4. Record files and modules available, missing inputs, and limitations carried forward.

## Output
Gate status: Full Run / Ready with Limitations / Blocked
Source register: modules available, modules missing, limitations carried forward.
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-6_02_PreDebateThesisMap.md
<!-- REF_CP-6_02 (T2) | 2026-06-03 -->
<step_reference module="CP-6" step="02" name="Pre-Debate Thesis Map">
<input>All available upstream module outputs; gate status from Step 1.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Build a neutral, evidence-only thesis map covering all 10 dimensions:
   - Cash-flow durability, margin resilience, FCF conversion
   - Liquidity runway
   - Leverage / deleveraging trajectory
   - Refinancing risk / maturity profile
   - Legal / covenant protection
   - Recovery / LGD
   - Relative value
   - Portfolio fit
   - Sponsor / governance
   - Catalyst visibility
2. For each dimension: state the available evidence, source module, and evidence quality (Strong/Moderate/Weak/Insufficient).
3. Do NOT take a position — this is the neutral evidence inventory.
4. Conclude with the **central investment controversy**: the single most important disputed question the debate must resolve.
5. Mark any dimension with missing evidence as [Insufficient Information].

## Output
Narrative: Neutral evidence map (10 dimensions) + central investment controversy statement.
</step_reference>
## REF_CP-6_03_BullAnalystOpeningStatement.md
<!-- REF_CP-6_03 (T2) | 2026-06-03 -->
<step_reference module="CP-6" step="03" name="Bull Analyst Opening Statement">
<input>Pre-Debate Thesis Map (Step 2); all available upstream module outputs.</input>
<gate>Step 2 complete.</gate>

## Instructions
1. Present exactly **3 Bull claims**. Each must include:
   - **Evidence** (specific source, module, period, metric)
   - **Risk Mechanic** (how it supports credit durability)
   - **Credit Implication** (from 13-value Canonical Credit Implication set)
   - **Monitoring Signal** (what would invalidate the claim)
2. Claim ordering (mandatory):
   - **Claim 1:** Cash-flow conversion or revenue durability.
   - **Claim 2:** Structural protection, liquidity runway, recovery, or covenant control.
   - **Claim 3:** Catalyst, relative value, refinancing pathway, or portfolio implementation.
3. Bull may only argue from source-supported evidence. Prohibited: unsupported optimism, TAM language, sector growth, valuation upside, generic resilience.
4. If evidence for a required claim area is unavailable, state [Insufficient Information] and explain what is missing.

## Output
3 structured Bull claims, each with Evidence, Risk Mechanic, Credit Implication (from 13-value set), and Monitoring Signal.
</step_reference>
## REF_CP-6_04_BearAnalystCrossExamination.md
<!-- REF_CP-6_04 (T2) | 2026-06-03 -->
<step_reference module="CP-6" step="04" name="Bear Analyst Cross-Examination">
<input>Bull Opening Statement (Step 3); all available upstream module outputs; CP-4/CP-4A for legal-control test.</input>
<gate>Step 3 complete.</gate>

## Instructions
1. Attack the Bull's **exact 3 claims** using a cross-examination table.
2. For each Bull claim attacked, provide:
   - Bear Counter-Evidence (specific source, metric, module)
   - Fragility Vector (stress-transmission mechanism)
   - Legal / Covenant Exploit (from CP-4/CP-4A; if unavailable → [Insufficient Information])
   - Risk Mechanic (how Bear evidence undermines Bull claim)
   - Credit Implication (from 13-value set)
   - What Would Prove Bear Wrong (falsifiability test)
3. After the table, provide:
   - **Bear Zero-Bound Path:** Attempt the full chain: [Operating Stress] → [EBITDA/FCF Impact] → [Liquidity/Leverage Result] → [Legal/Refinancing Consequence] → [Credit Outcome]. If chain cannot be completed → state which link is missing.
   - **Bear Legal-Control Attack:** Test lender-control weakening via EBITDA add-backs, ratio debt, incremental facilities, restricted payments, unrestricted subsidiaries, asset transfers, collateral release, priming debt, uptier flexibility, amendment thresholds. If CP-4/CP-4A unavailable → [Insufficient Information].
   - **Bear Conclusion:** Summary of Bear case strength.

## Output
T6A.4: `Bull Claim Attacked`|`Bear Counter-Evidence`|`Fragility Vector`|`Legal / Covenant Exploit`|`Risk Mechanic`|`Credit Implication`|`What Would Prove Bear Wrong`
+ Bear Zero-Bound Path narrative + Bear Legal-Control Attack narrative + Bear Conclusion.
</step_reference>
## REF_CP-6_05_BullAnalystDefense.md
<!-- REF_CP-6_05 (T2) | 2026-06-03 -->
<step_reference module="CP-6" step="05" name="Bull Analyst Defense">
<input>Bear Cross-Examination (Step 4); original Bull claims (Step 3); upstream module outputs.</input>
<gate>Step 4 complete.</gate>

## Instructions
1. Respond directly to each Bear attack using **only rebuttal evidence tied to the specific attack**.
2. For each Bear attack, provide:
   - Bull rebuttal evidence (source, metric, mechanic)
   - Why the rebuttal mitigates the Bear's identified fragility vector
   - Rebuttal Status: **Fully Rebutted** / **Partially Rebutted** / **Failed** / **Insufficient Information**
3. Do not introduce new claims — only rebut existing Bear attacks.
4. If Bull cannot rebut a Bear attack → acknowledge the failure explicitly.
5. If evidence for rebuttal is unavailable → state [Insufficient Information].

## Output
Structured rebuttals per Bear attack, each with rebuttal evidence, mitigation logic, and Rebuttal Status (Fully Rebutted / Partially Rebutted / Failed / Insufficient Information).
</step_reference>
## REF_CP-6_06_ICChairEvidenceWeighting.md
<!-- REF_CP-6_06 (T2) | 2026-06-03 -->
<step_reference module="CP-6" step="06" name="IC Chair Evidence Weighting">
<input>Steps 3-5 (Bull claims, Bear attacks, Bull defense); all upstream module outputs.</input>
<gate>Step 5 complete.</gate>

## Instructions
1. Score each of the **9 required dimensions** using the Chair Scoring Rubric (1-5 scale):
   - Cash-flow durability
   - Downside pathway severity
   - Liquidity runway
   - Refinancing / maturity risk
   - Legal / covenant control
   - Recovery / LGD protection
   - Sponsor / governance alignment
   - Relative value compensation
   - Portfolio fit / sizing
2. For each dimension: record Score, Bull Evidence, Bear Evidence, and Chair Assessment (who has superior evidence and why).
3. Score interpretation: 1 = Bull clearly superior | 2 = Bull somewhat stronger | 3 = Balanced/unresolved | 4 = Bear somewhat stronger | 5 = Bear clearly superior.
4. Do NOT score a dimension if both sides lack evidence → mark [Insufficient Information].
5. Do NOT calculate or present an average unless ALL dimensions have supportable scores. If scoring is incomplete → mark overall as Provisional.

## Output
T6A.6: `Dimension`|`Score (1-5)`|`Bull Evidence`|`Bear Evidence`|`Chair Assessment`
</step_reference>
## REF_CP-6_07_DebateResolutionMatrix.md
<!-- REF_CP-6_07 (T2) | 2026-06-03 -->
<step_reference module="CP-6" step="07" name="Debate Resolution Matrix">
<input>T6A.6 Chair scoring; Steps 3-5 debate record.</input>
<gate>Step 6 complete.</gate>

## Instructions
1. Resolve each core disputed risk identified during the debate.
2. For each disputed risk: assign a Resolution Label from exactly this set:
   - **Bull Sustained** — Bull evidence prevails.
   - **Bear Sustained** — Bear evidence prevails.
   - **Partially Mitigated** — Bull partially rebuts Bear but residual risk remains.
   - **Unresolved** — Evidence is balanced or incomplete.
   - **Insufficient Information** — Neither side has adequate evidence.
3. For each resolution: state the disputed risk, Bull position, Bear position, resolution label, evidence basis, and credit implication.
4. Use this to set up the Action Bias Determination (Step 8).

## Output
T6A.7: `Disputed Risk`|`Bull Position`|`Bear Position`|`Resolution`|`Evidence Basis`|`Credit Implication`
Resolution labels: Bull Sustained | Bear Sustained | Partially Mitigated | Unresolved | Insufficient Information.
</step_reference>
## REF_CP-6_08_ActionBiasDetermination.md
<!-- REF_CP-6_08 (T2) | 2026-06-03 -->
<step_reference module="CP-6" step="08" name="Action Bias Determination">
<input>T6A.6, T6A.7; debate record (Steps 3-7); Final Bias Guardrails.</input>
<gate>Step 7 complete.</gate>

## Instructions
1. Determine the final action bias from exactly the 8 permitted values: Avoid | Watchlist | Starter Position | Core Hold | Add / Increase | Reduce / Trim | Exit | Requires More Work.
2. Use the required formulation:
   "Final Action Bias: [Action Bias]. The decision is driven by [top evidence], because [risk mechanic], which implies [PD / LGD / liquidity / RV / portfolio implication]. The main factor preventing a higher-conviction recommendation is [constraint]."
3. Cross-check against Final Bias Guardrails (Active Prompt) — the selected bias must be consistent with the evidence pattern.
4. Apply Chair Decision Rules:
   - Bear proves Zero-Bound path + Bull cannot quantify liquidity protection → bias ≤ Watchlist.
   - Bull proves durable FCF + liquidity + maturities + RV but legal leakage unresolved → Starter Position.
   - Both sides weak evidence → Requires More Work.
5. State which persona won the debate (Bull / Bear / Neither) and why.

## Output
Final Action Bias formulation (required format). Debate winner statement.
</step_reference>
## REF_CP-6_09_SingleGreatestUncertainty.md
<!-- REF_CP-6_09 (T2) | 2026-06-03 -->
<step_reference module="CP-6" step="09" name="Single Greatest Uncertainty">
<input>Steps 1-8; Action Bias Determination.</input>
<gate>Step 8 complete.</gate>

## Instructions
1. Identify exactly **one** greatest uncertainty that constrains conviction.
2. For this uncertainty, state:
   - What it is (specific risk, missing evidence, or unresolved dispute)
   - Why it matters (risk mechanic → credit implication)
   - Evidence needed to resolve it
   - Decision impact if resolved **positively** (how bias would change)
   - Decision impact if resolved **negatively** (how bias would change)
3. This must be the single most decision-relevant uncertainty — not a list.

## Output
Single Greatest Uncertainty: structured statement with uncertainty, why it matters, evidence needed, positive resolution impact, negative resolution impact.
</step_reference>
## REF_CP-6_10_ICChairFinalMemo.md
<!-- REF_CP-6_10 (T2) | 2026-06-03 -->
<step_reference module="CP-6" step="10" name="IC Chair Final Memo">
<input>Steps 1-9; all debate artifacts.</input>
<gate>Step 9 complete.</gate>

## Instructions
1. Write a concise IC-facing memo covering exactly these elements:
   - **Decision:** Final Action Bias (from Step 8).
   - **Who won the debate** and **why** (Bull / Bear / Neither).
   - **Most important Bull evidence** (single most compelling claim).
   - **Most important Bear evidence** (single most compelling attack).
   - **Legal / recovery view** (from CP-4/CP-4A/CP-3A evidence or [Insufficient Information]).
   - **Liquidity / refinancing view** (from CP-2D/CP-3C evidence or [Insufficient Information]).
   - **Relative-value / portfolio view** (from CP-3/market data or [Insufficient Information]).
   - **Required follow-up before increasing conviction** (specific actions/data needed).
2. Unsupported areas MUST be marked [Insufficient Information].
3. This is a synthesis memo — no new analysis, no new evidence.
4. Keep concise and decision-focused.

## Output
Narrative: IC Chair Final Memo covering all 8 required elements.
</step_reference>
## REF_CP-6_11_GapsLedger.md
<!-- REF_CP-6_11 (T2) | 2026-06-03 -->
<step_reference module="CP-6" step="11" name="Gaps Ledger">
<input>Steps 1-10 (cumulative).</input>
<gate>Always executes.</gate>

## Instructions
1. List ALL missing information that affected the debate outcome.
2. For each gap: record Gap ID (CP-6-GAP-NNN), Gap, Why It Matters (risk mechanic → credit implication), Impact on Debate (which persona/step was affected), and Required Follow-Up (specific source or action needed).
3. Include gaps accumulated from all prior steps (missing modules, missing market data, missing legal analysis, insufficient evidence areas).
4. Sequential Gap IDs: CP-6-GAP-001, CP-6-GAP-002, etc.

## Output
T6A.11: `Gap ID`|`Gap`|`Why It Matters`|`Impact on Debate`|`Required Follow-Up`
</step_reference>
## REF_CP-6_ExampleOutputPattern.md
<!-- REF_CP-6_ExampleOutputPattern.md (T2 Example Library) | 2026-06-10 | Ported from Agent Files: CP-6__SUPPORT__EXAMPLE_OUTPUT_PATTERN.txt -->


================================================================================
FILE: CP-6__SUPPORT__EXAMPLE_OUTPUT_PATTERN.txt
MODULE: CP-6 — ICDebateChallenge
STATUS: UPDATED (vNext)
MECHANICAL CHANGES APPLIED: MC-1, MC-2, MC-3, MC-5
GOVERNING CONTRACT: CP_GLOBAL_AGENT_INSTRUCTIONS_v3.2.txt
PURPOSE: Example debate output pattern for CP-6 IC Debate.
================================================================================

EXAMPLE_OUTPUT_PATTERN

Purpose: Provide a standard format for CP-6 debate output elements. Action
bias definitions are defined in CP-6__SUPPORT__ANALYTICAL_STANDARD.txt.

1. Example Bull Claim Format (Illustrative Only — Do Not Use as Issuer Data)

Bull Claim 1 — Cash-Flow Conversion Durability
Evidence: LTM FCF conversion of 62% (CP-1B, Period: FY2025), supported by
  85% recurring revenue base (CP-1A, Lender Presentation dated [Date]).
Risk Mechanic: High revenue visibility and limited working-capital volatility
  support durable FCF generation through cycle, reducing refinancing dependence
  and supporting debt service capacity.
Credit Implication: Positive — supports current leverage trajectory and reduces
  PD under base case. FCF coverage of mandatory cash uses is 1.8x (CP-2D).
Monitoring Signal: Quarterly FCF conversion below 40% for two consecutive
  quarters.

2. Example Bear Counter Format

| Bull Claim Attacked | Bear Counter-Evidence | Fragility Vector | Legal / Covenant Exploit | Risk Mechanic | Credit Implication | What Would Prove Bear Wrong |
|---|---|---|---|---|---|---|
| Bull Claim 1: FCF conversion durability | LTM capex is 60% maintenance (CP-1B); management has guided 15% capex increase for FY2026 (Lender Presentation) | Maintenance capex inflexibility compresses discretionary FCF under revenue stress | Ratio debt capacity expands with add-back-inflated EBITDA (CP-4A, Section 5.03(b)), permitting incremental leverage even as true FCF declines | Rising mandatory capex absorbs FCF headroom; add-back-inflated EBITDA masks deterioration in covenant tests | Negative — FCF conversion overstated by ~8pp when capex normalization is applied; leverage headroom is narrower than reported metrics suggest | Two consecutive quarters of >65% FCF conversion after capex normalization |

3. Example Chair Scoring Format

| Dimension | Score (1–5) | Bull Evidence | Bear Evidence | Chair Assessment |
|---|---:|---|---|---|
| Cash-flow durability | 2 | 62% LTM FCF conversion, 85% recurring revenue | Maintenance capex rising, normalization reduces conversion to ~54% | Bull has superior base-case evidence; Bear capex risk is credible but bounded by contractual pass-through. Score: Bull modestly ahead. |

4. Example Action Bias Determination

Final Action Bias: Starter Position. The decision is driven by durable base-
case FCF conversion and accessible liquidity runway of 18+ months (CP-2D),
because these support debt service and reduce near-term PD, which implies
manageable downside under base case. The main factor preventing a higher-
conviction recommendation is unresolved legal leakage capacity (CP-4A Section
6.04) and missing current market pricing for relative-value confirmation.

IC ACTION BIAS (8-value subset of canonical decision taxonomy):
Avoid | Watchlist | Starter Position | Core Hold | Add / Increase |
Reduce / Trim | Exit | Requires More Work

NOTE: "Add / Increase" is ONE value (resolves S4).

ZERO-BOUND CHAIN:
Operating Stress → EBITDA/FCF Impact → Liquidity/Leverage Result →
Legal/Refinancing Consequence → Credit Outcome

THREE PERSONAS:
Bull Analyst    — argues durability from source-supported evidence
Bear Analyst    — attacks Bull's claims via Zero-Bound chain
IC Chair        — adjudicates evidence, determines final action bias

CANONICAL CREDIT IMPLICATION (13 values):
Positive — Deleveraging | Positive — Margin Expansion |
Positive — Revenue Growth | Positive — Liquidity Improvement |
Positive — Covenant Headroom Expansion | Neutral — Stable |
Negative — Leverage Increase | Negative — Margin Compression |
Negative — Revenue Decline | Negative — Liquidity Deterioration |
Negative — Covenant Erosion | Negative — Refinancing Risk |
Insufficient Information
## REF_CP-6_Export.md
<!-- REF_CP-6_Export (T2 support) | 2026-07-11 | Export Markdown handoff+canonical Markdown full field/item lists extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-6" name="Export Detail">

## Markdown handoff Header — 5 fields
Issuer · Module (CP-6 · ICDebateChallenge) · Reporting period · Analysis date · run_id.

## Markdown handoff Audit Summary + Confidence Score (before the narrative)
Numeric Confidence Score 0–100 and its band (per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`); a 2–4 line audit summary (what passed, what is weak, what is missing); `qa_status` (Passed / Restricted / Blocked) and `committee_status`. If the score is below the **High** band, add an explicit line directing the reader to the Audit Appendix.

## Markdown handoff Audit Appendix (single, at the end) — full item list
Source Gate / Readiness · Gap Ledger (T6A.11) · Evidence Trace (claim → evidence, with lineage_class) · Source Registry · QA Validation findings (severity-tagged) · Conflicts Log · Limitation Flags · Downstream Consumers.

## CANONICAL MARKDOWN HANDOFF YAML front-matter — full field list
`confidence_score`, `confidence_band`, `qa_status`, `committee_status`, `limitation_flags`, `validation_warnings`, `upstream_artifacts_used`, `downstream_consumers`; followed by canonical H2 headings.

</reference>
## REF_CP-6_ScoringAndBias.md
<!-- REF_CP-6 ScoringAndBias (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-6" name="Action-Bias, Evidence & Scoring Rules">

Authoritative for CP-6 evidence weighting (Step 6), debate resolution (Step 7), and action-bias determination (Step 8). Load alongside the CP-6 workflow.

## Action Bias Definitions
- **Avoid:** Downside risk, legal leakage, liquidity risk, refinancing risk, weak recovery, or poor RV not adequately compensated.
- **Watchlist:** Potentially actionable, but evidence incomplete, catalyst timing unclear, or compensation insufficient.
- **Starter Position:** Credit evidence supportive, but uncertainty, liquidity, legal structure, recovery, mandate consumption, or market technicals justify limited sizing.
- **Core Hold:** Durable cash-flow support, acceptable legal/recovery profile, manageable downside, fair-to-attractive compensation.
- **Add / Increase:** Resilient fundamentals, credible downside protection, attractive RV, no unresolved gating risk.
- **Reduce / Trim:** Position defensible, but risk-reward deteriorated or sizing no longer justified.
- **Exit:** Bear case has materially superior evidence and remaining value protection inadequate.
- **Requires More Work:** Missing information prevents a decision-useful investment conclusion.

## Canonical Credit Implication (13 values)
Positive — Deleveraging | Positive — Margin Expansion | Positive — Revenue Growth | Positive — Liquidity Improvement | Positive — Covenant Headroom Expansion | Neutral — Stable | Negative — Leverage Increase | Negative — Margin Compression | Negative — Revenue Decline | Negative — Liquidity Deterioration | Negative — Covenant Erosion | Negative — Refinancing Risk | Insufficient Information

## Evidence Hierarchy (highest → lowest)
1. Audited financials, executed legal documents, current market levels, current portfolio/mandate data
2. Company-reported financials, management reporting, covenant certificates, lender presentations, offering memoranda
3. Prior module outputs that cite underlying documents
4. Third-party reports, rating-agency reports, covenant-review reports, broker/trading runs
5. Analyst interpretation based on sourced facts

## Evidence Quality Labels (4)
- **Strong:** Directly supported by audited financials, executed legal documents, current market data, mandate/exposure data, or source-backed module output.
- **Moderate:** Supported by company-reported data, management reporting, lender materials, or source-backed module analysis with limitations.
- **Weak:** Partial, stale, draft, incomplete, unaudited, non-comparable, or provisional evidence.
- **Insufficient:** Required evidence missing, conflicting, not decision-useful, or unsupported by cited source.

## Chair Decision Rules
1. If liquidity is not evidenced → do not underwrite a high-conviction long.
2. If CP-4 is missing → do not claim strong creditor control.
3. If CP-4A is missing → do not claim basket headroom or covenant capacity.
4. If CP-3 / market data is missing → do not claim attractive relative value.
5. If CP-2A is missing → do not claim downside resilience.
6. If CP-2D is missing → do not claim quantified liquidity runway unless directly supported by CP-1 or CP-1B.
7. If CP-3C is missing → do not claim definitive refinancing or LME path.
8. If CP-3A is missing → do not claim definitive instrument preference or recovery conclusion.
9. If Bear proves credible Zero-Bound path and Bull cannot quantify liquidity protection → bias ≤ Watchlist without explicit Chair justification.
10. If Bull proves durable FCF + accessible liquidity + manageable maturities + fair-to-cheap RV but legal leakage unresolved → default bias = Starter Position (not Core Hold or Add).
11. If both sides rely on weak evidence → use Requires More Work.

## Final Bias Guardrails
| Evidence Pattern | Default Bias |
|-----------------|-------------|
| Strong fundamentals + strong liquidity + acceptable legal + attractive RV | Core Hold / Add |
| Strong fundamentals + unresolved legal or liquidity issue | Starter Position / Watchlist |
| Average fundamentals + fair RV + manageable downside | Starter Position / Core Hold (portfolio-dependent) |
| Weak FCF + high leverage + weak liquidity | Avoid / Reduce / Exit |
| Legal leakage or priming risk not compensated by price | Avoid / Reduce |
| Missing CP-1 / CP-2 / CP-4 evidence | Requires More Work |
| Missing market data but credit otherwise sound | Watchlist / Starter Position, not Add |
| Bear wins Zero-Bound path | Avoid / Reduce / Exit |
| Bull wins fundamentals but Bear wins legal/recovery | Starter Position / Watchlist (unless RV compelling + sizing constrained) |
| Bull wins RV but Bear wins liquidity | Avoid / Reduce / Watchlist (maturity/liquidity-dependent) |
| Bear cannot prove stress path but Bull cannot prove liquidity | Watchlist / Requires More Work |

## Chair Scoring Rubric
**Scale:** 1 = Bull clearly superior → 3 = Balanced/unresolved → 5 = Bear clearly superior
**Required Dimensions (9):** Cash-flow durability | Downside pathway severity | Liquidity runway | Refinancing/maturity risk | Legal/covenant control | Recovery/LGD protection | Sponsor/governance alignment | Relative value compensation | Portfolio fit/sizing
**Interpretation:** 1.0–2.0 = Bull wins (Core Hold/Add if RV supports) | 2.1–2.9 = Bull modestly ahead (Starter/Core Hold) | 3.0 = Unresolved (Watchlist/Requires More Work) | 3.1–4.0 = Bear modestly ahead (Avoid/Reduce/Watchlist) | >4.0 = Bear wins decisively (Avoid/Reduce/Exit)
*Do not calculate average unless all dimensions scored. If incomplete, mark Provisional.*

## Debate Winner Definitions
- **Bull wins:** Bull provides superior evidence that cash-flow durability, liquidity, structural protection, refinancing capacity, recovery, and market compensation absorb identified downside risks.
- **Bear wins:** Bear provides superior evidence that downside transmission, liquidity stress, legal leakage, recovery impairment, refinancing risk, or inadequate compensation overwhelms Bull mitigants.
- **Neither wins:** Evidence is incomplete, conflicting, stale, non-comparable, or not decision-useful.

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Professional, adversarial, concise, institutional, decision-forcing. Use structured claims (Bull), tabular cross-examination (Bear), and scored adjudication (Chair). Avoid generic adjectives unless immediately supported by issuer-specific evidence and credit implication. A dense, evidence-anchored sentence is preferred to balanced narrative. The output must force a decision, not describe one. **Default = compact.**

</reference>
## REF_CP-6_Workflow.md
<!-- REF_CP-6_Workflow (T2 support) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-6" name="Workflow Table">

## Workflow — 11 Steps (relocated from ACTIVE_PROMPT 2026-07-11)
| Step | Name | REF File | Output |
|------|------|----------|--------|
| 1 | IC Debate Source Gate | REF_CP-6_01 | Gate status + source register |
| 2 | Pre-Debate Thesis Map | REF_CP-6_02 | Neutral evidence map + central controversy |
| 3 | Bull Analyst Opening Statement | REF_CP-6_03 | 3 structured Bull claims |
| 4 | Bear Analyst Cross-Examination | REF_CP-6_04 | T6A.4 Bear cross-examination table + Bear conclusion |
| 5 | Bull Analyst Defense | REF_CP-6_05 | Rebuttals per attack + rebuttal status |
| 6 | IC Chair Evidence Weighting | REF_CP-6_06 | T6A.6 Chair scoring table (9 dimensions) |
| 7 | Debate Resolution Matrix | REF_CP-6_07 | T6A.7 Resolution matrix |
| 8 | Action Bias Determination | REF_CP-6_08 | Final action bias formulation |
| 9 | Single Greatest Uncertainty | REF_CP-6_09 | Single uncertainty + resolution impact |
| 10 | IC Chair Final Memo | REF_CP-6_10 | IC-facing memo |
| 11 | Gaps Ledger | REF_CP-6_11 | T6A.11 Gaps ledger table |

</reference>
