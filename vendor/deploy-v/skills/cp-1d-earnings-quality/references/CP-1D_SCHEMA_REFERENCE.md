# CP-1D — Schema Reference

Governed output sections, register columns and the QA checklist for CP-1D
EarningsQuality.

## Canonical sections
`## Audit Summary` · `## Analysis` · `## Evidence Trace` · `## Source Registry` ·
`## Gaps & Conflicts` · `## QA Validation`

## Registers

| ID | Name | Columns |
|---|---|---|
| T1D.1 | Add-Back Register | Add-Back ID; Description; Amount; Period; Category; Source / Locator; Management Rationale; Evidence ID |
| T1D.2 | Achievability Assessment | Add-Back ID; Achievability Basis; Actions Taken To Date; Run-Rate Claimed; Realized To Date; Time To Realize; Evidence Quality; Countervailing Evidence; Assessment; Evidence ID |
| T1D.3 | Recurrence Test | Add-Back ID; Claimed Non-Recurring; Prior Occurrences (periods); Recurrence Pattern; Verdict; Risk Mechanic; Credit Implication; Evidence ID |
| T1D.4 | Quality-Adjusted EBITDA Bridge | Step; Amount; Basis; Supported / Challenged / Rejected; Cumulative EBITDA; Evidence ID |
| T1D.5 | Cash Conversion Test | Period; Adjusted EBITDA; CFO; Conversion %; Gap; Explanation; Risk Mechanic; Credit Implication; Evidence ID |
| T1D.6 | Leverage Sensitivity | Metric; On Reported EBITDA; On Adjusted EBITDA; On Quality-Adjusted EBITDA; Delta (turns); Credit Implication; Evidence ID |
| T1D.7 | Gaps Ledger | Gap; Missing Data; Why It Matters; Impact on Output; Required Follow-Up |

## Closed value sets

- **Category** (T1D.1): `Cost-Out` | `Synergy` | `One-Off Cost` | `Pro-Forma Run-Rate` |
  `Accounting Normalization` | `Other`
- **Assessment** (T1D.2) and **Supported / Challenged / Rejected** (T1D.4):
  `Supported` | `Challenged` | `Rejected` | `Insufficient Information`
- **Verdict** (T1D.3): `Non-Recurring Confirmed` | `Recurring` | `Insufficient Information`

## QA checklist
- [ ] Every add-back in CP-1's `cp1.adjusted_ebitda_bridge` appears in T1D.1
- [ ] No figure re-extracted or restated from CP-1 / CP-1B
- [ ] `Supported` cites evidence of action taken, not of intention
- [ ] Recurrence verdicts name the prior periods examined
- [ ] T1D.4 cumulative column reconciles step by step
- [ ] Leverage restated on all three EBITDA bases in T1D.6
- [ ] Quality-adjusted EBITDA never presented as reported or covenant EBITDA
- [ ] Unresolved add-backs carried in T1D.7, not silently accepted or rejected
- [ ] Numeric Confidence Score (0-100) + band per `CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`
- [ ] Null never converted to zero
