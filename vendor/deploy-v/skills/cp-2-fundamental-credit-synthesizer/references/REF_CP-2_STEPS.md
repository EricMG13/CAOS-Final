Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-2_Discipline.md, REF_CP-2_Frameworks.md, REF_CP-2_Workflow.md.

Original files, in this bundle: REF_CP-2_01_SourceGateReadiness.md, REF_CP-2_02-04_BusinessAndOperatingModel.md, REF_CP-2_05_MarketFrameworks.md, REF_CP-2_06_KeyStrengthsWeaknesses.md, REF_CP-2_07_FinancialProfileCreditQuality.md, REF_CP-2_08_OutlookTailwindsHeadwinds.md, REF_CP-2_09_QualitativeDownsideScenario.md, REF_CP-2_10_MaterialityFilter.md, REF_CP-2_11_IssuerMatrix.md, REF_CP-2_12_MonitoringTriggers.md, REF_CP-2_13_OverallCreditView.md, REF_CP-2_Discipline.md, REF_CP-2_Frameworks.md, REF_CP-2_Workflow.md

## REF_CP-2_01_SourceGateReadiness.md
<!-- REF_CP-2_01 (T2) | 2026-06-03 -->
<step_reference module="CP-2" step="01" name="Source Gate and Readiness">
<input>Uploaded files, CP-0 registry, CP-1/CP-1A/CP-1B/CP-1C outputs (if available)</input>
<gate>Always executes. Determines module status: Full Run / Ready with Limitations / Blocked.</gate>

## Instructions
Confirm available sources, source quality, issuer entity keys, reporting periods, and capital-structure data. Assess each source for quality, period coverage, entity coverage, data supplied, limitations, and downstream use.

Build a source register. State module status:
- **Full Run:** All gating sources available.
- **Ready with Limitations:** Partial sources — proceed with gap logging.
- **Blocked:** Missing gating evidence — stop after identifying gaps.

If blocked, stop after the blocked message.

## Output
**Source Register:** `source_document_id`|`source_document_name`|`source_quality`|`period`|`entity_covered`|`data_supplied`|`limitation`|`downstream_use`
**Module Status:** Full Run / Ready with Limitations / Blocked
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-2_02-04_BusinessAndOperatingModel.md
<!-- REF_CP-2_02-04 (T2) | 2026-06-03 -->
<step_reference module="CP-2" step="02" name="Company Description">
<input>Source register from Step 1; uploaded files; CP-1A business/transaction summary</input>
<gate>Step 1 complete.</gate>

## Instructions
Provide a credit-relevant description of the issuer. Cover only facts relevant to credit quality: core activities, products/services, customer base, end-markets, geography, revenue model, operating history, acquisitions/disposals/restructurings/carve-outs/strategic shifts, revenue visibility, customer stickiness, product/service criticality, cyclicality, concentration, regulation, and cash-generation durability.

**Required credit linkage:** Explain how the business model supports or weakens cash-flow visibility, debt service capacity, liquidity preservation, and refinancing confidence.

## Output
Narrative: Credit-relevant issuer description with explicit credit linkage.
</step_reference>

<step_reference module="CP-2" step="03" name="Ownership & Group Structure">
<input>Source register from Step 1; uploaded files; CP-1A</input>
<gate>Step 2 complete. If unavailable, state: [Insufficient Information] Ownership and group-structure details are not available in the provided materials.</gate>

## Instructions
Assess ownership, group structure, sponsor/parent/shareholder behavior, and financial-policy implications where source-supported. Cover: public/private/sponsor-backed/founder-led/family-owned/sovereign-backed/subsidiary status, sponsor identity, LBOs, take-privates, recaps, dividend recaps, IPOs, carve-outs, mergers, exits, restructurings, holding-company structure, restricted/unrestricted groups, structurally senior debt, material subsidiaries, leverage tolerance, dividends, M&A appetite, governance, transparency, and creditor alignment.

## Output
Narrative: Ownership/governance assessment with credit implications.
</step_reference>

<step_reference module="CP-2" step="04A" name="Revenue Drivers and Pricing Power">
<input>Steps 1-3 outputs; CP-1B earnings data; uploaded financials</input>
<gate>Step 3 complete.</gate>

## Instructions
Assess volume drivers, price/mix, recurring vs transactional revenue, contract duration, renewal rates/churn, customer concentration, switching costs, product/service criticality, pass-through mechanisms, and macro/sector/commodity/regulatory/budget/substitution sensitivity.

State whether revenue is predictable, recurring, cyclical, discretionary, concentrated, regulated, exposed to substitution, or structurally declining.

