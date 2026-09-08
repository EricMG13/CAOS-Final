Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-4_AggressivenessRubric.md, REF_CP-4_EDGARCovenantSourceMap.md, REF_CP-4_ExampleOutputPattern.md, REF_CP-4_Workflow.md.

Original files, in this bundle: REF_CP-4_01-02_LegalSourceGate.md, REF_CP-4_01_LegalFileGateSourceQuality.md, REF_CP-4_02_ControllingDocumentsSourceAuthority.md, REF_CP-4_03_CovenantFeatureRegister.md, REF_CP-4_04_EBITDADefinitionsRatioMechanics.md, REF_CP-4_05_DebtIncurrenceIncrementalMFN.md, REF_CP-4_06_LeakageRPInvestmentsAssetTransfers.md, REF_CP-4_07_CollateralGuaranteesStructuralSubordination.md, REF_CP-4_08_EventsOfDefaultRemediesAmendmentRisk.md, REF_CP-4_09_PDversusLGDRecoveryTranslation.md, REF_CP-4_10_MarketNormCovenantReviewComparison.md, REF_CP-4_11_CovenantAggressivenessScore.md, REF_CP-4_12_RedFlagsMonitoringTriggers.md, REF_CP-4_13_GapsLedger.md, REF_CP-4_14_OverallLegalCreditView.md, REF_CP-4_AggressivenessRubric.md, REF_CP-4_EDGARCovenantSourceMap.md, REF_CP-4_ExampleOutputPattern.md, REF_CP-4_Workflow.md

## REF_CP-4_01-02_LegalSourceGate.md
# Consolidated companion — REF_CP-4_01-02_LegalSourceGate.md

<!-- MERGED_FROM:REF_CP-4_01_LegalFileGateSourceQuality.md sha256=6a0f607a790803633be6daadd3f44d45a0b9de1aefdd6878112c01e9ea63a64d -->
## Source: REF_CP-4_01_LegalFileGateSourceQuality.md

<!-- REF_CP-4_01 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="01" name="Legal File Gate and Source Quality">
<input>All available source materials: executed credit agreements, indentures, intercreditor agreements, amendments, waivers, compliance certificates, term sheets, offering memoranda, lender presentations, covenant-review reports, rating agency legal commentary, debt schedules, guarantor/collateral/subsidiary schedules, security documents, regulatory filings, CP-1 financial foundation, CP-1A transaction summary, CP-3C refinancing/LME output.</input>
<gate>Always executes. This IS the gate check. BLOCKING: At least one executed governing legal document (credit agreement or indenture) must be available. If none: Module Status = Blocked, STOP.</gate>

## Instructions
1. Confirm execution mode and legal-document availability.
2. Assess document status for each source: executed / draft / posting-version / unsigned / incomplete / stale.
3. Rank source authority using 6-rank hierarchy (executed CA/indenture > ICA > compliance certs > OM > third-party review > lender pres/term sheet).
4. Identify completeness limitations: missing amendments, schedules, exhibits, compliance certificates.
5. Note governing law and jurisdiction.
6. Check covenant-review report availability.
7. Verify structured-export readiness.
8. Assign Module Status:
   - **Completed:** Executed governing doc(s) + current financial inputs.
   - **Completed with Limitations:** Executed governing doc(s) but missing supplements. State each limitation and downstream impact.
   - **Blocked:** No executed governing document. Output blocked message and STOP.
9. If CP-1 financials missing: headroom/capacity calculations limited — flag.
10. If CP-3C missing: LME legal-capacity overlay incomplete — flag.

> **Free acquisition lane (added 2026-06-15):** Before assigning **Blocked** for a
> missing governing document, attempt the free SEC EDGAR lane in
> `REF_CP-4_EDGARCovenantSourceMap` (credit agreements = Ex-10.x; indentures /
> supplements = Ex-4.x; covenant "Description of Notes" = S-4 / 424B). A
> **pulled-and-vaulted** EDGAR exhibit is an executed primary source (Authority
> Rank 1–4); an **unfetched** full-text hit is `external · unverified` and does
> **not** satisfy the BLOCKING gate until the exhibit is ingested.

## Output
T4.1: Source gate register (document inventory + quality assessment + authority rank + limitations)
+ Module Status: Completed / Completed with Limitations / Blocked
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>

<!-- MERGED_FROM:REF_CP-4_02_ControllingDocumentsSourceAuthority.md sha256=3a3d6564caba322adc6d4640c25effb700a06df7fcd5bb04e4484c131448ec72 -->
## Source: REF_CP-4_02_ControllingDocumentsSourceAuthority.md

<!-- REF_CP-4_02 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="02" name="Controlling Documents and Source Authority">
<input>T4.1 Source Gate output; all legal documents identified in Step 1.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Build a controlling-document register for all legal sources.
2. For each document: record Authority Rank (1–6), Document name, Document Type, Version/Date, Status (executed/draft/posting/etc.), Governing Role, Credit Relevance, and Evidence ID.
3. Explain which documents control the analysis and which are summaries, marketing materials, posting versions, or third-party interpretations.
4. If source conflicts exist between authority levels, note the conflict and state which document governs.
5. If key documents are missing (e.g., no ICA, no compliance cert), flag the gap and downstream impact.

