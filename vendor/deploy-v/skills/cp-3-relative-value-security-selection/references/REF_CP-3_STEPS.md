Consolidated method bundle. Each section retains its reference filename as a heading; the text reflects the current CP-3 workflow.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-3_Discipline.md, REF_CP-3_ScoringAndModes.md, REF_CP-3_Workflow.md.

Original files, in this bundle: REF_CP-3_01_FileGateSourceQuality.md, REF_CP-3_02_FundamentalCreditSummary.md, REF_CP-3_03_IssuerSecurityScorecard.md, REF_CP-3_04_OverrideReview.md, REF_CP-3_05_RelativeValueTable.md, REF_CP-3_06_FundamentalValueMatrix.md, REF_CP-3_07_FinalRanking.md, REF_CP-3_08_SecuritySelectionConclusions.md, REF_CP-3_09_MonitoringTriggers.md, REF_CP-3_10_GapsLedger.md, REF_CP-3_11_FinalCreditRVView.md, REF_CP-3_Discipline.md, REF_CP-3_ScoringAndModes.md, REF_CP-3_Workflow.md

## REF_CP-3_01_FileGateSourceQuality.md
<!-- REF_CP-3_01 (T2) | 2026-06-03 -->
<step_reference module="CP-3" step="01" name="File Gate & Source Quality">
<input>All available source materials: CP-1/CP-1C/CP-2/CP-2D exports, market data, legal review, pricing sheets, mandatory maintained enterprise Sector RV workbook for loan analysis (the local REF_CP-3_Sector_RV.xlsx is a deployment placeholder), CLO lists, prior CP-3 outputs, credit agreements, recovery analysis, trading sheets, internal notes.</input>
<gate>Always executes. This IS the gate check.</gate>

## Instructions
1. Reuse validated matching context. On every loan run, resolve and open the enterprise Sector RV workbook under the maintained-source policy and reading conventions in SKILL.md: always assume it is current and relevant, derive the comparable set from its rows, and ask no freshness, relevance, benchmark or timestamp setup question. Analyse all identified loans for an issuer-level request. Resolve a single-instrument ambiguity from identifiers or borrower/facility/currency/maturity/seniority; identical summary/sector observations count once. Record actual access or missing-cell issues once, and ask only about an unresolved material ambiguity that prevents the affected conclusion.
2. Determine execution mode: CLO Screening / Single-Name RV / Capital-Structure RV / Watchlist Monitoring. Verify required inputs per mode (see Active Prompt — Execution Modes).
3. Catalogue all sources: record source_document_id, source_document_name, source_quality, period, entity_covered, data_supplied, limitation, downstream_use.
4. Record pricing source, metric basis, quote quality and any stated dates. Apply the maintained Sector RV source basis to loans; date-age or missing-date checks do not disqualify that workbook. Evaluate dates normally for other market sources.
5. Assess legal-data quality (credit agreement, indenture, intercreditor, recovery analysis availability).
6. Confirm issuer and security identifiers, resolve conflicts without fuzzy matching, and test structured-export feasibility.
7. Assign Module Status:
   - **Full Run:** Sufficient fundamental + market + legal evidence for complete scoring, RV, and recommendation.
   - **Ready with Limitations:** Partial evidence; proceed but flag gaps (e.g., no market data → RV = Unclear).
   - **Blocked:** Critical sources absent (e.g., no CP-1/CP-2 or equivalent fundamental evidence).
8. If Blocked, STOP after the blocked message.