Apply [Evidence] → [Risk Mechanic] → [Credit Implication] for each material finding.

## Output
Narrative: Revenue durability assessment with credit linkage.
</step_reference>

<step_reference module="CP-2" step="04B" name="Cost Structure and Margin Resilience">
<input>Steps 1-4A outputs; CP-1B earnings data; uploaded financials</input>
<gate>Step 4A complete.</gate>

## Instructions
Assess fixed vs variable costs, labour intensity, raw materials/inputs, energy, logistics, freight, technology/hosting/cloud, sales and marketing, procurement, operating leverage, downside cost flexibility, input-cost volatility, and pass-through mechanisms.

State whether margins can be defended under volume pressure, cost inflation, wage inflation, input shocks, adverse mix, or operating deleverage.

## Output
Narrative: Margin resilience assessment with credit linkage.
</step_reference>

<step_reference module="CP-2" step="04C" name="Capital Intensity and FCF Conversion">
<input>Steps 1-4B outputs; CP-1B earnings data; uploaded financials</input>
<gate>Step 4B complete.</gate>

## Instructions
Assess maintenance capex, growth capex, capitalized R&D, working capital, leases, restructuring/integration cash costs, cash taxes, cash interest, seasonality, EBITDA-to-FCF conversion, and capex flexibility over the debt maturity wall.

State whether EBITDA translates into durable FCF available for debt service, deleveraging, liquidity preservation, and refinancing support.

## Output
Narrative: FCF conversion assessment with credit linkage.
</step_reference>
## REF_CP-2_05_MarketFrameworks.md
<!-- REF_CP-2_05 (T2) | 2026-06-03 -->
<step_reference module="CP-2" step="05A" name="Porter's Five Forces">
<input>Steps 1-4C outputs; CP-1A business summary; uploaded sources</input>
<gate>Step 4C complete.</gate>

## Instructions
Assess each force only to the extent it affects PD, LGD, liquidity, margin durability, FCF, recovery, or refinancing capacity. Use [Evidence] → [Risk Mechanic] → [Credit Implication] for each material force. Do not restate prior sections.

Cover: Competitive Rivalry; Threat of New Entrants; Threat of Substitutes; Buyer Power; Supplier Power.

## Output
Narrative: Porter's Five Forces — credit-translated, per-force assessment.
</step_reference>

<step_reference module="CP-2" step="05B" name="PEST Analysis">
<input>Steps 1-5A outputs; uploaded sources</input>
<gate>Conditional — Run only if macro, FX, regulation, policy, country, social, or technology factors materially alter PD, LGD, liquidity, FCF, or refinancing capacity. If immaterial, write: "PEST factors do not appear to be a primary credit driver based on the provided materials."</gate>

## Instructions
If material, cover only relevant categories: Political/Regulatory; Economic; Social; Technological. Each category must connect to credit quality via [Evidence] → [Risk Mechanic] → [Credit Implication].

## Output
Narrative: PEST credit translation (material categories only) or skip statement.
</step_reference>

<step_reference module="CP-2" step="05C" name="SWOT Analysis">
<input>Steps 1-5B outputs</input>
<gate>Step 5A complete (5B may have been skipped).</gate>

## Instructions
Provide a concise SWOT translated into credit terms:
- **Strengths:** 3-5 credit-supportive factors.
- **Weaknesses:** 3-5 credit constraints.
- **Opportunities:** Only factors that could improve credit quality.
- **Threats:** Only factors that could weaken credit quality.

## Output
Narrative: Credit-translated SWOT (4 quadrants, 3-5 items each).
</step_reference>
## REF_CP-2_06_KeyStrengthsWeaknesses.md
<!-- REF_CP-2_06 (T2) | 2026-06-03 -->
<step_reference module="CP-2" step="06" name="Key Strengths & Weaknesses Summary">
<input>Steps 1-5C outputs</input>
<gate>Step 5C complete.</gate>

## Instructions
Provide the top 1-5 credit strengths and top 1-5 credit weaknesses.

Format:
- **[Strength]:** [Evidence] → [Risk Mechanic] → [Credit Implication].
- **[Weakness]:** [Evidence] → [Risk Mechanic] → [Credit Implication].

## Output
Narrative: Ranked strengths/weaknesses with analytical chain per item.

Append on every run:

`<!-- table-id: cp2.cp_model_strengths_weaknesses -->`

Columns:
`direction | rank | label | mechanism | evidence_ids | status | source_id | source_locator | as_of`

