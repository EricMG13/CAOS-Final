Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-6A_Discipline.md, REF_CP-6A_ExampleOutputPattern.md, REF_CP-6A_ScoringAndConstraints.md, REF_CP-6A_Workflow.md.

Original files, in this bundle: REF_CP-6A_01_PortfolioDebateSourceGate.md, REF_CP-6A_02_PreDebatePortfolioThesisMap.md, REF_CP-6A_03_RVTraderPitch.md, REF_CP-6A_04_ComplianceOfficerAttack.md, REF_CP-6A_05_RVTraderDefense.md, REF_CP-6A_06_CIOEvidenceWeighting.md, REF_CP-6A_07-10_DecisionAndSizing.md, REF_CP-6A_07_AllocationDecisionMatrix.md, REF_CP-6A_08_FinalSizingPosture.md, REF_CP-6A_09_ExactPortfolioConstraint.md, REF_CP-6A_10_CIOFinalMemo.md, REF_CP-6A_11_GapsLedger.md, REF_CP-6A_Discipline.md, REF_CP-6A_ExampleOutputPattern.md, REF_CP-6A_ScoringAndConstraints.md, REF_CP-6A_Workflow.md

## REF_CP-6A_01_PortfolioDebateSourceGate.md
<!-- REF_CP-6A_01 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="01" name="Portfolio Debate Source Gate">
<input>CP-0 registry, all upstream module canonical `.md` handoffs (YAML envelope + canonical H2 headings), CP-6 debate output, source files, market data, portfolio/mandate inputs, exposure reports, optional live REF_CP-6A_Portfolio_Debate_Inputs.xlsx.</input>
<gate>Always executes. This IS the gate check. BLOCKING: If CP-3 is unavailable → Module Status = Blocked, STOP (RV Trader cannot make evidence-led pitch).</gate>

## Instructions
1. Confirm availability of all upstream canonical `.md` handoffs, source materials, market data, portfolio/mandate inputs, and the ability to author one valid Markdown handoff this run.
2. If using the consolidated workbook, validate its Mandate, Exposure Report and Compliance Monitor sheets against portfolio/legal vehicle, measurement basis and as-of. Treat mismatched Test CLO data as schema only. Do not substitute it for CP-3B.
3. Determine gate status:
   - **Full Run:** CP-3, CP-3B, CP-2A, and market data/mandate inputs available.
   - **Ready with Limitations:** CP-3 available but CP-3B, CP-2A, mandate data, exposure data, or other modules missing. Carry each limitation forward.
   - **Blocked:** CP-3 unavailable → STOP.
4. Apply limitation rules:
   - CP-3B missing → mandate fit and sizing cannot be fully tested.
   - CP-2A missing → downside path cannot be fully tested.
   - Current market pricing missing → RV conclusions = [Insufficient Information].
   - Mandate/portfolio constraints missing → exact constraint = [Insufficient Information].
   - Ratings/downgrade trajectory missing → CCC-basket/downgrade arguments = [Insufficient Information].
5. Record files and modules available, missing inputs, and limitations carried forward.

## Output
Gate status: Full Run / Ready with Limitations / Blocked
Source register: modules available, modules missing, limitations carried forward.
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-6A_02_PreDebatePortfolioThesisMap.md
<!-- REF_CP-6A_02 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="02" name="Pre-Debate Portfolio Thesis Map">
<input>All available upstream module outputs; CP-6 debate output; gate status from Step 1.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Build a neutral, evidence-only portfolio thesis map before personas begin.
2. Cover all relevant dimensions: spread/YTW/DM compensation, peer RV, downside pathway, liquidity/refinancing, legal/recovery, CCC-basket/downgrade, concentration/correlation, mandate fit, implementation liquidity.
3. For each dimension: state available evidence, source module, and evidence quality (Strong/Moderate/Weak/Insufficient).
4. Incorporate CP-6 action bias as input context (not as binding constraint).
5. Do NOT take a position — this is the neutral evidence inventory.
6. Conclude with: "Pre-debate, the central portfolio controversy is whether [spread / yield / RV evidence] is sufficient to compensate for [downside / downgrade / concentration / mandate / legal / liquidity risk]."
7. Mark any dimension with missing evidence as [Insufficient Information].

## Output
Narrative: Neutral portfolio evidence map + central portfolio controversy statement.
</step_reference>
## REF_CP-6A_03_RVTraderPitch.md
<!-- REF_CP-6A_03 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="03" name="The RV Trader's Pitch">
<input>Pre-Debate Thesis Map (Step 2); CP-3/CP-3A/CP-3B outputs; market data; upstream module outputs.</input>
<gate>Step 2 complete.</gate>