## Output
T3.1: `source_document_id`|`source_document_name`|`source_quality`|`period`|`entity_covered`|`data_supplied`|`limitation`|`downstream_use`
+ Module Status: Full Run / Ready with Limitations / Blocked
+ Execution Mode: CLO Screening / Single-Name RV / Capital-Structure RV / Watchlist Monitoring
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-3_02_FundamentalCreditSummary.md
<!-- REF_CP-3_02 (T2) | 2026-06-03 -->
<step_reference module="CP-3" step="02" name="Fundamental Credit Summary">
<input>T3.1 Source Register; CP-1/CP-2 family outputs or equivalent fundamental evidence.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Summarize the issuer's fundamental credit profile from available source materials.
2. Cover: business risk, financial risk, FCF durability, leverage, liquidity, refinancing risk, governance/financial policy, key downside path, and most important missing datapoints.
3. Use Evidence → Risk Mechanic → Credit Implication chain for every material conclusion.
4. Do not perform new fundamental analysis — summarize and translate CP-1/CP-2 findings into credit implications relevant for scoring and RV.
5. Highlight any fundamental conclusions that are Insufficient Information and their impact on downstream scoring.

## Output
Narrative: issuer fundamental credit profile covering business risk, financial risk, FCF durability, leverage, liquidity, refinancing risk, governance, key downside path, and missing datapoints.
</step_reference>
## REF_CP-3_03_IssuerSecurityScorecard.md
<!-- REF_CP-3_03 (T2) | 2026-06-03 -->
<step_reference module="CP-3" step="03" name="Issuer / Security Scorecard">
<input>T3.1, Step 2 narrative; fundamental evidence from CP-1/CP-2 family.</input>
<gate>Step 2 complete.</gate>

## Instructions
1. Build the scorecard using the Score Direction and rubric in the Active Prompt. Factor weights are **mode-dependent**: use weights supplied by the portfolio mandate, sector framework, or explicit user instruction. No system default weights exist. If weights are absent, present supported unweighted factor assessments, mark the composite Not Scorable, and record the missing framework once. Continue loan RV and security selection; ask for weights only if a weighted numeric score is specifically required. Do not invent weights or silently substitute equal weighting.
2. Score Direction: 1 = Conservative/creditor-favorable/low-risk → 5 = Aggressive/creditor-unfavorable/high-risk.
3. For each supported factor: assign Raw Score (1–5) and a Confidence tag (High/Medium/Low/Not Assessable). Apply Weight and calculate Weighted Score only when the governing weights are available.
4. For each score: provide Evidence, Risk Mechanic, and Credit Implication.
5. If factor evidence is materially incomplete, do NOT assign a precise score — use range, Not Scorable, or Not Assessable.
6. When factor evidence and governing weights support a composite, calculate the weighted sum and map it to Credit Tier (1.0–1.9 = High Quality, 2.0–2.9 = Acceptable, 3.0–3.7 = Stretched, 3.8–5.0 = Weak). Otherwise retain Not Scorable and continue the supported qualitative/RV analysis.

## Output
T3.3: `Category`|`Factor`|`Weight`|`Raw Score 1–5`|`Weighted Score`|`Confidence`|`Evidence`|`Risk Mechanic`|`Credit Implication`
+ Composite Score + Credit Tier
</step_reference>
## REF_CP-3_04_OverrideReview.md
<!-- REF_CP-3_04 (T2) | 2026-06-03 -->
<step_reference module="CP-3" step="04" name="Override Review">
<input>T3.3 Scorecard; hard-risk override rules.</input>
<gate>Step 3 complete.</gate>

## Instructions
1. Apply hard-risk overrides where justified by evidence.
2. For each override considered: log Override Type, Trigger Evidence, Score Cap / Penalty applied, Revised Composite Score, and Explanation.
3. If no override applies, state: "No hard-risk override triggered."
4. Do not use scoring overrides to force a desired ranking.
5. Revised composite score (if any) feeds into Steps 5–7.

## Output
T3.4: `Override Type`|`Trigger Evidence`|`Score Cap / Penalty`|`Revised Composite Score`|`Explanation`
OR "No hard-risk override triggered."
</step_reference>
## REF_CP-3_05_RelativeValueTable.md
<!-- REF_CP-3_05 (T2) | 2026-06-03 -->
<step_reference module="CP-3" step="05" name="Relative Value Table">
<input>T3.1 (market data quality), T3.3/T3.4 (scorecard + overrides); pricing/spread/yield/DM evidence; comparable instruments.</input>
<gate>Steps 3–4 complete. If no market data available, label all securities as Unclear and proceed.</gate>

