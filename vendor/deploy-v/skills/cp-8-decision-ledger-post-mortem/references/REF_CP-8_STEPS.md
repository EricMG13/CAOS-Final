Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-8_Discipline.md, REF_CP-8_StyleAndFormat.md, REF_CP-8_Workflow.md.

Original files, in this bundle: REF_CP-8_01_DecisionIntakeSourceGate.md, REF_CP-8_02_ThesisExpectationCapture.md, REF_CP-8_03_OutcomeTracking.md, REF_CP-8_04_RealizedVsExpectedComparison.md, REF_CP-8_05_Attribution.md, REF_CP-8_06_CalibrationSignal.md, REF_CP-8_07_LessonsTrackRecordRollup.md, REF_CP-8_08_GapsLedger.md, REF_CP-8_09_PostMortemSynthesis.md, REF_CP-8_Discipline.md, REF_CP-8_StyleAndFormat.md, REF_CP-8_Workflow.md

## REF_CP-8_01_DecisionIntakeSourceGate.md
<!-- REF_CP-8_01 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-8" step="01" name="Decision Intake and Source Gate">
<input>The IC decision record: CP-6 IC Action Bias, CP-6A Portfolio Posture, instrument, size, decision date, decision-maker role; the original thesis artifacts (CP-6 final memo, single greatest uncertainty); independent market-pricing, rating-action, default/restructuring and recovery sources. Every event must be re-verified against its cited source.</input>
<gate>Always executes. This IS the gate check. BLOCKING: a dated decision record must exist to attribute against. If none: Module Status = Blocked, STOP — do not reconstruct a thesis after the fact.</gate>

## Instructions
1. Confirm a decision was made and is dated; record action bias, posture, instrument, size, and decision-maker role (role, not individual).
2. Inventory the thesis artifacts available for capture in Step 2.
3. Identify the realized-outcome data sources and the observation window (how much time has elapsed since the decision).
4. Assign Module Status:
   - **Completed:** decision record + thesis + observable outcomes available.
   - **Completed with Limitations:** decision recorded but observation window still open — interim tracking only.
   - **Blocked:** no decision record. Output blocked message and STOP.