## Instructions
1. Present exactly **3 RV Trader bullets**. Each must include:
   - **Evidence** (specific source, module, period, market level)
   - **Risk Mechanic** (how compensation or mispricing supports allocation)
   - **Credit Implication** (from 13-value Canonical Credit Implication set, plus portfolio-specific: yield contribution, risk-budget impact)
   - **Monitoring Signal** (what would invalidate the pitch)
2. Bullet ordering (mandatory):
   - **Bullet 1:** Spread / YTW / DM pickup versus peers or rating cohort.
   - **Bullet 2:** Instrument-level mispricing versus seniority, collateral, maturity, liquidity, or recovery.
   - **Bullet 3:** Portfolio implementation despite risk-budget consumption.
3. RV Trader may only argue from source-supported evidence. Prohibited: claiming cheapness without current market data, peer comparison, and downside/recovery evidence.
4. If evidence for a required bullet is unavailable, state [Insufficient Information].

## Output
3 structured RV bullets, each with Evidence, Risk Mechanic, Credit Implication, and Monitoring Signal.
</step_reference>
## REF_CP-6A_04_ComplianceOfficerAttack.md
<!-- REF_CP-6A_04 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="04" name="The Mandate Compliance Officer's Attack">
<input>RV Trader's Pitch (Step 3); mandate documents; exposure reports; portfolio constraints; upstream module outputs.</input>
<gate>Step 3 complete.</gate>

## Instructions
1. Attack the RV Trader's **exact 3 bullets** using a cross-examination table.
2. For each RV bullet attacked, provide:
   - Compliance Counter-Evidence (specific source, metric, constraint)
   - Constraint Vector (which constraint taxonomy item is threatened)
   - Risk Mechanic (how the constraint undermines the RV argument)
   - Credit Implication (from 13-value set, plus portfolio-specific)
   - What Would Prove Compliance Wrong (falsifiability test)
3. Required attack focus areas (test all that apply):
   - Concentration limits (issuer, sector, sponsor, country, currency, rating, instrument type)
   - CCC-basket / downgrade trajectory
   - Correlation / factor-risk budget
   - Liquidity / tradability
   - Downside-budget consumption
   - Maturity wall / refinancing risk / LME / priming
   - Legal / recovery weakness
   - Mandate exclusions / prohibited exposures
4. After the table: write **Compliance Attack Summary** (overall case strength).
5. If mandate data unavailable for a specific attack → state [Insufficient Information].

## Output
T6E.4: `RV Bullet Attacked`|`Compliance Counter-Evidence`|`Constraint Vector`|`Risk Mechanic`|`Credit Implication`|`What Would Prove Compliance Wrong`
+ Compliance Attack Summary narrative.
</step_reference>
## REF_CP-6A_05_RVTraderDefense.md
<!-- REF_CP-6A_05 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="05" name="The RV Trader's Defense">
<input>Compliance Attack (Step 4); original RV pitch (Step 3); CP-3B/mandate inputs; upstream outputs.</input>
<gate>Step 4 complete.</gate>

## Instructions
1. Defend directly against each Compliance attack using only rebuttal evidence tied to the specific attack.
2. For each attack, provide:
   - RV rebuttal evidence (source, metric, mechanic)
   - Why the rebuttal mitigates the identified constraint vector
   - Rebuttal Status: **Fully Rebutted** / **Partially Rebutted** / **Failed** / **Insufficient Information**
3. Propose a specific position-sizing constraint only where supported by CP-3B or mandate inputs.
4. If no mandate inputs exist → propose a provisional posture and label exact size [Insufficient Information].
5. Do not introduce new RV arguments — only rebut existing Compliance attacks.

## Output
Structured rebuttals per Compliance attack, each with rebuttal evidence, mitigation logic, and Rebuttal Status. Proposed sizing constraint (if supported).
</step_reference>
## REF_CP-6A_06_CIOEvidenceWeighting.md
<!-- REF_CP-6A_06 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="06" name="CIO Evidence Weighting">
<input>Steps 3-5 (RV pitch, Compliance attacks, RV defense); all upstream module outputs.</input>
<gate>Step 5 complete.</gate>

## Instructions
1. Score each of the **9 required dimensions** using the Allocation Decision Rubric (1-5 scale):
   - Spread / YTW Benefit
   - Peer Relative Value
   - Downside Pathway Severity
   - Liquidity / Refinancing Risk
   - Legal / Recovery Protection
   - CCC-Basket / Downgrade Risk
   - Concentration / Correlation Risk
   - Mandate Compliance
   - Implementation Liquidity
2. For each dimension: record Score, RV Evidence, Compliance Evidence, and CIO Assessment.
3. Score interpretation: 1 = RV clearly superior | 2 = RV somewhat stronger | 3 = Balanced/unresolved | 4 = Compliance somewhat stronger | 5 = Compliance clearly superior.
4. Do NOT score a dimension without supportable evidence → mark [Insufficient Information].
5. Missing market data blocks fully supported RV conclusion. Missing mandate data blocks fully supported sizing conclusion.
6. Do NOT calculate average unless ALL dimensions have supportable scores. If incomplete → mark Provisional.