Emit one to five `STRENGTH` rows and one to five `WEAKNESS` rows. Rank each
direction independently from 1 with no duplicates. `status` is `READY`.
`mechanism` compresses the evidence-to-credit implication chain for workbook
display. Every row requires evidence IDs, source ID, precise locator and ISO
as-of date.
</step_reference>
## REF_CP-2_07_FinancialProfileCreditQuality.md
<!-- REF_CP-2_07 (T2) | 2026-06-03 -->
<step_reference module="CP-2" step="07" name="Financial Profile & Credit Quality Assessment">
<input>Steps 1-6 outputs; CP-1B financial data; uploaded financials</input>
<gate>Step 6 complete.</gate>

## Instructions
Evaluate issuer financial durability using a ratings-style lens. Complete the 9-dimension Financial Profile table (permitted Assessment values per Active Prompt: Strong / Average / Weak / Not Assessable). For each dimension provide Assessment + Credit Rationale grounded in the dimension-specific factors below:

| Dimension | Credit Rationale must consider |
|---|---|
| Scale / market position | Revenue scale, market relevance, market share if available, competitive standing, shock absorption |
| Competitive advantage | Moat, differentiation, switching costs, retention, IP, brand, contracts, regulation, network effects, execution |
| Business diversification | Product, customer, end-market, geography, channel, supplier, contract diversification |
| Cost and capex flexibility | Fixed-cost burden, input-cost exposure, maintenance capex, growth capex, working capital, cash preservation |
| Margin stability | Pricing power, pass-through, volatility, operating leverage, input costs, integration / restructuring risk |
| Free cash flow stability | EBITDA-to-FCF conversion, interest, taxes, capex, working capital, restructuring, dividends, recurring leakage |
| Ability to refinance / access capital markets | Maturity profile, market access, ratings trajectory if available, sponsor / parent support, lender appetite, market-window sensitivity |
| Liquidity position | Cash, revolver availability, covenant headroom, near-term maturities, working-capital needs, seasonality, cash burn |
| Financial policy and governance | Leverage tolerance, dividend policy, M&A appetite, sponsor behavior, governance, reporting transparency, creditor alignment |

After the table, synthesize: main credit supports, constraints, trend, and key missing datapoints.

If detailed financial data is unavailable, state: "Financial profile assessment is qualitative because detailed financial data is not available in the provided materials."

## Output
**T2.7 Financial Profile Scorecard:** `Dimension`|`Assessment`|`Credit Rationale`
Narrative: Synthesis of credit supports, constraints, trend, missing data.
</step_reference>
## REF_CP-2_08_OutlookTailwindsHeadwinds.md
<!-- REF_CP-2_08 (T2) | 2026-06-03 -->
<step_reference module="CP-2" step="08" name="Outlook, Tailwinds & Headwinds">
<input>Steps 1-7 outputs; uploaded sources</input>
<gate>Step 7 complete.</gate>

## Instructions
Assess:
- Short-term outlook: 12-24 months.
- Medium-term outlook: 3-5 years.
- Sector tailwinds / headwinds.
- Company-specific tailwinds / headwinds.

For each material item, explain whether it supports or pressures revenue, margin resilience, cash-flow visibility, liquidity, deleveraging, refinancing confidence, PD, LGD, recovery, or monitoring posture.

## Output
Narrative: Structured outlook with credit implications per tailwind/headwind.
</step_reference>
## REF_CP-2_09_QualitativeDownsideScenario.md
<!-- REF_CP-2_09 (T2) | 2026-06-03 -->
<step_reference module="CP-2" step="09" name="Qualitative Downside / Stress Scenario">
<input>Steps 1-8 outputs</input>
<gate>Step 8 complete.</gate>

## Instructions
Provide one realistic downside scenario tailored to the issuer's sector and capital structure. Explain: operational event, revenue effect, margin effect, FCF effect, liquidity effect, leverage/refinancing effect, management levers, and whether resilience appears sufficient to avoid liquidity distress.

Do not assume default risk unless supported by evidence. Do not produce a generic recession scenario — the downside must be issuer-specific and source-supported.

## Output
Narrative: Issuer-specific downside scenario with causal transmission chain.
</step_reference>
## REF_CP-2_10_MaterialityFilter.md
<!-- REF_CP-2_10 (T2) | 2026-06-03 -->
<step_reference module="CP-2" step="10" name="Materiality Filter">
<input>Steps 1-9 outputs</input>
<gate>Step 9 complete.</gate>

## Instructions
Rank the most important PD, LGD, liquidity, refinancing, or relative-value drivers. Prioritize drivers material to default probability, recovery value, maturity-wall risk, refinancing access, liquidity runway, or downside-case formation.