## Instructions
1. Build the RV table for each available security/instrument. For loans, always use Sector RV borrower/instrument rows and relevant sector loan peers, citing sheet/row locations. Also use the sheet’s available Index Statistics and Sector Ratings Average sections as labelled benchmark context. Keep aggregate/index rows out of the individual-loan peer sample. Other sources supplement this required reference.
2. For each: record market level (spread/yield/DM/price), market-data date, pricing source, quote quality, relevant comps (with seniority/maturity/currency/metric basis disclosed), market compensation vs. risk assessment, and RV Label (Cheap / Fair / Rich / Unclear).
3. RV conclusions require current market evidence under CP-3's maintained-source policy. If absent, RV = Unclear.
4. Do not state current relative value without current market evidence under CP-3's maintained-source policy.
5. Do not compare instruments unless seniority, maturity, currency, metric basis, and pricing-source limitations are disclosed.
6. Identify liquidity/quote-quality limitations for each security.

## Output
T3.5: `Security`|`Market Level`|`Market Date`|`Source`|`Quote Quality`|`Comps`|`Seniority / Security`|`Compensation vs. Risk`|`RV Label`
</step_reference>
## REF_CP-3_06_FundamentalValueMatrix.md
<!-- REF_CP-3_06 (T2) | 2026-06-03 -->
<step_reference module="CP-3" step="06" name="Fundamental Value Matrix">
<input>T3.3/T3.4 (scorecard + overrides), T3.5 (RV table); structural/recovery evidence where available.</input>
<gate>Step 5 complete.</gate>

## Instructions
1. Build the Fundamental Value Matrix separating four dimensions:
   - Fundamental View (from scorecard/credit summary)
   - Relative-Value View (from RV table)
   - Structural / Recovery View (from legal/recovery evidence)
   - Final Matrix Bucket (synthesis)
2. For each security/issuer: record Fundamental View, Relative-Value View, Structural / Recovery View, Final Matrix Bucket, Rationale and an Evidence ID resolving to the scorecard/source support.
3. Maintain strict separation between fundamental quality and market compensation.
4. A wide spread alone cannot override weak fundamentals into a positive matrix bucket.

## Output
T3.6: `Security / Issuer`|`Fundamental View`|`Relative-Value View`|`Structural / Recovery View`|`Final Matrix Bucket`|`Rationale`|`Evidence ID`
</step_reference>
## REF_CP-3_07_FinalRanking.md
<!-- REF_CP-3_07 (T2) | 2026-06-03 -->
<step_reference module="CP-3" step="07" name="Final Ranking">
<input>T3.3/T3.4 (scorecard + overrides), T3.5 (RV table), T3.6 (matrix).</input>
<gate>Step 6 complete. If evidence is insufficient, avoid forced ranking — use Requires More Work.</gate>

## Instructions
1. Build the final ranking table where evidence supports ranking.
2. If only one issuer in scope, rank available securities or state single-name only.
3. If evidence is insufficient, avoid forced ranking and use Requires More Work.
4. Do not classify a weak credit as Preferred solely because spread is wide.
5. Do not classify a strong credit as Avoid solely because spread is tight unless compensation is clearly inadequate.

## Output
T3.7: `Rank`|`Issuer`|`Security / Tranche`|`Composite Score /100`|`Normalized /5.0`|`Credit Tier`|`Fundamental View`|`Relative Value View`|`Final Recommendation`|`Strongest Attribute`|`Weakest Attribute`|`Key Credit Issue`|`Monitoring Trigger`|`Evidence ID`|`Countervailing Evidence`