## Output
T6E.6: `Dimension`|`Score (1-5)`|`RV Evidence`|`Compliance Evidence`|`CIO Assessment`
</step_reference>
## REF_CP-6A_07-10_DecisionAndSizing.md
# Consolidated companion — REF_CP-6A_07-10_DecisionAndSizing.md

<!-- MERGED_FROM:REF_CP-6A_07_AllocationDecisionMatrix.md sha256=50d54633bde87a43a26283c9120b5adb7646a81015f30135b16d4c0f1d00fef3 -->
## Source: REF_CP-6A_07_AllocationDecisionMatrix.md

<!-- REF_CP-6A_07 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="07" name="Allocation Decision Matrix">
<input>T6E.6 CIO scoring; Steps 3-5 debate record.</input>
<gate>Step 6 complete.</gate>

## Instructions
1. Build the Allocation Decision Matrix resolving each core disputed risk.
2. For each disputed risk: assign a Resolution Label from exactly this set:
   - **RV Sustained** — RV evidence prevails.
   - **Compliance Sustained** — Compliance evidence prevails.
   - **Partially Mitigated** — RV partially rebuts Compliance but residual risk remains.
   - **Unresolved** — Evidence is balanced or incomplete.
   - **Insufficient Information** — Neither side has adequate evidence.
3. For each resolution: state disputed risk, RV position, Compliance position, resolution label, evidence basis, and credit/portfolio implication.
4. Use this to set up the Final Sizing Posture (Step 8).

## Output
T6E.7: `Disputed Risk`|`RV Position`|`Compliance Position`|`Resolution`|`Evidence Basis`|`Credit / Portfolio Implication`
Resolution labels: RV Sustained | Compliance Sustained | Partially Mitigated | Unresolved | Insufficient Information.
</step_reference>

<!-- MERGED_FROM:REF_CP-6A_08_FinalSizingPosture.md sha256=c0229fb6c54a76d071a93b8b4fb6c4c3114f4f65bfc490c1dcbce6bba536b391 -->
## Source: REF_CP-6A_08_FinalSizingPosture.md

<!-- REF_CP-6A_08 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="08" name="Final Sizing Posture">
<input>T6E.6, T6E.7; debate record (Steps 3-7); Posture Guardrails.</input>
<gate>Step 7 complete.</gate>

## Instructions
1. Choose one of the 6 permitted Portfolio Posture values: Include | Avoid | Resize-Reduce | Resize-Increase | Maintain-Hold | Requires More Work.
2. Use the required formulation:
   "Final Sizing Posture: [Posture]. The decision is driven by [top evidence], because [risk mechanic], which implies [portfolio yield / concentration / downgrade / liquidity / recovery / mandate implication]."
3. Cross-check against Posture Guardrails (Active Prompt) — selected posture must be consistent with the evidence pattern.
4. Apply CIO Decision Rules:
   - CP-3 missing → cannot Include.
   - CP-3B/mandate missing → cannot claim sizing within limits.
   - Compliance proves binding breach + RV cannot show headroom → cannot Include.
   - RV proves spread + downside + headroom but legal leakage unresolved → Include (Starter Position) with constraint.
   - Both sides weak → Requires More Work.
5. State which persona won the debate (RV Trader / Compliance Officer / Neither) and why.
6. Include the canonical translation (e.g., "Include maps to Starter Position given constraint").

## Output
Final Sizing Posture formulation (required format). Debate winner statement. Canonical translation.
</step_reference>

<!-- MERGED_FROM:REF_CP-6A_09_ExactPortfolioConstraint.md sha256=ff2bfccc9360da43f768955db8ef56f11329c29c5e397e4fba17321567fbf756 -->
## Source: REF_CP-6A_09_ExactPortfolioConstraint.md

<!-- REF_CP-6A_09 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="09" name="Exact Portfolio Constraint">
<input>Steps 1-8; Portfolio Constraint Taxonomy.</input>
<gate>Step 8 complete.</gate>

## Instructions
1. Identify exactly **one** binding portfolio constraint using the Portfolio Constraint Taxonomy (12-type priority order in Active Prompt).
2. For this constraint, state:
   - **Exact Portfolio Constraint:** [Constraint category from taxonomy]
   - **Evidence:** (specific source, metric, limit)
   - **Risk Mechanic:** (how the constraint caps position size)
   - **Credit / Portfolio Implication:** (what happens if breached or near-breached)
   - **Evidence Needed to Resolve:** (what data would relax or confirm the constraint)
