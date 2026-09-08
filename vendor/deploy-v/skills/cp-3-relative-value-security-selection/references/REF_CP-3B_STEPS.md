Consolidated method bundle. Each section retains its reference filename as a heading; the text reflects the current CP-3 workflow.

This is an absorbed phase of CP-3. References to CP-3/CP-3A outputs mean the source-grounded results already produced in the current run, or a matching validated handoff when available. No intermediate export, separate invocation or user approval is required. Apply SKILL.md’s maintained Sector RV loan-reference policy here, including its current-source basis and date treatment. Append this phase’s registers to the single CP-3 handoff.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-3B_Discipline.md, REF_CP-3B_FitAndActionLabels.md, REF_CP-3B_Workflow.md.

Original files, in this bundle: REF_CP-3B_01_PortfolioInputGate.md, REF_CP-3B_02_PortfolioFitRegister.md, REF_CP-3B_03_PositionSizingPostureTable.md, REF_CP-3B_04_RiskBudgetFlags.md, REF_CP-3B_05_ConcentrationCorrelationRegister.md, REF_CP-3B_06_LiquidityImplementationAssessment.md, REF_CP-3B_07_DownsideBudgetRecoverySensitivity.md, REF_CP-3B_08_MonitoringAddTrimTriggers.md, REF_CP-3B_09_GapsLedger.md, REF_CP-3B_10_OverallPortfolioFitView.md, REF_CP-3B_Discipline.md, REF_CP-3B_FitAndActionLabels.md, REF_CP-3B_Workflow.md

## REF_CP-3B_01_PortfolioInputGate.md
<!-- REF_CP-3B_01 (T2) | 2026-06-03 -->
<step_reference module="CP-3B" step="01" name="Portfolio Input Gate">
<input>All available source materials: CP-3 output, issuer/security identifiers, mandate constraints, optional live REF_CP-3B_Portfolio_Constraints.xlsx, current holdings/exposure, concentration data, liquidity/trading constraints, downside/recovery/legal/LME inputs, portfolio reports, PM notes, committee notes.</input>
<gate>Always executes after the current run’s CP-3 security-selection and CP-3A preference stages. Their source-grounded results, including documented limitations, satisfy workflow progress without a separate file. If the preceding stage has not run, complete it in this run. Do not retry a completed stage merely because evidence is missing; withhold dependent conclusions and continue supported work.</gate>

## Instructions
1. Reuse the current run’s source-grounded security-selection and instrument-preference conclusions. Do not request an intermediate CP-3/CP-3A export.
2. Validate any constraints workbook against portfolio identity, basis and as-of. The bundled Test CLO workbook is schema-only for every other portfolio; its legacy CP-3C source label does not change current module ownership.
3. Catalogue all sources: source_document_id, source_document_name, source_quality, period/date, entity_covered, data_supplied, limitation, downstream_use.
4. Check each required input: CP-3 output, issuer/security identifiers, mandate constraints, current holdings/exposure, concentration data, liquidity/trading constraints, downside/recovery/legal/LME inputs.
5. For each: record Available/Missing, Source, Limitation, Portfolio Impact.
6. Use mandate-specific analysis when portfolio inputs are available; otherwise provide generic portfolio-fit logic, retain the gaps and avoid a numeric sizing recommendation. Missing portfolio inputs do not halt supported loan RV or require repeated setup questions.
7. Assign Module Status: Completed / Completed with Limitations / Blocked.
8. Flag stale, draft, incomplete, unaudited, management-adjusted, pro forma, or conflicting sources.

## Output
T3C.1: `Input`|`Available / Missing`|`Source`|`Limitation`|`Portfolio Impact`
+ Module Status: Completed / Completed with Limitations / Blocked
+ Output Mode: Mandate-Specific / Generic Portfolio-Fit Logic
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-3B_02_PortfolioFitRegister.md
<!-- REF_CP-3B_02 (T2) | 2026-06-03 -->
<step_reference module="CP-3B" step="02" name="Portfolio Fit Register">
<input>T3C.1 Portfolio Input Gate; CP-3 output, CP-3A instrument preference, CP-3C refinancing/LME, CP-2A downside, CP-2D liquidity, CP-4/CP-4A legal/covenant, mandate guidelines.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Assess whether the issuer/security fits the relevant strategy, mandate, and portfolio role.
2. Assign Fit Category: Mandate fit / RV fit / Liquidity fit / Risk-budget fit / Not fit / Not assessable.
3. Identify portfolio role where supported: yield carry, spread duration, convexity, defensive senior secured, catalyst, RV switch, recovery-sensitive upside, watchlist/monitoring only.
4. For each issuer/security: provide Evidence, Risk Mechanic, Why It Fits / Does Not Fit, Constraints/Notes, and Source Trace.
5. Incorporate where available: mandate eligibility, RV support (CP-3), instrument support (CP-3A), downside support (CP-2A/CP-2D), legal/covenant support (CP-4/CP-4A), refinancing/LME support (CP-3C).