Each ranking row retains its Evidence ID and the strongest supported contrary case, including what would make that contrary case win, as required by SKILL.md.
</step_reference>
## REF_CP-3_08_SecuritySelectionConclusions.md
<!-- REF_CP-3_08 (T2) | 2026-06-03 -->
<step_reference module="CP-3" step="08" name="Security Selection Conclusions">
<input>T3.5–T3.7; all scoring, RV, matrix, and ranking evidence.</input>
<gate>Step 7 complete.</gate>

## Instructions
1. For each issuer/security, provide:
   - Final Credit View: Preferred / Neutral / Avoid / Requires More Work
   - Fundamental conclusion
   - Relative-value conclusion
   - Structural / recovery conclusion (where data exists)
   - Main upside to debt
   - Main downside risk to debt
   - Key reason code
   - Monitoring trigger
2. Use required formulation:
   "[Security] is [Preferred / Neutral / Avoid / Requires More Work] because [fundamental view], while [relative-value view], and [structural / liquidity / refinancing consideration]. The main upside to debt is [upside]. The main downside risk is [downside]. Monitoring should focus on [trigger]."
3. A security may be Preferred only when fundamentals, structure, downside protection, liquidity, refinancing profile, and market compensation are collectively supportive.

## Output
Narrative: per-security conclusion using required formulation.
</step_reference>
## REF_CP-3_09_MonitoringTriggers.md
<!-- REF_CP-3_09 (T2) | 2026-06-03 -->
<step_reference module="CP-3" step="09" name="Monitoring Triggers">
<input>T3.3–T3.8; all scoring, RV, recommendation, and risk evidence.</input>
<gate>Step 8 complete.</gate>

## Instructions
1. Generate specific, observable monitoring triggers for each security/issuer.
2. For each trigger: record Threshold / Signal, Why It Matters, Credit / RV Impact, and Evidence ID.
3. If hard thresholds are unsupported, state: "Quantitative threshold not available in provided materials."
4. Triggers should be actionable: tied to observable data points that would change the recommendation.

## Output
T3.9: `Trigger`|`Threshold / Signal`|`Why It Matters`|`Credit / RV Impact`|`Evidence ID`
</step_reference>
## REF_CP-3_10_GapsLedger.md
<!-- REF_CP-3_10 (T2) | 2026-06-03 -->
<step_reference module="CP-3" step="10" name="Gaps Ledger">
<input>All prior step outputs (T3.1–T3.9); cumulative gaps identified throughout workflow.</input>
<gate>Always executes.</gate>

## Instructions
1. Compile all gaps identified across Steps 1–9 into a consolidated ledger.
2. For each gap: record Missing Data, Why It Matters, Impact on Output (which step/table/score/recommendation is affected), and Required Follow-Up.
3. Cover gaps in: market data (pricing, spreads, yields, DM), comparable instruments, legal/recovery data (credit agreements, indentures, intercreditor, collateral), covenant terms, financial data (leverage, FCF, liquidity), rating-agency views, trading technicals, ownership/concentration data, portfolio constraints.
4. Flag gaps that prevent scoring, RV classification, ranking, or recommendation assignment.

## Output
T3.10: `Gap`|`Missing Data`|`Why It Matters`|`Impact on Output`|`Required Follow-Up`
</step_reference>
## REF_CP-3_11_FinalCreditRVView.md
<!-- REF_CP-3_11 (T2) | 2026-06-03 -->
<step_reference module="CP-3" step="11" name="Final Credit / RV View">
<input>All prior step outputs (T3.1–T3.10); all scoring, RV, recommendation, and gap evidence.</input>
<gate>Always executes. Synthesis only — no new data.</gate>

## Instructions
1. Write a committee-ready narrative synthesis answering:
   - What is the fundamental credit view?
   - What is the relative-value view?
   - Which security is Preferred, Neutral, Avoided, or Requires More Work?
   - What is the main upside to debt?
   - What is the main downside risk to debt?
   - What is the top monitoring trigger?
   - What additional information is needed for a more definitive decision?