3. If several constraints apply → pick the one that most directly caps size; list others as residual risks in CIO memo.
4. If mandate constraints are unavailable → write [Insufficient Information] and specify the missing mandate/exposure report.
5. Do NOT convert generic credit risk into a portfolio constraint unless it maps to an explicit limit, bucket, or risk-budget metric.

## Output
Exact Portfolio Constraint: structured statement with constraint category, evidence, risk mechanic, credit/portfolio implication, evidence needed to resolve.
</step_reference>

<!-- MERGED_FROM:REF_CP-6A_10_CIOFinalMemo.md sha256=3b0b2552121cf870a3f2e22654c8df1cfb899d458f45839c5e1a3ad13649f972 -->
## Source: REF_CP-6A_10_CIOFinalMemo.md

<!-- REF_CP-6A_10 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="10" name="CIO Final Memo">
<input>Steps 1-9; all debate artifacts.</input>
<gate>Step 9 complete.</gate>

## Instructions
1. Write a concise CIO-facing memo covering exactly these elements:
   - **Decision:** Final Sizing Posture (from Step 8) + canonical translation.
   - **Who won the debate** and **why** (RV Trader / Compliance Officer / Neither).
   - **Most important RV evidence** (single most compelling bullet).
   - **Most important Compliance evidence** (single most compelling attack).
   - **Legal / recovery view** (from CP-4/CP-4A/CP-3A or [Insufficient Information]).
   - **Liquidity / refinancing view** (from CP-2D/CP-3C or [Insufficient Information]).
   - **Relative-value / portfolio view** (from CP-3/CP-3B/market data or [Insufficient Information]).
   - **Sizing constraint** (from Step 9).
   - **Required follow-up before increasing conviction** (specific actions/data needed).
2. Unsupported areas MUST be marked [Insufficient Information].
3. This is a synthesis memo — no new analysis, no new evidence.
4. Keep concise and decision-focused.

## Output
Narrative: CIO Final Memo covering all 9 required elements.
</step_reference>
## REF_CP-6A_07_AllocationDecisionMatrix.md
<!-- REF_CP-6A_07 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="07" name="Allocation Decision Matrix">
<input>T6E.6 CIO scoring; Steps 3-5 debate record.</input>
<gate>Step 6 complete.</gate>

## Instructions
1. Build the Allocation Decision Matrix resolving each core disputed risk.
2. For each disputed risk: assign a Resolution Label from exactly this set:
   - **RV Sustained** — RV evidence prevails.
   - **Compliance Sustained** — Compliance evidence prevails.
   - **Partially Mitigated** — RV partially rebuts Compliance but residual risk remains.
   - **Unresolved** — Evidence is balanced or incomplete.
   - **Insufficient Information** — Neither side has adequate evidence.
3. For each resolution: state disputed risk, RV position, Compliance position, resolution label, evidence basis, and credit/portfolio implication.
4. Use this to set up the Final Sizing Posture (Step 8).

## Output
T6E.7: `Disputed Risk`|`RV Position`|`Compliance Position`|`Resolution`|`Evidence Basis`|`Credit / Portfolio Implication`
Resolution labels: RV Sustained | Compliance Sustained | Partially Mitigated | Unresolved | Insufficient Information.
</step_reference>
## REF_CP-6A_08_FinalSizingPosture.md
<!-- REF_CP-6A_08 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="08" name="Final Sizing Posture">
<input>T6E.6, T6E.7; debate record (Steps 3-7); Posture Guardrails.</input>
<gate>Step 7 complete.</gate>

## Instructions
1. Choose one of the 6 permitted Portfolio Posture values: Include | Avoid | Resize-Reduce | Resize-Increase | Maintain-Hold | Requires More Work.
2. Use the required formulation:
   "Final Sizing Posture: [Posture]. The decision is driven by [top evidence], because [risk mechanic], which implies [portfolio yield / concentration / downgrade / liquidity / recovery / mandate implication]."
3. Cross-check against Posture Guardrails (Active Prompt) — selected posture must be consistent with the evidence pattern.
4. Apply CIO Decision Rules:
   - CP-3 missing → cannot Include.
   - CP-3B/mandate missing → cannot claim sizing within limits.
   - Compliance proves binding breach + RV cannot show headroom → cannot Include.
   - RV proves spread + downside + headroom but legal leakage unresolved → Include (Starter Position) with constraint.
   - Both sides weak → Requires More Work.
5. State which persona won the debate (RV Trader / Compliance Officer / Neither) and why.
6. Include the canonical translation (e.g., "Include maps to Starter Position given constraint").

## Output
Final Sizing Posture formulation (required format). Debate winner statement. Canonical translation.
</step_reference>
## REF_CP-6A_09_ExactPortfolioConstraint.md
<!-- REF_CP-6A_09 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="09" name="Exact Portfolio Constraint">
<input>Steps 1-8; Portfolio Constraint Taxonomy.</input>
<gate>Step 8 complete.</gate>