## Output
T7.1: Decision record + source/observation-window inventory + Module Status: Completed / Completed with Limitations / Blocked
<!-- Upstream re-anchor (common_rules #10): re-import and verify the specific upstream outputs consumed (CP-6 action bias + final memo and CP-6A posture); restate exact run_id/period. Source and date each realized event independently. If a required upstream value is absent or mismatched, mark [Insufficient Information] and gate the dependent step — do not infer it. -->
</step_reference>
## REF_CP-8_02_ThesisExpectationCapture.md
<!-- REF_CP-8_02 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-8" step="02" name="Thesis and Expectation Capture">
<input>T7.1; CP-6 final memo and single greatest uncertainty; CP-2 / CP-3 expectations; CP-6A posture rationale; named catalysts (CP-2B) and downside pathways (CP-2A) relied on.</input>
<gate>Step 1 complete and not Blocked.</gate>

## Instructions
1. Record the credit thesis **as decided** — do not revise it with hindsight. Capture the single greatest uncertainty as stated at decision time.
2. Record the named catalysts and downside pathways the decision relied on (so Step 5 can tell flagged risk from unflagged).
3. Capture expectations: expected spread / return, expected rating trajectory, expected holding period, and the stated exit triggers.
4. Where the record does not state an expectation, mark [Insufficient Information] — do not infer intent after the fact.

## Output
T7.2: Thesis / Expectation Register — `Thesis`|`Greatest Uncertainty`|`Flagged Catalysts / Downside Paths`|`Expected Spread/Return`|`Expected Rating Path`|`Expected Hold`|`Exit Triggers`|`Evidence ID`
</step_reference>
## REF_CP-8_03_OutcomeTracking.md
<!-- REF_CP-8_03 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-8" step="03" name="Outcome Tracking">
<input>T7.2; independently sourced market pricing, rating actions, default/restructuring records and realized-recovery data.</input>
<gate>Step 2 complete.</gate>

## Instructions
1. Log realized outcomes, each **sourced and dated**: realized spread move, rating migration, default / restructuring incidence, realized recovery, actual holding period, and whether stated exit triggers were honored.
2. Do not fabricate or estimate an outcome — if not yet observable, mark it interim and note the open window.
3. Keep realized facts separate from any interpretation (interpretation is Steps 4–5).
4. Where the recovery is observed, capture it for comparison against the CP-3A estimate in Step 4.

## Output
T7.3: Realized Outcome Log — `Metric`|`Realized Value`|`As-of Date`|`Source`|`Interim / Final`|`Evidence ID`
</step_reference>
## REF_CP-8_04_RealizedVsExpectedComparison.md
<!-- REF_CP-8_04 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-8" step="04" name="Realized-vs-Expected Comparison">
<input>T7.2 (expectations) and T7.3 (realized outcomes).</input>
<gate>Step 3 complete.</gate>

## Instructions
1. For each metric, compute the variance of realized vs expected: spread Δ vs expected, rating migration vs expected path, realized recovery vs CP-3A estimate, holding period vs plan, and exit-trigger discipline (was the stated trigger honored).
2. State direction and magnitude where the data supports it; else [Insufficient Information].
3. Keep this step descriptive — assigning cause is Step 5, not here.

## Output
T7.4: Variance Table — `Metric`|`Expected`|`Realized`|`Variance (direction + magnitude)`|`Confidence`|`Evidence ID`
</step_reference>
## REF_CP-8_05_Attribution.md
<!-- REF_CP-8_05 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-8" step="05" name="Attribution">
<input>T7.2 (thesis + flagged risks) and T7.4 (variances).</input>
<gate>Step 4 complete.</gate>

## Instructions
1. For each material variance, assign one Attribution label: Thesis Confirmed | Flagged Risk Materialized | Unflagged Risk Materialized | Right for Wrong Reason | Premature / Mistimed | Insufficient Information.
2. Separate **process quality** from **outcome**: a downside that the analysis named and sized (in T7.2) and that then materialized is **Flagged Risk Materialized** — sound process, adverse outcome — not a miss.
3. Where the outcome reveals a process gap (Unflagged Risk Materialized), name the originating module so Step 6 can test for a pattern.
4. Do not assign blame to named individuals — attribute to the decision and the reasoning, not the person.

## Output
T7.5: Attribution Table — `Variance`|`Attribution Label`|`Process Sound? (Y/N)`|`Originating Module (if gap)`|`Basis`|`Evidence ID`
</step_reference>
## REF_CP-8_06_CalibrationSignal.md
<!-- REF_CP-8_06 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-8" step="06" name="Calibration Signal (pattern-gated)">
<input>T7.5 attribution across the decision population.</input>
<gate>Step 5 complete AND at least 3 comparable decisions available. With fewer than 3, record the decision but produce NO calibration recommendation.</gate>

## Instructions
1. Scan the attribution population for a **pattern**: the same directional miss recurring across ≥3 comparable decisions (e.g., "CP-3A recovery estimates ran high in 2L industrials across N cases").
2. For each pattern record: target module, the specific prior to adjust, the evidence list (the decisions exhibiting it), and the advisory recommendation.
3. Mark every calibration entry **advisory / non-binding** — upstream modules are not bound by it; it informs, it does not gate.
4. A single-decision miss is recorded in the ledger but does not trigger a calibration recommendation. Separate process gaps from outcome luck before calling a pattern.

## Output
T7.6: Calibration Register (advisory) — `Pattern`|`Target Module`|`Specific Prior`|`Supporting Decisions`|`Advisory Recommendation`
</step_reference>
## REF_CP-8_07_LessonsTrackRecordRollup.md
<!-- REF_CP-8_07 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-8" step="07" name="Lessons and Track-Record Roll-up">
<input>T7.1–T7.6 across the decision population.</input>
<gate>Step 6 complete.</gate>

## Instructions
1. Roll up the track record: hit rate, realized-vs-expected by pathway, by sector, and by sponsor where data supports the cut.
2. Report the attribution distribution, keeping process quality and outcome separate (e.g., share of adverse outcomes that were flagged vs unflagged).
3. Compile reusable, evidence-grounded lessons — each tied to the decisions that support it.
4. No individual blame; report decision-level and process-level findings only.

## Output
T7.7: Track-Record Dashboard — hit rate, realized-vs-expected by cut, attribution distribution, and lessons register.
</step_reference>
## REF_CP-8_08_GapsLedger.md
<!-- REF_CP-8_08 (T2) | PROPOSED | 2026-06-22 -->
<step_reference module="CP-8" step="08" name="Gaps Ledger">
<input>All prior step outputs (T7.1–T7.7); cumulative gaps identified throughout the workflow.</input>
<gate>Always executes.</gate>

## Instructions
1. Compile all gaps from Steps 1–7 into one consolidated ledger.
2. For each gap record: Gap, Missing Item (decision record, thesis statement, realized-outcome source, observation window), Why It Matters, Impact on Output, Required Follow-Up.
3. Flag decisions whose observation window is still open (outcome not yet attributable) for future revisit.
4. Every section marked [Insufficient Information] in Steps 1–7 must have a corresponding gap entry.

## Output
T7.8: Gaps Ledger — `Gap`|`Missing Item`|`Why It Matters`|`Impact on Output`|`Required Follow-Up`
</step_reference>
## REF_CP-8_09_PostMortemSynthesis.md
<!-- REF_CP-8_09 (T2) | 2026-08-02 -->
<step_reference module="CP-8" step="09" name="Post-Mortem Synthesis">
<input>T7.1-T7.8</input>
<gate>Steps 1-8 complete and an original decision record exists. If it does not, remain Blocked.</gate>

## Instructions
1. Compare the sourced outcome with the thesis and expectations recorded contemporaneously in T7.1-T7.2; never reconstruct or improve the original thesis with hindsight.
2. State the canonical attribution label and the evidence supporting it.
3. Judge process quality separately from outcome quality, including whether the realized path was flagged or unflagged.
4. Address timing, sizing and exit-trigger discipline only where the original record and realized evidence support the comparison.
5. State an evidence-grounded lesson only when supported by the record. Calibration advice remains pattern-gated to at least three comparable decisions; otherwise record an observation, not a changed prior.
6. Name the most material unresolved gap or open observation window. Do not form a new credit view, override the committee, assign individual blame or introduce a new fact.

## Output
Narrative `### Decision` final view in `## Analysis` of the canonical Markdown handoff. Render this conclusion before reader tables while retaining T7.1-T7.8 losslessly below the analytical appendix heading.
</step_reference>
## REF_CP-8_Discipline.md
<!-- REF_CP-8_Discipline.md | relocated from CP-8_ACTIVE_PROMPT.md | rev 2026-07-11: SEC8 compression -->

## Prohibited Behaviors — Full Binding List (relocated from ACTIVE_PROMPT 2026-07-11)
1. Do not form, revise, or override a credit view — you record and attribute, you do not analyze the credit.
2. Do not fabricate outcomes, prices, rating actions, recovery figures, or attribution — every realized fact is sourced and dated.
3. Do not score a decision as a "miss" if the flagged downside materialized as disclosed — distinguish process quality from outcome luck.
4. Do not assign blame to named individuals — record the decision-maker role and the decision, not personal judgement.
5. Do not convert a single outcome into a binding model change — calibration feedback is advisory and requires a pattern across decisions.
6. Do not cite a source for a realized outcome the source does not support.
7. If the original decision record or thesis is missing, mark [Insufficient Information] — do not reconstruct intent after the fact.
## REF_CP-8_StyleAndFormat.md
<!-- REF_CP-8_StyleAndFormat.md | relocated from CP-8_ACTIVE_PROMPT.md | rev 2026-07-11: SEC8 compression -->

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Institutional, governance-grade, accountability-first, evidence-led. Prefer ledgers, variance tables, and attribution registers over narrative. Separate process quality from outcome explicitly in every attribution. Use track-record language: thesis confirmed, flagged risk, unflagged risk, attribution, realized vs expected, calibration prior, hit rate. Never editorialize about individuals. Target a concise ledger entry per decision plus a periodic roll-up.
## REF_CP-8_Workflow.md
<!-- REF_CP-8_Workflow.md | relocated from CP-8_ACTIVE_PROMPT.md | rev 2026-07-11: SEC8 compression -->

## Workflow — 9 Steps (relocated from ACTIVE_PROMPT 2026-07-11; final synthesis added 2026-08-02)
| Step | Name | REF File | Output |
|------|------|----------|--------|
| 1 | Decision Intake & Source Gate | REF_CP-8_01 | T7.1 Decision Record + Module Status |
| 2 | Thesis & Expectation Capture | REF_CP-8_02 | T7.2 Thesis / Expectation Register |
| 3 | Outcome Tracking | REF_CP-8_03 | T7.3 Realized Outcome Log |
| 4 | Realized-vs-Expected Comparison | REF_CP-8_04 | T7.4 Variance Table |
| 5 | Attribution | REF_CP-8_05 | T7.5 Attribution Table |
| 6 | Calibration Signal (pattern-gated) | REF_CP-8_06 | T7.6 Calibration Register (advisory) |
| 7 | Lessons & Track-Record Roll-up | REF_CP-8_07 | T7.7 Track-Record Dashboard |
| 8 | Gaps Ledger | REF_CP-8_08 | T7.8 Gaps Ledger |
| 9 | Post-Mortem Synthesis | REF_CP-8_09 | Narrative decision and learning view in canonical Markdown Analysis |
