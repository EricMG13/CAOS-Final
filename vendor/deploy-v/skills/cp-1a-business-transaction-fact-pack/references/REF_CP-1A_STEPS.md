Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-1A_BusinessFactTaxonomy.md.

Original files, in this bundle: REF_CP-1A_01_SourceBasisEstablishment.md, REF_CP-1A_02_SourceClassification.md, REF_CP-1A_03_TransactionSummary.md, REF_CP-1A_04_BusinessDescription.md, REF_CP-1A_05_OwnershipRegister.md, REF_CP-1A_06_OperatingModel.md, REF_CP-1A_07_HistoryTimeline.md, REF_CP-1A_08_CreditTranslation.md, REF_CP-1A_09_GapsLedger.md, REF_CP-1A_10_ModuleSummary.md, REF_CP-1A_BusinessFactTaxonomy.md

## REF_CP-1A_01_SourceBasisEstablishment.md
<!-- REF_CP-1A_01_SourceBasisEstablishment (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1A" step="01" name="SourceBasisEstablishment">
Identify all source materials. Record: name, type, date, issuer relevance, period, evidence tier. Assess sufficiency per section. Flag limitations. Gate: no sources -> BLOCKED.
</step_reference>
## REF_CP-1A_02_SourceClassification.md
<!-- REF_CP-1A_02_SourceClassification (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1A" step="02" name="SourceClassification">
Classify sources: transaction doc, FS, lender/sponsor pres, rating, mgmt commentary, regulatory, internal, external, other. Assign quality tier. Output: source_classification table.
</step_reference>
## REF_CP-1A_03_TransactionSummary.md
<!-- REF_CP-1A_03_TransactionSummary (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1A" step="03" name="TransactionSummary">
Structured summary: type (LBO/refi/recap/add-on/acq/IPO/other), date, borrower, sponsor, target, size, facilities, use of proceeds, structure, maturity, conditions. Each element cited. Gate: no txn sources >= Secondary-Reputable -> skip.
</step_reference>
## REF_CP-1A_04_BusinessDescription.md
<!-- REF_CP-1A_04_BusinessDescription (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1A" step="04" name="BusinessDescription">
Credit-focused: what issuer does, products/services, revenue model, end-markets, customers, geography, competitive position, regulatory, operational dependencies, business-model risks. Five-category separation. Gate: no biz sources -> skip.
</step_reference>
## REF_CP-1A_05_OwnershipRegister.md
<!-- REF_CP-1A_05_OwnershipRegister (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1A" step="05" name="OwnershipRegister">
Ownership structure, sponsor identity/history, changes, acquisitions, equity transactions, minorities, management participation, creditor alignment. Each cited. Gate: no ownership sources -> skip.
</step_reference>
## REF_CP-1A_06_OperatingModel.md
<!-- REF_CP-1A_06_OperatingModel (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1A" step="06" name="OperatingModel">
Revenue drivers/mix, cost structure, margin mechanics, capex, WC, cash conversion, seasonality, KPIs. Connect each to credit implication. Flag CP-2/CP-2C gaps. Gate: no op data -> flag, continue.
</step_reference>
## REF_CP-1A_07_HistoryTimeline.md
<!-- REF_CP-1A_07_HistoryTimeline (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1A" step="07" name="HistoryTimeline">
Timeline of credit events: founding, acquisitions, ownership changes, restructurings, refinancings, covenant events, defaults, rating changes, regulatory. Dated + cited. Gate: no events -> skip.
</step_reference>
## REF_CP-1A_08_CreditTranslation.md
<!-- REF_CP-1A_08_CreditTranslation (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1A" step="08" name="CreditTranslation">
Synthesize Steps 3-7: Revenue Durability, Margin/CF Risk, Concentration Risk, Sponsor Alignment, Key Uncertainties. Analytical chain required. No new evidence. Gate: all prior insufficient -> skip.
</step_reference>
## REF_CP-1A_09_GapsLedger.md
<!-- REF_CP-1A_09_GapsLedger (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1A" step="09" name="GapsLedger">
All gaps + limitations + unresolved conflicts. Per gap: description, section, source limitation, downstream impact, severity, remediation. Plus Conflict Log. Always executes.
</step_reference>
## REF_CP-1A_10_ModuleSummary.md
<!-- REF_CP-1A_10_ModuleSummary (Tier 2) | 2026-06-02 -->
<step_reference module="CP-1A" step="10" name="ModuleSummary">
Module summary: issuer scope, txn context, 3-5 credit-relevant characteristics,
material gaps, downstream readiness per consumer (CP-2, CP-2C, CP-MODEL).
Always executes.

Append this stable table on every run:

`<!-- table-id: cp1a.cp_model_snapshot_fields -->`

Columns:
`field_id | value | status | source_id | source_locator | as_of`

Emit exactly one `READY` row for each field ID:

- `issuer_name`
- `sector`
- `country`
- `shareholders`
- `transaction_summary`
- `business_description`

Use concise plain text suitable for direct workbook display. `country` is the
issuer country description already established in CP-1A; it is not a
Bloomberg country code. Do not emit ticker/FIGI fields. Every value requires a
source ID, precise locator and ISO as-of date. A missing row blocks CP-MODEL.
</step_reference>
## REF_CP-1A_BusinessFactTaxonomy.md
<!-- REF_CP-1A_BusinessFactTaxonomy (T2 Library) | 2026-06-20 | Restored from CP-1A_BusinessTransactionFactPack__Role_Scope_and_Analytical_Standard §Business-Fact Taxonomy + Core Analytical Standard -->
<library_reference module="CP-1A" name="Business-Fact Taxonomy and Credit-Relevance Mapping">
<consumers>REF_CP-1A_03 (Transaction Summary); REF_CP-1A_04 (Business Description); REF_CP-1A_05 (Ownership Register); REF_CP-1A_06 (Operating Model); REF_CP-1A_07 (History/Timeline); REF_CP-1A_08 (Credit Translation)</consumers>

# CP-1A Business-Fact Taxonomy

Each numbered step captures facts in one or more fact areas. This library defines, per area, the
source-supported facts to capture **and why each matters for credit** — so every extracted fact is
translated to a creditor dimension, never left as a neutral description.

## Fact Area → Capture → Credit Relevance

| Fact Area | Source-Supported Facts to Capture | Credit Relevance |
|---|---|---|
| **Business Description** (Step 04) | Core activities, products, services, end markets, geography, customers, revenue model | Cash-flow visibility, business risk, refinancing confidence |
| **Transaction Context** (Step 03) | Transaction type, buyer/seller/sponsor, use of proceeds, sources and uses, purchase price, valuation, debt raised, pro forma leverage, liquidity impact | Leverage tolerance, liquidity, refinancing capacity, sponsor alignment, PD / LGD |
| **Ownership / Sponsor** (Step 05) | Current owner, prior ownership, sponsor history, ownership percentage, control rights, dividend-recap history | Governance risk, creditor alignment, debt-funded distribution risk |
| **Operating Model** (Step 06) | Revenue streams, pricing, volume drivers, cost structure, fixed/variable cost mix, capex, working capital | Revenue durability, margin resilience, FCF conversion, downside sensitivity |
| **Timeline** (Step 07) | Founding, acquisitions, disposals, ownership changes, refinancings, carve-outs, strategic shifts | Business evolution, event risk, leverage history, monitoring focus |
| **Gaps / Conflicts** (Step 09) | Missing transaction source, missing revenue mix, missing customer concentration, conflicting descriptions | Limits committee readiness and downstream modules |

## Evidence → Risk Mechanic → Credit Implication (expanded for CP-1A)

- **Evidence** — a specific source file, document clause, transaction table, company-description
  statement, financial figure, ownership disclosure, operating metric, revenue mix, cost item, or
  factual source statement.
- **Risk Mechanic** — how that evidence affects business risk, revenue visibility, margin resilience,
  operating leverage, FCF durability, liquidity, refinancing capacity, governance risk, sponsor
  alignment, PD, LGD, or downstream credit work.
- **Credit Implication** — the impact on PD, LGD, liquidity, debt service capacity, FCF durability,
  leverage tolerance, refinancing capacity, recovery prospects, monitoring posture, committee
  readiness, or relative value.

## Capture Discipline
- Every captured fact in Steps 03–07 must carry its credit relevance (the third column), or be marked
  `[Insufficient Information]` with the specific missing datapoint and why it matters.
- Do **not** fabricate LBO entry multiples, valuation, sources and uses, sponsor economics, ownership
  percentages, purchase price, leverage, maturity profile, debt quantum, revenue mix, customer
  concentration, operating KPIs, ownership dates, or transaction terms.
- Do not silently harmonize source-defined operating/financial metrics with CP-1. If definitions
  differ, show both and log the comparability issue for CP-2.
</library_reference>