## Instructions
1. Identify exactly **one** binding portfolio constraint using the Portfolio Constraint Taxonomy (12-type priority order in Active Prompt).
2. For this constraint, state:
   - **Exact Portfolio Constraint:** [Constraint category from taxonomy]
   - **Evidence:** (specific source, metric, limit)
   - **Risk Mechanic:** (how the constraint caps position size)
   - **Credit / Portfolio Implication:** (what happens if breached or near-breached)
   - **Evidence Needed to Resolve:** (what data would relax or confirm the constraint)
3. If several constraints apply → pick the one that most directly caps size; list others as residual risks in CIO memo.
4. If mandate constraints are unavailable → write [Insufficient Information] and specify the missing mandate/exposure report.
5. Do NOT convert generic credit risk into a portfolio constraint unless it maps to an explicit limit, bucket, or risk-budget metric.

## Output
Exact Portfolio Constraint: structured statement with constraint category, evidence, risk mechanic, credit/portfolio implication, evidence needed to resolve.
</step_reference>
## REF_CP-6A_10_CIOFinalMemo.md
<!-- REF_CP-6A_10 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="10" name="CIO Final Memo">
<input>Steps 1-9; all debate artifacts.</input>
<gate>Step 9 complete.</gate>

## Instructions
1. Write a concise CIO-facing memo covering exactly these elements:
   - **Decision:** Final Sizing Posture (from Step 8) + canonical translation.
   - **Who won the debate** and **why** (RV Trader / Compliance Officer / Neither).
   - **Most important RV evidence** (single most compelling bullet).
   - **Most important Compliance evidence** (single most compelling attack).
   - **Legal / recovery view** (from CP-4/CP-4A/CP-3A or [Insufficient Information]).
   - **Liquidity / refinancing view** (from CP-2D/CP-3C or [Insufficient Information]).
   - **Relative-value / portfolio view** (from CP-3/CP-3B/market data or [Insufficient Information]).
   - **Sizing constraint** (from Step 9).
   - **Required follow-up before increasing conviction** (specific actions/data needed).
2. Unsupported areas MUST be marked [Insufficient Information].
3. This is a synthesis memo — no new analysis, no new evidence.
4. Keep concise and decision-focused.

## Output
Narrative: CIO Final Memo covering all 9 required elements.
</step_reference>
## REF_CP-6A_11_GapsLedger.md
<!-- REF_CP-6A_11 (T2) | 2026-06-03 -->
<step_reference module="CP-6A" step="11" name="Gaps Ledger">
<input>Steps 1-10 (cumulative).</input>
<gate>Always executes.</gate>

## Instructions
1. List ALL missing information that affected the debate outcome.
2. For each gap: record Gap ID (CP-6A-GAP-NNN), Gap, Why It Matters (risk mechanic → portfolio implication), Impact on Debate (which persona/step was affected), and Required Follow-Up (specific source or action needed).
3. Include gaps accumulated from all prior steps (missing modules, missing market data, missing mandate data, missing exposure reports, insufficient evidence areas).
4. Sequential Gap IDs: CP-6A-GAP-001, CP-6A-GAP-002, etc.

## Output
T6E.11: `Gap ID`|`Gap`|`Why It Matters`|`Impact on Debate`|`Required Follow-Up`
</step_reference>
## REF_CP-6A_Discipline.md
<!-- REF_CP-6A Discipline (T2 support) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-6A" name="Prohibited Behaviors — Full Binding List">

## Prohibited Behaviors (relocated from ACTIVE_PROMPT 2026-07-11)
1. Do not fabricate market levels, portfolio limits, mandate constraints, ratings, downgrade probability, legal capacity, recovery value, or position size.
2. Do not allow the RV Trader to claim cheapness without current market data, peer comparison, and downside/recovery evidence.
3. Do not allow the Compliance Officer to claim constraint breach without mandate data or exposure report.
4. Do not allow the CIO to split the difference where evidence favors one side.
5. Do not cite a module for a claim that the module does not explicitly support.
6. Missing evidence reduces conviction; it does not automatically prove either side.
7. Do not score a dimension if both sides lack supportable evidence; mark [Insufficient Information].
8. Do not convert generic credit risk into a portfolio constraint unless the risk maps to an explicit limit, bucket, or risk-budget metric.
9. Store unavailable numeric values as null in machine-readable exports, not zero, unless the source explicitly states zero.

</reference>
## REF_CP-6A_ExampleOutputPattern.md
<!-- REF_CP-6A_ExampleOutputPattern.md (T2 Example Library) | 2026-06-10 | Ported from Agent Files: CP-6A__SUPPORT__EXAMPLE_OUTPUT_PATTERN.txt -->