## Output
T3C.2: `Name / Instrument`|`Fit Category`|`Evidence`|`Risk Mechanic`|`Why It Fits / Does Not Fit`|`Constraints / Notes`|`Source Trace`
</step_reference>
## REF_CP-3B_03_PositionSizingPostureTable.md
<!-- REF_CP-3B_03 (T2) | 2026-06-03 -->
<step_reference module="CP-3B" step="03" name="Position Sizing Posture Table">
<input>T3C.1, T3C.2; SUPPORT__Position_Sizing_and_Risk_Budget.txt rules.</input>
<gate>Step 2 complete.</gate>

## Instructions
1. Assign sizing posture per issuer/security using Sizing Posture Taxonomy: Avoid / Watchlist / Starter Position / Core Hold / Hold Existing Only / Reduce / Trim / Requires More Work.
2. Apply Minimum Evidence for Core: all 7 items required. If any missing, Core may not be assigned unless labelled as hypothetical framework-only view.
3. Apply Starter Conditions: CP-3 favourable/conditional, downside identifiable, mandate data not clearly adverse, liquidity allows exit.
4. Sizing posture must be explicitly linked to evidence via Evidence → Risk Mechanic → Portfolio Implication.
5. If portfolio constraints are missing, do not express a numeric size unless user provided one.
6. If a proposed size is provided, test it against concentration, liquidity, downside, and mandate constraints.
7. Assign Confidence as the derived band label (High / Medium / Low / Insufficient Information) per the score→band map in `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`; the module-level primary measure is the numeric Confidence Score (0–100).

## Output
T3C.3: `Name / Instrument`|`Sizing Posture`|`Evidence`|`Reason`|`Key Risk`|`Implementation Note`|`Confidence`|`Source Trace`
</step_reference>
## REF_CP-3B_04_RiskBudgetFlags.md
<!-- REF_CP-3B_04 (T2) | 2026-06-03 -->
<step_reference module="CP-3B" step="04" name="Risk Budget Flags">
<input>T3C.1–T3C.3; portfolio reports, concentration data, liquidity data, downside/recovery inputs.</input>
<gate>Step 3 complete.</gate>

## Instructions
1. Identify risk-budget flags and portfolio impact across all relevant dimensions.
2. Cover where source-supported: concentration, correlation, liquidity, downside budget, sector exposure, rating bucket, capital-structure exposure, maturity wall, refinancing/LME, legal/covenant, and recovery/LGD risk.
3. For each flag: provide Evidence, Risk Mechanic, Why It Matters (credit/portfolio relevance), Caution Level (High/Medium/Low/Not Assessable), Portfolio Impact, and Source Trace.
4. Use Evidence → Risk Mechanic → Portfolio/Credit Implication chain.

## Output
T3C.4: `Flag`|`Evidence`|`Risk Mechanic`|`Why It Matters`|`Caution Level`|`Portfolio Impact`|`Source Trace`
</step_reference>
## REF_CP-3B_05_ConcentrationCorrelationRegister.md
<!-- REF_CP-3B_05 (T2) | 2026-06-03 -->
<step_reference module="CP-3B" step="05" name="Concentration and Correlation Register">
<input>T3C.1 (holdings/exposure data), T3C.3 (sizing posture); concentration reports, mandate limits.</input>
<gate>Step 4 complete. If concentration data unavailable, populate with null and flag in Gaps Ledger.</gate>

## Instructions
1. Assess concentration and correlation across 7 exposure dimensions:
   - Issuer / group
   - Sector / subsector
   - Sponsor / ownership
   - Rating bucket
   - Maturity year / wall
   - Capital-structure layer
   - Correlated holdings / common factor
2. For each dimension: record Current Exposure, Proposed/Pro Forma Exposure, Limit/Capacity, Evidence Status (Source Fact / Calculation / Not Provided), Risk Mechanic, Portfolio Implication, and Source Trace.
3. Use null for unavailable numeric values — do not leave unexplained blanks.
4. If proposed size is provided, calculate pro forma exposure where data supports.
5. Flag dimensions where concentration exceeds or approaches limits.