## Output
**T2.10 Materiality Filter:** `Rank`|`Driver`|`Evidence`|`Risk Mechanic`|`Credit Implication`|`Direction`|`Confidence`
- Direction: Positive / Negative / Mixed
- Confidence: High / Medium / Low / Not Assessable
</step_reference>
## REF_CP-2_11_IssuerMatrix.md
<!-- REF_CP-2_11 (T2) | 2026-06-03 -->
<step_reference module="CP-2" step="11" name="Issuer Matrix">
<input>Steps 1-10 outputs</input>
<gate>Step 10 complete.</gate>

## Instructions
Assess 6 business quality factors using the Issuer Matrix table. For each factor provide Assessment, Primary Downside Path, and Credit Relevance.

Conclude with: Primary downside path: [one concise sentence].

## Output
**T2.11 Issuer Matrix:** `Business Quality Factor`|`Assessment`|`Primary Downside Path`|`Credit Relevance`
Factors: Revenue durability, Margin resilience, FCF conversion, Liquidity buffer, Refinancing capacity, Governance / financial policy.
Assessment: Strong / Average / Weak / Not Assessable.
</step_reference>
## REF_CP-2_12_MonitoringTriggers.md
<!-- REF_CP-2_12 (T2) | 2026-06-03 -->
<step_reference module="CP-2" step="12" name="Monitoring Triggers">
<input>Steps 1-11 outputs</input>
<gate>Step 11 complete.</gate>

## Instructions
Generate specific, observable monitoring triggers. Use quantitative thresholds only if source-supported. If thresholds are unsupported, state: "Quantitative threshold not available in provided materials."

## Output
**T2.12 Monitoring Triggers:** `Trigger`|`Threshold / Signal`|`Why It Matters`|`Credit Impact`|`Source / Limitation`
Standard rows: Revenue decline, EBITDA margin pressure, FCF deterioration, Liquidity reduction, Leverage increase, Refinancing delay, Sponsor/shareholder action, Sector deterioration.
</step_reference>
## REF_CP-2_13_OverallCreditView.md
<!-- REF_CP-2_13 (T2) | 2026-06-03 -->
<step_reference module="CP-2" step="13" name="Overall Credit View">
<input>Steps 1-12 outputs</input>
<gate>Always executes. Synthesis only — no new data.</gate>

## Instructions
End with a concise overall credit view answering: primary credit strengths, primary credit constraints, business profile vs typical leveraged-credit issuers in the sector, financial profile trend, primary downside path, key refinancing risks, and information needed for a more definitive credit opinion.

Use formulation: "Overall, [Issuer] presents a [strong/adequate/weak/not fully assessable] business profile supported by [key strengths], but credit quality is constrained by [key weaknesses]. Cash-flow durability appears [strong/adequate/weak/not fully assessable] due to [reasons]. Refinancing capacity is likely to depend on [factors]. The primary downside path is [risk path]. Further analysis would require [missing data]."

End with: CP-2 Completed. Top Risk: [Risk].

## Output
Narrative: Overall credit view synthesis. No new data — synthesis of Steps 1-12 only.
</step_reference>
## REF_CP-2_Discipline.md
<!-- REF_CP-2 Discipline (T2 support) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-2" name="Prohibited Behaviors — Full Binding List">

Authoritative complete Prohibited Behaviors list for CP-2. The 4 highest-risk items remain inline in ACTIVE_PROMPT; this is the full binding list — all 9 items bind regardless of inline/relocated status.

## Prohibited Behaviors (relocated from ACTIVE_PROMPT 2026-07-11)
1. Do not fabricate financial metrics, leverage, liquidity, maturity profiles, covenant headroom, customer concentration, ownership details, market share, ratings-agency views, or sponsor behavior.
2. Do not assign a formal rating unless explicitly instructed.
3. Do not assign final relative-value labels unless imported from CP-3 / CP-3A or dated market data and clearly identified.
4. Do not use equity-upside framing, TAM-based optimism, or generic consultant language unless directly tied to issuer-specific evidence and credit mechanics.
5. Do not use generic adjectives ("market-leading," "robust," "strong," "resilient," "diversified," "ample," "cheap," "rich") unless immediately supported by issuer-specific evidence and credit implication.
6. Do not perform full legal/covenant basket analysis, formal recovery waterfall, standalone relative-value recommendation, portfolio position-sizing, employee/individual performance assessment, equity valuation thesis, or legal advice. Hand off to appropriate downstream module.
7. Do not cite a source for a claim that is not explicitly supported by that source.
8. Do not reconcile conflicting sources silently — log the conflict.
9. Remove any paragraph that does not directly support a credit conclusion.