================================================================================
FILE: CP-6A__SUPPORT__EXAMPLE_OUTPUT_PATTERN.txt
MODULE: CP-6A — PortfolioDebateChallenge
STATUS: UPDATED (vNext)
MECHANICAL CHANGES APPLIED: MC-1, MC-2, MC-3, MC-5
GOVERNING CONTRACT: CP_GLOBAL_AGENT_INSTRUCTIONS_v3.2.txt
PURPOSE: Example portfolio debate output patterns for CP-6A.
================================================================================

EXAMPLE_OUTPUT_PATTERN

Purpose: Provide standard formatting templates for CP-6A portfolio debate
output elements. Execution rules and posture definitions are defined in
CP-6A__SUPPORT__ANALYTICAL_STANDARD.txt. Allocation rubric and constraint
taxonomy are defined in CP-6A__SUPPORT__PORTFOLIO_DEBATE_PLAYBOOK.txt.

All examples are illustrative only — do not use as issuer data.

1. Example RV Trader Pitch Format

RV Bullet 1 — Spread Compensation
Evidence: TLB currently trades at E+475 / 96.5 (CP-3, Pricing Run dated
  [Date]), versus BB-rated European HY leveraged loan cohort median of E+400
  (CP-3B, Peer RV Table). 75bp pickup.
Risk Mechanic: Spread premium compensates for single-name concentration and
  below-median liquidity score, while fundamental credit quality (4.8x net
  leverage, CP-2) is in line with cohort median of 4.9x.
Credit Implication: Portfolio yield enhancement of ~8bp on notional allocation
  of [X]bp of AUM. Compensation exceeds downside-adjusted spread loss under
  CP-2A base stress by ~120bp.
Monitoring Signal: Spread compression below E+400 or loss of pickup versus
  cohort median.

2. Example Compliance Officer Attack Format

| RV Bullet Attacked | Compliance Counter-Evidence | Constraint Vector | Risk Mechanic | Credit Implication | What Would Prove Compliance Wrong |
|---|---|---|---|---|---|
| Bullet 1: Spread compensation | Issuer would bring sector exposure to 14.2% vs 15% internal limit (Mandate Report, [Date]); next-largest issuer in sector is 3.5% | Sector concentration limit consumption: 95% of capacity after allocation | Near-limit concentration reduces portfolio flexibility; any sector downgrade or additional allocation would breach | Negative — concentration risk limits ability to add to defensive positions in same sector if opportunities arise | Sector exposure below 12% after allocation or internal limit raised above 15% |

3. Example CIO Scoring Format

| Dimension | Score (1–5) | RV Evidence | Compliance Evidence | CIO Assessment |
|---|---:|---|---|---|
| Spread / YTW Benefit | 2 | 75bp pickup vs cohort; current data (CP-3) | Spread partially explained by lower liquidity score | RV modestly ahead; pickup is real but liquidity discount accounts for ~20bp. Net benefit ~55bp. |
| Concentration Risk | 4 | Below hard limit | 95% of sector capacity consumed | Compliance ahead; near-limit position restricts future flexibility. Binding constraint candidate. |

4. Example Final Sizing Posture Determination

Final Sizing Posture: Include. The decision is driven by 55bp net spread
pickup versus BB cohort (CP-3, Pricing Run dated [Date]) after adjusting for
liquidity discount, because this compensation exceeds CP-2A base-case
downside-adjusted loss and supports portfolio yield targets, which implies
positive portfolio yield contribution with manageable downside budget
consumption. The main factor preventing a higher-conviction recommendation is
sector concentration at 95% of internal limit, which constrains position size
to [X]bp of AUM and eliminates incremental allocation capacity.

5. Example Exact Portfolio Constraint

Exact Portfolio Constraint: Concentration.
Evidence: Sector exposure would reach 14.2% vs 15% internal limit (Mandate
  Report, [Date]).
Risk Mechanic: Near-limit allocation consumes 95% of sector capacity,
  eliminating flexibility to add defensive positions in the same sector.
Credit / Portfolio Implication: Position size must be capped at [X]bp to
  preserve minimum 1% sector headroom; any additional same-sector opportunity
  would require reducing this position first.
Evidence Needed to Resolve: Updated sector exposure report confirming
  post-trade headroom; internal limit review outcome.

PORTFOLIO POSTURE (6-value CP-6A subset):
Include | Avoid | Resize-Reduce | Resize-Increase |
Maintain-Hold | Requires More Work

TRANSLATION TO CANONICAL 9:
Include → Starter Position, Core Hold, Add / Increase
Avoid → Avoid, Exit
Resize-Reduce → Reduce / Trim
Resize-Increase → Add / Increase
Maintain-Hold → Hold Existing Only, Core Hold
Requires More Work → Requires More Work

9-ITEM CONSTRAINT TAXONOMY:
Mandate | Concentration | Rating | Geography | Liquidity |
Correlation | Downside | Legal / Recovery | Data quality