## Output
T4.2: `Authority Rank`|`Document`|`Document Type`|`Version / Date`|`Status`|`Governing Role`|`Credit Relevance`|`Evidence ID`
</step_reference>
## REF_CP-4_01_LegalFileGateSourceQuality.md
<!-- REF_CP-4_01 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="01" name="Legal File Gate and Source Quality">
<input>All available source materials: executed credit agreements, indentures, intercreditor agreements, amendments, waivers, compliance certificates, term sheets, offering memoranda, lender presentations, covenant-review reports, rating agency legal commentary, debt schedules, guarantor/collateral/subsidiary schedules, security documents, regulatory filings, CP-1 financial foundation, CP-1A transaction summary, CP-3C refinancing/LME output.</input>
<gate>Always executes. This IS the gate check. BLOCKING: At least one executed governing legal document (credit agreement or indenture) must be available. If none: Module Status = Blocked, STOP.</gate>

## Instructions
1. Confirm execution mode and legal-document availability.
2. Assess document status for each source: executed / draft / posting-version / unsigned / incomplete / stale.
3. Rank source authority using 6-rank hierarchy (executed CA/indenture > ICA > compliance certs > OM > third-party review > lender pres/term sheet).
4. Identify completeness limitations: missing amendments, schedules, exhibits, compliance certificates.
5. Note governing law and jurisdiction.
6. Check covenant-review report availability.
7. Verify structured-export readiness.
8. Assign Module Status:
   - **Completed:** Executed governing doc(s) + current financial inputs.
   - **Completed with Limitations:** Executed governing doc(s) but missing supplements. State each limitation and downstream impact.
   - **Blocked:** No executed governing document. Output blocked message and STOP.
9. If CP-1 financials missing: headroom/capacity calculations limited — flag.
10. If CP-3C missing: LME legal-capacity overlay incomplete — flag.

> **Free acquisition lane (added 2026-06-15):** Before assigning **Blocked** for a
> missing governing document, attempt the free SEC EDGAR lane in
> `REF_CP-4_EDGARCovenantSourceMap` (credit agreements = Ex-10.x; indentures /
> supplements = Ex-4.x; covenant "Description of Notes" = S-4 / 424B). A
> **pulled-and-vaulted** EDGAR exhibit is an executed primary source (Authority
> Rank 1–4); an **unfetched** full-text hit is `external · unverified` and does
> **not** satisfy the BLOCKING gate until the exhibit is ingested.

## Output
T4.1: Source gate register (document inventory + quality assessment + authority rank + limitations)
+ Module Status: Completed / Completed with Limitations / Blocked
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-4_02_ControllingDocumentsSourceAuthority.md
<!-- REF_CP-4_02 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="02" name="Controlling Documents and Source Authority">
<input>T4.1 Source Gate output; all legal documents identified in Step 1.</input>
<gate>Step 1 complete; Module Status ≠ Blocked.</gate>

## Instructions
1. Build a controlling-document register for all legal sources.
2. For each document: record Authority Rank (1–6), Document name, Document Type, Version/Date, Status (executed/draft/posting/etc.), Governing Role, Credit Relevance, and Evidence ID.
3. Explain which documents control the analysis and which are summaries, marketing materials, posting versions, or third-party interpretations.
4. If source conflicts exist between authority levels, note the conflict and state which document governs.
5. If key documents are missing (e.g., no ICA, no compliance cert), flag the gap and downstream impact.

## Output
T4.2: `Authority Rank`|`Document`|`Document Type`|`Version / Date`|`Status`|`Governing Role`|`Credit Relevance`|`Evidence ID`
</step_reference>
## REF_CP-4_03_CovenantFeatureRegister.md
<!-- REF_CP-4_03 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="03" name="Covenant Feature Register">
<input>T4.1, T4.2; controlling legal documents.</input>
<gate>Step 2 complete.</gate>

## Instructions
1. Build a comprehensive covenant feature register covering (where available): maintenance covenants, incurrence covenants, EBITDA add-backs, MFN, leakage baskets, restricted payments, investments, asset transfers, guarantor coverage, collateral flexibility, debt incurrence, asset sales, unrestricted subsidiaries, Events of Default, and amendment/waiver provisions.
2. For each feature: record Topic, Provision Summary, Source/Clause (exact clause/section reference), Risk Mechanic, Credit Implication (8-value label), Market Norm Assessment (only if supported by comparative source), and Evidence ID.
3. Use Standard Finding Format where provision-level detail warrants it.
4. This register is the foundation for Steps 4–8 deep-dive analysis.

## Output
T4.3: `Topic`|`Provision Summary`|`Source / Clause`|`Risk Mechanic`|`Credit Implication`|`Market Norm Assessment`|`Evidence ID`
</step_reference>
## REF_CP-4_04_EBITDADefinitionsRatioMechanics.md
<!-- REF_CP-4_04 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="04" name="EBITDA, Definitions, and Ratio Mechanics">
<input>T4.2, T4.3; EBITDA/definition provisions from controlling documents; CP-1 financial foundation.</input>
<gate>Step 3 complete.</gate>

## Instructions
1. Analyze definitions that affect debt capacity, covenant compliance, leverage reporting, and refinancing capacity.
2. Cover: Consolidated EBITDA / Adjusted EBITDA, synergies, cost savings, pro forma adjustments, caps, time limits, documentation requirements, cash netting, acquisitions/dispositions, unrestricted subsidiaries, and covenant EBITDA vs. reported EBITDA.
3. For each material definition: apply Evidence → Risk Mechanic → Credit Implication chain.
4. Use Standard Finding Format: Provision → Source → Summary → Risk Mechanic → PD Effect → LGD/Recovery Effect → Monitoring Implication → Credit Implication → Confidence → Evidence ID.
5. Flag EBITDA add-back provisions that inflate denominator and expand grower baskets.
6. Flag where covenant EBITDA materially diverges from reported EBITDA.