</reference>
## REF_CP-2_Frameworks.md
<!-- REF_CP-2 Frameworks (T2 support) | 2026-06-22 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-2" name="Credit-Translated Analytical Frameworks">

Authoritative for CP-2 framework steps (5A Porter, 5B PEST, 5C SWOT) and the credit mechanism map. Load alongside the CP-2 workflow.

## Analytical Frameworks
- **Porter's Five Forces:** Assess each force only to extent it affects PD, LGD, liquidity, margin durability, FCF, recovery, or refinancing capacity.
- **PEST:** Run only if macro/FX/regulation/policy/country/social/technology factors materially alter PD, LGD, liquidity, FCF, or refinancing capacity. If immaterial, skip with statement.
- **SWOT:** Credit-translated only — strengths/weaknesses as credit-supportive/constraining factors; opportunities/threats only as credit-quality improvers/weakeners.
- **Credit Mechanism Map:** Evidence → Risk Mechanic → Credit Implication chain for each material conclusion.

## Style (relocated from ACTIVE_PROMPT 2026-07-11)
Professional, neutral, detailed, institutional, ratings-style, creditor-first, evidence-led, committee-ready. 1–5 pages per issuer scaled to source quality and complexity. Clean Excel-ready Markdown tables where instructed; detailed paragraphs and dense bullets for narrative. **Default = compact** (Prohibited Behavior #9 applies: cut any paragraph that does not support a credit conclusion).

## Deep Synthesis Mode (relocated from ACTIVE_PROMPT 2026-07-11)
Trigger only when the user explicitly asks for a "full thesis", "committee memo", "deep synthesis", or "long-form" credit view. Every invocation is already a full run, so these phrases govern only Deep Synthesis: a "committee memo" request is a full run with Deep Synthesis ON. When ON: relax the page budget and write full narrative prose for Company Description, Operating Model, Downside Scenario, and Overall Credit View (Evidence → Risk Mechanic → Credit Implication throughout); keep all tables/registers. Prohibited Behavior #9 still bars filler — more length must mean more sourced analysis, not padding. When OFF (default), keep the compact 1–5 page form.

</reference>
## REF_CP-2_Workflow.md
<!-- REF_CP-2 Workflow (T2 support) | 2026-07-11 | extracted from ACTIVE_PROMPT for the 8000-char cap (SEC8) -->
<reference module="CP-2" name="Workflow — 18 Steps">

Authoritative full step table for the CP-2 workflow. Load alongside the CP-2 module for step-by-step execution.

## Workflow — 18 Steps (relocated from ACTIVE_PROMPT 2026-07-11)
| Step | Name | REF File | Output |
|------|------|----------|--------|
| 1 | Source Gate and Readiness | REF_CP-2_01 | Source register, module status |
| 2 | Company Description | REF_CP-2_02 | Credit-relevant issuer description |
| 3 | Ownership & Group Structure | REF_CP-2_03 | Ownership/governance assessment |
| 4A | Revenue Drivers and Pricing Power | REF_CP-2_04A | Revenue durability assessment |
| 4B | Cost Structure and Margin Resilience | REF_CP-2_04B | Margin resilience assessment |
| 4C | Capital Intensity and FCF Conversion | REF_CP-2_04C | FCF conversion assessment |
| 5A | Porter's Five Forces | REF_CP-2_05A | Porter credit translation |
| 5B | PEST Analysis | REF_CP-2_05B | PEST credit translation (if material) |
| 5C | SWOT Analysis | REF_CP-2_05C | Credit-translated SWOT |
| 6 | Key Strengths & Weaknesses Summary | REF_CP-2_06 | Top 1–5 strengths / 1–5 weaknesses |
| 7 | Financial Profile & Credit Quality | REF_CP-2_07 | 9-dimension scorecard + synthesis |
| 8 | Outlook, Tailwinds & Headwinds | REF_CP-2_08 | Short/medium-term outlook |
| 9 | Qualitative Downside / Stress Scenario | REF_CP-2_09 | Issuer-specific downside scenario |
| 10 | Materiality Filter | REF_CP-2_10 | Ranked PD/LGD/liquidity/refi drivers |
| 11 | Issuer Matrix | REF_CP-2_11 | 6-dimension quality matrix |
| 12 | Monitoring Triggers | REF_CP-2_12 | Observable trigger table |
| 13 | Overall Credit View | REF_CP-2_13 | Synthesis narrative — no new data |

</reference>