9-DIMENSION ALLOCATION RUBRIC:
Spread | Peers | Downside | Liquidity | Legal protection |
CCC risk | Concentration | Mandate fit | Implementation liquidity

THREE PERSONAS:
RV Trader           — argues inclusion from RV evidence
Compliance Officer  — challenges via constraints
CIO                 — final posture and binding constraint

CANONICAL CREDIT IMPLICATION (13 values):
Positive — Deleveraging | Positive — Margin Expansion |
Positive — Revenue Growth | Positive — Liquidity Improvement |
Positive — Covenant Headroom Expansion | Neutral — Stable |
Negative — Leverage Increase | Negative — Margin Compression |
Negative — Revenue Decline | Negative — Liquidity Deterioration |
Negative — Covenant Erosion | Negative — Refinancing Risk |
Insufficient Information
## REF_CP-6A_ScoringAndConstraints.md
<!-- REF_CP-6A ScoringAndConstraints (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-6A" name="Scoring, Evidence & Constraint Rules">

Load this alongside the CP-6A workflow. It holds the posture definitions, mappings, evidence rules, the 9-dimension allocation rubric, constraint taxonomies, CIO decision rules, and posture guardrails. Authoritative for all CP-6A scoring and posture decisions.

## Portfolio Posture Definitions
- **Include:** RV supports allocation; credit acceptable; mandate/concentration permit sizing; downside manageable; legal/recovery adequate. Maps → Starter Position, Core Hold, or Add/Increase.
- **Avoid:** Spread/yield does not compensate for risk, or fundamental evidence insufficient. Maps → Avoid or Exit.
- **Resize-Reduce:** Risk-reward deteriorated, position consumes too much risk budget, concentration pressure, or downside/legal/liquidity weakened. Maps → Reduce/Trim.
- **Resize-Increase:** Existing exposure can increase; RV attractive, downside controlled, mandate/concentration permit. Maps → Add/Increase.
- **Maintain-Hold:** Current position defensible; no evidence supports increasing or reducing. Maps → Hold Existing Only or Core Hold.
- **Requires More Work:** Missing information prevents decision-useful sizing. Maps → Requires More Work.

## Translation to Canonical 9
Include → Starter Position, Core Hold, Add / Increase | Avoid → Avoid, Exit | Resize-Reduce → Reduce / Trim | Resize-Increase → Add / Increase | Maintain-Hold → Hold Existing Only, Core Hold | Requires More Work → Requires More Work

## Canonical Credit Implication (13 values)
Positive — Deleveraging | Positive — Margin Expansion | Positive — Revenue Growth | Positive — Liquidity Improvement | Positive — Covenant Headroom Expansion | Neutral — Stable | Negative — Leverage Increase | Negative — Margin Compression | Negative — Revenue Decline | Negative — Liquidity Deterioration | Negative — Covenant Erosion | Negative — Refinancing Risk | Insufficient Information

## Evidence Hierarchy (highest → lowest)
1. Current market data (spreads, yields, prices, DM, trading levels) from dated, sourced pricing runs or broker sheets
2. CP-3 / CP-3A / CP-3B RV and portfolio-fit outputs citing underlying market data and peer comparables
3. CP-2A / CP-2D / CP-2E downside, liquidity, and macro outputs with source-supported stress scenarios
4. CP-4 / CP-4A legal / covenant outputs citing governing documents
5. CP-6 IC debate output with evidence-based action bias
6. Portfolio constraints, mandate documents, risk dashboards, exposure reports
7. Analyst interpretation based on sourced facts

## Evidence Quality Labels (4)
- **Strong:** Directly supported by current market data, executed mandate/exposure report, audited financials, or source-backed module output.
- **Moderate:** Supported by company-reported data, prior module analysis with limitations, or stale-but-recent market data.
- **Weak:** Partial, stale, draft, incomplete, or non-comparable evidence.
- **Insufficient:** Required evidence missing, conflicting, or not decision-useful.

## 9-Dimension Allocation Rubric
**Scale:** 1 = RV clearly superior → 3 = Balanced/unresolved → 5 = Compliance clearly superior
**Dimensions:** Spread/YTW Benefit | Peer Relative Value | Downside Pathway Severity | Liquidity/Refinancing Risk | Legal/Recovery Protection | CCC-Basket/Downgrade Risk | Concentration/Correlation Risk | Mandate Compliance | Implementation Liquidity
**Interpretation:** 1.0–2.0 = RV wins (Include: Core Hold/Add if mandate permits) | 2.1–2.9 = RV modestly ahead (Include: Starter Position) | 3.0 = Unresolved (Requires More Work) | 3.1–4.0 = Compliance modestly ahead (Avoid/Resize-Reduce/constrained Include) | >4.0 = Compliance wins decisively (Avoid)
*Do not calculate average unless all dimensions scored. If incomplete, mark Provisional.*

## 9-Item Constraint Taxonomy
Mandate | Concentration | Rating | Geography | Liquidity | Correlation | Downside | Legal / Recovery | Data quality

## Portfolio Constraint Taxonomy (binding-constraint priority order)
1. Explicit mandate prohibition or eligibility failure
2. Hard issuer/borrower concentration limit
3. Hard sector/industry concentration limit
4. Rating bucket / CCC basket / downgrade trajectory limit
5. Country / currency / geography limit
6. Sponsor / ownership / PE concentration limit
7. Instrument type / lien / secured-unsecured / subordinated bucket limit
8. Liquidity / tradability / position exitability limit
9. Correlation / factor-risk budget limit
10. Downside-budget / expected-loss / stress-loss limit
11. Legal / recovery / LME-risk tolerance limit
12. Data-quality limitation preventing decision-useful sizing

## CIO Decision Rules
1. If CP-3 is missing → do not underwrite an Include posture.
2. If CP-3B / mandate data is missing → do not claim sizing is within limits.
3. If CP-2A is missing → do not claim downside is controlled.
4. If current market pricing is missing → do not claim spread is attractive.
5. If portfolio exposure data is missing → do not claim concentration is safe.
6. If Compliance proves binding constraint breach and RV Trader cannot demonstrate headroom → posture cannot be Include.
7. If RV Trader proves attractive spread + controlled downside + mandate headroom but legal leakage unresolved → default = Include (Starter Position) with constraint, not full Include.
8. If both sides rely on weak evidence → use Requires More Work.

## Posture Guardrails
| Evidence Pattern | Default Posture |
|-----------------|----------------|
| Strong RV + controlled downside + acceptable legal + mandate headroom | Include (Core Hold / Add) |
| Strong RV + unresolved legal or liquidity issue | Include (Starter Position) with constraint |
| Average RV + fair fundamentals + manageable downside | Include (Starter Position) or Maintain-Hold |
| Weak RV or spread insufficient for risk | Avoid |
| Concentration / mandate breach or near-breach | Avoid or Resize-Reduce |
| CCC-basket / downgrade risk binding | Avoid or Resize-Reduce |
| Missing CP-3 / market data | Requires More Work |
| Missing mandate / exposure data | Requires More Work |
| Compliance wins implementation liquidity | Avoid or Resize-Reduce |
| RV wins spread but Compliance wins downside | Maintain-Hold or Resize-Reduce |
| Both sides rely on weak evidence | Requires More Work |

## Content Distinctions (relocated from ACTIVE_PROMPT 2026-07-11)
Source Evidence | RV Trader Pitch | Compliance Counter-Evidence | CIO Assessment | Risk Mechanic | Credit Implication | Monitoring Signal | [Insufficient Information]

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Professional, adversarial, concise, institutional, decision-forcing. Use structured bullets (RV Trader), tabular cross-examination (Compliance), and scored adjudication (CIO). Avoid generic adjectives unless immediately supported by issuer-specific evidence and portfolio implication. A dense, evidence-anchored sentence is preferred to balanced narrative. The output must force a sizing decision, not describe one. **Default = compact.**

</reference>
## REF_CP-6A_Workflow.md
<!-- REF_CP-6A Workflow (T2 support) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-6A" name="Workflow Table">

## Workflow — 11 Steps (relocated from ACTIVE_PROMPT 2026-07-11)
| Step | Name | REF File | Output |
|------|------|----------|--------|
| 1 | Portfolio Debate Source Gate | REF_CP-6A_01 | Gate status + source register |
| 2 | Pre-Debate Portfolio Thesis Map | REF_CP-6A_02 | Neutral evidence map + central controversy |
| 3 | The RV Trader's Pitch | REF_CP-6A_03 | 3 structured RV bullets |
| 4 | The Mandate Compliance Officer's Attack | REF_CP-6A_04 | T6E.4 Compliance cross-examination table + attack summary |
| 5 | The RV Trader's Defense | REF_CP-6A_05 | Rebuttals per attack + proposed sizing constraint |
| 6 | CIO Evidence Weighting | REF_CP-6A_06 | T6E.6 CIO scoring table (9 dimensions) |
| 7 | Allocation Decision Matrix | REF_CP-6A_07 | T6E.7 Decision matrix |
| 8 | Final Sizing Posture | REF_CP-6A_08 | Final posture formulation |
| 9 | Exact Portfolio Constraint | REF_CP-6A_09 | Single binding constraint |
| 10 | CIO Final Memo | REF_CP-6A_10 | CIO-facing memo |
| 11 | Gaps Ledger | REF_CP-6A_11 | T6E.11 Gaps ledger table |

</reference>