## Output
T3C.5: `Exposure Dimension`|`Current Exposure`|`Proposed / Pro Forma Exposure`|`Limit / Capacity`|`Evidence Status`|`Risk Mechanic`|`Portfolio Implication`|`Source Trace`
</step_reference>
## REF_CP-3B_06_LiquidityImplementationAssessment.md
<!-- REF_CP-3B_06 (T2) | 2026-06-03 -->
<step_reference module="CP-3B" step="06" name="Liquidity and Implementation Assessment">
<input>T3C.3 (sizing posture), T3C.5 (concentration); market data, trading colour, dealer evidence.</input>
<gate>Step 5 complete.</gate>

## Instructions
1. Assess liquidity and implementation feasibility across 4 dimensions:
   - Trading depth / bid-ask / dealer colour
   - Settlement / minimum size / operational constraint
   - Exit route under stress
   - Ability to add / trim
2. For each: provide Evidence, Risk Mechanic, Implementation Consequence, Constraint/Action, and Source Trace.
3. If liquidity is missing, state that exit risk is not assessable.
4. If bid/ask, market depth, settlement, or minimum denomination is adverse, reduce sizing posture or require more work.
5. Do not assume a loan or bond can be scaled without price impact unless supported by trading evidence.

## Output
T3C.6: `Liquidity / Implementation Factor`|`Evidence`|`Risk Mechanic`|`Implementation Consequence`|`Constraint / Action`|`Source Trace`
</step_reference>
## REF_CP-3B_07_DownsideBudgetRecoverySensitivity.md
<!-- REF_CP-3B_07 (T2) | 2026-06-03 -->
<step_reference module="CP-3B" step="07" name="Downside Budget and Recovery Sensitivity">
<input>T3C.3 (sizing posture), T3C.5 (concentration); CP-2A downside pathways, CP-2D liquidity bridge, CP-3A recovery sensitivity, CP-4/CP-4A legal findings.</input>
<gate>Step 6 complete.</gate>

## Instructions
1. Assess downside budget and recovery sensitivity across 4 scenario dimensions:
   - Price downside
   - Recovery / LGD sensitivity
   - Refinancing / maturity-wall downside
   - Legal / priming / leakage downside
2. For each: record Input Basis, Formula/Method, Result/Directional View, Portfolio Loss/Risk-Budget Implication, Status (Calculated / Directional Only / Not Calculable), and Source Trace.
3. Connect expected downside to portfolio impact: price downside, loss at proposed size, liquidity under stress, covenant/LME/priming/leakage scenarios, refinancing failure, rating migration and forced-seller risk.
4. If data supports calculation, use formula. If directional only, state clearly. If not calculable, state why.

## Output
T3C.7: `Downside Scenario / Driver`|`Input Basis`|`Formula / Method`|`Result / Directional View`|`Portfolio Loss / Risk-Budget Implication`|`Status`|`Source Trace`
</step_reference>
## REF_CP-3B_08_MonitoringAddTrimTriggers.md
<!-- REF_CP-3B_08 (T2) | 2026-06-03 -->
<step_reference module="CP-3B" step="08" name="Monitoring and Add / Trim Triggers">
<input>T3C.3–T3C.7; all sizing, risk, concentration, liquidity, and downside evidence.</input>
<gate>Step 7 complete.</gate>

## Instructions
1. Generate specific, observable monitoring triggers linked to portfolio actions.
2. For each trigger: record Trigger ID (CP-3B-MON-NNN), Indicator, Leading/Lagging classification, Threshold or Qualitative Signal, Linked Risk Flag (from T3C.4), Portfolio Action (Add/Hold/Trim/Avoid/Escalate), Source Trace, and Limitation.
3. Use quantitative thresholds only if source-supported.
4. If thresholds are unsupported, use observable qualitative signals and state: "Quantitative threshold not available in provided materials."
5. Triggers must be actionable: tied to observable data points that would change sizing posture.

## Output
T3C.8: `Trigger ID`|`Indicator`|`Leading / Lagging`|`Threshold or Qualitative Signal`|`Linked Risk Flag`|`Portfolio Action`|`Source Trace`|`Limitation`
</step_reference>
## REF_CP-3B_09_GapsLedger.md
<!-- REF_CP-3B_09 (T2) | 2026-06-03 -->
<step_reference module="CP-3B" step="09" name="Gaps Ledger">
<input>All prior step outputs (T3C.1–T3C.8); cumulative gaps identified throughout workflow.</input>
<gate>Always executes.</gate>