## Output
Provision-level analysis using Standard Finding Format. Each material definition produces a finding with full analytical chain. Narrative synthesis of how definitions collectively affect creditor position.
</step_reference>
## REF_CP-4_05_DebtIncurrenceIncrementalMFN.md
<!-- REF_CP-4_05 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="05" name="Debt Incurrence, Incremental Facilities, and MFN">
<input>T4.2, T4.3, Step 4 definition analysis; debt capacity provisions from controlling documents.</input>
<gate>Step 4 complete.</gate>

## Instructions
1. Assess: ratio debt, free-and-clear baskets, grower baskets, incremental facilities, incremental equivalent debt, acquisition debt, refinancing debt, delayed-draw mechanics, pari/junior/unsecured debt capacity, MFN protection, MFN sunset, and priming risk.
2. For each material provision: apply Standard Finding Format with full Evidence → Risk Mechanic → Credit Implication chain.
3. Assess total debt incurrence capacity across all baskets (fixed + grower + ratio + incremental).
4. Flag priming-enabling provisions: pari secured incremental, drop-down capacity, non-pro-rata exchange mechanics.
5. Flag MFN sunset dates and repricing risk for existing lenders.
6. Flag grower basket tied to EBITDA (capacity expands with add-back-inflated EBITDA).

## Output
Provision-level analysis using Standard Finding Format. Each material debt/lien capacity provision produces a finding with full analytical chain. Summary of total incurrence capacity and priming risk.
</step_reference>
## REF_CP-4_06_LeakageRPInvestmentsAssetTransfers.md
<!-- REF_CP-4_06 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="06" name="Leakage, Restricted Payments, Investments, and Asset Transfers">
<input>T4.2, T4.3, Steps 4–5 analysis; leakage/RP/investment provisions from controlling documents.</input>
<gate>Step 5 complete.</gate>

## Instructions
1. Assess: restricted payment baskets, dividends, sponsor distributions, junior debt payments, builder baskets, available amount, investments, asset sales, unrestricted subsidiaries, IP/material asset transfers, non-guarantor transfers, reinvestment rights, and prepayment requirements.
2. For each material provision: apply Standard Finding Format.
3. Flag USub designation capacity and asset-transfer mechanics (J.Crew-style IP transfer, drop-down, non-guarantor transfer).
4. Flag value leakage paths: RP + investment + asset transfer combined capacity.
5. Assess builder basket / available amount mechanics and cumulative capacity.
6. Translate leakage capacity into recovery/LGD implications.

## Output
Provision-level analysis using Standard Finding Format. Each material leakage provision produces a finding with full analytical chain. Summary of total leakage capacity and value-leakage risk to creditors.
</step_reference>
## REF_CP-4_07_CollateralGuaranteesStructuralSubordination.md
<!-- REF_CP-4_07 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="07" name="Collateral, Guarantees, and Structural Subordination">
<input>T4.2, T4.3, Steps 4–6 analysis; collateral/guarantor provisions, ICA, security documents, subsidiary schedules.</input>
<gate>Step 6 complete.</gate>

## Instructions
1. Assess: secured/unsecured status, first-lien/second-lien/subordinated ranking, collateral package, guarantor coverage, excluded subsidiaries, material subsidiaries, foreign subsidiary limitations, local-law limitations, restricted/unrestricted group, intercreditor provisions, release mechanics, and structural subordination.
2. For each material provision: apply Standard Finding Format.
3. Flag collateral release mechanics that permit material reduction without full lender consent.
4. Flag excluded/non-guarantor subsidiaries holding material assets or EBITDA.
5. Flag structural subordination risk from non-guarantor entities.
6. Translate collateral/guarantor coverage into LGD/recovery implications.

## Output
Provision-level analysis using Standard Finding Format. Each material collateral/guarantor provision produces a finding. Summary of recovery position by creditor class.
</step_reference>
## REF_CP-4_08_EventsOfDefaultRemediesAmendmentRisk.md
<!-- REF_CP-4_08 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="08" name="Events of Default, Remedies, and Amendment Risk">
<input>T4.2, T4.3, Steps 4–7 analysis; EoD, remedy, and amendment provisions from controlling documents.</input>
<gate>Step 7 complete.</gate>

## Instructions
1. Assess: payment defaults, covenant defaults, cross-default/cross-acceleration, insolvency defaults, judgment defaults, change of control, cure periods, equity cure, acceleration mechanics, lender thresholds, amendment/waiver provisions, sacred rights, collateral release amendments, and class voting.
2. For each material provision: apply Standard Finding Format.
3. Flag weak lender-control mechanics: low amendment thresholds, narrow sacred rights, broad waiver flexibility.
4. Flag equity cure mechanics and limitations.
5. Flag amendment provisions that permit covenant weakening without full consent.
6. Translate EoD/amendment mechanics into PD and creditor-control implications.

## Output
Provision-level analysis using Standard Finding Format. Each material EoD/amendment provision produces a finding. Summary of lender control position and amendment risk.
</step_reference>
## REF_CP-4_09_PDversusLGDRecoveryTranslation.md
<!-- REF_CP-4_09 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="09" name="PD versus LGD / Recovery Translation">
<input>All provision-level analysis from Steps 3–8.</input>
<gate>Step 8 complete.</gate>