2. Use required formulation:
   "Overall, [Issuer / Security] is [Preferred / Neutral / Avoid / Requires More Work]. Fundamentally, [Issuer] presents a [high-quality / acceptable / stretched / weak / not scorable] credit profile because [key evidence]. Relative value appears [Cheap / Fair / Rich / Unclear] because [market evidence versus credit risk]. The final security-selection conclusion is [recommendation] because [fundamental view + value view + structural / liquidity / refinancing view]. The main upside to debt is [upside]. The main downside risk is [risk]. Further analysis would require [missing data]."
3. Do not introduce new data, new calculations, or new assessments — synthesize only.
4. End with one of:
   - "CP-3 Completed. Recommendation: [Label]. RV: [Label]."
   - "CP-3 Completed with Limitations. Recommendation: [Label]. RV: [Label]. Key Gaps: [List]."
   - "CP-3 Blocked. Missing Required Inputs: [List]."

## Output
Narrative synthesis (no table). Module completion statement with Recommendation and RV labels.
</step_reference>
## REF_CP-3_Discipline.md
<!-- REF_CP-3 Discipline (T2 support) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-3" name="Prohibited Behaviors — Full Binding List">

## Prohibited Behaviors (relocated from ACTIVE_PROMPT 2026-07-11) — full binding list
1. Do not fabricate spreads, prices, yields, discount margins, ratings, maturity profiles, leverage, liquidity, covenant terms, recovery assumptions, ownership details, customer concentration, market share, rating-agency views, or trading technicals.
2. Do not assign a formal rating unless explicitly instructed.
3. Do not force a value label, ranking, score, or recommendation when evidence is weak.
4. Do not use promotional equity-style language, TAM-based upside framing, valuation-multiple upside, or consultant-style strategic commentary unless directly tied to debt mechanics.
5. Do not use generic adjectives (market-leading, robust, strong, resilient, diversified, ample, cheap, rich) unless immediately supported by issuer-specific evidence, current market data under the maintained-source policy, and credit implication.
6. Do not assign a precise composite score if factor evidence is missing — use range, Not Scorable, or Not Assessable.
7. Do not state current relative value without current market evidence under CP-3's maintained-source policy.
8. Do not compare instruments unless seniority, maturity, currency, metric basis, and pricing-source limitations are disclosed.
9. Do not use scoring overrides to force a desired ranking.
10. Do not classify a weak credit as Preferred solely because spread is wide.
11. Do not classify a strong credit as Avoid solely because spread is tight unless compensation is clearly inadequate or better alternatives exist.
12. Do not cite a source for a claim not explicitly supported by that source.
13. Do not convert missing information into either a positive or adverse conclusion.