## Instructions
1. Compile all gaps identified across Steps 1–8 into a consolidated ledger.
2. For each gap: record Gap ID (CP-3B-GAP-NNN), Missing Data, Why It Matters (portfolio relevance), Affected Sizing/Risk Budget/Trigger, Consequence for Confidence (High/Medium/Low impact), and Required Follow-Up Source.
3. Cover gaps in: mandate fit, current exposure, pro forma exposure, concentration capacity, sector/rating limits, liquidity, market date, downside loss budget, recovery, legal/covenant constraints, refinancing/LME risk, and implementation feasibility.
4. Flag gaps that prevent sizing posture assignment or force Requires More Work.

## Output
T3C.9: `Gap ID`|`Missing Data`|`Why It Matters`|`Affected Sizing / Risk Budget / Trigger`|`Consequence for Confidence`|`Required Follow-Up Source`
</step_reference>
## REF_CP-3B_10_OverallPortfolioFitView.md
<!-- REF_CP-3B_10 (T2) | 2026-06-03 -->
<step_reference module="CP-3B" step="10" name="Overall Portfolio Fit View">
<input>All prior step outputs (T3C.1–T3C.9); all sizing, risk, concentration, liquidity, downside, and gap evidence.</input>
<gate>Always executes. Synthesis only — no new data.</gate>

## Instructions
1. Write a committee-ready narrative synthesis using required formulation:
   "Overall, [Issuer / Security] is [Avoid / Watchlist / Starter Position / Core Hold / Hold Existing Only / Reduce / Trim / Requires More Work] for portfolio implementation. The sizing posture is driven by [evidence], which matters because [risk mechanic] and implies [portfolio impact]. Further analysis requires [missing constraints / data]."
2. Cover: sizing posture and justification, key risk-budget constraint, concentration/correlation highlights, liquidity/implementation feasibility, downside/recovery sensitivity, top monitoring trigger, and critical gaps.
3. Do not introduce new data, new calculations, or new assessments — synthesize only from Steps 1–9.
4. End with one of:
   - "CP-3B Completed. Sizing Posture: [Posture]."
   - "CP-3B Completed with Limitations. Sizing Posture: [Posture / Requires More Work]. Missing Inputs: [List]."
   - "CP-3B Blocked. Missing Required Inputs: [List]."
   Canonical `[IssuerID]_CP-3B_[YYYYMMDD].md` is produced and validated every run per `../../../CANON_SHARED.md § CP_AB_EXPORT_SPEC.md`, using exact front-matter `issuer_id` and `analysis_date` without hyphens. Do not create alternate analytical exports.

## Output
Narrative synthesis (no table). Module completion statement with Sizing Posture.
</step_reference>
## REF_CP-3B_Discipline.md
<!-- REF_CP-3B Discipline (Full Prohibited Behaviors List) | 2026-07-11 | relocated from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-3B" name="Prohibited Behaviors — Full Binding List">

## Prohibited Behaviors (relocated from ACTIVE_PROMPT 2026-07-11)
1. Do not invent mandate limits, fund constraints, liquidity capacity, or current holdings.
2. Do not recommend a size that conflicts with missing or unavailable mandate data.
3. Do not treat credit attractiveness as sufficient for Core Hold sizing without portfolio capacity, liquidity, concentration, and downside-budget support.
4. Do not provide legal advice, formal ratings, or investment advice outside the provided evidence package.
5. Do not cite a source for a claim not explicitly supported by that source.
6. Do not fabricate sizing; mark [Insufficient Information] and log the gap.
7. Do not use generic buy/sell language unless user explicitly requests trade-language conversion.
8. Do not use generic "good credit" or "attractive yield" statements without portfolio mechanics.
9. Do not use promotional language, equity-upside framing, or unsupported sizing conviction.
10. Do not assume a loan or bond can be scaled without price impact unless supported by trading evidence.
11. Do not express a numeric size unless user provided one and portfolio constraints are available.
12. Do not hide limitations in footnotes — state them next to the affected conclusion.