## Instructions
1. Translate key legal provisions into separate default-risk (PD) and recovery-risk (LGD) effects.
2. For each material legal topic: record Legal Topic, Supported Fact (provision-level), Risk Mechanic, PD Effect, LGD/Recovery Effect, Monitoring Implication, and Evidence ID.
3. Ensure every entry clearly distinguishes PD channel (covenant pressure, liquidity, refinancing, operating flexibility) from LGD channel (collateral, claim priority, guarantor coverage, structural subordination, value leakage).
4. Prioritize provisions with the highest combined PD + LGD severity.
5. This table is a key downstream input for CP-4A (covenant capacity) and CP-6 (debate evidence).

## Output
T4.9: `Legal Topic`|`Supported Fact`|`Risk Mechanic`|`PD Effect`|`LGD / Recovery Effect`|`Monitoring Implication`|`Evidence ID`
</step_reference>
## REF_CP-4_10_MarketNormCovenantReviewComparison.md
<!-- REF_CP-4_10 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="10" name="Market Norm and Covenant Review Comparison">
<input>T4.3, Steps 4–9 analysis; third-party covenant-review reports, market-norm sources (if available).</input>
<gate>Step 9 complete. CONDITIONAL: Run only where a comparative source exists. If no market comparison or Covenant Review Report is available, state: "Market-norm and third-party covenant-review comparison is limited because no supported comparative source was provided."</gate>