</reference>
## REF_CP-3_ScoringAndModes.md
<!-- REF_CP-3 ScoringAndModes (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-3" name="Execution Modes, Scoring & RV/Recommendation Labels">

Authoritative for CP-3 mode selection (Step 1) and scoring/labelling (Steps 3–8). Load alongside the CP-3 workflow. The RV / Security-Selection / Portfolio discipline rules stay in the ACTIVE_PROMPT.

## Execution Modes

Every mode involving loans uses the maintained Sector RV workbook. The current-source basis in SKILL.md satisfies the loan-market date requirement in all modes.

### CLO Screening Mode
Required: CP-1 export or equivalent; CP-2 export or equivalent; CLO list or investable security universe; risk scorecard or equivalent; Sector RV workbook for loans, with other peer/market data as supplemental evidence.

### Single-Name RV Mode
Required: CP-1 or equivalent; CP-2 or equivalent; capital structure and instrument terms; current or dated pricing/spread/yield/DM evidence; at least one comparable instrument or explicit statement that comparables are unavailable.

### Capital-Structure RV Mode
Required: instrument stack; seniority/collateral/covenant/maturity details; market data by instrument if available; legal review or limitation flag where not available.

### Watchlist Monitoring Mode
Required: prior CP-3 output or prior security-selection rationale; latest pricing/spread/yield/DM where available; new credit, legal, liquidity, catalyst, technical, or market information.

## Score Direction
Raw scores from 1 to 5:
- **1** = Conservative / creditor-favorable / low-risk
- **3** = Market-standard / acceptable / mid-risk
- **5** = Aggressive / creditor-unfavorable / high-risk

## Score Confidence Tags
**High:** Source-supported financial, legal, and market evidence available.
**Medium:** Core evidence available but one important area incomplete.
**Low:** Market data, legal data, or financial data materially incomplete.
**Not Assessable:** Scoring would require fabrication or unsupported assumptions.

## Credit Tier Mapping
| Score Range | Credit Tier |
|-------------|-------------|
| 1.0–1.9 | High Quality |
| 2.0–2.9 | Acceptable |
| 3.0–3.7 | Stretched |
| 3.8–5.0 | Weak |
| N/A | Not Scorable |

## Relative-Value Labels
**Cheap:** Compensation appears high relative to sourced fundamental risk, structural position, maturity, liquidity, and comparables.
**Fair:** Compensation appears broadly aligned with sourced risk and comparables.
**Rich:** Compensation appears insufficient for sourced fundamental, structural, maturity, liquidity, or downside risks.
**Unclear:** Market data, comparables, quote quality, or security-level information are insufficient.

## Recommendation Labels
**Preferred:** Fundamentals, structure, downside protection, liquidity, refinancing profile, and relative value are collectively supportive.
**Neutral:** Risk-adjusted compensation is adequate but not compelling, or positives and negatives are balanced.
**Avoid:** Credit risk, structural risk, valuation richness, liquidity risk, refinancing risk, technical risk, or governance risk is not adequately compensated.
**Requires More Work:** Missing information prevents a decision-useful conclusion.

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Professional, neutral, concise, institutional, ratings-style, creditor-first, evidence-led, committee-ready, portfolio-decision oriented, and relative-value disciplined. Prefer clean Excel-ready Markdown tables, detailed paragraphs, and dense bullets. Use creditor language: spread compensation, discount margin, yield, price, maturity wall, refinancing capacity, recovery, LGD, PD, liquidity runway, FCF durability, covenant headroom, collateral, priming risk, technicals, security selection, monitoring posture, committee readiness. Target 1–5 pages per issuer, scaled to source quality and issuer complexity.

</reference>
## REF_CP-3_Workflow.md
<!-- REF_CP-3 Workflow (T2 support) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-3" name="Workflow Table">

## Workflow (relocated from ACTIVE_PROMPT 2026-07-11) — 11 Steps
| Step | Name | REF File | Output |
|------|------|----------|--------|
| 1 | File Gate & Source Quality | REF_CP-3_01 | T3.1 Source Register + Module Status + Execution Mode |
| 2 | Fundamental Credit Summary | REF_CP-3_02 | Narrative: issuer fundamental credit profile |
| 3 | Issuer / Security Scorecard | REF_CP-3_03 | T3.3 Scorecard Table |
| 4 | Override Review | REF_CP-3_04 | T3.4 Override Log + revised composite |
| 5 | Relative Value Table | REF_CP-3_05 | T3.5 RV Table |
| 6 | Fundamental Value Matrix | REF_CP-3_06 | T3.6 Fundamental Value Matrix |
| 7 | Final Ranking | REF_CP-3_07 | T3.7 Final Ranking Table |
| 8 | Security Selection Conclusions | REF_CP-3_08 | Narrative: per-security conclusions |
| 9 | Monitoring Triggers | REF_CP-3_09 | T3.9 Monitoring Triggers Table |
| 10 | Gaps Ledger | REF_CP-3_10 | T3.10 Gaps Ledger |
| 11 | Final Credit / RV View | REF_CP-3_11 | Narrative synthesis |

</reference>