</reference>
## REF_CP-3B_FitAndActionLabels.md
<!-- REF_CP-3B FitAndActionLabels (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-3B" name="Fit Categories, Portfolio Roles & Action Language">

Authoritative label sets for CP-3B portfolio fit and implementation (Steps 2–8). Load alongside the CP-3B workflow.

## Fit Categories
Mandate fit | RV fit | Liquidity fit | Risk-budget fit | Not fit | Not assessable

## Portfolio Roles
Yield carry | Spread duration | Convexity | Defensive senior secured exposure | Catalyst | Relative-value switch | Recovery-sensitive upside | Watchlist / monitoring only

## Portfolio-Action Language
Add/initiate (source-supported + mandate-compatible) | Hold/maintain (acceptable but adding not supported) | Trim/reduce (adverse concentration/liquidity/downside/legal/RV/mandate) | Avoid (unacceptable risk/reward/legal/liquidity/mandate fit) | Monitor (action depends on trigger resolution)

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Institutional-grade, evidence-led, portfolio-action oriented, explicit about uncertainty and missing constraints. Focus on risk budget, downside, liquidity, concentration, and implementation feasibility. Tables must include source trace or evidence status; where values are missing, write "Not provided" or null — do not leave unexplained blanks. Use Evidence → Risk Mechanic → Portfolio/Credit Implication chains. Target concise but decision-useful output: 1–3 paragraph executive view, complete tables for committee review.

## Content Distinctions (relocated from ACTIVE_PROMPT 2026-07-11)
Required separation of: Source Fact | Calculation | Analyst Inference | Portfolio Implication | Gap

## Minimum Evidence for Core Sizing (relocated from ACTIVE_PROMPT 2026-07-11)
Core sizing requires source-supported evidence for ALL of:
1. CP-3 recommendation and current market context
2. Mandate eligibility
3. Current and pro forma exposure capacity
4. Liquidity and exit feasibility
5. Downside loss budget / recovery sensitivity
6. Concentration and correlation with existing holdings
7. Legal/covenant/refinancing/maturity-wall risk not inconsistent with larger exposure

If any item is missing, Core may not be assigned unless output clearly states the label is a hypothetical framework-only view, not an executable sizing recommendation.

## Confidence Discipline (relocated from ACTIVE_PROMPT 2026-07-11)
The module's primary confidence measure is the numeric **Confidence Score (0–100)** computed per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md` (evidence quality × coverage × source-gate multiplier, less QA penalties; recomputed/audited by CP-5A). Report the score and its derived **band** in the Audit Summary at the top of Markdown handoff and in the `confidence_score` / `confidence_band` envelope fields of canonical Markdown. The band is a derived label only (per the score→band map): **High ≥ 80 · Medium 60–79 · Low 40–59 · Insufficient Information < 40**. Substantive drivers for CP-3B:
- **High score band:** source-supported CP-3 conclusion, security data, market date, mandate/portfolio exposure, and liquidity/concentration evidence.
- **Medium score band:** CP-3 and security evidence exist but some portfolio constraints are incomplete.
- **Low score band:** portfolio data, mandate limits, or liquidity evidence are materially incomplete.
- **Insufficient Information band:** required evidence is missing or the file gate blocks execution.

Do not invent a different formula; reference `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`. The per-row `Confidence` column in T3C.3 remains a derived band label for that sizing conclusion.

</reference>
## REF_CP-3B_Workflow.md
<!-- REF_CP-3B Workflow (10-Step Table) | 2026-07-11 | relocated from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-3B" name="Workflow — 10 Steps">

## Workflow — 10 Steps (relocated from ACTIVE_PROMPT 2026-07-11)
| Step | Name | REF File | Output |
|------|------|----------|--------|
| 1 | Portfolio Input Gate | REF_CP-3B_01 | T3C.1 Portfolio Input Gate + Module Status |
| 2 | Portfolio Fit Register | REF_CP-3B_02 | T3C.2 Portfolio Fit Register |
| 3 | Position Sizing Posture Table | REF_CP-3B_03 | T3C.3 Position Sizing Posture Table |
| 4 | Risk Budget Flags | REF_CP-3B_04 | T3C.4 Risk Budget Flags |
| 5 | Concentration and Correlation Register | REF_CP-3B_05 | T3C.5 Concentration and Correlation Register |
| 6 | Liquidity and Implementation Assessment | REF_CP-3B_06 | T3C.6 Liquidity and Implementation Assessment |
| 7 | Downside Budget and Recovery Sensitivity | REF_CP-3B_07 | T3C.7 Downside Budget and Recovery Sensitivity |
| 8 | Monitoring and Add / Trim Triggers | REF_CP-3B_08 | T3C.8 Monitoring Triggers |
| 9 | Gaps Ledger | REF_CP-3B_09 | T3C.9 Gaps Ledger |
| 10 | Overall Portfolio Fit View | REF_CP-3B_10 | Narrative synthesis |

</reference>