## Instructions
1. If comparative source exists: compare issuer provisions against market norms or third-party covenant-review findings.
2. For each comparable topic: record Topic, Issuer Provision, Market/Third-Party Reference, Relative Assessment, Agreement/Discrepancy, Credit Implication (8-value label), and Evidence ID.
3. Do not force market-norm commentary if no comparative source exists (Prohibited Behavior #4).
4. Where discrepancies exist between issuer provisions and market norms, translate into credit implications.
5. Note where third-party assessment differs from CP-4's own analysis and explain.

## Output
T4.10: `Topic`|`Issuer Provision`|`Market / Third-Party Reference`|`Relative Assessment`|`Agreement / Discrepancy`|`Credit Implication`|`Evidence ID`
(Or: conditional skip statement if no comparative source.)
</step_reference>
## REF_CP-4_11_CovenantAggressivenessScore.md
<!-- REF_CP-4_11 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="11" name="Covenant Aggressiveness Score">
<input>All provision-level analysis from Steps 3–10; Covenant Aggressiveness Rubric.</input>
<gate>Step 10 complete (or conditional skip for Step 10).</gate>

## Instructions
1. Score covenant aggressiveness using the 1–5 Rubric across 7 Scoring Areas:
   - Maintenance covenant architecture
   - Debt / lien incurrence capacity
   - RP / investment / leakage capacity
   - EBITDA definitions and add-back flexibility
   - Collateral / guarantor protection
   - Amendment / control mechanics
   - Overall (composite)
2. For each area: record Area, Score (1–5), Evidence, Risk Mechanic, Credit Implication, Confidence, and Evidence ID.
3. Apply Scoring Rules:
   - Do not score without provision-level evidence → [Not Scorable].
   - Overall is NOT a simple average — weight toward highest creditor-adverse severity.
   - If fewer than 3 areas scorable → overall = [Not Scorable] or [Provisional].
4. Provide: Covenant Aggressiveness Score: [X/5], Score Rationale, Status (Completed / Provisional / Not Scorable).

## Output
T4.11: `Area`|`Score 1–5`|`Evidence`|`Risk Mechanic`|`Credit Implication`|`Confidence`|`Evidence ID`
+ Covenant Aggressiveness Score: [X/5]
+ Score Rationale + Status (Completed / Provisional / Not Scorable)
</step_reference>
## REF_CP-4_12_RedFlagsMonitoringTriggers.md
<!-- REF_CP-4_12 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="12" name="Red Flags and Monitoring Triggers">
<input>All provision-level analysis from Steps 3–11.</input>
<gate>Step 11 complete.</gate>

## Instructions
1. List legal and covenant red flags identified across all analytical steps.
2. For each: record Red Flag/Trigger, Provision or Signal, Why It Matters, PD/LGD/RV Impact, Monitoring Action, and Evidence ID.
3. Prioritize: provisions enabling priming, subordination, collateral leakage, value transfer, covenant erosion, or amendment without full lender consent.
4. Include observable monitoring actions: track utilization, basket drawdowns, amendment filings, compliance certificates, USub designations, asset transfers, rating actions, and borrower reporting.
5. Red flags must be provision-specific, not generic.

## Output
T4.12: `Red Flag / Trigger`|`Provision or Signal`|`Why It Matters`|`PD / LGD / RV Impact`|`Monitoring Action`|`Evidence ID`
</step_reference>
## REF_CP-4_13_GapsLedger.md
<!-- REF_CP-4_13 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="13" name="Gaps Ledger">
<input>All prior step outputs (T4.1–T4.12); cumulative gaps identified throughout workflow.</input>
<gate>Always executes.</gate>

## Instructions
1. Compile all gaps identified across Steps 1–12 into a consolidated ledger.
2. For each gap: record Gap, Missing Document/Clause/Schedule, Why It Matters, Impact on Output (which step/table/score/section is affected), and Required Follow-Up.
3. Cover gaps in: governing documents, amendments, ICA, compliance certificates, schedules/exhibits, financial inputs (CP-1), CP-3C LME output, market-norm comparators, covenant-review reports, rating agency commentary.
4. Flag gaps that prevent scoring (aggressiveness score), capacity calculation, or recovery assessment.
5. Flag gaps requiring downstream resolution (CP-4A for capacity calcs, CP-6 for debate evidence).
6. Every section marked [Insufficient Information] in Steps 1–12 must have a corresponding gap entry.

## Output
T4.13: `Gap`|`Missing Document / Clause / Schedule`|`Why It Matters`|`Impact on Output`|`Required Follow-Up`
</step_reference>
## REF_CP-4_14_OverallLegalCreditView.md
<!-- REF_CP-4_14 (T2) | 2026-06-03 -->
<step_reference module="CP-4" step="14" name="Overall Legal Credit View">
<input>All prior step outputs (T4.1–T4.13); all provision-level analysis, scores, red flags, and gaps.</input>
<gate>Always executes. Synthesis only — no new data.</gate>

## Instructions
1. Write a committee-ready narrative synthesis using this formulation:
   "Overall, [Issuer] presents a [lender-friendly / disciplined / market-standard / aggressive / highly creditor-adverse / not scorable] covenant package based on [key evidence]. The main creditor protections are [protections], while the main covenant weaknesses are [weaknesses]. The primary PD risk is [risk path], and the primary LGD / recovery risk is [risk path]. For security selection, the most important legal consideration is [provision / structural issue]. Further analysis would require [missing documents / clauses / schedules]."
2. Reference the Covenant Aggressiveness Score and key drivers.
3. Reference the top red flags and monitoring triggers.
4. Reference critical gaps.
5. Do not introduce new data, new calculations, or new assessments — synthesize only from Steps 1–13.
6. End with module completion statement:
   - "CP-4 Completed. Covenant Aggressiveness: [X/5]. Gate Status: Completed."
   - "CP-4 Completed with Limitations. Covenant Aggressiveness: [X/5 or Not Scorable]. Key Gaps: [List]."
   - "CP-4 Blocked. No executed governing document available."

## Output
Narrative synthesis (no table). Module completion statement with Aggressiveness Score and Gate Status.
</step_reference>
## REF_CP-4_AggressivenessRubric.md
<!-- REF_CP-4 AggressivenessRubric (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-4" name="Source Authority & Aggressiveness Scoring">

Authoritative for CP-4 source ranking (Step 2) and the covenant aggressiveness score (Step 11). Load alongside the CP-4 workflow.

## Source Authority Hierarchy (6 ranks)
| Rank | Source Type | Governing Role |
|------|-----------|----------------|
| 1 | Executed credit agreement / indenture (incl. amendments) | Controls all provision-level analysis |
| 2 | Executed intercreditor agreement | Controls lien priority and enforcement mechanics |
| 3 | Compliance certificates / covenant schedules | Controls tested ratios and usage |
| 4 | Offering memorandum covenant description | Summary of key provisions; verify against executed doc |
| 5 | Third-party covenant-review report | Independent assessment; verify against executed doc |
| 6 | Lender presentation / term sheet / posting memorandum | Marketing / pre-execution; lowest authority |

## Covenant Aggressiveness Rubric (1–5 Scale)
| Score | Label | Description |
|-------|-------|-------------|
| 1 | Lender-Friendly | Tight maintenance covenants, limited incurrence, narrow leakage, comprehensive collateral/guarantor, strong lender control |
| 2 | Disciplined | Maintenance present with adequate headroom, moderate incurrence subject to tests, bounded RP/investment baskets, standard protections |
| 3 | Market-Standard | Typical LBO/HY package, standard grower baskets, standard builder basket, standard collateral with some release flexibility |
| 4 | Aggressive | Cov-lite/limited maintenance, large incurrence baskets, broad leakage/USub flexibility, material EBITDA add-back inflation, weak MFN |
| 5 | Highly Creditor-Adverse | No meaningful maintenance, uncapped debt/lien capacity, priming-enabling provisions, broad asset transfer, weak/absent lender protections |

## Aggressiveness Scoring Areas (7)
| Area | What to Assess |
|------|---------------|
| Maintenance covenant architecture | Presence, type, step-down, headroom, consequence, cure |
| Debt / lien incurrence capacity | Fixed, grower, ratio, incremental, free-and-clear, MFN |
| RP / investment / leakage capacity | RP baskets, builder basket, investment capacity, USub, asset transfer |
| EBITDA definitions and add-back flexibility | Add-back caps, synergy provisions, pro forma rules, time limits |
| Collateral / guarantor protection | Coverage, release mechanics, excluded subsidiaries, non-guarantor risk |
| Amendment / control mechanics | Thresholds, sacred rights, class voting, waiver flexibility |
| Overall | Composite weighted toward highest-severity area with most material credit implication |

## Scoring Rules
- Do not score an area unless provision-level evidence supports the assessment.
- If evidence for an area is insufficient: [Not Scorable].
- Overall score is NOT a simple average — weight toward highest creditor-adverse severity and most material credit implication.
- If fewer than 3 areas scorable: overall = [Not Scorable] or [Provisional].
- Every score must include: evidence basis, risk mechanic, credit implication, and confidence level.
- Confidence levels: Completed (full executed documents + financial inputs) | Provisional (partial evidence or draft documents) | Not Scorable (insufficient evidence).

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Professional, neutral, precise, institutional, legal-risk focused, creditor-oriented, evidence-led, committee-ready, recovery-aware. Use clean Markdown tables where instructed. Use concise paragraphs and dense bullets. Use creditor language: debt capacity, lien capacity, leakage, priming, MFN, incremental facilities, USub, restricted group, guarantor coverage, collateral release, amendment risk, lender control, structural subordination, PD, LGD, recovery, relative value. A dense, accurate sentence is preferred to broad generic commentary. Target 1–5 pages per issuer scaled to complexity.

## Content Distinctions (relocated from ACTIVE_PROMPT 2026-07-11)
Documentary Fact | Analyst Interpretation | Market Comparison | PD Effect | LGD / Recovery Effect | Monitoring Implication

</reference>
## REF_CP-4_EDGARCovenantSourceMap.md
# REF_CP-4_EDGAR | EDGAR Covenant Source-Retrieval Map
# Version: 1.0 | Date: 2026-06-15
# Parent System: CP Agents — Credit Analysis Co-Pilot
# Purpose: A free, primary-source acquisition lane for covenant/legal documents via SEC EDGAR

---

## 1. Purpose

`REF_CP-4_EDGARCovenantSourceMap.md` defines how to **locate and acquire**
controlling legal documents (credit agreements, indentures, supplements,
intercreditor agreements, covenant descriptions) from **SEC EDGAR** — a free,
public, primary source requiring **no paid API or key**.

It exists to give the **Legal File Gate (Step 1, `REF_CP-4_01`)** a sourcing path
when an executed governing document is *missing*, so the gate can attempt free
acquisition before declaring **Blocked**. It does **not** replace the Covenant
Feature Register (Step 3) or the deep-dive steps (4–8) — it feeds them with
better-provenanced source material.

Works alongside:

- `REF_CP-4_01_LegalFileGateSourceQuality.md` (Step 1 — consumes this)
- `REF_CP-4_02_ControllingDocumentsSourceAuthority.md` (Step 2 — ranks what this returns)
- `REF_CP-4_03_CovenantFeatureRegister.md` (Step 3 — built from the executed text)
- `caos/docs/AGENT_SKILLS_REVIEW.md` §2–§3 (why EDGAR over a paid aggregator)

> **Provenance note:** the *filing → covenant-document* taxonomy in §3 is lifted
> from the open (MIT) Octagon SEC skill methodology. Only the **free methodology**
> is used — **not** Octagon's paid data API. The data path here is EDGAR direct,
> which is also a *primary* source and therefore higher-authority than any
> aggregator's read of it.

---

## 2. Core Principle (provenance gate)

EDGAR may **inform, bootstrap, or locate** a document, but a covenant claim is
only as good as the **executed exhibit it resolves to**:

1. A full-text **search hit** or filing-index entry, before the exhibit is pulled
   and ingested, is a **pointer only** — flagged `external · unverified`. It
   **cannot** satisfy the Step-1 BLOCKING gate and **cannot** be cited in the
   Covenant Feature Register.
2. Once the **actual exhibit document** is fetched and ingested (vault → chunks),
   it becomes an **executed primary source** with a real **E-xx Evidence ID**,
   eligible for Authority Rank 1–4 (§5) and able to clear **CP-5A / CP-5**.
3. **Never** quote a covenant term, basket, threshold, or definition from an
   EDGAR full-text *snippet* — pull and vault the exhibit, then read the clause.

This is the same gate CAOS applies everywhere: *a number with no source trace is
exactly what the platform prevents.* EDGAR satisfies it more cleanly than an
aggregator could — re-vaulting the primary document is trivial when the source
already **is** the primary document.

---

## 3. Filing → Controlling-Document Map (the taxonomy)

Where each covenant-bearing document is filed on EDGAR. Only **reporting issuers**
file (see §6 limitations).

| Controlling Document | EDGAR Exhibit | Carrier Forms | Notes |
|---|---|---|---|
| **Credit agreement** (TLA/TLB, revolver) | **Ex-10.x** (material contract) | **8-K** (Item 1.01 entry / Item 2.03 obligation), then **10-Q / 10-K** | Conformed executed copy; primary for first-lien/loan covenants |
| **Amended & restated / amendment** to a credit agreement | Ex-10.x | **8-K** (Item 1.01/2.03) | A&E, repricings, incremental joinders |
| **Indenture** (notes) | **Ex-4.x** | **8-K** (Item 1.01/2.03), **S-1 / S-4**, **10-K** | Primary for bond covenants |
| **Supplemental indenture** (new notes, amendments, guarantor accession) | Ex-4.x | **8-K** | Tracks covenant changes over time |
| **Indenture (unregistered, TIA-qualified)** | filed with the form | **Form T-3** | Common in **exchange offers / LME / restructurings** |
| **Covenant description** ("Description of Notes") | body of prospectus | **424B** (registered notes), **S-4** (A/B exchange of 144A notes) | The free EDGAR proxy for a 144A **OM** covenant section |
| **Intercreditor / collateral agency agreement** | Ex-10.x / Ex-4.x | **8-K**, S-1/S-4 | Controls lien priority & enforcement (Authority Rank 2) |
| **Security / pledge / guarantee agreement** | Ex-10.x / Ex-4.x | **8-K**, exhibits to CA/indenture | Collateral package, guarantor coverage |
| **Compliance certificate / covenant schedule** | Ex-10.x / Ex-99.x | occasionally **8-K / 10-Q** | Rarely filed; treat as Rank 3 when present |
| **Investor deck / press release** (terms summary) | Ex-99.x | **8-K** (Item 7.01/2.02) | Marketing only — Authority Rank 6 |

**Key leveraged-finance insight:** for **144A high-yield** where the offering
memorandum is *not* public, the **S-4 exchange-offer prospectus "Description of
Notes"** is the free EDGAR equivalent of the OM covenant description — and any
**registered** notes carry it in the **424B**.

---

## 4. EDGAR Retrieval Methods (free, no key)

1. **Full-text search (EFTS)** — filings 2001–present. Query the public endpoint
   `efts.sec.gov/LATEST/search-index?q="..."` (the same API the EDGAR FTS UI
   calls); filter by `forms=8-K,S-4,10-K` and date. Useful queries: issuer name +
   `"Credit Agreement"` / `"Indenture"` / `"Supplemental Indenture"` /
   `"Description of Notes"` / a known tranche name.
2. **Submissions API** — `data.sec.gov/submissions/CIK##########.json` (10-digit
   zero-padded CIK): the issuer's full filing history; filter to the carrier forms
   in §3.
3. **Company browse** — `sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=…&type=8-K`
   to list filings by type.
4. **Exhibit pull** — each filing's index at
   `sec.gov/Archives/edgar/data/{cik}/{accession}/` lists exhibits; fetch the
   specific **Ex-4.x / Ex-10.x** document, not the cover 8-K.

**Fair-access (mandatory):** send a descriptive `User-Agent` (name + contact)
and stay **≤ 10 requests/second**. No key, no cost.

---

## 5. Source-Authority Mapping (to the CP-4 6-rank hierarchy)

EDGAR documents enter the existing Step-1/Step-2 authority hierarchy **after**
they are fetched and vaulted (§2):

| EDGAR document (vaulted) | CP-4 Authority Rank |
|---|---|
| Executed credit agreement / indenture / supplemental indenture (Ex-10.x / Ex-4.x; incl. T-3 indenture) | **Rank 1** |
| Executed intercreditor agreement (Ex-10.x) | **Rank 2** |
| Compliance certificate / covenant schedule (where filed) | **Rank 3** |
| "Description of Notes" in 424B / S-4 prospectus | **Rank 4** (summary — verify against the executed indenture) |
| Investor deck / press-release terms (Ex-99.x) | **Rank 6** |

Filed exhibits are typically **conformed executed copies** (`/s/` signatures) and
are authoritative for provision-level analysis. An unfetched FTS hit has **no
rank** — it is an `external · unverified` pointer until ingested.

---

## 6. Coverage & Limitations (leveraged-finance reality)

EDGAR is a strong **free** lane for a meaningful subset of the universe — not all
of it:

- **Reporting issuers only.** The issuer must file with the SEC (registered
  securities, or reporting obligations under §15(d) / an indenture reporting
  covenant). Many LBO borrowers **do** file because their HY notes were registered
  via an A/B exchange or their documents require SEC-style reporting.
- **Pure-private gaps.** Sponsor-owned borrowers with **144A-for-life** debt (no
  registration rights) and no public reporting may **not** appear on EDGAR — and
  their **offering memoranda are generally not on EDGAR** at all.
- **Pre-2001** filings are outside EDGAR full-text search (browse still works).
- EDGAR **supplements**, never replaces, analyst-uploaded executed documents. The
  Step-1 BLOCKING rule stands: at least one **executed** governing document
  (uploaded *or* EDGAR-vaulted) must exist, or Module Status = **Blocked**.

---

## 7. Wiring (which steps consume this)

| Step | Use |
|---|---|
| **Step 1 — Legal File Gate** (`REF_CP-4_01`) | Before declaring **Blocked** for a missing governing doc, attempt the EDGAR lane (§3–§4). A vaulted exhibit can satisfy the gate; a search hit cannot. |
| **Step 2 — Controlling Documents** (`REF_CP-4_02`) | Rank EDGAR-vaulted documents via §5 and the 6-rank hierarchy. |
| **Step 3 — Covenant Feature Register** (`REF_CP-4_03`) | Populate from the executed EDGAR text with exact clause/section + E-xx Evidence ID. |
| **CP-5A / CP-5** | Validate that every EDGAR-derived covenant claim resolves to a vaulted exhibit (not a snippet) with a real E-xx; flag `external · unverified` pointers as orphan-claim candidates. |

**Implementation status:** this lane is wired, not just described. The CAOS server
exposes it at `/api/edgar/*` (`caos/server/edgar.py` + `caos/server/routes/edgar.py`)
— `search` / `filings` / `exhibits` return pointers; `vault-exhibit` fetches an
exhibit and runs it through the standard ingest path (→ E-xx eligible). An MCP
wrapper (`caos/mcp/edgar/`) surfaces the same four tools to an agent. Off until
`EDGAR_USER_AGENT` is set (SEC fair-access; no key, no cost).

---

## 8. Version History

| Version | Date | Notes |
|---|---|---|
| 1.0 | 2026-06-15 | Initial EDGAR covenant source-retrieval map. Free (no-paid-services constraint); lifts the open Octagon SEC filing→covenant taxonomy; binds it to the CP-4 6-rank authority hierarchy and the CP-5A/CP-5 provenance gate. See `caos/docs/AGENT_SKILLS_REVIEW.md`. |
## REF_CP-4_ExampleOutputPattern.md
<!-- REF_CP-4_ExampleOutputPattern.md (T2 Example Library) | 2026-06-10 | Ported from Agent Files: CP-4__SUPPORT__EXAMPLE_OUTPUT_PATTERN.txt -->


================================================================================
FILE: CP-4__SUPPORT__EXAMPLE_OUTPUT_PATTERN.txt
MODULE: CP-4 — LegalCovenantInterpreter
STATUS: UPDATED (vNext)
MECHANICAL CHANGES APPLIED: MC-1, MC-2, MC-3, MC-4, MC-5
GOVERNING CONTRACT: CP_GLOBAL_AGENT_INSTRUCTIONS_v3.2.txt
PURPOSE: Example finding format for CP-4 covenant / legal analysis.
================================================================================

EXAMPLE_OUTPUT_PATTERN

Purpose: Provide a standard finding format for CP-4 provision-level analysis.
Each material covenant finding should follow this structure.

1. Standard Finding Format

Provision: [Exact clause / section reference from governing document]
Source: [Document name | version / date | authority rank]
Summary: [What the provision permits / restricts / conditions]
Risk Mechanic: [How this affects creditor position under stress or borrower
  action]
PD Effect: [Impact on default probability, covenant pressure, operating
  flexibility, or refinancing risk]
LGD / Recovery Effect: [Impact on collateral value, claim priority, guarantor
  coverage, structural subordination, or value leakage]
Monitoring Implication: [Observable data, reporting item, legal event,
  utilization, or borrower action to track]
Credit Implication: [8-value subset label]
Confidence: [High / Medium / Low / Provisional / Not Scorable]
Evidence ID: [Trace ID]

2. Example (Illustrative Only — Do Not Use as Issuer Data)

Provision: Section 7.03(b)(iv) — Incremental Facility
Source: Credit Agreement dated [Date] | Executed | Authority Rank 1
Summary: Permits up to the greater of $200m and 100% of LTM Consolidated
  EBITDA in incremental first-lien pari debt, subject to pro forma first-lien
  net leverage ratio not exceeding 4.25x. No MFN protection after 12-month
  sunset.
Risk Mechanic: Grower basket tied to EBITDA means capacity expands with
  add-back-inflated EBITDA. MFN sunset permits repricing of incremental debt
  without economics protection for existing lenders after 12 months.
PD Effect: Moderate — capacity permits releveraging under stress if EBITDA
  add-backs inflate denominator.
LGD / Recovery Effect: High — pari secured incremental debt directly dilutes
  recovery for existing first-lien creditors.
Monitoring Implication: Track incremental facility utilization, EBITDA add-back
  trajectory, and MFN sunset date.
Credit Implication: Negative — Leverage Increase
Confidence: High
Evidence ID: [CP4-EV-001]

CREDIT IMPLICATION (8-value Legal/Covenant subset):
Positive — Covenant Headroom Expansion | Positive — Deleveraging |
Neutral — Stable | Negative — Covenant Erosion |
Negative — Leverage Increase | Negative — Refinancing Risk |
Negative — Liquidity Deterioration | Insufficient Information
## REF_CP-4_Workflow.md
<!-- REF_CP-4 Workflow (T2 support) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-4" name="Workflow — 14 Steps">

## Workflow (relocated from ACTIVE_PROMPT 2026-07-11)
| Step | Name | REF File | Output |
|------|------|----------|--------|
| 1 | Legal File Gate and Source Quality | REF_CP-4_01 | T4.1 Source Gate + Module Status |
| 2 | Controlling Documents and Source Authority | REF_CP-4_02 | T4.2 Controlling Document Register |
| 3 | Covenant Feature Register | REF_CP-4_03 | T4.3 Covenant Feature Register |
| 4 | EBITDA, Definitions, and Ratio Mechanics | REF_CP-4_04 | Provision-level analysis (narrative + findings) |
| 5 | Debt Incurrence, Incremental Facilities, and MFN | REF_CP-4_05 | Provision-level analysis (narrative + findings) |
| 6 | Leakage, Restricted Payments, Investments, and Asset Transfers | REF_CP-4_06 | Provision-level analysis (narrative + findings) |
| 7 | Collateral, Guarantees, and Structural Subordination | REF_CP-4_07 | Provision-level analysis (narrative + findings) |
| 8 | Events of Default, Remedies, and Amendment Risk | REF_CP-4_08 | Provision-level analysis (narrative + findings) |
| 9 | PD versus LGD / Recovery Translation | REF_CP-4_09 | T4.9 PD vs LGD Translation Table |
| 10 | Market Norm and Covenant Review Comparison | REF_CP-4_10 | T4.10 Market Norm Comparison Table |
| 11 | Covenant Aggressiveness Score | REF_CP-4_11 | T4.11 Aggressiveness Score Table + Composite Score |
| 12 | Red Flags and Monitoring Triggers | REF_CP-4_12 | T4.12 Red Flags Table |
| 13 | Gaps Ledger | REF_CP-4_13 | T4.13 Gaps Ledger |
| 14 | Overall Legal Credit View | REF_CP-4_14 | Narrative synthesis |

</reference>

## Binding discipline

These rules are per-module applications of the Canon Core items they cite.

**Covenant debt definition vs. canonical basis:** for the covenant/credit-agreement definition of Indebtedness (or Consolidated Total Debt) used in ratio tests, record whether it is measured on carrying value, gross principal, or a bespoke definition (e.g., excluding unamortized discount, including or excluding capitalized leases); log any divergence from the canonical carrying-value basis as a Definition Conflict Register row (both figures, both locators) (Canon Core item 5).

**Multi-figure debt amounts across documents:** where the same debt/facility amount is stated differently across governing documents (commitment amount in the credit agreement vs. outstanding amount in the most recent compliance certificate vs. amount recited in an amendment), extract ALL figures, label each with its document role and date, and log the set as ONE Conflict-Register row explaining why they differ rather than silently reconciling them (Canon Core item 6).

**Non-debt funding liabilities inside the debt-capacity tests:** where the Indebtedness / Total Debt definition used for ratio debt, free-and-clear, or grower baskets excludes material non-debt funding liabilities that fund operations (customer deposits, deferred revenue, supplier-finance / reverse-factoring programs), flag this as a capacity-relevant gap — that liability is credit-relevant float sitting outside every debt basket and ratio test, not ordinary trade payables (Canon Core item 8).
